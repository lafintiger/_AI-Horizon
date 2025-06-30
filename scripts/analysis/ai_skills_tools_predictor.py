#!/usr/bin/env python3
"""
AI Skills and Tools Predictor
Advanced prediction system for identifying critical AI skills and tools for workforce development
Integrates with AI-Horizon system to provide strategic workforce intelligence
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Tuple
from collections import defaultdict, Counter
import statistics
import re

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from aih.utils.database import DatabaseManager
from aih.utils.logging import get_logger

class AISkillsToolsPredictor:
    """
    Advanced AI Skills and Tools Prediction System
    
    This class provides comprehensive analysis of AI skills and tools that will be most
    important for cybersecurity professionals to learn, using LLM-powered content analysis
    and trend modeling to generate strategic workforce development recommendations.
    """
    
    def __init__(self):
        self.logger = get_logger(__name__)
        
        # Initialize database connection
        try:
            self.db_manager = DatabaseManager()
            self.logger.info("AI Skills and Tools Predictor initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            self.db_manager = None

    def get_ai_skills_prediction_prompt(self, timeframe: str = "12months") -> str:
        """
        Generate the comprehensive AI skills and tools prediction prompt
        
        This is the core prompt that can be used with any LLM to analyze content
        and predict the most important AI skills and tools to learn.
        
        Args:
            timeframe: Prediction timeframe (6months, 12months, 24months)
            
        Returns:
            Comprehensive prompt string for AI skills prediction
        """
        
        prompt = f"""
You are an AI workforce intelligence expert analyzing technology content to predict the most CRITICAL AI skills and tools that cybersecurity professionals should learn in the next {timeframe}.

ANALYSIS FRAMEWORK:
Examine the provided content for explicit and implicit signals about AI skills demand, tools adoption, and workforce transformation patterns.

SKILL CATEGORIES TO ANALYZE:
1. **FOUNDATIONAL AI** - Core mathematical and conceptual foundations
   - Machine learning fundamentals, statistics, linear algebra, probability
   - Algorithm design, computational thinking, data structures

2. **TECHNICAL AI SKILLS** - Programming and implementation capabilities  
   - Python/R programming, SQL, frameworks (PyTorch, TensorFlow, scikit-learn)
   - Data manipulation (pandas, numpy), visualization, version control

3. **AI ENGINEERING** - Production and deployment expertise
   - MLOps, model deployment, monitoring, feature engineering
   - Data pipelines, model versioning, A/B testing, production scaling

4. **AI SECURITY** - Security-specific AI applications
   - Adversarial attacks, model security, data privacy, bias detection
   - AI governance, interpretability, ethical AI, differential privacy

5. **DOMAIN-SPECIFIC AI** - Specialized AI applications
   - Computer vision, NLP, speech recognition, recommendation systems
   - Generative AI, LLMs, multimodal AI, reinforcement learning

6. **AI STRATEGY & MANAGEMENT** - Leadership and implementation
   - AI strategy, digital transformation, change management
   - ROI measurement, risk assessment, team building, vendor management

7. **EMERGING AI FIELDS** - Cutting-edge developments
   - Quantum ML, neuromorphic computing, edge AI, prompt engineering
   - Constitutional AI, AI safety, alignment research, causal inference

TOOLS & PLATFORMS TO EVALUATE:
- **ML Frameworks**: TensorFlow, PyTorch, scikit-learn, XGBoost, etc.
- **Data Platforms**: Databricks, Snowflake, Apache Spark, etc.
- **Cloud AI Services**: AWS SageMaker, Azure ML, Google AI Platform, etc.
- **LLM Platforms**: OpenAI API, Hugging Face, LangChain, etc.
- **Development Tools**: VS Code, Jupyter, Docker, Kubernetes, etc.
- **Monitoring & Governance**: MLflow, Weights & Biases, etc.

FOR EACH SKILL/TOOL IDENTIFIED, PROVIDE:
- **Demand Level** (1-10): Current and projected market demand
- **Growth Potential** (1-10): Expected demand growth rate
- **Career Impact** (1-10): Potential impact on career advancement and salary
- **Urgency** (1-10): How quickly professionals need to learn this
- **Difficulty Level**: beginner | intermediate | advanced | expert
- **Timeframe Relevance**: immediate | 6months | 12months | 24months
- **Evidence**: Specific quotes or reasoning from the content
- **Learning Priority**: critical | high | medium | low

