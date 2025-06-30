#!/usr/bin/env python3
"""
AI Skills and Tools Predictor
Advanced prediction system for identifying critical AI skills and tools for workforce development
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

from aih.utils.database import get_database_connection
from aih.utils.logging import setup_logging

class AISkillsPredictor:
    """Advanced AI Skills and Tools Prediction System"""
    
    def __init__(self):
        self.logger = setup_logging()
        
        # Core AI skill categories with specific focus areas
        self.ai_skill_categories = {
            'foundational_ai': [
                'machine learning', 'deep learning', 'neural networks', 'artificial intelligence',
                'data science', 'statistics', 'linear algebra', 'calculus', 'probability',
                'algorithm design', 'computational thinking'
            ],
            'technical_ai_skills': [
                'python programming', 'r programming', 'sql', 'javascript', 'pytorch', 'tensorflow',
                'scikit-learn', 'pandas', 'numpy', 'matplotlib', 'seaborn', 'jupyter notebooks',
                'git version control', 'docker', 'kubernetes', 'cloud computing', 'aws', 'azure', 'gcp'
            ],
            'ai_engineering': [
                'mlops', 'model deployment', 'model monitoring', 'feature engineering', 'data pipelines',
                'model versioning', 'a/b testing', 'experiment tracking', 'automated testing',
                'model optimization', 'model compression', 'edge deployment', 'production scaling'
            ],
            'ai_security': [
                'adversarial attacks', 'model security', 'data privacy', 'differential privacy',
                'federated learning', 'secure multiparty computation', 'ai governance',
                'model interpretability', 'bias detection', 'fairness metrics', 'ethical ai'
            ],
            'domain_specific_ai': [
                'computer vision', 'natural language processing', 'speech recognition',
                'robotics', 'autonomous systems', 'recommendation systems', 'time series analysis',
                'generative ai', 'large language models', 'multimodal ai', 'reinforcement learning'
            ],
            'ai_strategy_management': [
                'ai strategy', 'digital transformation', 'change management', 'stakeholder alignment',
                'roi measurement', 'risk assessment', 'vendor management', 'team building',
                'project management', 'agile methodologies', 'cross-functional collaboration'
            ],
            'emerging_ai_fields': [
                'quantum machine learning', 'neuromorphic computing', 'edge ai', 'ai chips',
                'prompt engineering', 'fine-tuning', 'model merging', 'constitutional ai',
                'ai safety', 'alignment research', 'interpretable ai', 'causal inference'
            ]
        }
        
        # AI tools and platforms taxonomy
        self.ai_tools_categories = {
            'ml_frameworks': [
                'tensorflow', 'pytorch', 'scikit-learn', 'keras', 'xgboost', 'lightgbm',
                'catboost', 'h2o.ai', 'auto-sklearn', 'mlflow', 'weights & biases', 'neptune'
            ],
            'data_platforms': [
                'databricks', 'snowflake', 'apache spark', 'hadoop', 'kafka', 'airflow',
                'prefect', 'dask', 'ray', 'apache beam', 'bigquery', 'redshift'
            ],
            'cloud_ai_services': [
                'aws sagemaker', 'azure ml', 'google ai platform', 'vertex ai',
                'aws bedrock', 'azure openai', 'amazon comprehend', 'google translate',
                'aws rekognition', 'azure cognitive services'
            ],
            'llm_platforms': [
                'openai api', 'anthropic claude', 'hugging face', 'langchain', 'llama index',
                'pinecone', 'weaviate', 'chroma', 'ollama', 'together ai', 'replicate'
            ],
            'development_tools': [
                'visual studio code', 'pycharm', 'jupyter lab', 'colab', 'kaggle kernels',
                'streamlit', 'gradio', 'dash', 'fastapi', 'flask', 'docker', 'kubernetes'
            ],
            'monitoring_governance': [
                'wandb', 'mlflow', 'neptune', 'comet', 'tensorboard', 'evidently ai',
                'whylabs', 'fiddler', 'arthur ai', 'truera', 'datadog', 'prometheus'
            ]
        }
        
        # Initialize database connection
        try:
            self.db = get_database_connection()
            self.logger.info("AI Skills Predictor initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            self.db = None

    def predict_critical_ai_skills(self, timeframe: str = "12months") -> Dict[str, Any]:
        """
        Main prediction method that analyzes content to predict critical AI skills and tools
        
        Args:
            timeframe: Prediction timeframe (6months, 12months, 24months)
            
        Returns:
            Comprehensive prediction results
        """
        self.logger.info(f"Starting AI skills prediction analysis for {timeframe}")
        
        # Load articles from database
        articles = self._load_articles()
        if not articles:
            return {"error": "No articles available for analysis"}
        
        # Run comprehensive AI skills analysis
        skills_analysis = self._analyze_ai_skills_demand(articles, timeframe)
        tools_analysis = self._analyze_ai_tools_trends(articles, timeframe)
        market_analysis = self._analyze_market_demand_signals(articles, timeframe)
        learning_pathways = self._generate_learning_pathways(skills_analysis, tools_analysis)
        career_impact = self._assess_career_impact(skills_analysis, articles)
        
        # Generate strategic recommendations
        recommendations = self._generate_strategic_recommendations(
            skills_analysis, tools_analysis, market_analysis, timeframe
        )
        
        # Calculate confidence metrics
        confidence_metrics = self._calculate_confidence_metrics(articles, skills_analysis)
        
        return {
            'skills_analysis': skills_analysis,
            'tools_analysis': tools_analysis,
            'market_analysis': market_analysis,
            'learning_pathways': learning_pathways,
            'career_impact': career_impact,
            'recommendations': recommendations,
            'confidence_metrics': confidence_metrics,
            'timeframe': timeframe,
            'analysis_date': datetime.now().isoformat(),
            'data_source': f"{len(articles)} articles analyzed",
            'methodology': 'LLM-powered content analysis + trend modeling'
        }

    def _analyze_ai_skills_demand(self, articles: List[Dict], timeframe: str) -> Dict[str, Any]:
        """Analyze AI skills demand using LLM-powered content analysis"""
        
        skills_demand = {category: {} for category in self.ai_skill_categories.keys()}
        skill_trends = defaultdict(list)
        skill_contexts = defaultdict(list)
        
        # Use LLM analysis for sophisticated skills extraction
        try:
            import openai
            client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            llm_available = True
        except (ImportError, Exception):
            llm_available = False
            self.logger.warning("OpenAI not available - using pattern matching fallback")
        
        for article in articles:
            content = article.get('content', '') + ' ' + article.get('wisdom', '')
            title = article.get('title', '')
            category = article.get('category', 'unknown')
            
            if not content.strip():
                continue
            
            if llm_available:
                # LLM-powered skills analysis
                analysis = self._llm_analyze_ai_skills(client, title, content, timeframe)
                if analysis:
                    self._aggregate_llm_skills_analysis(analysis, skills_demand, skill_trends, skill_contexts)
            else:
                # Fallback to pattern matching
                self._pattern_analyze_ai_skills(content, skills_demand, skill_trends)
        
        # Rank and prioritize skills
        prioritized_skills = self._prioritize_skills(skills_demand, skill_trends, timeframe)
        emerging_skills = self._identify_emerging_skills(skill_trends, skill_contexts)
        declining_skills = self._identify_declining_skills(skill_trends)
        
        return {
            'skills_by_category': skills_demand,
            'prioritized_skills': prioritized_skills,
            'emerging_skills': emerging_skills,
            'declining_skills': declining_skills,
            'skill_trends': dict(skill_trends),
            'total_skills_analyzed': sum(len(skills) for skills in skills_demand.values()),
            'analysis_method': 'LLM-powered' if llm_available else 'Pattern-based'
        }

    def _llm_analyze_ai_skills(self, client, title: str, content: str, timeframe: str) -> Dict:
        """Use LLM to analyze AI skills mentioned in content"""
        
        # Create comprehensive skills analysis prompt
        skills_prompt = f"""
