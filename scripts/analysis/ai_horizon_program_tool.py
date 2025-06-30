#!/usr/bin/env python3
"""
AI-Horizon PROGRAM Tool
Takes FORECAST findings and creates educational resource repositories.

This tool bridges the gap between research findings and actionable education by:
1. Analyzing FORECAST findings from category narratives
2. Generating targeted Perplexity searches for educational content
3. Curating and rating educational resources  
4. Creating public-facing resource pages
5. Maintaining separate lists for free vs paid/restricted resources

Focus Areas: NEW TASKS, HUMAN-ONLY, AUGMENT categories for career development

RESILIENCE DESIGN:
- Independent operation: Can run without breaking main system
- Graceful degradation: Continues with available data if components fail
- Error isolation: Individual failures don't cascade
- Optional dependencies: Functions with minimal requirements
"""

import sys
import os
import json
import requests
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
from urllib.parse import urlparse

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Core imports (required)
try:
    from aih.utils.database import DatabaseManager
    from aih.utils.logging import get_logger
    from aih.config import settings
    CORE_DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    print(f"WARNING: Core dependencies unavailable: {e}")
    CORE_DEPENDENCIES_AVAILABLE = False

# Optional imports (graceful degradation)
try:
    from aih.gather.perplexity import PerplexityConnector
    PERPLEXITY_AVAILABLE = True
except ImportError:
    PERPLEXITY_AVAILABLE = False

logger = get_logger(__name__) if CORE_DEPENDENCIES_AVAILABLE else None

# Configuration flags for resilience
PROGRAM_CONFIG = {
    'ENABLE_PERPLEXITY_SEARCH': PERPLEXITY_AVAILABLE and hasattr(settings, 'perplexity_api_key') and settings.perplexity_api_key,
    'FALLBACK_MODE': not CORE_DEPENDENCIES_AVAILABLE,
    'MAX_LEARNING_NEEDS_PER_CATEGORY': 10,
    'ENABLE_RESOURCE_DISCOVERY': True,
    'SAFE_MODE': True  # Extra error checking
}