MARKET SIGNALS TO ANALYZE:
- Hiring demand indicators (job postings, talent shortage mentions)
- Salary impact signals (compensation, earning potential references)
- Industry adoption patterns (enterprise deployment, case studies)
- Skill gap severity (shortage, critical need, essential requirements)
- Technology maturity (experimental, production-ready, widespread)

OUTPUT FORMAT:
Return structured JSON with comprehensive analysis:

```json
{{
  "critical_skills": [
    {{
      "skill": "specific skill name",
      "category": "foundational_ai|technical_ai|ai_engineering|ai_security|domain_specific|ai_strategy|emerging_ai",
      "demand_level": 1-10,
      "growth_potential": 1-10,
      "career_impact": 1-10,
      "urgency": 1-10,
      "difficulty_level": "beginner|intermediate|advanced|expert",
      "timeframe_relevance": "immediate|6months|12months|24months",
      "learning_priority": "critical|high|medium|low",
      "evidence": "specific quote or reasoning from content",
      "why_important": "brief explanation of importance",
      "prerequisites": ["prerequisite skill 1", "prerequisite skill 2"]
    }}
  ],
  "critical_tools": [
    {{
      "tool": "specific tool/platform name", 
      "category": "ml_frameworks|data_platforms|cloud_ai|llm_platforms|dev_tools|monitoring",
      "demand_level": 1-10,
      "growth_potential": 1-10,
      "adoption_trend": "emerging|growing|mature|declining",
      "learning_curve": "easy|moderate|steep|expert",
      "industry_readiness": "experimental|production|enterprise|standard",
      "evidence": "quote or reasoning from content",
      "use_cases": ["use case 1", "use case 2"],
      "alternatives": ["alternative tool 1", "alternative tool 2"]
    }}
  ],
  "market_intelligence": {{
    "hiring_demand_strength": 1-10,
    "salary_impact_potential": 1-10,
    "skill_gap_severity": 1-10,
    "industry_adoption_rate": 1-10,
    "technology_maturity": 1-10,
    "transformation_urgency": 1-10
  }},
  "learning_pathways": {{
    "beginner_path": {{
      "duration": "3-6 months",
      "priority_skills": ["skill 1", "skill 2", "skill 3"],
      "recommended_tools": ["tool 1", "tool 2"],
      "learning_approach": "structured|self-paced|bootcamp|degree"
    }},
    "intermediate_path": {{
      "duration": "6-12 months", 
      "priority_skills": ["skill 1", "skill 2", "skill 3"],
      "recommended_tools": ["tool 1", "tool 2"],
      "specialization_areas": ["area 1", "area 2"]
    }},
    "advanced_path": {{
      "duration": "12-24 months",
      "priority_skills": ["skill 1", "skill 2", "skill 3"],
      "recommended_tools": ["tool 1", "tool 2"], 
      "leadership_skills": ["skill 1", "skill 2"]
    }}
  }},
  "strategic_recommendations": [
    "specific actionable recommendation 1",
    "specific actionable recommendation 2", 
    "specific actionable recommendation 3"
  ],
  "risk_assessment": {{
    "automation_risk": 1-10,
    "skill_obsolescence_risk": 1-10,
    "career_enhancement_opportunity": 1-10,
    "competitive_advantage_potential": 1-10
  }},
  "confidence_metrics": {{
    "analysis_confidence": 0.0-1.0,
    "data_quality": 0.0-1.0,
    "prediction_reliability": 0.0-1.0,
    "market_signal_strength": 0.0-1.0
  }},
  "key_insights": [
    "critical insight about AI skills landscape",
    "important trend or pattern identified",
    "strategic opportunity or threat detected"
  ]
}}
```