Analyze this technology/cybersecurity article for AI skills and tools that will be CRITICAL to learn in the next {timeframe}.

Title: {title}
Content: {content[:3000]}...

Your task: Identify AI skills and tools mentioned or IMPLIED that will be important for cybersecurity professionals.

Focus on:
1. FOUNDATIONAL AI SKILLS (math, programming, ML basics)
2. TECHNICAL AI SKILLS (frameworks, tools, platforms) 
3. AI ENGINEERING (MLOps, deployment, monitoring)
4. AI SECURITY (model security, privacy, governance)
5. DOMAIN-SPECIFIC AI (computer vision, NLP, etc.)
6. AI STRATEGY & MANAGEMENT (leadership, implementation)
7. EMERGING AI FIELDS (quantum ML, edge AI, prompt engineering)

For each skill/tool mentioned:
- Rate DEMAND LEVEL (1-10): How in-demand will this be?
- Rate GROWTH POTENTIAL (1-10): How much will demand grow?
- Rate CAREER IMPACT (1-10): How much will this impact careers?
- Provide EVIDENCE: Quote or reasoning from the article

Return JSON:
{{
  "critical_skills": [
    {{
      "skill": "specific skill name",
      "category": "foundational_ai|technical_ai_skills|ai_engineering|ai_security|domain_specific_ai|ai_strategy_management|emerging_ai_fields",
      "demand_level": 1-10,
      "growth_potential": 1-10,
      "career_impact": 1-10,
      "evidence": "quote or reasoning from article",
      "timeframe_relevance": "immediate|6months|12months|24months",
      "difficulty_level": "beginner|intermediate|advanced|expert"
    }}
  ],
  "critical_tools": [
    {{
      "tool": "specific tool/platform name",
      "category": "ml_frameworks|data_platforms|cloud_ai_services|llm_platforms|development_tools|monitoring_governance",
      "demand_level": 1-10,
      "growth_potential": 1-10,
      "adoption_trend": "emerging|growing|mature|declining",
      "evidence": "quote or reasoning from article"
    }}
  ],
  "market_signals": {{
    "hiring_demand": 1-10,
    "salary_impact": 1-10,
    "industry_adoption": 1-10,
    "skill_gap_severity": 1-10
  }},
  "confidence_score": 0.0-1.0,
  "key_insights": ["insight 1", "insight 2", "insight 3"]
}}

