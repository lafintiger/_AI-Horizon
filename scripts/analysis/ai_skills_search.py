#!/usr/bin/env python3
"""
AI Skills Search Tool
Proactively searches for emerging AI skills from diverse sources and analyzes their relevance to cybersecurity professionals.

This tool fills the gap by finding skills that:
- Are emerging in general AI/tech discussions
- May not be explicitly labeled as "cybersecurity" relevant  
- Could provide competitive advantages for cybersecurity professionals
- Are trending in adjacent technical domains

Search Strategy:
1. Query diverse sources (not just cybersecurity content)
2. Analyze broader AI/tech trends
3. Assess cybersecurity relevance of general AI skills
4. Identify cross-domain skill transfer opportunities
"""

import os
import sys
import json
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from aih.utils.database import DatabaseManager
    from aih.utils.logging import get_logger
    from aih.gather.perplexity import PerplexityConnector
    from aih.config import settings
    CORE_DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    print(f"Core dependencies not available: {e}")
    CORE_DEPENDENCIES_AVAILABLE = False

logger = get_logger(__name__) if CORE_DEPENDENCIES_AVAILABLE else None

class AISkillsSearchTool:
    """
    Proactive AI Skills Search Tool
    
    Searches for emerging AI skills from diverse sources and evaluates their
    relevance to cybersecurity professionals, including skills not explicitly
    tagged as cybersecurity-related.
    """
    
    def __init__(self):
        if not CORE_DEPENDENCIES_AVAILABLE:
            raise Exception("AI Skills Search requires core dependencies")
            
        self.db = DatabaseManager()
        self.perplexity = PerplexityConnector() if hasattr(settings, 'perplexity_api_key') and settings.perplexity_api_key else None
        self.status_tracker = None  # Will be set by the caller if real-time updates are needed
        
        # Define search categories for broader skill discovery
        self.search_categories = {
            'emerging_ai_tech': [
                'latest AI breakthroughs 2024 2025',
                'new machine learning techniques',
                'cutting edge AI tools platforms',
                'AI startup technologies',
                'research AI developments'
            ],
            'adjacent_domains': [
                'DevOps AI automation tools',
                'cloud security AI technologies', 
                'financial AI fraud detection',
                'healthcare AI privacy security',
                'automotive AI security'
            ],
            'skill_transfer_opportunities': [
                'AI prompt engineering skills',
                'LLM fine-tuning techniques',
                'AI model deployment practices',
                'AI ethics governance frameworks',
                'human-AI collaboration methods'
            ],
            'industry_transformation': [
                'AI disrupting traditional roles',
                'new AI job categories 2024',
                'AI skills in demand employers',
                'enterprise AI adoption challenges',
                'AI consulting opportunities'
            ]
        }
        
        # Cybersecurity relevance assessment criteria
        self.relevance_criteria = {
            'security_applications': [
                'threat detection', 'anomaly detection', 'fraud prevention',
                'vulnerability analysis', 'incident response', 'risk assessment',
                'compliance automation', 'identity verification', 'access control'
            ],
            'privacy_protection': [
                'data privacy', 'differential privacy', 'federated learning',
                'secure computation', 'encryption', 'anonymization'
            ],
            'system_security': [
                'model security', 'adversarial attacks', 'robustness',
                'AI safety', 'model interpretability', 'bias detection'
            ],
            'operational_security': [
                'security operations', 'automation', 'orchestration',
                'monitoring', 'incident management', 'response coordination'
            ]
        }
    
    async def run_comprehensive_search(self, focus_area: str = "emerging_skills", 
                                     timeframe: str = "6months", custom_prompts: Dict[str, List[str]] = None) -> Dict[str, Any]:
        """
        Run comprehensive AI skills search across multiple sources and categories
        """
        logger.info(f"Starting comprehensive AI skills search - Focus: {focus_area}, Timeframe: {timeframe}")
        
        if self.status_tracker:
            self.status_tracker.update_progress(20, 100, "Initializing search categories...")
            self.status_tracker.add_log("INFO", f"Starting comprehensive search across multiple categories", "SEARCH")
        
        search_results = {
            'search_metadata': {
                'focus_area': focus_area,
                'timeframe': timeframe,
                'search_timestamp': datetime.now().isoformat(),
                'sources_searched': [],
                'total_queries': 0
            },
            'discovered_skills': [],
            'trending_technologies': [],
            'cross_domain_opportunities': [],
            'skill_gaps_identified': [],
            'cybersecurity_relevance_scores': {},
            'learning_recommendations': []
        }
        
        # Use custom prompts if provided, otherwise use defaults
        search_categories = custom_prompts if custom_prompts else self.search_categories
        
        if self.status_tracker:
            total_queries = sum(len(queries) for queries in search_categories.values())
            self.status_tracker.add_log("INFO", f"Prepared {len(search_categories)} categories with {total_queries} queries", "SEARCH")
            self.status_tracker.update_progress(30, 100, f"Executing {total_queries} search queries...")
        
        # Execute searches across all categories
        all_discoveries = []
        query_count = 0
        total_queries = sum(len(queries) for queries in search_categories.values())
        
        for category, queries in search_categories.items():
            logger.info(f"Searching category: {category}")
            
            if self.status_tracker:
                self.status_tracker.add_log("INFO", f"Searching category: {category} ({len(queries)} queries)", "SEARCH")
            
            for i, query in enumerate(queries):
                query_count += 1
                
                if self.status_tracker:
                    progress = 30 + int((query_count / total_queries) * 40)  # 30-70% for queries
                    self.status_tracker.update_progress(progress, 100, f"Query {query_count}/{total_queries}: {category}")
                
                if self.perplexity:
                    # Enhanced query for broader skill discovery
                    enhanced_query = self._enhance_query_for_skill_discovery(query, focus_area, timeframe)
                    discovery = await self._search_with_perplexity(enhanced_query, category)
                    if discovery:
                        all_discoveries.append(discovery)
                        search_results['search_metadata']['total_queries'] += 1
                        
                        if self.status_tracker:
                            skills_found = len(discovery.get('extracted_skills', []))
                            self.status_tracker.add_log("INFO", f"Found {skills_found} skills from query: {query[:50]}...", "SEARCH")
                
                # Add simulated search if Perplexity not available
                else:
                    if self.status_tracker:
                        self.status_tracker.add_log("INFO", f"Perplexity not available, using realistic simulation for: {query[:50]}...", "SEARCH")
                    
                    discovery = self._simulate_skill_discovery(query, category)
                    if discovery:
                        all_discoveries.append(discovery)
                        search_results['search_metadata']['total_queries'] += 1
                        
                        if self.status_tracker:
                            skills_found = len(discovery.get('extracted_skills', []))
                            self.status_tracker.add_log("INFO", f"Simulation generated {skills_found} realistic skills for: {query[:50]}...", "SEARCH")
        
        if self.status_tracker:
            self.status_tracker.update_progress(70, 100, "Processing and analyzing discovered skills...")
            self.status_tracker.add_log("INFO", f"Completed {query_count} queries, processing {len(all_discoveries)} discoveries", "SEARCH")
        
        # Process and analyze all discoveries
        processed_results = self._process_skill_discoveries(all_discoveries, focus_area, timeframe)
        search_results.update(processed_results)
        
        if self.status_tracker:
            self.status_tracker.update_progress(90, 100, "Generating learning recommendations...")
            total_skills = len(search_results['discovered_skills'])
            self.status_tracker.add_log("INFO", f"Processed discoveries: {total_skills} unique skills identified", "SEARCH")
        
        # Generate learning recommendations
        search_results['learning_recommendations'] = self._generate_learning_recommendations(
            search_results['discovered_skills'], 
            search_results['cross_domain_opportunities']
        )
        
        if self.status_tracker:
            learning_recs = len(search_results['learning_recommendations'])
            self.status_tracker.update_progress(100, 100, f"Completed! Found {total_skills} skills, {learning_recs} recommendations")
            self.status_tracker.add_log("INFO", f"Search completed: {total_skills} skills, {learning_recs} learning recommendations", "SEARCH")
        
        logger.info(f"Search completed: {len(search_results['discovered_skills'])} skills discovered")
        return search_results
    
    def _enhance_query_for_skill_discovery(self, base_query: str, focus_area: str, timeframe: str) -> str:
        """
        Enhance search queries to find skills not explicitly labeled as cybersecurity
        """
        
        # Add temporal modifiers
        temporal_terms = {
            '3months': ['recent', '2024', 'latest', 'new'],
            '6months': ['emerging', '2024', 'trending', 'growing'],
            '12months': ['future', '2024', '2025', 'upcoming', 'next-generation'],
            '24months': ['future', '2025', 'next-generation', 'revolutionary']
        }
        
        time_terms = temporal_terms.get(timeframe, ['emerging', 'new'])
        
        # Add skill discovery modifiers
        skill_modifiers = [
            'skills professionals need',
            'capabilities requirements',
            'competencies demand',
            'expertise trending',
            'knowledge areas growth'
        ]
        
        # Add domain expansion terms
        domain_expansions = [
            'enterprise adoption',
            'industry implementation', 
            'business applications',
            'professional development',
            'career advancement'
        ]
        
        enhanced_query = f"{base_query} {' '.join(time_terms[:2])} {skill_modifiers[0]} {domain_expansions[0]}"
        
        # Add relevance indicators without being too specific to cybersecurity
        if focus_area == "emerging_skills":
            enhanced_query += " technology professionals learn"
        elif focus_area == "cross_domain":
            enhanced_query += " interdisciplinary applications"
        
        return enhanced_query
    
    async def _search_with_perplexity(self, query: str, category: str) -> Optional[Dict[str, Any]]:
        """
        Search for skills using Perplexity with optimized queries
        """
        try:
            # Create skill-focused search prompt
            search_prompt = f"""
Find emerging AI skills and technologies related to: {query}

Focus on:
1. NEW skills that didn't exist 2 years ago
2. Skills growing in demand across industries
3. Technologies being adopted by enterprises
4. Capabilities that provide competitive advantage
5. Skills that bridge different domains

For each skill/technology found:
- Name and brief description
- Why it's gaining importance
- Industries adopting it
- Skill level required
- Learning resources available

Format as structured information with clear skill names and relevance indicators.
"""
            
            # Use the correct method name 'collect' instead of 'search'
            artifacts = await self.perplexity.collect(search_prompt, max_results=5, category=category, timeframe="2024")
            
            if artifacts:
                # Extract content from artifacts
                content = ""
                citations = []
                
                for artifact in artifacts:
                    content += artifact.content + "\n\n"
                    if hasattr(artifact, 'url') and artifact.url:
                        citations.append(artifact.url)
                
                # Extract skills from the response
                extracted_skills = self._extract_skills_from_content(content, category)
                
                return {
                    'category': category,
                    'query': query,
                    'content': content,
                    'citations': citations,
                    'extracted_skills': extracted_skills,
                    'search_timestamp': datetime.now().isoformat()
                }
            
        except Exception as e:
            logger.error(f"Perplexity search failed for query '{query}': {e}")
            
        return None
    
    def _simulate_skill_discovery(self, query: str, category: str) -> Dict[str, Any]:
        """
        Simulate realistic skill discovery results for testing and fallback
        """
        
        # Realistic simulated skills by category
        realistic_skills = {
            'emerging_ai_tech': [
                {
                    'name': 'Generative AI Security',
                    'relevance': 0.92,
                    'description': 'Securing and governing generative AI applications in enterprise environments',
                    'confidence': 0.9,
                    'learning_priority': 'Critical',
                    'market_demand': 'Very High',
                    'difficulty_level': 'Advanced'
                },
                {
                    'name': 'Prompt Engineering',
                    'relevance': 0.88,
                    'description': 'Designing effective prompts for AI systems to enhance security analysis and response',
                    'confidence': 0.85,
                    'learning_priority': 'High',
                    'market_demand': 'Very High',
                    'difficulty_level': 'Intermediate'
                },
                {
                    'name': 'AI Red Teaming',
                    'relevance': 0.85,
                    'description': 'Testing AI systems for vulnerabilities and adversarial attacks',
                    'confidence': 0.8,
                    'learning_priority': 'High',
                    'market_demand': 'High',
                    'difficulty_level': 'Advanced'
                },
                {
                    'name': 'Large Language Model Operations',
                    'relevance': 0.82,
                    'description': 'Managing and securing large language models in production environments',
                    'confidence': 0.75,
                    'learning_priority': 'High',
                    'market_demand': 'Very High',
                    'difficulty_level': 'Advanced'
                }
            ],
            'cybersecurity_applications': [
                {
                    'name': 'AI-Powered Threat Detection',
                    'relevance': 0.95,
                    'description': 'Using machine learning to identify and respond to security threats in real-time',
                    'confidence': 0.9,
                    'learning_priority': 'Critical',
                    'market_demand': 'Very High',
                    'difficulty_level': 'Advanced'
                },
                {
                    'name': 'Behavioral Analytics',
                    'relevance': 0.87,
                    'description': 'Analysis of user and system behavior patterns to detect anomalies and threats',
                    'confidence': 0.85,
                    'learning_priority': 'High',
                    'market_demand': 'Very High',
                    'difficulty_level': 'Intermediate'
                },
                {
                    'name': 'Security Automation & Orchestration',
                    'relevance': 0.83,
                    'description': 'Implementing automated security responses using SOAR platforms',
                    'confidence': 0.8,
                    'learning_priority': 'High',
                    'market_demand': 'Very High',
                    'difficulty_level': 'Intermediate'
                }
            ],
            'industry_transformation': [
                {
                    'name': 'Zero Trust Architecture',
                    'relevance': 0.91,
                    'description': 'Implementation of never-trust, always-verify security frameworks',
                    'confidence': 0.88,
                    'learning_priority': 'Critical',
                    'market_demand': 'Very High',
                    'difficulty_level': 'Intermediate'
                },
                {
                    'name': 'Cloud Security Posture Management',
                    'relevance': 0.86,
                    'description': 'Continuous monitoring and compliance of cloud infrastructure security',
                    'confidence': 0.82,
                    'learning_priority': 'High',
                    'market_demand': 'Very High',
                    'difficulty_level': 'Intermediate'
                },
                {
                    'name': 'DevSecOps Integration',
                    'relevance': 0.84,
                    'description': 'Integrating security practices into development and operations workflows',
                    'confidence': 0.8,
                    'learning_priority': 'High',
                    'market_demand': 'Very High',
                    'difficulty_level': 'Intermediate'
                }
            ],
            'adjacent_domains': [
                {
                    'name': 'Privacy Engineering',
                    'relevance': 0.78,
                    'description': 'Building privacy-preserving systems and ensuring data protection compliance',
                    'confidence': 0.75,
                    'learning_priority': 'Medium',
                    'market_demand': 'High',
                    'difficulty_level': 'Intermediate'
                },
                {
                    'name': 'Regulatory Compliance Automation',
                    'relevance': 0.76,
                    'description': 'Automating compliance workflows for security and privacy regulations',
                    'confidence': 0.72,
                    'learning_priority': 'Medium',
                    'market_demand': 'High',
                    'difficulty_level': 'Intermediate'
                }
            ],
            'skill_transfer_opportunities': [
                {
                    'name': 'Risk Assessment Analytics',
                    'relevance': 0.81,
                    'description': 'Quantitative analysis of security risks using data science techniques',
                    'confidence': 0.78,
                    'learning_priority': 'High',
                    'market_demand': 'High',
                    'difficulty_level': 'Intermediate'
                },
                {
                    'name': 'Digital Forensics AI',
                    'relevance': 0.79,
                    'description': 'Using AI to enhance digital forensics investigations and evidence analysis',
                    'confidence': 0.75,
                    'learning_priority': 'High',
                    'market_demand': 'High',
                    'difficulty_level': 'Advanced'
                }
            ]
        }
        
        # Get skills for this category
        skills = realistic_skills.get(category, [])
        
        # Add discovery metadata to each skill
        for skill in skills:
            skill.update({
                'category': category,
                'discovery_source': category,
                'search_query': query,
                'discovery_timestamp': datetime.now().isoformat()
            })
        
        return {
            'category': category,
            'query': query,
            'content': f"Simulated search results for: {query}",
            'citations': ['https://example.com/ai-trends', 'https://example.com/emerging-skills'],
            'extracted_skills': skills,
            'search_timestamp': datetime.now().isoformat()
        }
    
    def _extract_skills_from_content(self, content: str, category: str) -> List[Dict[str, Any]]:
        """
        Extract meaningful skill information from search content using improved patterns and known vocabularies
        """
        skills = []
        
        # Define known AI/cybersecurity skills and technologies
        known_skills = {
            'machine_learning': [
                'Machine Learning', 'Deep Learning', 'Neural Networks', 'Computer Vision',
                'Natural Language Processing', 'MLOps', 'AutoML', 'Feature Engineering',
                'Model Deployment', 'Data Science', 'Predictive Analytics', 'AI Ethics'
            ],
            'cybersecurity_ai': [
                'AI-Powered Threat Detection', 'Behavioral Analytics', 'Anomaly Detection',
                'Security Automation', 'Threat Intelligence', 'SOAR Platforms',
                'Zero Trust Architecture', 'AI Incident Response', 'Security Orchestration',
                'Predictive Threat Modeling', 'AI-Enhanced SIEM', 'Adversarial ML Defense'
            ],
            'emerging_tech': [
                'Generative AI', 'Large Language Models', 'Prompt Engineering',
                'AI Red Teaming', 'Explainable AI', 'Federated Learning',
                'Edge AI', 'Quantum-Safe Cryptography', 'AI Governance',
                'Responsible AI', 'AI Risk Management', 'Digital Forensics AI'
            ],
            'cloud_security': [
                'Cloud Security Posture Management', 'Container Security',
                'Serverless Security', 'Multi-Cloud Security', 'DevSecOps',
                'Infrastructure as Code Security', 'Cloud Access Security Broker',
                'Cloud Workload Protection', 'Identity Access Management'
            ],
            'data_analytics': [
                'Threat Hunting', 'Log Analysis', 'Security Metrics',
                'Risk Assessment Analytics', 'Compliance Automation',
                'Security Data Lake', 'Real-time Analytics', 'Forensic Analysis'
            ]
        }
        
        # Create a comprehensive skill list
        all_known_skills = []
        for skill_list in known_skills.values():
            all_known_skills.extend(skill_list)
        
        # Add variations and related terms
        skill_variations = {
            'Machine Learning': ['ML', 'machine learning', 'artificial intelligence'],
            'Natural Language Processing': ['NLP', 'text analytics', 'language models'],
            'Threat Detection': ['threat hunting', 'intrusion detection', 'malware detection'],
            'Security Automation': ['automated security', 'security orchestration', 'SOAR'],
            'Generative AI': ['GenAI', 'generative artificial intelligence', 'AI generation'],
            'Prompt Engineering': ['prompt design', 'AI prompting', 'language model prompting']
        }
        
        # Extract skills using improved logic
        content_lower = content.lower()
        
        # Direct skill matching
        for skill in all_known_skills:
            skill_lower = skill.lower()
            if skill_lower in content_lower or any(var in content_lower for var in skill_variations.get(skill, [])):
                relevance = self._calculate_cybersecurity_relevance(skill, content)
                if relevance > 0.4:  # Higher threshold for quality
                    skills.append({
                        'name': skill,
                        'relevance': relevance,
                        'description': self._generate_skill_description(skill, category),
                        'category': category,
                        'confidence': 0.85,
                        'learning_priority': self._assess_learning_priority(skill, relevance),
                        'market_demand': self._assess_market_demand(skill),
                        'difficulty_level': self._assess_difficulty_level(skill)
                    })
        
        # Extract technology mentions with context
        tech_patterns = [
            r'(?:using|with|implementing|deploying|leveraging)\s+([A-Z][a-zA-Z\s]{2,30}?)(?:\s+(?:to|for|in|can))',
            r'(?:skills in|expertise in|experience with)\s+([A-Z][a-zA-Z\s]{2,30}?)(?:\s+(?:is|are|to))',
            r'([A-Z][a-zA-Z\s]{2,30}?)\s+(?:certification|training|specialist|expert|professional)',
            r'(?:learn|master|develop)\s+([A-Z][a-zA-Z\s]{2,30}?)\s+(?:skills|capabilities|techniques)'
        ]
        
        import re
        
        for pattern in tech_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = ' '.join(match)
                
                skill_name = match.strip().title()
                
                # Validate skill name quality
                if (3 <= len(skill_name) <= 40 and 
                    not any(word in skill_name.lower() for word in ['the', 'and', 'or', 'but', 'to', 'of', 'in', 'on', 'at']) and
                    any(char.isupper() for char in skill_name)):
                    
                    relevance = self._calculate_cybersecurity_relevance(skill_name, content)
                    if relevance > 0.5:  # Higher threshold for extracted skills
                        skills.append({
                            'name': skill_name,
                            'relevance': relevance,
                            'description': self._generate_skill_description(skill_name, category),
                            'category': category,
                            'confidence': 0.7,
                            'learning_priority': self._assess_learning_priority(skill_name, relevance),
                            'market_demand': self._assess_market_demand(skill_name),
                            'difficulty_level': self._assess_difficulty_level(skill_name)
                        })
        
        # Remove duplicates and sort by relevance
        unique_skills = []
        seen_names = set()
        
        for skill in sorted(skills, key=lambda x: x['relevance'], reverse=True):
            skill_name_lower = skill['name'].lower()
            if skill_name_lower not in seen_names:
                unique_skills.append(skill)
                seen_names.add(skill_name_lower)
        
        return unique_skills[:8]  # Top 8 skills per category
    
    def _generate_skill_description(self, skill_name: str, category: str) -> str:
        """
        Generate meaningful descriptions for skills
        """
        descriptions = {
            'Machine Learning': 'Core AI technology for pattern recognition and predictive analytics in cybersecurity applications',
            'Threat Detection': 'Advanced techniques for identifying and analyzing potential security threats in real-time',
            'Security Automation': 'Implementation of automated security responses and orchestration platforms',
            'Prompt Engineering': 'Designing effective prompts for AI systems to enhance security analysis and response',
            'Behavioral Analytics': 'Analysis of user and system behavior patterns to detect anomalies and threats',
            'AI Ethics': 'Responsible development and deployment of AI systems in security contexts',
            'Zero Trust Architecture': 'Implementation of never-trust, always-verify security frameworks',
            'Cloud Security': 'Protection of cloud-based infrastructure, applications, and data',
            'Incident Response': 'Systematic approach to handling and recovering from security incidents'
        }
        
        # Check for exact matches first
        for key, desc in descriptions.items():
            if key.lower() in skill_name.lower():
                return desc
        
        # Generate category-based description
        category_descriptions = {
            'emerging_ai_tech': f'Cutting-edge AI technology skill: {skill_name}',
            'cybersecurity_applications': f'Security-focused application of {skill_name}',
            'industry_transformation': f'Industry-transforming capability in {skill_name}',
            'adjacent_domains': f'Cross-domain skill opportunity: {skill_name}',
            'skill_transfer_opportunities': f'Transferable expertise in {skill_name}'
        }
        
        return category_descriptions.get(category, f'Emerging professional skill: {skill_name}')
    
    def _assess_learning_priority(self, skill_name: str, relevance: float) -> str:
        """
        Assess learning priority based on skill characteristics
        """
        if relevance >= 0.8:
            return 'Critical'
        elif relevance >= 0.6:
            return 'High'
        elif relevance >= 0.4:
            return 'Medium'
        else:
            return 'Low'
    
    def _assess_market_demand(self, skill_name: str) -> str:
        """
        Assess market demand for skills
        """
        high_demand_keywords = ['ai', 'machine learning', 'cloud', 'security', 'automation', 'threat', 'detection']
        medium_demand_keywords = ['analytics', 'monitoring', 'compliance', 'governance', 'risk']
        
        skill_lower = skill_name.lower()
        
        if any(keyword in skill_lower for keyword in high_demand_keywords):
            return 'Very High'
        elif any(keyword in skill_lower for keyword in medium_demand_keywords):
            return 'High'
        else:
            return 'Moderate'
    
    def _assess_difficulty_level(self, skill_name: str) -> str:
        """
        Assess difficulty level for learning the skill
        """
        advanced_keywords = ['machine learning', 'deep learning', 'ai', 'quantum', 'advanced']
        intermediate_keywords = ['automation', 'analytics', 'cloud', 'security']
        
        skill_lower = skill_name.lower()
        
        if any(keyword in skill_lower for keyword in advanced_keywords):
            return 'Advanced'
        elif any(keyword in skill_lower for keyword in intermediate_keywords):
            return 'Intermediate'
        else:
            return 'Beginner to Intermediate'
    
    def _calculate_cybersecurity_relevance(self, skill_name: str, context: str) -> float:
        """
        Calculate how relevant a general AI skill is to cybersecurity professionals
        """
        relevance_score = 0.0
        skill_lower = skill_name.lower()
        context_lower = context.lower()
        
        # Direct security relevance
        for criteria_category, terms in self.relevance_criteria.items():
            category_score = 0
            for term in terms:
                if term in skill_lower:
                    category_score += 0.3
                if term in context_lower:
                    category_score += 0.1
            
            relevance_score += min(category_score, 0.25)  # Cap per category
        
        # Technology relevance indicators
        tech_indicators = ['ai', 'machine learning', 'automation', 'detection', 'analysis', 'monitoring']
        for indicator in tech_indicators:
            if indicator in skill_lower:
                relevance_score += 0.1
        
        # Cross-domain application potential
        domain_indicators = ['enterprise', 'business', 'operational', 'strategic', 'governance']
        for indicator in domain_indicators:
            if indicator in context_lower:
                relevance_score += 0.05
        
        return min(relevance_score, 1.0)  # Cap at 1.0
    
    def _process_skill_discoveries(self, discoveries: List[Dict[str, Any]], 
                                 focus_area: str, timeframe: str) -> Dict[str, Any]:
        """
        Process and consolidate all skill discoveries
        """
        all_skills = []
        trending_tech = []
        cross_domain_opps = []
        
        for discovery in discoveries:
            category = discovery['category']
            extracted_skills = discovery.get('extracted_skills', [])
            
            for skill in extracted_skills:
                # Add discovery metadata
                skill['discovery_source'] = category
                skill['search_query'] = discovery.get('query', '')
                skill['discovery_timestamp'] = discovery.get('search_timestamp', '')
                
                # Categorize by type
                if skill['relevance'] >= 0.8:
                    if category in ['emerging_ai_tech', 'industry_transformation']:
                        trending_tech.append(skill)
                    elif category in ['adjacent_domains', 'skill_transfer_opportunities']:
                        cross_domain_opps.append(skill)
                
                all_skills.append(skill)
        
        # Sort and prioritize
        all_skills.sort(key=lambda x: x['relevance'], reverse=True)
        trending_tech.sort(key=lambda x: x['relevance'], reverse=True)
        cross_domain_opps.sort(key=lambda x: x['relevance'], reverse=True)
        
        return {
            'discovered_skills': all_skills[:25],  # Top 25 overall
            'trending_technologies': trending_tech[:10],  # Top 10 trending
            'cross_domain_opportunities': cross_domain_opps[:10],  # Top 10 cross-domain
            'skill_gaps_identified': self._identify_skill_gaps(all_skills),
            'cybersecurity_relevance_scores': self._generate_relevance_summary(all_skills)
        }
    
    def _identify_skill_gaps(self, skills: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Identify potential skill gaps based on discovered trends
        """
        gaps = []
        
        # Group skills by category
        category_groups = {}
        for skill in skills:
            cat = skill.get('discovery_source', 'unknown')
            if cat not in category_groups:
                category_groups[cat] = []
            category_groups[cat].append(skill)
        
        # Identify gaps
        for category, cat_skills in category_groups.items():
            if len(cat_skills) >= 3:  # Significant trend
                avg_relevance = sum(s['relevance'] for s in cat_skills) / len(cat_skills)
                
                if avg_relevance >= 0.7:  # High relevance category
                    gaps.append({
                        'gap_area': category.replace('_', ' ').title(),
                        'skill_count': len(cat_skills),
                        'average_relevance': round(avg_relevance, 2),
                        'top_skills': [s['name'] for s in cat_skills[:3]],
                        'urgency': 'High' if avg_relevance >= 0.8 else 'Medium'
                    })
        
        return sorted(gaps, key=lambda x: x['average_relevance'], reverse=True)
    
    def _generate_relevance_summary(self, skills: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Generate summary of cybersecurity relevance scores by category
        """
        category_scores = {}
        category_counts = {}
        
        for skill in skills:
            cat = skill.get('discovery_source', 'unknown')
            relevance = skill.get('relevance', 0)
            
            if cat not in category_scores:
                category_scores[cat] = 0
                category_counts[cat] = 0
            
            category_scores[cat] += relevance
            category_counts[cat] += 1
        
        # Calculate averages
        summary = {}
        for cat in category_scores:
            if category_counts[cat] > 0:
                avg_score = category_scores[cat] / category_counts[cat]
                summary[cat.replace('_', ' ').title()] = round(avg_score, 2)
        
        return summary
    
    def _generate_learning_recommendations(self, discovered_skills: List[Dict[str, Any]], 
                                         cross_domain_opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate specific learning recommendations based on discoveries
        """
        recommendations = []
        
        # High-priority skills (top 5)
        high_priority = sorted(discovered_skills, key=lambda x: x['relevance'], reverse=True)[:5]
        
        for skill in high_priority:
            recommendations.append({
                'type': 'priority_skill',
                'skill_name': skill['name'],
                'relevance_score': skill['relevance'],
                'learning_path': self._suggest_learning_path(skill),
                'estimated_time': self._estimate_learning_time(skill),
                'difficulty': self._assess_difficulty(skill),
                'business_case': f"High cybersecurity relevance ({skill['relevance']:.1%}) with growing industry demand"
            })
        
        # Cross-domain opportunities (top 3)
        for opportunity in cross_domain_opportunities[:3]:
            recommendations.append({
                'type': 'cross_domain_opportunity',
                'skill_name': opportunity['name'],
                'relevance_score': opportunity['relevance'],
                'opportunity_description': f"Transfer skills from {opportunity['discovery_source'].replace('_', ' ')} to cybersecurity",
                'competitive_advantage': "Early adoption before widespread cybersecurity integration",
                'estimated_time': self._estimate_learning_time(opportunity)
            })
        
        return recommendations
    
    def _suggest_learning_path(self, skill: Dict[str, Any]) -> List[str]:
        """Suggest learning path for a skill"""
        paths = {
            'beginner': ['Online course', 'Hands-on tutorials', 'Practice projects'],
            'intermediate': ['Advanced certification', 'Real-world application', 'Mentorship'],
            'advanced': ['Research papers', 'Industry conferences', 'Teaching others']
        }
        
        difficulty = self._assess_difficulty(skill)
        return paths.get(difficulty, paths['intermediate'])
    
    def _estimate_learning_time(self, skill: Dict[str, Any]) -> str:
        """Estimate time needed to learn a skill"""
        relevance = skill.get('relevance', 0.5)
        
        if relevance >= 0.9:
            return "2-4 weeks (critical priority)"
        elif relevance >= 0.7:
            return "1-2 months (high priority)"
        else:
            return "2-3 months (medium priority)"
    
    def _assess_difficulty(self, skill: Dict[str, Any]) -> str:
        """Assess learning difficulty of a skill"""
        name = skill.get('name', '').lower()
        
        if any(term in name for term in ['advanced', 'expert', 'architecture', 'research']):
            return 'advanced'
        elif any(term in name for term in ['engineering', 'implementation', 'management']):
            return 'intermediate'
        else:
            return 'beginner'
    
    async def store_skills_in_database(self, discoveries: List[Dict[str, Any]], 
                                     focus_area: str, timeframe: str) -> int:
        """
        Store discovered skills in the database as artifacts.
        
        Args:
            discoveries: List of discovered/processed skills with metadata
            focus_area: The search focus area used
            timeframe: The timeframe for the search
            
        Returns:
            Number of skills successfully stored
        """
        if not CORE_DEPENDENCIES_AVAILABLE:
            logger.warning("Core dependencies not available for database storage")
            return 0
            
        try:
            db = DatabaseManager()
            stored_count = 0
            
            for discovery in discoveries:
                # Handle both raw discoveries (skill_name) and processed skills (name)
                skill_name = discovery.get('name') or discovery.get('skill_name', 'Unknown Skill')
                relevance_score = discovery.get('relevance') or discovery.get('relevance_score', 0.8)
                
                # Create artifact data for the skill
                artifact_data = {
                    'id': f"ai_skill_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{stored_count:03d}",
                    'url': discovery.get('source_url', f'ai-skills-search://{focus_area}/{timeframe}'),
                    'title': f"AI Skill: {skill_name}",
                    'content': self._format_skill_content(discovery),
                    'source_type': 'ai_skills_search',
                    'collected_at': datetime.now(),
                    'metadata': {
                        'ai_impact_category': self._determine_skill_category(discovery),
                        'ai_impact_categories': {
                            self._determine_skill_category(discovery): {
                                'confidence': relevance_score,
                                'reasoning': discovery.get('reasoning', 'Discovered through AI skills search')
                            }
                        },
                        'search_metadata': {
                            'search_focus': focus_area,
                            'timeframe': timeframe,
                            'discovery_date': datetime.now().isoformat(),
                            'search_type': 'proactive_ai_skills_discovery',
                            'relevance_score': relevance_score,
                            'skill_type': discovery.get('skill_type', 'emerging_ai_skill'),
                            'learning_priority': discovery.get('learning_priority', 'Unknown'),
                            'market_demand': discovery.get('market_demand', 'Unknown'),
                            'difficulty_level': discovery.get('difficulty_level', 'Unknown'),
                            'discovery_source': discovery.get('discovery_source', 'ai_skills_search'),
                            'domains': discovery.get('domains', []),
                            'technologies': discovery.get('technologies', [])
                        }
                    }
                }
                
                # Store in database using the correct method
                try:
                    artifact_id = db.save_artifact(artifact_data)
                    stored_count += 1
                    
                    if self.status_tracker:
                        self.status_tracker.add_log("INFO", f"✅ Stored AI skill: {skill_name} (ID: {artifact_id})", "SEARCH")
                    
                    logger.info(f"Stored AI skill: {skill_name} with ID: {artifact_id}")
                except Exception as e:
                    logger.error(f"Failed to store skill {skill_name}: {e}")
                    if self.status_tracker:
                        self.status_tracker.add_log("ERROR", f"❌ Failed to store skill {skill_name}: {e}", "SEARCH")
                    
            return stored_count
            
        except Exception as e:
            logger.error(f"Error storing skills in database: {e}")
            if self.status_tracker:
                self.status_tracker.add_log("ERROR", f"Database storage error: {e}", "SEARCH")
            return 0
    
    def _format_skill_content(self, discovery: Dict[str, Any]) -> str:
        """Format skill discovery into structured content for database storage."""
        # Handle both raw discoveries (skill_name) and processed skills (name)
        skill_name = discovery.get('name') or discovery.get('skill_name', 'Unknown Skill')
        description = discovery.get('description', 'No description available')
        relevance_score = discovery.get('relevance') or discovery.get('relevance_score', 0.0)
        domains = discovery.get('domains', [])
        technologies = discovery.get('technologies', [])
        learning_resources = discovery.get('learning_resources', [])
        
        # Additional processed skill fields
        learning_priority = discovery.get('learning_priority', 'Unknown')
        market_demand = discovery.get('market_demand', 'Unknown')
        difficulty_level = discovery.get('difficulty_level', 'Unknown')
        discovery_source = discovery.get('discovery_source', 'ai_skills_search')
        
        content = f"""# AI Skill Discovery: {skill_name}

## Overview
{description}

## Relevance Analysis
- **Cybersecurity Relevance**: {relevance_score:.1%}
- **Skill Type**: {discovery.get('skill_type', 'Emerging AI Skill')}
- **Discovery Source**: {discovery_source.replace('_', ' ').title()}
- **Learning Priority**: {learning_priority}
- **Market Demand**: {market_demand}
- **Difficulty Level**: {difficulty_level}

## Domain Applications
{chr(10).join([f"- {domain}" for domain in domains]) if domains else "- General applicability"}

## Related Technologies
{chr(10).join([f"- {tech}" for tech in technologies]) if technologies else "- Technology-agnostic"}

## Learning Path Recommendations
{chr(10).join([f"- {resource}" for resource in learning_resources]) if learning_resources else "- Learning resources to be identified"}

## Strategic Importance
This skill was identified through proactive search across diverse sources, indicating its emerging importance in the cybersecurity field. Early adoption of this skill could provide competitive advantages in:

- Risk Management and Assessment
- Threat Detection and Response
- Security Architecture and Design
- Compliance and Governance
- Innovation and Digital Transformation

## Categorization Reasoning
{discovery.get('reasoning', 'Skill identified as relevant to cybersecurity through AI-powered analysis of cross-domain trends and industry signals.')}

## Next Steps
1. Assess current team capabilities in this area
2. Identify specific training resources and programs
3. Develop implementation roadmap
4. Monitor industry adoption trends
5. Create metrics for skill development progress
"""
        return content
    
    def _determine_skill_category(self, discovery: Dict[str, Any]) -> str:
        """
        Determine the appropriate AI impact category for a discovered skill.
        
        Args:
            discovery: Skill discovery data (either raw discovery or processed skill)
            
        Returns:
            Category string (new_tasks, augment, or replace)
        """
        # Handle both data structures
        skill_name = discovery.get('name') or discovery.get('skill_name', '')
        skill_type = discovery.get('skill_type', '').lower()
        description = discovery.get('description', '').lower()
        technologies = [tech.lower() for tech in discovery.get('technologies', [])]
        
        # Check for new_tasks indicators
        new_tasks_indicators = [
            'emerging', 'novel', 'innovative', 'cutting-edge', 'breakthrough',
            'unprecedented', 'new paradigm', 'revolutionary', 'next-generation',
            'future-oriented', 'advanced', 'experimental'
        ]
        
        # Check for augment indicators  
        augment_indicators = [
            'enhance', 'improve', 'optimize', 'augment', 'assist', 'support',
            'collaborate', 'hybrid', 'human-ai', 'ai-assisted', 'amplify',
            'boost', 'strengthen', 'complement'
        ]
        
        # Check for replace indicators (though these are less common in cybersecurity)
        replace_indicators = [
            'automate', 'replace', 'eliminate', 'substitute', 'fully automated',
            'no human intervention', 'autonomous', 'self-managing'
        ]
        
        # Analyze skill description and type
        skill_text = f"{skill_name} {skill_type} {description}".lower()
        
        # Count matches for each category
        new_tasks_score = sum(1 for indicator in new_tasks_indicators if indicator in skill_text)
        augment_score = sum(1 for indicator in augment_indicators if indicator in skill_text)
        replace_score = sum(1 for indicator in replace_indicators if indicator in skill_text)
        
        # Technology-based scoring
        if any(tech in ['ai', 'machine learning', 'neural networks', 'deep learning'] for tech in technologies):
            if 'human' in skill_text or 'collaborate' in skill_text:
                augment_score += 2
            elif 'new' in skill_text or 'emerging' in skill_text:
                new_tasks_score += 2
        
        # Determine category based on highest score
        if new_tasks_score >= augment_score and new_tasks_score >= replace_score:
            return 'new_tasks'
        elif augment_score >= replace_score:
            return 'augment'
        else:
            # Default to new_tasks for cybersecurity context - most AI skills create new opportunities
            return 'new_tasks'
    
    def format_search_results_for_display(self, results: Dict[str, Any]) -> str:
        """
        Format search results in a human-readable way
        """
        output = []
        output.append("=" * 80)
        output.append("🔍 AI SKILLS SEARCH RESULTS")
        output.append("=" * 80)
        
        metadata = results.get('search_metadata', {})
        output.append(f"📊 Search Focus: {metadata.get('focus_area', 'Unknown').replace('_', ' ').title()}")
        output.append(f"⏱️  Timeframe: {metadata.get('timeframe', 'Unknown')}")
        output.append(f"🔎 Total Queries: {metadata.get('total_queries', 0)}")
        output.append(f"⏰ Search Time: {metadata.get('search_timestamp', 'Unknown')}")
        output.append("")
        
        # Discovered Skills Section
        discovered_skills = results.get('discovered_skills', [])
        if discovered_skills:
            output.append("🎯 DISCOVERED SKILLS")
            output.append("-" * 50)
            
            for i, skill in enumerate(discovered_skills[:10], 1):  # Top 10
                output.append(f"{i:2d}. 📚 {skill.get('name', 'Unknown')}")
                output.append(f"    💡 {skill.get('description', 'No description available')}")
                output.append(f"    🎯 Relevance: {skill.get('relevance', 0):.1%}")
                output.append(f"    📈 Market Demand: {skill.get('market_demand', 'Unknown')}")
                output.append(f"    🎓 Learning Priority: {skill.get('learning_priority', 'Unknown')}")
                output.append(f"    📊 Difficulty: {skill.get('difficulty_level', 'Unknown')}")
                output.append(f"    🏷️  Category: {skill.get('category', 'Unknown').replace('_', ' ').title()}")
                output.append("")
        
        # Trending Technologies Section
        trending = results.get('trending_technologies', [])
        if trending:
            output.append("🚀 TRENDING TECHNOLOGIES")
            output.append("-" * 50)
            
            for i, tech in enumerate(trending[:5], 1):  # Top 5
                output.append(f"{i}. 🔥 {tech.get('name', 'Unknown')}")
                output.append(f"   📊 Relevance: {tech.get('relevance', 0):.1%}")
                output.append(f"   📈 Priority: {tech.get('learning_priority', 'Unknown')}")
                output.append("")
        
        # Skill Gaps Section
        gaps = results.get('skill_gaps_identified', [])
        if gaps:
            output.append("⚠️  SKILL GAPS IDENTIFIED")
            output.append("-" * 50)
            
            for gap in gaps[:3]:  # Top 3 gaps
                output.append(f"🎯 {gap.get('gap_area', 'Unknown')}")
                output.append(f"   📊 Skills Found: {gap.get('skill_count', 0)}")
                output.append(f"   📈 Avg Relevance: {gap.get('average_relevance', 0):.1%}")
                output.append(f"   🚨 Urgency: {gap.get('urgency', 'Unknown')}")
                output.append(f"   🔝 Top Skills: {', '.join(gap.get('top_skills', []))}")
                output.append("")
        
        # Learning Recommendations Section
        recommendations = results.get('learning_recommendations', [])
        if recommendations:
            output.append("📖 LEARNING RECOMMENDATIONS")
            output.append("-" * 50)
            
            for i, rec in enumerate(recommendations[:5], 1):  # Top 5
                output.append(f"{i}. 🎓 {rec.get('skill_name', 'Unknown')}")
                output.append(f"   ⏱️  Estimated Time: {rec.get('estimated_time', 'Unknown')}")
                output.append(f"   📚 Learning Path: {', '.join(rec.get('learning_path', []))}")
                output.append(f"   🎯 Priority: {rec.get('priority', 'Unknown')}")
                output.append("")
        
        # Summary Statistics
        output.append("📊 SUMMARY STATISTICS")
        output.append("-" * 50)
        output.append(f"Total Skills Discovered: {len(discovered_skills)}")
        output.append(f"High Priority Skills: {len([s for s in discovered_skills if s.get('learning_priority') in ['Critical', 'High']])}")
        output.append(f"Very High Demand Skills: {len([s for s in discovered_skills if s.get('market_demand') == 'Very High'])}")
        output.append(f"Skill Gaps Identified: {len(gaps)}")
        output.append("")
        
        return "\n".join(output)

# CLI interface
async def main():
    """Main function for command-line usage"""
    if not CORE_DEPENDENCIES_AVAILABLE:
        print("❌ Core dependencies not available. Please install required packages.")
        return
    
    search_tool = AISkillsSearchTool()
    
    print("🔍 AI Skills Search Tool")
    print("========================")
    print("Searching for emerging AI skills relevant to cybersecurity professionals...")
    
    # Run comprehensive search
    results = await search_tool.run_comprehensive_search(
        focus_area="emerging_skills",
        timeframe="6months"
    )
    
    # Display results
    print(search_tool.format_search_results_for_display(results))
    
    # Save results
    output_file = f"data/ai_skills_search_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    Path("data").mkdir(exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: {output_file}")

if __name__ == "__main__":
    asyncio.run(main()) 