class CircuitBreaker:
    """Circuit breaker pattern for component failure isolation."""
    
    def __init__(self, failure_threshold: int = 3, recovery_timeout: int = 300):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self.state == 'OPEN':
            if self._should_attempt_reset():
                self.state = 'HALF_OPEN'
            else:
                raise Exception("Circuit breaker is OPEN - component temporarily disabled")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if not self.last_failure_time:
            return True
        return (datetime.now() - self.last_failure_time).seconds >= self.recovery_timeout
    
    def _on_success(self):
        """Reset circuit breaker on successful call."""
        self.failure_count = 0
        self.state = 'CLOSED'
        self.last_failure_time = None
    
    def _on_failure(self):
        """Handle failure - increment counter and potentially open circuit."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'

@dataclass
class EducationalResource:
    """Educational resource data structure."""
    title: str
    url: str
    resource_type: str  # 'course', 'tutorial', 'video', 'documentation', 'tool', 'article'
    access_type: str    # 'free', 'paid', 'login_required', 'restricted'
    platform: str       # 'youtube', 'coursera', 'github', 'university', 'vendor', 'blog'
    description: str
    skills_covered: List[str]
    target_audience: str  # 'beginner', 'intermediate', 'advanced', 'all_levels'
    quality_score: float  # 0-1 rating from AI assessment
    evidence_snippets: List[str]
    source_category: str  # 'new_tasks', 'human_only', 'augment'
    discovery_method: str # 'perplexity_auto', 'manual_entry', 'curator_added'
    collected_at: str
    metadata: Dict[str, Any]

@dataclass
class ResourceSearchPrompt:
    """Structured search prompt for resource discovery."""
    category: str
    skill_area: str
    search_query: str
    target_resources: List[str]
    expected_platforms: List[str]

class AIHorizonProgramTool:
    """
    Main PROGRAM component for AI-Horizon educational resource generation.
    """
    
    def __init__(self):
        # Initialize with resilience patterns
        if PROGRAM_CONFIG['FALLBACK_MODE']:
            raise Exception("PROGRAM tool requires core dependencies - running in fallback mode")
        
        self.db = DatabaseManager()
        self.perplexity = PerplexityConnector() if PROGRAM_CONFIG['ENABLE_PERPLEXITY_SEARCH'] else None
        self.output_dir = Path("data/program_resources")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Circuit breakers for component isolation
        self.forecast_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=300)
        self.perplexity_breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=600)
        self.database_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=120)
        
        # Component health tracking
        self.component_health = {
            'forecast_analyzer': True,
            'database': True,
            'perplexity': PROGRAM_CONFIG['ENABLE_PERPLEXITY_SEARCH'],
            'file_system': True
        }
        
        # Resource categories aligned with FORECAST findings
        self.focus_categories = {
            'new_tasks': {
                'title': 'AI-Created Cybersecurity Roles',
                'description': 'New positions and responsibilities emerging from AI adoption',
                'key_areas': ['AI Security Engineering', 'Prompt Security', 'AI Governance', 'AI Risk Assessment']
            },
            'human_only': {
                'title': 'Human-Centric Security Leadership',
                'description': 'Skills that remain uniquely human and increase in value',
                'key_areas': ['Strategic Leadership', 'Crisis Management', 'Ethical Decision Making', 'Stakeholder Communication']
            },
            'augment': {
                'title': 'AI-Enhanced Security Skills',
                'description': 'Traditional skills amplified through AI collaboration',
                'key_areas': ['AI-Assisted Analysis', 'Human-AI Teaming', 'AI Tool Mastery', 'Enhanced Threat Hunting']
            }
        }
        
        # Resource type priorities (focus on free/open access)
        self.resource_priorities = {
            'free': ['youtube', 'github', 'university_open', 'blog', 'documentation'],
            'monitored': ['coursera_audit', 'edx_audit', 'vendor_free'],
            'restricted': ['paid_courses', 'enterprise_only', 'certification_required']
        }

    def get_forecast_findings(self, category: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve FORECAST findings for a specific category.
        Integrates with existing category narrative system with circuit breaker protection.
        """
        def _get_forecast_data():
            # Import the existing analyzer
            from scripts.analysis.comprehensive_category_narratives import ComprehensiveCategoryNarrativeAnalyzer
            analyzer = ComprehensiveCategoryNarrativeAnalyzer()
            
            # Get category report
            report = analyzer.generate_category_report(category)
            
            if report:
                if logger:
                    logger.info(f"Retrieved {report['total_articles_analyzed']} articles for {category}")
                return report
            else:
                if logger:
                    logger.warning(f"No forecast findings found for category: {category}")
                return None
        
        try:
            # Use circuit breaker for resilience
            if PROGRAM_CONFIG['SAFE_MODE']:
                return self.forecast_breaker.call(_get_forecast_data)
            else:
                return _get_forecast_data()
                
        except Exception as e:
            if logger:
                logger.error(f"Error retrieving forecast findings for {category}: {e}")
            self.component_health['forecast_analyzer'] = False
            return None

    def extract_learning_needs(self, forecast_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract specific learning needs from FORECAST findings."""
        learning_needs = []
        category = forecast_data.get('category', 'unknown')
        jobs_tasks = forecast_data.get('jobs_and_tasks', {})
        
        logger.info(f"Extracting learning needs from {len(jobs_tasks)} jobs/tasks in {category}")
        
        for job_task, details in jobs_tasks.items():
            # Use avg_confidence from the forecast data structure
            confidence = details.get('avg_confidence', 0)
            evidence_count = details.get('evidence_count', 0)
            
            # Only process items with meaningful confidence and evidence
            if confidence >= 0.25 and evidence_count >= 1:
                learning_need = {
                    'category': category,
                    'skill_area': job_task.replace('_', ' ').title(),
                    'confidence': confidence,
                    'evidence_count': evidence_count,
                    'learning_priority': confidence * 0.9 if category in ['new_tasks', 'human_only'] else confidence * 0.7,
                    'target_skills': [f"{job_task.replace('_', ' ')} skills", f"AI-enhanced {job_task.replace('_', ' ')}"],
                    'explanations': details.get('explanations', [])[:3]  # Top 3 explanations
                }
                learning_needs.append(learning_need)
        
        learning_needs.sort(key=lambda x: x['learning_priority'], reverse=True)
        logger.info(f"Identified {len(learning_needs)} learning needs for {category}")
        
        return learning_needs

    def generate_search_prompts(self, learning_needs: List[Dict[str, Any]]) -> List[ResourceSearchPrompt]:
        """
        Generate targeted Perplexity search prompts from learning needs.
        """
        search_prompts = []
        
        for need in learning_needs[:10]:  # Limit to top 10 priorities
            category = need['category']
            skill_area = need['skill_area']
            target_skills = need['target_skills']
            
            # Create focused search queries
            for skill in target_skills[:3]:  # Top 3 skills per area
                # Base search terms
                search_terms = [
                    "free online course",
                    "tutorial",
                    "learning resource", 
                    "training",
                    skill.lower(),
                    "cybersecurity"
                ]
                
                # Add category-specific terms
                if category == 'new_tasks':
                    search_terms.extend(["AI security", "emerging role", "2024", "2025"])
                elif category == 'human_only':
                    search_terms.extend(["leadership", "management", "strategic"])
                elif category == 'augment':
                    search_terms.extend(["AI-assisted", "human-AI collaboration", "AI tools"])
                
                # Construct search query
                search_query = f"find {' '.join(search_terms[:6])} site:youtube.com OR site:github.com OR site:coursera.org OR site:edu"
                
                prompt = ResourceSearchPrompt(
                    category=category,
                    skill_area=skill_area,
                    search_query=search_query,
                    target_resources=['courses', 'tutorials', 'videos', 'documentation'],
                    expected_platforms=['youtube', 'github', 'coursera', 'edx', 'university']
                )
                search_prompts.append(prompt)
        
        logger.info(f"Generated {len(search_prompts)} search prompts")
        return search_prompts

    async def search_resources_with_perplexity(self, prompts: List[ResourceSearchPrompt]) -> List[EducationalResource]:
        """
        Use Perplexity to search for educational resources.
        """
        if not self.perplexity:
            logger.warning("Perplexity not available, skipping automated search")
            return []
        
        resources = []
        
        for prompt in prompts[:5]:  # Limit API calls
            try:
                logger.info(f"Searching for {prompt.skill_area} resources in {prompt.category}")
                
                # Use Perplexity to find resources
                artifacts = await self.perplexity.collect(
                    query=prompt.search_query,
                    max_results=3,
                    category=prompt.category
                )
                
                # Process artifacts into educational resources
                for artifact in artifacts:
                    resource = self._process_artifact_to_resource(artifact, prompt)
                    if resource:
                        resources.append(resource)
                
            except Exception as e:
                logger.error(f"Error searching with Perplexity for {prompt.skill_area}: {e}")
                continue
        
        logger.info(f"Found {len(resources)} resources via Perplexity")
        return resources

    def _process_artifact_to_resource(self, artifact, prompt: ResourceSearchPrompt) -> Optional[EducationalResource]:
        """Convert Perplexity artifact to educational resource."""
        try:
            # Extract URLs from content
            urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', artifact.content)
            
            if not urls:
                return None
            
            url = urls[0]  # Use first URL found
            domain = urlparse(url).netloc.lower()
            
            # Determine resource type and access level
            resource_type = self._classify_resource_type(artifact.content, url)
            access_type = self._determine_access_type(domain, artifact.content)
            platform = self._identify_platform(domain)
            
            # Rate the resource quality
            quality_score = self._rate_resource_quality(artifact.content, prompt.skill_area)
            
            return EducationalResource(
                title=artifact.title,
                url=url,
                resource_type=resource_type,
                access_type=access_type,
                platform=platform,
                description=artifact.content[:300] + "..." if len(artifact.content) > 300 else artifact.content,
                skills_covered=prompt.target_resources,
                target_audience='all_levels',  # Default, could be refined
                quality_score=quality_score,
                evidence_snippets=[artifact.content[:200]],
                source_category=prompt.category,
                discovery_method='perplexity_auto',
                collected_at=datetime.now().isoformat(),
                metadata={
                    'search_query': prompt.search_query,
                    'skill_area': prompt.skill_area,
                    'artifact_source': artifact.metadata.get('source_type', 'unknown')
                }
            )
            
        except Exception as e:
            logger.error(f"Error processing artifact to resource: {e}")
            return None

    def _classify_resource_type(self, content: str, url: str) -> str:
        """Classify the type of educational resource."""
        content_lower = content.lower()
        url_lower = url.lower()
        
        if 'youtube.com' in url_lower or 'video' in content_lower:
            return 'video'
        elif 'github.com' in url_lower or 'repository' in content_lower:
            return 'tool'
        elif 'course' in content_lower or 'coursera' in url_lower or 'edx' in url_lower:
            return 'course'
        elif 'tutorial' in content_lower or 'guide' in content_lower:
            return 'tutorial'
        elif 'doc' in url_lower or 'documentation' in content_lower:
            return 'documentation'
        else:
            return 'article'

    def _determine_access_type(self, domain: str, content: str) -> str:
        """Determine if resource is free, paid, or requires login."""
        content_lower = content.lower()
        
        # Check for free indicators
        if any(term in content_lower for term in ['free', 'open source', 'no cost', 'github']):
            return 'free'
        elif any(term in content_lower for term in ['subscription', 'premium', 'paid', 'purchase']):
            return 'paid'
        elif any(term in content_lower for term in ['login', 'register', 'account required']):
            return 'login_required'
        elif domain in ['youtube.com', 'github.com', 'wikipedia.org']:
            return 'free'
        else:
            return 'free'  # Default assumption for analysis

    def _identify_platform(self, domain: str) -> str:
        """Identify the platform hosting the resource."""
        platform_mapping = {
            'youtube.com': 'youtube',
            'github.com': 'github',
            'coursera.org': 'coursera',
            'edx.org': 'edx',
            'medium.com': 'blog',
            'linkedin.com': 'linkedin_learning',
            'udemy.com': 'udemy',
            'khanacademy.org': 'khan_academy'
        }
        
        for platform_domain, platform_name in platform_mapping.items():
            if platform_domain in domain:
                return platform_name
        
        if '.edu' in domain:
            return 'university'
        else:
            return 'other'

    def _rate_resource_quality(self, content: str, skill_area: str) -> float:
        """
        Rate resource quality based on content analysis.
        Returns score from 0.0 to 1.0
        """
        score = 0.5  # Base score
        content_lower = content.lower()
        skill_lower = skill_area.lower()
        
        # Positive indicators
        quality_indicators = [
            'practical', 'hands-on', 'examples', 'step-by-step',
            'comprehensive', 'detailed', 'updated', '2024', '2025',
            'certification', 'accredited', 'university', 'expert'
        ]
        
        # Skill relevance
        if skill_lower in content_lower:
            score += 0.2
        
        # Quality indicators
        for indicator in quality_indicators:
            if indicator in content_lower:
                score += 0.05
        
        # Negative indicators
        negative_indicators = ['outdated', 'deprecated', 'old', '2020', '2019']
        for indicator in negative_indicators:
            if indicator in content_lower:
                score -= 0.1
        
        return max(0.0, min(1.0, score))

    def add_manual_resource(self, resource_data: Dict[str, Any]) -> EducationalResource:
        """
        Add a manually curated resource.
        """
        resource = EducationalResource(
            title=resource_data['title'],
            url=resource_data['url'],
            resource_type=resource_data.get('resource_type', 'other'),
            access_type=resource_data.get('access_type', 'free'),
            platform=resource_data.get('platform', 'other'),
            description=resource_data.get('description', ''),
            skills_covered=resource_data.get('skills_covered', []),
            target_audience=resource_data.get('target_audience', 'all_levels'),
            quality_score=resource_data.get('quality_score', 0.7),  # Manual entries get benefit of doubt
            evidence_snippets=resource_data.get('evidence_snippets', []),
            source_category=resource_data['source_category'],
            discovery_method='manual_entry',
            collected_at=datetime.now().isoformat(),
            metadata=resource_data.get('metadata', {})
        )
        
        logger.info(f"Added manual resource: {resource.title}")
        return resource

    def categorize_resources_by_access(self, resources: List[EducationalResource]) -> Dict[str, List[EducationalResource]]:
        """
        Separate resources by access type for different publication approaches.
        """
        categorized = {
            'public_free': [],      # Publish immediately 
            'monitored_paid': [],   # Review list for researchers
            'restricted': []        # Special handling needed
        }
        
        for resource in resources:
            if resource.access_type == 'free':
                categorized['public_free'].append(resource)
            elif resource.access_type in ['paid', 'login_required']:
                categorized['monitored_paid'].append(resource)
            else:
                categorized['restricted'].append(resource)
        
        logger.info(f"Categorized resources: {len(categorized['public_free'])} free, "
                   f"{len(categorized['monitored_paid'])} paid/restricted, "
                   f"{len(categorized['restricted'])} special handling")
        
        return categorized

    def generate_public_resource_page(self, resources: List[EducationalResource], category: str) -> str:
        """
        Generate public-facing HTML resource page for theaihorizon.org
        """
        category_info = self.focus_categories.get(category, {'title': category.title(), 'description': ''})
        
        # Group resources by skill area
        by_skill = {}
        for resource in resources:
            skill_area = resource.metadata.get('skill_area', 'General Skills')
            if skill_area not in by_skill:
                by_skill[skill_area] = []
            by_skill[skill_area].append(resource)
        
        # Generate HTML
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{category_info['title']} - Learning Resources | AI-Horizon</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; margin-bottom: 40px; }}
        .category-title {{ color: #2c3e50; font-size: 2.5em; margin-bottom: 10px; }}
        .category-description {{ color: #7f8c8d; font-size: 1.2em; }}
        .skill-section {{ margin-bottom: 40px; }}
        .skill-title {{ color: #34495e; font-size: 1.8em; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #3498db; }}
        .resource-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 20px; }}
        .resource-card {{ background: #fff; border: 1px solid #e0e0e0; border-radius: 8px; padding: 20px; transition: transform 0.2s, box-shadow 0.2s; }}
        .resource-card:hover {{ transform: translateY(-2px); box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
        .resource-title {{ font-weight: bold; font-size: 1.3em; margin-bottom: 10px; }}
        .resource-title a {{ color: #2980b9; text-decoration: none; }}
        .resource-title a:hover {{ color: #3498db; }}
        .resource-meta {{ display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 15px; }}
        .resource-tag {{ background: #ecf0f1; color: #2c3e50; padding: 4px 8px; border-radius: 4px; font-size: 0.9em; }}
        .resource-type {{ background: #3498db; color: white; }}
        .access-free {{ background: #27ae60; color: white; }}
        .platform-tag {{ background: #e74c3c; color: white; }}
        .quality-score {{ background: #f39c12; color: white; }}
        .resource-description {{ color: #7f8c8d; margin-bottom: 15px; }}
        .skills-covered {{ }}
        .skills-covered h5 {{ margin: 10px 0 5px 0; color: #2c3e50; }}
        .skills-list {{ display: flex; flex-wrap: wrap; gap: 5px; }}
        .skill-tag {{ background: #d5dbdb; color: #2c3e50; padding: 2px 6px; border-radius: 3px; font-size: 0.8em; }}
        .footer {{ text-align: center; margin-top: 40px; color: #7f8c8d; border-top: 1px solid #e0e0e0; padding-top: 20px; }}
        .generated-info {{ background: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 30px; color: #6c757d; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 class="category-title">{category_info['title']}</h1>
            <p class="category-description">{category_info['description']}</p>
        </div>
        
        <div class="generated-info">
            <strong>🤖 AI-Generated Resources:</strong> These learning resources were automatically discovered and curated by AI-Horizon's PROGRAM component based on NSF-funded workforce research. All resources are free and publicly accessible. Updated: {datetime.now().strftime('%B %d, %Y')}
        </div>
"""
        
        # Add skill sections
        for skill_area, skill_resources in by_skill.items():
            html += f"""
        <div class="skill-section">
            <h2 class="skill-title">📚 {skill_area}</h2>
            <div class="resource-grid">
"""
            
            for resource in sorted(skill_resources, key=lambda r: r.quality_score, reverse=True):
                html += f"""
                <div class="resource-card">
                    <div class="resource-title">
                        <a href="{resource.url}" target="_blank" rel="noopener">{resource.title}</a>
                    </div>
                    <div class="resource-meta">
                        <span class="resource-tag resource-type">{resource.resource_type.title()}</span>
                        <span class="resource-tag access-free">{resource.access_type.replace('_', ' ').title()}</span>
                        <span class="resource-tag platform-tag">{resource.platform.title()}</span>
                        <span class="resource-tag quality-score">Quality: {resource.quality_score:.1f}</span>
                    </div>
                    <div class="resource-description">{resource.description}</div>
                    <div class="skills-covered">
                        <h5>Skills Covered:</h5>
                        <div class="skills-list">
"""
                for skill in resource.skills_covered[:4]:  # Limit display
                    html += f'<span class="skill-tag">{skill}</span>'
                
                html += """
                        </div>
                    </div>
                </div>
"""
            
            html += """
            </div>
        </div>
"""
        
        # Add footer
        html += f"""
        <div class="footer">
            <p><strong>AI-Horizon Project</strong> | NSF EAGER Award #2528858 | California State University, San Bernardino</p>
            <p>Predicting cybersecurity workforce transformation and adaptive skill development through AI impact analysis.</p>
            <p>Generated from analysis of {len(resources)} educational resources | <a href="https://theaihorizon.org">theaihorizon.org</a></p>
        </div>
    </div>
</body>
</html>
"""
        
        return html

    def save_resources(self, resources: List[EducationalResource], category: str):
        """Save resources to files for further processing."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save as JSON for data processing
        json_file = self.output_dir / f"{category}_resources_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump([asdict(resource) for resource in resources], f, indent=2, ensure_ascii=False)
        
        # Save public HTML page
        public_resources = [r for r in resources if r.access_type == 'free']
        if public_resources:
            html_content = self.generate_public_resource_page(public_resources, category)
            html_file = self.output_dir / f"{category}_public_resources.html"
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"Generated public resource page: {html_file}")
        
        # Save research review list (paid/restricted resources)
        review_resources = [r for r in resources if r.access_type != 'free']
        if review_resources:
            review_file = self.output_dir / f"{category}_research_review_{timestamp}.json"
            with open(review_file, 'w', encoding='utf-8') as f:
                json.dump([asdict(resource) for resource in review_resources], f, indent=2, ensure_ascii=False)
            
            logger.info(f"Generated research review list: {review_file}")
        
        logger.info(f"Saved {len(resources)} resources for {category} category")

    def check_component_health(self) -> Dict[str, Any]:
        """Check health of all components for monitoring."""
        health_status = {
            'overall_health': 'healthy',
            'components': self.component_health.copy(),
            'circuit_breakers': {
                'forecast': self.forecast_breaker.state,
                'perplexity': self.perplexity_breaker.state,
                'database': self.database_breaker.state
            },
            'capabilities': {
                'can_analyze_forecast': self.component_health['forecast_analyzer'],
                'can_search_resources': self.component_health['perplexity'],
                'can_access_database': self.component_health['database'],
                'can_save_files': self.component_health['file_system']
            }
        }
        
        # Determine overall health
        failed_components = [k for k, v in self.component_health.items() if not v]
        if failed_components:
            health_status['overall_health'] = 'degraded' if len(failed_components) <= 2 else 'critical'
            health_status['failed_components'] = failed_components
        
        return health_status

    async def run_category_analysis(self, category: str) -> Dict[str, Any]:
        """Run complete PROGRAM analysis for a single category with resilience."""
        if logger:
            logger.info(f"Starting PROGRAM analysis for category: {category}")
        
        # Check component health before proceeding
        health = self.check_component_health()
        
        result = {
            'category': category,
            'timestamp': datetime.now().isoformat(),
            'component_health': health,
            'success': False
        }
        
        try:
            # Get FORECAST findings with error handling
            forecast_data = self.get_forecast_findings(category)
            if not forecast_data:
                return {
                    **result,
                    'error': f'No forecast findings available for {category}',
                    'suggested_action': 'Check if FORECAST analysis has been run for this category'
                }
            
            # Extract learning needs with limits
            learning_needs = self.extract_learning_needs(forecast_data)
            
            # Limit results for performance (configurable)
            max_needs = PROGRAM_CONFIG['MAX_LEARNING_NEEDS_PER_CATEGORY']
            limited_needs = learning_needs[:max_needs] if len(learning_needs) > max_needs else learning_needs
            
            result.update({
                'forecast_articles': forecast_data.get('total_articles_analyzed', 0),
                'learning_needs_identified': len(learning_needs),
                'learning_needs_returned': len(limited_needs),
                'learning_needs': limited_needs,
                'success': True
            })
            
            if logger:
                logger.info(f"✅ PROGRAM analysis completed for {category}: {len(learning_needs)} needs found")
            
            return result
            
        except Exception as e:
            error_msg = f"PROGRAM analysis failed for {category}: {str(e)}"
            if logger:
                logger.error(error_msg)
            
            return {
                **result,
                'error': error_msg,
                'exception_type': type(e).__name__,
                'recovery_suggestions': [
                    "Check if FORECAST component is functioning",
                    "Verify database connectivity",
                    "Try running analysis for a different category",
                    "Check system logs for detailed error information"
                ]
            }

async def main():
    """Main execution function for PROGRAM tool."""
    print("🚀 AI-Horizon PROGRAM Tool")
    print("=" * 60)
    print("Converting FORECAST findings into educational resources")
    
    tool = AIHorizonProgramTool()
    target_categories = ['new_tasks', 'human_only', 'augment']
    
    all_results = {}
    
    for category in target_categories:
        print(f"\n📚 Processing {category.replace('_', ' ').title()} category...")
        try:
            result = await tool.run_category_analysis(category)
            all_results[category] = result
            
            if result.get('success'):
                print(f"✅ {category}: {result['learning_needs_identified']} learning needs identified")
                for need in result.get('learning_needs', [])[:3]:
                    print(f"   └── {need['skill_area']} (priority: {need['learning_priority']:.2f})")
            else:
                print(f"⚠️  {category}: {result.get('error', 'Unknown error')}")
        
        except Exception as e:
            print(f"❌ Error processing {category}: {e}")
            all_results[category] = {'error': str(e)}
    
    # Summary
    print(f"\n📊 PROGRAM Tool Summary")
    print("=" * 40)
    total_needs = sum(r.get('learning_needs_identified', 0) for r in all_results.values())
    
    print(f"Total Learning Needs Identified: {total_needs}")
    print(f"Categories Processed: {len([r for r in all_results.values() if r.get('success')])}")
    
    print("🎉 PROGRAM tool execution completed!")
    return all_results

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 