Focus on PRACTICAL, LEARNABLE skills that cybersecurity professionals should prioritize.
"""

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": skills_prompt}],
                temperature=0.3,
                max_tokens=2000
            )
            
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            self.logger.error(f"LLM analysis failed: {e}")
            return None

    def _analyze_ai_tools_trends(self, articles: List[Dict], timeframe: str) -> Dict[str, Any]:
        """Analyze AI tools and platform trends"""
        
        tools_mentions = defaultdict(int)
        tools_contexts = defaultdict(list)
        tools_trends = defaultdict(list)
        
        # Extract tool mentions and contexts
        for article in articles:
            content = article.get('content', '') + ' ' + article.get('wisdom', '')
            category = article.get('category', 'unknown')
            
            for tool_category, tools in self.ai_tools_categories.items():
                for tool in tools:
                    pattern = r'\b' + re.escape(tool.lower()) + r'\b'
                    matches = re.findall(pattern, content.lower())
                    
                    if matches:
                        tools_mentions[tool] += len(matches)
                        tools_trends[tool].append(category)
                        
                        # Extract context
                        context = self._extract_tool_context(content, tool)
                        if context:
                            tools_contexts[tool].append(context)
        
        # Rank tools by importance and trend
        trending_tools = self._rank_trending_tools(tools_mentions, tools_trends, tools_contexts)
        platform_recommendations = self._generate_platform_recommendations(trending_tools)
        
        return {
            'tools_by_category': self._categorize_tools(tools_mentions),
            'trending_tools': trending_tools,
            'platform_recommendations': platform_recommendations,
            'adoption_signals': self._analyze_adoption_signals(tools_contexts),
            'total_tools_analyzed': len(tools_mentions)
        }

    def _generate_learning_pathways(self, skills_analysis: Dict, tools_analysis: Dict) -> Dict[str, Any]:
        """Generate structured learning pathways for different career levels"""
        
        pathways = {
            'beginner': {
                'title': 'AI Foundations for Cybersecurity Professionals',
                'duration': '3-6 months',
                'skills': [],
                'tools': [],
                'resources': []
            },
            'intermediate': {
                'title': 'Applied AI in Cybersecurity',
                'duration': '6-12 months',
                'skills': [],
                'tools': [],
                'resources': []
            },
            'advanced': {
                'title': 'AI Security Leadership & Innovation',
                'duration': '12-24 months',
                'skills': [],
                'tools': [],
                'resources': []
            }
        }
        
        # Populate pathways based on analysis
        prioritized_skills = skills_analysis.get('prioritized_skills', [])
        trending_tools = tools_analysis.get('trending_tools', [])
        
        for skill_data in prioritized_skills[:20]:  # Top 20 skills
            skill = skill_data.get('skill', '')
            difficulty = skill_data.get('difficulty_level', 'intermediate')
            
            if difficulty in pathways:
                pathways[difficulty]['skills'].append(skill)
        
        for tool_data in trending_tools[:15]:  # Top 15 tools
            tool = tool_data.get('tool', '')
            complexity = self._assess_tool_complexity(tool)
            
            if complexity in pathways:
                pathways[complexity]['tools'].append(tool)
        
        # Add learning resources recommendations
        for level in pathways:
            pathways[level]['resources'] = self._recommend_learning_resources(level)
        
        return pathways

    def _generate_strategic_recommendations(self, skills_analysis: Dict, tools_analysis: Dict, 
                                         market_analysis: Dict, timeframe: str) -> List[str]:
        """Generate strategic recommendations for AI skills development"""
        
        recommendations = []
        
        # Top skills recommendations
        top_skills = skills_analysis.get('prioritized_skills', [])[:5]
        if top_skills:
            top_skill = top_skills[0].get('skill', 'Unknown')
            recommendations.append(
                f"🎯 PRIORITY #1: Master '{top_skill}' - highest predicted demand with {top_skills[0].get('demand_level', 0)}/10 importance score"
            )
        
        # Emerging skills opportunities
        emerging = skills_analysis.get('emerging_skills', [])[:3]
        if emerging:
            recommendations.append(
                f"⭐ EMERGING OPPORTUNITY: Early investment in {', '.join([s.get('skill', '') for s in emerging])} could provide significant competitive advantage"
            )
        
        # Platform strategy
        trending_tools = tools_analysis.get('trending_tools', [])[:3]
        if trending_tools:
            recommendations.append(
                f"🛠️ PLATFORM FOCUS: Prioritize {', '.join([t.get('tool', '') for t in trending_tools])} for immediate practical impact"
            )
        
        # Market timing
        market_signals = market_analysis.get('signals', {})
        hiring_demand = market_signals.get('avg_hiring_demand', 0)
        if hiring_demand >= 7:
            recommendations.append(
                f"🚀 MARKET TIMING: High hiring demand detected ({hiring_demand}/10) - accelerate skill development for {timeframe} career opportunities"
            )
        
        # Skill gap warnings
        declining_skills = skills_analysis.get('declining_skills', [])
        if declining_skills:
            declining_names = [s.get('skill', '') for s in declining_skills[:2]]
            recommendations.append(
                f"⚠️ RESKILL ALERT: Consider transitioning from {', '.join(declining_names)} to growing AI-enhanced alternatives"
            )
        
        # Learning pathway recommendation
        total_skills = len(skills_analysis.get('prioritized_skills', []))
        if total_skills >= 10:
            recommendations.append(
                f"📚 LEARNING STRATEGY: Follow structured pathway - start with foundations, then specialize in domain-specific AI applications"
            )
        
        return recommendations

    def _load_articles(self) -> List[Dict]:
        """Load articles from database"""
        if not self.db:
            return []
        
        try:
            cursor = self.db.cursor()
            cursor.execute("""
                SELECT id, title, content, category, wisdom, created_at, quality_score, url
                FROM artifacts 
                WHERE category IN ('replace', 'augment', 'new_tasks', 'human_only')
                ORDER BY created_at DESC
                LIMIT 500
            """)
            
            articles = []
            for row in cursor.fetchall():
                articles.append({
                    'id': row[0],
                    'title': row[1],
                    'content': row[2],
                    'category': row[3],
                    'wisdom': row[4],
                    'created_at': row[5],
                    'quality_score': row[6],
                    'url': row[7]
                })
            
            self.logger.info(f"Loaded {len(articles)} articles for analysis")
            return articles
            
        except Exception as e:
            self.logger.error(f"Failed to load articles: {e}")
            return []

    def _aggregate_llm_skills_analysis(self, analysis: Dict, skills_demand: Dict, 
                                     skill_trends: Dict, skill_contexts: Dict):
        """Aggregate LLM analysis results into skills tracking"""
        
        critical_skills = analysis.get('critical_skills', [])
        for skill_data in critical_skills:
            skill = skill_data.get('skill', '').lower()
            category = skill_data.get('category', 'technical_ai_skills')
            
            if category in skills_demand:
                if skill not in skills_demand[category]:
                    skills_demand[category][skill] = {
                        'demand_level': [],
                        'growth_potential': [],
                        'career_impact': [],
                        'evidence': [],
                        'timeframe_relevance': [],
                        'difficulty_level': []
                    }
                
                skills_demand[category][skill]['demand_level'].append(skill_data.get('demand_level', 5))
                skills_demand[category][skill]['growth_potential'].append(skill_data.get('growth_potential', 5))
                skills_demand[category][skill]['career_impact'].append(skill_data.get('career_impact', 5))
                skills_demand[category][skill]['evidence'].append(skill_data.get('evidence', ''))
                skills_demand[category][skill]['timeframe_relevance'].append(skill_data.get('timeframe_relevance', '12months'))
                skills_demand[category][skill]['difficulty_level'].append(skill_data.get('difficulty_level', 'intermediate'))
            
            skill_trends[skill].append(skill_data)
            skill_contexts[skill].append(skill_data.get('evidence', ''))

    def _prioritize_skills(self, skills_demand: Dict, skill_trends: Dict, timeframe: str) -> List[Dict]:
        """Prioritize skills based on demand, growth potential, and career impact"""
        
        prioritized = []
        
        for category, skills in skills_demand.items():
            for skill, data in skills.items():
                if not data.get('demand_level'):
                    continue
                
                avg_demand = statistics.mean(data['demand_level'])
                avg_growth = statistics.mean(data['growth_potential']) if data.get('growth_potential') else avg_demand
                avg_impact = statistics.mean(data['career_impact']) if data.get('career_impact') else avg_demand
                
                # Calculate priority score
                priority_score = (avg_demand * 0.4 + avg_growth * 0.35 + avg_impact * 0.25)
                
                # Timeframe relevance boost
                timeframe_boost = 1.0
                if timeframe in ['6months', '12months']:
                    immediate_relevance = sum(1 for t in data.get('timeframe_relevance', []) 
                                            if t in ['immediate', '6months', '12months'])
                    if immediate_relevance > 0:
                        timeframe_boost = 1.2
                
                final_score = priority_score * timeframe_boost
                
                prioritized.append({
                    'skill': skill,
                    'category': category,
                    'priority_score': final_score,
                    'demand_level': avg_demand,
                    'growth_potential': avg_growth,
                    'career_impact': avg_impact,
                    'evidence_count': len(data['evidence']),
                    'difficulty_level': statistics.mode(data['difficulty_level']) if data['difficulty_level'] else 'intermediate'
                })
        
        # Sort by priority score
        prioritized.sort(key=lambda x: x['priority_score'], reverse=True)
        return prioritized

    def _identify_emerging_skills(self, skill_trends: Dict, skill_contexts: Dict) -> List[Dict]:
        """Identify emerging skills with high growth potential"""
        
        emerging = []
        
        for skill, trend_data in skill_trends.items():
            if len(trend_data) < 2:  # Need multiple mentions
                continue
            
            # Check for growth indicators in contexts
            contexts = skill_contexts.get(skill, [])
            growth_indicators = ['emerging', 'new', 'future', 'next-generation', 'cutting-edge', 'innovative']
            
            growth_score = 0
            for context in contexts:
                for indicator in growth_indicators:
                    if indicator in context.lower():
                        growth_score += 1
            
            if growth_score > 0:
                # Calculate emergence score
                avg_growth = statistics.mean([t.get('growth_potential', 5) for t in trend_data])
                emergence_score = (growth_score / len(contexts)) * avg_growth
                
                emerging.append({
                    'skill': skill,
                    'emergence_score': emergence_score,
                    'growth_indicators': growth_score,
                    'mentions': len(trend_data),
                    'avg_growth_potential': avg_growth
                })
        
        emerging.sort(key=lambda x: x['emergence_score'], reverse=True)
        return emerging[:10]

    def _identify_declining_skills(self, skill_trends: Dict) -> List[Dict]:
        """Identify skills showing decline patterns"""
        
        declining = []
        
        for skill, trend_data in skill_trends.items():
            if len(trend_data) < 3:  # Need sufficient data
                continue
            
            # Check for decline indicators
            demand_levels = [t.get('demand_level', 5) for t in trend_data]
            
            if len(demand_levels) >= 3:
                # Simple trend analysis
                recent_avg = statistics.mean(demand_levels[-2:])  # Last 2 mentions
                early_avg = statistics.mean(demand_levels[:2])    # First 2 mentions
                
                if recent_avg < early_avg and recent_avg < 4:  # Declining and low demand
                    declining.append({
                        'skill': skill,
                        'decline_score': early_avg - recent_avg,
                        'recent_demand': recent_avg,
                        'mentions': len(trend_data)
                    })
        
        declining.sort(key=lambda x: x['decline_score'], reverse=True)
        return declining[:5]

    def _analyze_market_demand_signals(self, articles: List[Dict], timeframe: str) -> Dict[str, Any]:
        """Analyze market demand signals from article content"""
        
        demand_indicators = []
        hiring_signals = []
        salary_signals = []
        
        for article in articles:
            content = article.get('content', '') + ' ' + article.get('wisdom', '')
            
            # Look for market demand indicators
            hiring_keywords = ['hiring', 'jobs', 'career', 'employment', 'recruitment', 'talent shortage']
            salary_keywords = ['salary', 'compensation', 'pay', 'wages', 'earning potential']
            demand_keywords = ['demand', 'shortage', 'need', 'required', 'essential', 'critical']
            
            for keyword in hiring_keywords:
                if keyword in content.lower():
                    hiring_signals.append(self._extract_signal_context(content, keyword))
            
            for keyword in salary_keywords:
                if keyword in content.lower():
                    salary_signals.append(self._extract_signal_context(content, keyword))
            
            for keyword in demand_keywords:
                if keyword in content.lower():
                    demand_indicators.append(self._extract_signal_context(content, keyword))
        
        return {
            'signals': {
                'hiring_demand_mentions': len(hiring_signals),
                'salary_impact_mentions': len(salary_signals),
                'market_demand_mentions': len(demand_indicators),
                'avg_hiring_demand': min(len(hiring_signals) / 10, 10),  # Normalize to 1-10
                'avg_salary_impact': min(len(salary_signals) / 5, 10),
                'market_urgency': min(len(demand_indicators) / 15, 10)
            },
            'hiring_contexts': hiring_signals[:10],
            'salary_contexts': salary_signals[:10],
            'demand_contexts': demand_indicators[:10]
        }

    def _extract_signal_context(self, content: str, keyword: str) -> str:
        """Extract context around market signal keywords"""
        
        keyword_index = content.lower().find(keyword.lower())
        if keyword_index == -1:
            return ""
        
        start = max(0, keyword_index - 100)
        end = min(len(content), keyword_index + len(keyword) + 100)
        return content[start:end].strip()

    def _extract_tool_context(self, content: str, tool: str) -> str:
        """Extract context around tool mentions"""
        
        tool_index = content.lower().find(tool.lower())
        if tool_index == -1:
            return ""
        
        start = max(0, tool_index - 80)
        end = min(len(content), tool_index + len(tool) + 80)
        return content[start:end].strip()

    def _calculate_confidence_metrics(self, articles: List[Dict], skills_analysis: Dict) -> Dict[str, str]:
        """Calculate confidence levels for predictions"""
        
        # Data volume confidence
        data_confidence = min(len(articles) / 100, 1.0)  # 100 articles = high confidence
        
        # Skills coverage confidence  
        total_skills = skills_analysis.get('total_skills_analyzed', 0)
        skills_confidence = min(total_skills / 50, 1.0)  # 50 skills = high confidence
        
        # Evidence strength confidence
        prioritized_skills = skills_analysis.get('prioritized_skills', [])
        evidence_scores = [s.get('evidence_count', 0) for s in prioritized_skills[:10]]
        evidence_confidence = min(statistics.mean(evidence_scores) / 5, 1.0) if evidence_scores else 0.0
        
        # Overall confidence
        overall_confidence = (data_confidence + skills_confidence + evidence_confidence) / 3
        
        def confidence_level(score):
            if score >= 0.8:
                return "High"
            elif score >= 0.6:
                return "Medium"
            elif score >= 0.4:
                return "Low"
            else:
                return "Very Low"
        
        return {
            'data_volume_confidence': confidence_level(data_confidence),
            'skills_coverage_confidence': confidence_level(skills_confidence),
            'evidence_strength_confidence': confidence_level(evidence_confidence),
            'overall_confidence': confidence_level(overall_confidence),
            'confidence_score': overall_confidence
        }

    # Additional helper methods...
    def _pattern_analyze_ai_skills(self, content: str, skills_demand: Dict, skill_trends: Dict):
        """Fallback pattern-based analysis when LLM not available"""
        # Implementation for pattern matching fallback
        pass

    def _categorize_tools(self, tools_mentions: Dict) -> Dict:
        """Categorize tools by their types"""
        # Implementation for tool categorization
        pass

    def _rank_trending_tools(self, tools_mentions: Dict, tools_trends: Dict, tools_contexts: Dict) -> List[Dict]:
        """Rank tools by trending patterns"""
        # Implementation for tool ranking
        pass

    def _generate_platform_recommendations(self, trending_tools: List[Dict]) -> List[str]:
        """Generate platform-specific recommendations"""
        # Implementation for platform recommendations
        pass

    def _analyze_adoption_signals(self, tools_contexts: Dict) -> Dict:
        """Analyze adoption signals from tool contexts"""
        # Implementation for adoption analysis
        pass

    def _assess_tool_complexity(self, tool: str) -> str:
        """Assess learning complexity of a tool"""
        # Simple complexity assessment
        complex_tools = ['kubernetes', 'tensorflow', 'pytorch', 'apache spark']
        intermediate_tools = ['docker', 'scikit-learn', 'pandas', 'streamlit']
        
        if tool.lower() in complex_tools:
            return 'advanced'
        elif tool.lower() in intermediate_tools:
            return 'intermediate'
        else:
            return 'beginner'

    def _recommend_learning_resources(self, level: str) -> List[str]:
        """Recommend learning resources by level"""
        resources = {
            'beginner': [
                "Coursera AI for Cybersecurity Specialization",
                "MIT Introduction to Machine Learning course",
                "Python programming fundamentals",
                "Statistics and linear algebra review"
            ],
            'intermediate': [
                "Advanced ML algorithms and applications",
                "MLOps and model deployment platforms",
                "AI security and adversarial attacks course",
                "Cloud AI services hands-on labs"
            ],
            'advanced': [
                "AI research papers and conferences",
                "Custom model development projects",
                "AI governance and ethics frameworks",
                "Industry mentorship and networking"
            ]
        }
        return resources.get(level, [])

    def _assess_career_impact(self, skills_analysis: Dict, articles: List[Dict]) -> Dict[str, Any]:
        """Assess career impact of AI skills adoption"""
        
        prioritized_skills = skills_analysis.get('prioritized_skills', [])
        
        # Calculate potential career impacts
        high_impact_skills = [s for s in prioritized_skills if s.get('career_impact', 0) >= 8]
        salary_impact_potential = statistics.mean([s.get('career_impact', 5) for s in prioritized_skills[:10]]) if prioritized_skills else 5
        
        # Job security analysis
        security_enhancing = len([s for s in prioritized_skills if 'security' in s.get('skill', '')])
        automation_resistance = len([s for s in prioritized_skills if s.get('category') in ['ai_strategy_management', 'human_only']])
        
        return {
            'high_impact_skills_count': len(high_impact_skills),
            'salary_impact_potential': salary_impact_potential,
            'job_security_enhancement': security_enhancing,
            'automation_resistance_skills': automation_resistance,
            'career_transformation_likelihood': 'High' if salary_impact_potential >= 7 else 'Medium' if salary_impact_potential >= 5 else 'Low'
        }


def main():
    """Main function for testing the AI Skills Predictor"""
    predictor = AISkillsPredictor()
    
    # Run prediction analysis
    results = predictor.predict_critical_ai_skills("12months")
    
    print("AI Skills Prediction Results:")
    print("="*50)
    print(f"Analysis Method: {results.get('analysis_method', 'Unknown')}")
    print(f"Confidence Level: {results.get('confidence_metrics', {}).get('overall_confidence', 'Unknown')}")
    print(f"Data Source: {results.get('data_source', 'Unknown')}")
    
    # Display top skills
    prioritized = results.get('skills_analysis', {}).get('prioritized_skills', [])
    if prioritized:
        print(f"\nTop 5 Critical AI Skills:")
        for i, skill in enumerate(prioritized[:5], 1):
            print(f"{i}. {skill.get('skill', 'Unknown')} (Score: {skill.get('priority_score', 0):.2f})")
    
    # Display recommendations
    recommendations = results.get('recommendations', [])
    if recommendations:
        print(f"\nStrategic Recommendations:")
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec}")


if __name__ == "__main__":
    main() 