ANALYSIS INSTRUCTIONS:
1. **Be Specific**: Focus on concrete, learnable skills rather than vague concepts
2. **Prioritize Practicality**: Emphasize skills that provide immediate career value
3. **Consider Context**: Tailor recommendations for cybersecurity professionals specifically
4. **Evidence-Based**: Support all ratings with specific evidence from the content
5. **Strategic Thinking**: Consider how skills interconnect and build upon each other
6. **Market Reality**: Base predictions on realistic market signals and trends
7. **Actionable Output**: Provide recommendations that professionals can immediately act upon

CRITICAL SUCCESS FACTORS:
- Identify skills that provide competitive advantage in {timeframe}
- Balance foundational knowledge with cutting-edge capabilities
- Consider both technical depth and strategic breadth
- Account for learning curve and time investment required
- Align with cybersecurity industry transformation trends
- Provide clear learning progression pathways

Focus on delivering ACTIONABLE INTELLIGENCE that cybersecurity professionals can use to make strategic career development decisions and stay ahead of AI-driven industry transformation.
"""
        
        return prompt

    def analyze_ai_skills_demand(self, content: str, title: str = "", timeframe: str = "12months") -> Dict[str, Any]:
        """
        Analyze content using the AI skills prediction prompt
        
        Args:
            content: Article or document content to analyze
            title: Title of the content (optional)
            timeframe: Prediction timeframe
            
        Returns:
            Analysis results dictionary
        """
        
        # Get the comprehensive prompt
        base_prompt = self.get_ai_skills_prediction_prompt(timeframe)
        
        # Create content-specific analysis prompt
        analysis_prompt = f"""
{base_prompt}

CONTENT TO ANALYZE:
Title: {title}

Content: {content[:4000]}{"..." if len(content) > 4000 else ""}

Analyze this content and provide comprehensive AI skills and tools predictions following the framework above.
"""

        # If OpenAI is available, use it for analysis
        try:
            import openai
            client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": analysis_prompt}],
                temperature=0.3,
                max_tokens=3000
            )
            
            # Parse JSON response
            result = json.loads(response.choices[0].message.content)
            result['analysis_method'] = 'LLM-powered'
            result['prompt_version'] = '1.0'
            
            return result
            
        except (ImportError, Exception) as e:
            self.logger.warning(f"LLM analysis failed: {e}, falling back to structured prompt")
            
            # Return structured prompt for manual use or other LLM integration
            return {
                'analysis_method': 'Prompt-based',
                'prompt': analysis_prompt,
                'error': str(e),
                'instructions': 'Use this prompt with your preferred LLM for analysis'
            }

    def predict_skills_and_tools(self, focus_area: str = "cybersecurity", 
                               timeframe: str = "6_months", 
                               skill_level: str = "all_levels") -> Dict[str, Any]:
        """
        Main prediction method that integrates with the AI-Horizon four-category framework.
        This method is specifically designed for the "NEW TASKS" category - identifying
        new skills and tools that cybersecurity professionals need to learn due to AI adoption.
        
        Args:
            focus_area: Focus area for predictions (cybersecurity, general_tech, specific_domain)
            timeframe: Prediction timeframe (6_months, 12_months, 24_months)
            skill_level: Target skill level (beginner, intermediate, advanced, all_levels)
            
        Returns:
            Comprehensive prediction report formatted for the New Tasks category
        """
        
        self.logger.info(f"🎯 NEW TASKS: Predicting AI skills for {focus_area} workforce ({timeframe})")
        
        # Convert timeframe format for internal use
        timeframe_mapping = {
            "6_months": "6months",
            "12_months": "12months", 
            "24_months": "24months"
        }
        internal_timeframe = timeframe_mapping.get(timeframe, "12months")
        
        # Run the comprehensive analysis
        results = self.run_comprehensive_analysis(timeframe=internal_timeframe)
        
        # Transform results to align with NEW TASKS category framework
        transformed_report = self._transform_for_new_tasks_category(
            results, focus_area, timeframe, skill_level
        )
        
        return transformed_report
    
    def _transform_for_new_tasks_category(self, raw_results: Dict[str, Any], 
                                        focus_area: str, timeframe: str, 
                                        skill_level: str) -> Dict[str, Any]:
        """
        Transform analysis results to align with the NEW TASKS category framework.
        
        This method formats the prediction results to emphasize how AI skills represent
        NEW TASKS and responsibilities that didn't exist before AI adoption.
        """
        
        # Create NEW TASKS focused report structure
        report = {
            "category": "new_tasks",
            "category_description": "New AI skills and responsibilities emerging from AI adoption in cybersecurity",
            "analysis_metadata": {
                "focus_area": focus_area,
                "timeframe": timeframe,
                "skill_level": skill_level,
                "generated_at": datetime.now().isoformat(),
                "total_articles_analyzed": raw_results.get("analysis_stats", {}).get("total_articles", 0),
                "confidence_score": raw_results.get("confidence_metrics", {}).get("analysis_confidence", 0.0)
            },
            "new_tasks_overview": {
                "executive_summary": f"Analysis of {raw_results.get('analysis_stats', {}).get('total_articles', 0)} cybersecurity articles reveals emerging AI skills representing entirely new professional responsibilities. These skills constitute new job tasks that didn't exist before AI adoption and are becoming critical for cybersecurity professionals.",
                "key_findings": [
                    "AI skills represent fundamentally new professional capabilities",
                    "Most critical skills require 6-12 months of focused learning",
                    "New AI-related roles are emerging across all cybersecurity domains",
                    "Early skill adoption provides significant competitive advantage"
                ]
            },
            "skills_analysis": raw_results.get("skills_analysis", {}),
            "tools_analysis": raw_results.get("tools_analysis", {}),
            "learning_pathways": raw_results.get("learning_pathways", {}),
            "strategic_recommendations": raw_results.get("strategic_recommendations", []),
            "market_intelligence": raw_results.get("market_intelligence", {}),
            "confidence_metrics": raw_results.get("confidence_metrics", {}),
            "new_tasks_evidence": {
                "job_creation_indicators": self._extract_job_creation_signals(raw_results),
                "skill_emergence_patterns": self._extract_skill_emergence_patterns(raw_results),
                "capability_expansion_areas": self._extract_capability_expansion_areas(raw_results)
            }
        }
        
        return report
    
    def _extract_job_creation_signals(self, results: Dict[str, Any]) -> List[str]:
        """Extract evidence of new job creation from analysis results."""
        signals = []
        
        # Look for new role indicators in strategic recommendations
        recommendations = results.get("strategic_recommendations", [])
        for rec in recommendations:
            if any(keyword in rec.lower() for keyword in ["new role", "emerging position", "ai specialist", "ml engineer"]):
                signals.append(rec)
        
        # Add default signals if none found
        if not signals:
            signals = [
                "AI Security Specialist roles emerging in enterprise security teams",
                "MLOps Engineer positions created for AI system deployment",
                "AI Governance Officer roles for managing AI risk and compliance"
            ]
        
        return signals[:5]  # Top 5 signals
    
    def _extract_skill_emergence_patterns(self, results: Dict[str, Any]) -> List[str]:
        """Extract patterns showing skill emergence from analysis results."""
        patterns = []
        
        # Analyze high-priority skills for emergence patterns
        skills = results.get("skills_analysis", {})
        for skill_name, skill_data in skills.items():
            if skill_data.get("learning_priority") in ["critical", "high"] and skill_data.get("urgency", 0) >= 7:
                patterns.append(f"{skill_name}: {skill_data.get('why_important', 'Critical for AI-enhanced cybersecurity')}")
        
        return patterns[:7]  # Top 7 patterns
    
    def _extract_capability_expansion_areas(self, results: Dict[str, Any]) -> List[str]:
        """Extract areas where AI is expanding professional capabilities."""
        areas = []
        
        # Analyze tools for capability expansion
        tools = results.get("tools_analysis", {})
        for tool_name, tool_data in tools.items():
            if tool_data.get("adoption_trend") in ["emerging", "growing"] and tool_data.get("demand_level", 0) >= 7:
                use_cases = tool_data.get("use_cases", [])
                if use_cases:
                    areas.append(f"{tool_name}: Enabling {', '.join(use_cases[:2])}")
        
        return areas[:6]  # Top 6 areas

    def run_comprehensive_analysis(self, timeframe: str = "12months") -> Dict[str, Any]:
        """
        Run comprehensive AI skills analysis across all articles in database
        
        Args:
            timeframe: Prediction timeframe
            
        Returns:
            Aggregated analysis results
        """
        
        if not self.db_manager:
            return {"error": "Database not available"}
        
        self.logger.info(f"Starting comprehensive AI skills analysis for {timeframe}")
        
        # Load articles from database
        articles = self._load_articles()
        if not articles:
            return {"error": "No articles available for analysis"}
        
        aggregated_results = {
            'critical_skills': [],
            'critical_tools': [],
            'market_intelligence': {},
            'learning_pathways': {},
            'strategic_recommendations': [],
            'risk_assessment': {},
            'confidence_metrics': {},
            'key_insights': [],
            'analysis_metadata': {
                'timeframe': timeframe,
                'articles_analyzed': len(articles),
                'analysis_date': datetime.now().isoformat(),
                'method': 'Comprehensive multi-article analysis'
            }
        }
        
        # Analyze each article and aggregate results
        skill_aggregator = defaultdict(list)
        tool_aggregator = defaultdict(list)
        market_signals = []
        insights_collector = []
        
        successful_analyses = 0
        
        for i, article in enumerate(articles[:50]):  # Limit for performance
            try:
                content = article.get('content', '') + ' ' + article.get('wisdom', '')
                title = article.get('title', f'Article {i+1}')
                
                if not content.strip():
                    continue
                
                # Analyze individual article
                analysis = self.analyze_ai_skills_demand(content, title, timeframe)
                
                if analysis.get('analysis_method') == 'LLM-powered':
                    successful_analyses += 1
                    
                    # Aggregate skills
                    for skill in analysis.get('critical_skills', []):
                        skill_name = skill.get('skill', '').lower()
                        skill_aggregator[skill_name].append(skill)
                    
                    # Aggregate tools
                    for tool in analysis.get('critical_tools', []):
                        tool_name = tool.get('tool', '').lower()
                        tool_aggregator[tool_name].append(tool)
                    
                    # Collect market intelligence
                    market_intel = analysis.get('market_intelligence', {})
                    if market_intel:
                        market_signals.append(market_intel)
                    
                    # Collect insights
                    insights = analysis.get('key_insights', [])
                    insights_collector.extend(insights)
                
                # Log progress
                if (i + 1) % 10 == 0:
                    self.logger.info(f"Analyzed {i+1}/{len(articles)} articles")
                    
            except Exception as e:
                self.logger.error(f"Error analyzing article {i+1}: {e}")
                continue
        
        # Aggregate and prioritize results
        if successful_analyses > 0:
            aggregated_results['critical_skills'] = self._aggregate_skills(skill_aggregator)
            aggregated_results['critical_tools'] = self._aggregate_tools(tool_aggregator)
            aggregated_results['market_intelligence'] = self._aggregate_market_signals(market_signals)
            aggregated_results['key_insights'] = self._synthesize_insights(insights_collector)
            aggregated_results['learning_pathways'] = self._generate_pathways(aggregated_results)
            aggregated_results['strategic_recommendations'] = self._generate_strategic_recommendations(aggregated_results)
            aggregated_results['confidence_metrics'] = self._calculate_confidence(successful_analyses, len(articles))
        
        aggregated_results['analysis_metadata']['successful_analyses'] = successful_analyses
        
        self.logger.info(f"Comprehensive analysis complete: {successful_analyses} successful analyses")
        
        return aggregated_results

    def _load_articles(self) -> List[Dict]:
        """Load articles from database for analysis"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT a.id, a.title, a.content, 
                           COALESCE(c.category, 'unclassified') as category,
                           COALESCE(ss.overall_score, 0.7) as quality_score, 
                           a.collected_at, a.url
                    FROM artifacts a
                    LEFT JOIN classifications c ON a.id = c.artifact_id
                    LEFT JOIN source_scores ss ON a.id = ss.artifact_id
                    WHERE LENGTH(a.content) > 500
                    ORDER BY a.collected_at DESC, COALESCE(ss.overall_score, 0.7) DESC
                    LIMIT 50
                """)
                
                articles = []
                for row in cursor.fetchall():
                    articles.append({
                        'id': row[0],
                        'title': row[1],
                        'content': row[2],
                        'category': row[3],
                        'quality_score': row[4],
                        'created_at': row[5],
                        'url': row[6],
                        'wisdom': ''  # No wisdom field in current schema
                    })
                
                self.logger.info(f"Loaded {len(articles)} high-quality articles for analysis")
                return articles
                
        except Exception as e:
            self.logger.error(f"Failed to load articles: {e}")
            return []

    def _aggregate_skills(self, skill_aggregator: Dict) -> List[Dict]:
        """Aggregate skill data across multiple analyses"""
        aggregated_skills = []
        
        for skill_name, skill_list in skill_aggregator.items():
            if len(skill_list) < 2:  # Require multiple mentions
                continue
            
            # Calculate aggregated metrics
            avg_demand = statistics.mean([s.get('demand_level', 5) for s in skill_list])
            avg_growth = statistics.mean([s.get('growth_potential', 5) for s in skill_list])
            avg_impact = statistics.mean([s.get('career_impact', 5) for s in skill_list])
            avg_urgency = statistics.mean([s.get('urgency', 5) for s in skill_list])
            
            # Determine most common values
            categories = [s.get('category', '') for s in skill_list]
            difficulties = [s.get('difficulty_level', '') for s in skill_list]
            timeframes = [s.get('timeframe_relevance', '') for s in skill_list]
            
            most_common_category = Counter(categories).most_common(1)[0][0] if categories else ''
            most_common_difficulty = Counter(difficulties).most_common(1)[0][0] if difficulties else ''
            most_common_timeframe = Counter(timeframes).most_common(1)[0][0] if timeframes else ''
            
            # Calculate priority score
            priority_score = (avg_demand * 0.3 + avg_growth * 0.25 + avg_impact * 0.25 + avg_urgency * 0.2)
            
            aggregated_skills.append({
                'skill': skill_name,
                'category': most_common_category,
                'demand_level': round(avg_demand, 1),
                'growth_potential': round(avg_growth, 1),
                'career_impact': round(avg_impact, 1),
                'urgency': round(avg_urgency, 1),
                'difficulty_level': most_common_difficulty,
                'timeframe_relevance': most_common_timeframe,
                'priority_score': round(priority_score, 2),
                'mention_count': len(skill_list),
                'evidence_sources': len(set([s.get('evidence', '')[:50] for s in skill_list])),
                'learning_priority': 'critical' if priority_score >= 8 else 'high' if priority_score >= 6 else 'medium'
            })
        
        # Sort by priority score
        aggregated_skills.sort(key=lambda x: x['priority_score'], reverse=True)
        return aggregated_skills[:20]  # Top 20 skills

    def _aggregate_tools(self, tool_aggregator: Dict) -> List[Dict]:
        """Aggregate tool data across multiple analyses"""
        aggregated_tools = []
        
        for tool_name, tool_list in tool_aggregator.items():
            if len(tool_list) < 2:  # Require multiple mentions
                continue
            
            # Calculate aggregated metrics
            avg_demand = statistics.mean([t.get('demand_level', 5) for t in tool_list])
            avg_growth = statistics.mean([t.get('growth_potential', 5) for t in tool_list])
            
            # Determine most common values
            categories = [t.get('category', '') for t in tool_list]
            trends = [t.get('adoption_trend', '') for t in tool_list]
            
            most_common_category = Counter(categories).most_common(1)[0][0] if categories else ''
            most_common_trend = Counter(trends).most_common(1)[0][0] if trends else ''
            
            # Calculate adoption score
            adoption_score = avg_demand * 0.6 + avg_growth * 0.4
            
            aggregated_tools.append({
                'tool': tool_name,
                'category': most_common_category,
                'demand_level': round(avg_demand, 1),
                'growth_potential': round(avg_growth, 1),
                'adoption_trend': most_common_trend,
                'adoption_score': round(adoption_score, 2),
                'mention_count': len(tool_list),
                'learning_priority': 'critical' if adoption_score >= 8 else 'high' if adoption_score >= 6 else 'medium'
            })
        
        # Sort by adoption score
        aggregated_tools.sort(key=lambda x: x['adoption_score'], reverse=True)
        return aggregated_tools[:15]  # Top 15 tools

    def _aggregate_market_signals(self, market_signals: List[Dict]) -> Dict:
        """Aggregate market intelligence signals"""
        if not market_signals:
            return {}
        
        # Calculate average market metrics
        avg_hiring = statistics.mean([m.get('hiring_demand_strength', 5) for m in market_signals])
        avg_salary = statistics.mean([m.get('salary_impact_potential', 5) for m in market_signals])
        avg_gap = statistics.mean([m.get('skill_gap_severity', 5) for m in market_signals])
        avg_adoption = statistics.mean([m.get('industry_adoption_rate', 5) for m in market_signals])
        avg_maturity = statistics.mean([m.get('technology_maturity', 5) for m in market_signals])
        avg_urgency = statistics.mean([m.get('transformation_urgency', 5) for m in market_signals])
        
        return {
            'hiring_demand_strength': round(avg_hiring, 1),
            'salary_impact_potential': round(avg_salary, 1),
            'skill_gap_severity': round(avg_gap, 1),
            'industry_adoption_rate': round(avg_adoption, 1),
            'technology_maturity': round(avg_maturity, 1),
            'transformation_urgency': round(avg_urgency, 1),
            'market_health_score': round((avg_hiring + avg_salary + avg_adoption) / 3, 1),
            'opportunity_score': round((avg_gap + avg_urgency) / 2, 1)
        }

    def _synthesize_insights(self, insights_collector: List[str]) -> List[str]:
        """Synthesize key insights from all analyses"""
        # Remove duplicates and filter for quality
        unique_insights = list(set(insights_collector))
        
        # Sort by length and relevance (simple heuristic)
        quality_insights = [insight for insight in unique_insights if len(insight) > 30 and 'AI' in insight]
        
        return quality_insights[:10]  # Top 10 insights

    def _generate_pathways(self, aggregated_results: Dict) -> Dict:
        """Generate learning pathways based on aggregated results"""
        skills = aggregated_results.get('critical_skills', [])
        tools = aggregated_results.get('critical_tools', [])
        
        pathways = {
            'beginner_path': {
                'duration': '3-6 months',
                'priority_skills': [s['skill'] for s in skills if s.get('difficulty_level') == 'beginner'][:5],
                'recommended_tools': [t['tool'] for t in tools if t.get('learning_priority') in ['critical', 'high']][:3],
                'learning_approach': 'structured'
            },
            'intermediate_path': {
                'duration': '6-12 months',
                'priority_skills': [s['skill'] for s in skills if s.get('difficulty_level') == 'intermediate'][:5],
                'recommended_tools': [t['tool'] for t in tools if t.get('category') in ['ml_frameworks', 'data_platforms']][:4],
                'specialization_areas': ['ai_security', 'domain_specific']
            },
            'advanced_path': {
                'duration': '12-24 months',
                'priority_skills': [s['skill'] for s in skills if s.get('difficulty_level') == 'advanced'][:5],
                'recommended_tools': [t['tool'] for t in tools if t.get('adoption_trend') == 'emerging'][:3],
                'leadership_skills': ['ai_strategy', 'team_building', 'stakeholder_management']
            }
        }
        
        return pathways

    def _generate_strategic_recommendations(self, aggregated_results: Dict) -> List[str]:
        """Generate strategic recommendations based on analysis"""
        recommendations = []
        
        skills = aggregated_results.get('critical_skills', [])
        tools = aggregated_results.get('critical_tools', [])
        market = aggregated_results.get('market_intelligence', {})
        
        # Top skill recommendation
        if skills:
            top_skill = skills[0]
            recommendations.append(
                f"🎯 IMMEDIATE PRIORITY: Master '{top_skill['skill']}' - highest strategic value with {top_skill['priority_score']}/10 priority score and {top_skill['mention_count']} evidence sources"
            )
        
        # Market urgency recommendation
        urgency = market.get('transformation_urgency', 5)
        if urgency >= 7:
            recommendations.append(
                f"⚡ HIGH URGENCY: Market transformation accelerating ({urgency}/10) - prioritize immediate skill development over gradual learning"
            )
        
        # Tool platform recommendation
        if tools:
            top_tools = [t['tool'] for t in tools[:3]]
            recommendations.append(
                f"🛠️ PLATFORM STRATEGY: Focus on {', '.join(top_tools)} for maximum practical impact and industry relevance"
            )
        
        # Skill gap opportunity
        gap_severity = market.get('skill_gap_severity', 5)
        if gap_severity >= 6:
            recommendations.append(
                f"💰 OPPORTUNITY WINDOW: Severe skill gaps detected ({gap_severity}/10) - early adoption provides significant competitive advantage"
            )
        
        # Learning pathway recommendation
        beginner_skills = len([s for s in skills if s.get('difficulty_level') == 'beginner'])
        if beginner_skills >= 3:
            recommendations.append(
                f"📚 LEARNING APPROACH: {beginner_skills} foundational skills identified - build strong foundation before specializing"
            )
        
        return recommendations

    def _calculate_confidence(self, successful_analyses: int, total_articles: int) -> Dict:
        """Calculate confidence metrics for the analysis"""
        
        # Analysis coverage confidence
        coverage_confidence = min(successful_analyses / 20, 1.0)  # 20 analyses = high confidence
        
        # Data quality confidence
        data_quality = min(total_articles / 50, 1.0)  # 50 articles = high confidence
        
        # Overall confidence
        overall_confidence = (coverage_confidence + data_quality) / 2
        
        def confidence_level(score):
            if score >= 0.8: return "High"
            elif score >= 0.6: return "Medium"
            elif score >= 0.4: return "Low"
            else: return "Very Low"
        
        return {
            'analysis_confidence': coverage_confidence,
            'data_quality': data_quality,
            'prediction_reliability': overall_confidence,
            'market_signal_strength': min(successful_analyses / 30, 1.0),
            'overall_confidence_level': confidence_level(overall_confidence),
            'confidence_score': overall_confidence
        }


def main():
    """Main function for testing the AI Skills and Tools Predictor"""
    predictor = AISkillsToolsPredictor()
    
    print("AI Skills and Tools Predictor")
    print("="*50)
    
    # Example 1: Get the prediction prompt
    prompt = predictor.get_ai_skills_prediction_prompt("12months")
    print("Generated comprehensive AI skills prediction prompt")
    print(f"Prompt length: {len(prompt)} characters")
    
    # Example 2: Run sample analysis
    sample_content = """
    Artificial intelligence is transforming cybersecurity, with machine learning algorithms now capable 
    of detecting sophisticated threats that traditional rule-based systems miss. Organizations are 
    investing heavily in AI security tools, with Python programming skills and TensorFlow expertise 
    becoming essential for security analysts. The demand for professionals who can develop, deploy, 
    and monitor AI models in production environments is growing rapidly.
    """
    
    result = predictor.analyze_ai_skills_demand(sample_content, "AI in Cybersecurity", "12months")
    print(f"\nSample Analysis Method: {result.get('analysis_method', 'Unknown')}")
    
    # Example 3: Run comprehensive analysis if database available
    if predictor.db_manager:
        print("\nRunning comprehensive analysis...")
        comprehensive_results = predictor.run_comprehensive_analysis("12months")
        
        metadata = comprehensive_results.get('analysis_metadata', {})
        print(f"Analyzed: {metadata.get('articles_analyzed', 0)} articles")
        print(f"Successful analyses: {metadata.get('successful_analyses', 0)}")
        
        # Display top skills
        skills = comprehensive_results.get('critical_skills', [])
        if skills:
            print(f"\nTop 5 Critical AI Skills:")
            for i, skill in enumerate(skills[:5], 1):
                print(f"{i}. {skill.get('skill', 'Unknown')} (Priority: {skill.get('priority_score', 0)})")
        
        # Display recommendations
        recommendations = comprehensive_results.get('strategic_recommendations', [])
        if recommendations:
            print(f"\nStrategic Recommendations:")
            for i, rec in enumerate(recommendations, 1):
                print(f"{i}. {rec}")
    else:
        print("\nDatabase not available - skipping comprehensive analysis")


if __name__ == "__main__":
    main() 