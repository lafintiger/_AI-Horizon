#!/usr/bin/env python3
"""
AI Adoption Rate Predictions Analysis Tool

This module provides comprehensive predictive analysis of AI adoption patterns 
in cybersecurity, with specific focus on skill demand forecasting and 
workforce transformation predictions.

Features:
- Skill demand forecasting based on current trends
- Workforce transformation predictions by category
- Technology adoption curve analysis
- Enterprise adoption rate modeling
- Geographic and industry-specific insights
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import sqlite3
import json
import re
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import statistics
from typing import Dict, List, Tuple, Any
import logging

from aih.utils.database import DatabaseManager

class AIAdoptionPredictor:
    """Comprehensive AI adoption rate predictions and workforce transformation analysis."""
    
    def __init__(self):
        """Initialize the AI Adoption Predictor with enhanced DCWF task focus."""
        self.db_manager = DatabaseManager()
        self.logger = logging.getLogger(__name__)
        
        # Enhanced cybersecurity skills with DCWF task focus
        self.cybersecurity_skills = [
            # Technical Skills (DCWF Core Tasks)
            'vulnerability assessment', 'incident response', 'threat detection', 
            'penetration testing', 'security monitoring', 'forensic analysis',
            'risk assessment', 'compliance', 'network security', 'endpoint security',
            'cloud security', 'application security', 'data protection', 'identity management',
            'security architecture', 'cryptography', 'malware analysis', 'threat hunting',
            'security automation', 'SIEM management',
            
            # DCWF Specialty Areas
            'security operations', 'security engineering', 'security consulting',
            'governance risk compliance', 'security training', 'security research',
            'digital forensics', 'cyber threat intelligence', 'privacy protection',
            'business continuity', 'disaster recovery',
            
            # Human-Centric Skills (Enhanced with AI collaboration)
            'strategic planning', 'leadership', 'communication', 'decision making',
            'problem solving', 'critical thinking', 'project management',
            'stakeholder management', 'crisis management', 'ethical reasoning',
            
            # Emerging Hybrid Skills (AI-Enhanced Tasks)
            'ai security', 'machine learning security', 'threat modeling', 
            'security analytics', 'behavioral analysis', 'risk modeling',
            'automated response', 'security orchestration', 'adaptive security',
            'zero trust architecture', 'devsecops', 'cloud native security'
        ]
        
        # DCWF Task Categories mapped to AI Impact
        self.dcwf_task_mapping = {
            'replace': [
                'routine log analysis', 'basic vulnerability scanning', 'simple alert triage',
                'standard compliance checking', 'basic malware signature detection',
                'routine patch management', 'basic report generation'
            ],
            'augment': [
                'complex threat analysis', 'advanced incident response', 'strategic risk assessment',
                'threat intelligence analysis', 'security architecture design', 'forensic investigation',
                'compliance auditing', 'security training delivery', 'crisis communication'
            ],
            'new_tasks': [
                'ai security governance', 'algorithm bias detection', 'ai model security',
                'automated threat response', 'ai-powered threat hunting', 'behavioral analytics',
                'adaptive security controls', 'ai compliance validation'
            ],
            'human_only': [
                'ethical decision making', 'executive briefings', 'stakeholder negotiation',
                'crisis leadership', 'strategic planning', 'team building',
                'vendor relationships', 'regulatory liaison', 'board reporting'
            ]
        }
        
        # Technology adoption indicators
        self.adoption_indicators = [
            'implementation', 'deployment', 'adoption', 'integration', 'transformation',
            'automation', 'ai-powered', 'machine learning', 'artificial intelligence',
            'intelligent', 'automated', 'smart', 'predictive', 'adaptive'
        ]

    def analyze_skill_demand_forecasting(self, artifacts: List[Dict]) -> Dict[str, Any]:
        """
        Analyze skill demand patterns with focus on DCWF tasks and cybersecurity framework.
        
        Args:
            artifacts: List of artifact documents
            
        Returns:
            Dictionary containing skill demand forecasting results
        """
        self.logger.info("Analyzing DCWF-focused skill demand forecasting")
        
        skill_mentions = {}
        skill_sentiments = {}
        skill_categories = {}
        temporal_trends = {}
        
        for artifact in artifacts:
            content = artifact.get('content', '')
            category = artifact.get('category', 'unknown')
            created_date = artifact.get('created_at', '')
            
            if not content:
                continue
                
            # Analyze each cybersecurity skill
            for skill in self.cybersecurity_skills:
                pattern = r'\b' + re.escape(skill.lower()) + r'\b'
                matches = re.findall(pattern, content.lower())
                
                if matches:
                    # Count mentions
                    skill_mentions[skill] = skill_mentions.get(skill, 0) + len(matches)
                    
                    # Track by category
                    if skill not in skill_categories:
                        skill_categories[skill] = {}
                    skill_categories[skill][category] = skill_categories[skill].get(category, 0) + len(matches)
                    
                    # Extract context and analyze sentiment
                    context = self._extract_skill_context(content, skill)
                    sentiment = self._analyze_skill_sentiment(context)
                    
                    if skill not in skill_sentiments:
                        skill_sentiments[skill] = []
                    skill_sentiments[skill].append(sentiment)
                    
                    # Track temporal trends
                    if created_date:
                        month_key = created_date[:7]  # YYYY-MM
                        if month_key not in temporal_trends:
                            temporal_trends[month_key] = {}
                        temporal_trends[month_key][skill] = temporal_trends[month_key].get(skill, 0) + len(matches)
        
        # Calculate averages and forecasts
        skill_forecasts = {}
        for skill in skill_mentions:
            sentiments = skill_sentiments.get(skill, [0])
            categories = skill_categories.get(skill, {})
            
            skill_forecasts[skill] = self._generate_skill_forecast(
                skill, list(categories.keys()), sentiments, temporal_trends
            )
        
        # Rank skills by demand potential
        high_demand_skills = []
        emerging_skills = []
        declining_skills = []
        
        for skill, forecast in skill_forecasts.items():
            demand_score = forecast['demand_score']
            growth_trend = forecast['growth_trend']
            
            if demand_score >= 0.7:
                high_demand_skills.append({
                    'skill': skill,
                    'demand_score': demand_score,
                    'mentions': skill_mentions[skill],
                    'growth_trend': growth_trend,
                    'forecast': forecast
                })
            elif growth_trend >= 0.5:
                emerging_skills.append({
                    'skill': skill,
                    'demand_score': demand_score,
                    'mentions': skill_mentions[skill],
                    'growth_trend': growth_trend,
                    'forecast': forecast
                })
            elif growth_trend <= -0.3:
                declining_skills.append({
                    'skill': skill,
                    'demand_score': demand_score,
                    'mentions': skill_mentions[skill],
                    'growth_trend': growth_trend,
                    'forecast': forecast
                })
        
        # Sort by demand score
        high_demand_skills.sort(key=lambda x: x['demand_score'], reverse=True)
        emerging_skills.sort(key=lambda x: x['growth_trend'], reverse=True)
        declining_skills.sort(key=lambda x: x['growth_trend'])
        
        return {
            'skill_analysis': {
                'total_skills_analyzed': len(self.cybersecurity_skills),
                'skills_with_mentions': len(skill_mentions),
                'high_demand_skills': high_demand_skills[:10],
                'emerging_skills': emerging_skills[:10],
                'declining_skills': declining_skills[:5]
            },
            'dcwf_task_insights': self._analyze_dcwf_task_transformation(artifacts),
            'forecast_summary': self._generate_forecast_summary(
                high_demand_skills, emerging_skills, declining_skills
            ),
            'confidence_level': self._calculate_forecast_confidence(len(artifacts), len(skill_mentions))
        }

    def analyze_workforce_transformation_predictions(self, artifacts: List[Dict]) -> Dict[str, Any]:
        """Predict workforce transformation patterns across AI impact categories."""
        
        category_transformations = defaultdict(lambda: defaultdict(list))
        role_evolution = defaultdict(list)
        transformation_timeline = defaultdict(lambda: defaultdict(int))
        
        # Analyze transformation indicators by category
        for artifact in artifacts:
            content = artifact.get('content', '') + ' ' + artifact.get('wisdom', '')
            category = artifact.get('category', 'unknown')
            
            if not content:
                continue
            
            # Extract transformation indicators
            transformations = self._extract_transformation_patterns(content)
            
            for transformation_type, indicators in transformations.items():
                category_transformations[category][transformation_type].extend(indicators)
            
            # Analyze role evolution patterns
            roles = self._extract_role_mentions(content)
            for role in roles:
                role_evolution[role].append(category)
            
            # Timeline analysis
            timeline_indicators = self._extract_timeline_indicators(content)
            for timeline, intensity in timeline_indicators.items():
                transformation_timeline[timeline][category] += intensity
        
        # Generate transformation predictions
        predictions = {}
        
        for category in ['replace', 'augment', 'new_tasks', 'human_only']:
            if category in category_transformations:
                prediction = self._generate_transformation_prediction(
                    category, 
                    category_transformations[category],
                    role_evolution,
                    transformation_timeline
                )
                predictions[category] = prediction
        
        # Overall workforce transformation insights
        transformation_velocity = self._calculate_transformation_velocity(transformation_timeline)
        critical_transition_periods = self._identify_critical_periods(transformation_timeline)
        workforce_readiness = self._assess_workforce_readiness(category_transformations, role_evolution)
        
        return {
            'category_predictions': predictions,
            'transformation_velocity': transformation_velocity,
            'critical_transition_periods': critical_transition_periods,
            'workforce_readiness': workforce_readiness,
            'role_evolution_patterns': dict(role_evolution),
            'transformation_summary': self._generate_transformation_summary(predictions, transformation_velocity)
        }

    def analyze_technology_adoption_curve(self, artifacts: List[Dict]) -> Dict[str, Any]:
        """Analyze technology adoption patterns and predict adoption curves."""
        
        adoption_mentions = defaultdict(list)
        adoption_stages = defaultdict(int)
        enterprise_adoption = defaultdict(list)
        
        # Define adoption stage keywords
        stage_keywords = {
            'early_adopters': ['pilot', 'prototype', 'testing', 'trial', 'experiment'],
            'early_majority': ['implementation', 'deployment', 'rollout', 'adoption'],
            'late_majority': ['widespread', 'standard', 'mainstream', 'enterprise-wide'],
            'laggards': ['resistance', 'slow adoption', 'traditional', 'reluctant']
        }
        
        for artifact in artifacts:
            content = artifact.get('content', '') + ' ' + artifact.get('wisdom', '')
            
            if not content:
                continue
            
            # Identify adoption stage indicators
            for stage, keywords in stage_keywords.items():
                for keyword in keywords:
                    if keyword.lower() in content.lower():
                        adoption_stages[stage] += 1
            
            # Extract technology mentions with adoption context
            for indicator in self.adoption_indicators:
                pattern = r'\b' + re.escape(indicator.lower()) + r'\b[^.]{0,100}'
                matches = re.findall(pattern, content.lower())
                for match in matches:
                    adoption_mentions[indicator].append(match)
            
            # Enterprise adoption patterns
            enterprise_patterns = self._extract_enterprise_adoption_patterns(content)
            for pattern_type, mentions in enterprise_patterns.items():
                enterprise_adoption[pattern_type].extend(mentions)
        
        # Calculate adoption curve position
        total_mentions = sum(adoption_stages.values())
        if total_mentions > 0:
            adoption_distribution = {
                stage: (count / total_mentions) * 100 
                for stage, count in adoption_stages.items()
            }
        else:
            adoption_distribution = {}
        
        # Predict adoption trajectory
        current_phase = self._determine_current_adoption_phase(adoption_distribution)
        next_phase_timeline = self._predict_next_phase_timeline(adoption_distribution, adoption_mentions)
        
        return {
            'adoption_stages': dict(adoption_stages),
            'adoption_distribution': adoption_distribution,
            'current_phase': current_phase,
            'next_phase_timeline': next_phase_timeline,
            'enterprise_adoption_patterns': dict(enterprise_adoption),
            'technology_readiness': self._assess_technology_readiness(adoption_mentions),
            'adoption_curve_summary': self._generate_adoption_curve_summary(current_phase, adoption_distribution)
        }

    def _extract_skill_context(self, content: str, skill: str) -> str:
        """Extract context around skill mentions for sentiment analysis."""
        
        skill_pattern = r'\b' + re.escape(skill.lower()) + r'\b'
        match = re.search(skill_pattern, content.lower())
        
        if match:
            start = max(0, match.start() - 100)
            end = min(len(content), match.end() + 100)
            return content[start:end]
        
        return ""

    def _analyze_skill_sentiment(self, context: str) -> float:
        """Analyze sentiment around skill mentions."""
        
        positive_indicators = [
            'demand', 'growth', 'important', 'critical', 'essential', 'valuable',
            'opportunity', 'advantage', 'benefit', 'improvement', 'enhance'
        ]
        
        negative_indicators = [
            'replace', 'automate', 'eliminate', 'reduce', 'decline', 'obsolete',
            'threat', 'risk', 'challenge', 'difficulty', 'problem'
        ]
        
        positive_score = sum(1 for indicator in positive_indicators if indicator in context.lower())
        negative_score = sum(1 for indicator in negative_indicators if indicator in context.lower())
        
        if positive_score + negative_score == 0:
            return 0.0
        
        return (positive_score - negative_score) / (positive_score + negative_score)

    def _generate_skill_forecast(self, skill: str, categories: List[str], sentiments: List[float], temporal_trends: Dict) -> Dict[str, Any]:
        """Generate forecast data for a specific skill."""
        
        # Calculate demand score based on categories and sentiments
        category_weights = {
            'replace': 0.3,    # Lower weight for replaced skills
            'augment': 0.8,    # High weight for augmented skills
            'new_tasks': 0.9,  # Highest weight for new tasks
            'human_only': 0.7  # High weight for human-only skills
        }
        
        # Calculate weighted demand based on categories
        demand_score = 0.0
        if categories:
            for category in categories:
                demand_score += category_weights.get(category, 0.5)
            demand_score = min(demand_score / len(categories), 1.0)
        else:
            demand_score = 0.5  # Default moderate demand
        
        # Factor in sentiment
        avg_sentiment = statistics.mean(sentiments) if sentiments else 0.0
        sentiment_factor = (avg_sentiment + 1) / 2  # Normalize from [-1,1] to [0,1]
        demand_score = (demand_score * 0.7 + sentiment_factor * 0.3)
        
        # Calculate growth trend from temporal data
        growth_trend = 0.0
        if temporal_trends:
            skill_trends = []
            for month, skills in temporal_trends.items():
                if skill in skills:
                    skill_trends.append((month, skills[skill]))
            
            if len(skill_trends) >= 2:
                # Calculate simple linear trend
                skill_trends.sort()  # Sort by month
                early_mentions = sum([count for _, count in skill_trends[:len(skill_trends)//2]])
                late_mentions = sum([count for _, count in skill_trends[len(skill_trends)//2:]])
                
                if early_mentions > 0:
                    growth_trend = (late_mentions - early_mentions) / early_mentions
                else:
                    growth_trend = 1.0 if late_mentions > 0 else 0.0
                
                # Normalize to [-1, 1] range
                growth_trend = max(-1.0, min(1.0, growth_trend))
        
        return {
            'demand_score': demand_score,
            'growth_trend': growth_trend,
            'sentiment_avg': avg_sentiment,
            'categories': categories,
            'forecast_confidence': min(len(sentiments) / 10, 1.0),  # Based on data points
            'market_positioning': self._get_market_positioning(demand_score, growth_trend)
        }
    
    def _get_market_positioning(self, demand_score: float, growth_trend: float) -> str:
        """Determine market positioning based on demand and growth."""
        if demand_score >= 0.7 and growth_trend >= 0.3:
            return "High Priority - Strong Growth"
        elif demand_score >= 0.7:
            return "High Priority - Stable Demand"
        elif growth_trend >= 0.5:
            return "Emerging Opportunity"
        elif demand_score >= 0.5:
            return "Moderate Priority"
        elif growth_trend <= -0.3:
            return "Declining - Reskill Focus"
        else:
            return "Low Priority - Monitor"

    def _extract_transformation_patterns(self, content: str) -> Dict[str, List[str]]:
        """Extract workforce transformation patterns from content."""
        
        patterns = {
            'automation': [],
            'augmentation': [],
            'reskilling': [],
            'role_creation': [],
            'role_elimination': []
        }
        
        # Define pattern keywords
        automation_keywords = ['automate', 'automated', 'automation', 'replace', 'eliminate jobs']
        augmentation_keywords = ['augment', 'enhance', 'assist', 'support', 'collaborate']
        reskilling_keywords = ['reskill', 'retrain', 'upskill', 'training', 'education']
        creation_keywords = ['new role', 'emerging job', 'create position', 'new career']
        elimination_keywords = ['job loss', 'position eliminated', 'role obsolete', 'career ending']
        
        pattern_map = {
            'automation': automation_keywords,
            'augmentation': augmentation_keywords,
            'reskilling': reskilling_keywords,
            'role_creation': creation_keywords,
            'role_elimination': elimination_keywords
        }
        
        for pattern_type, keywords in pattern_map.items():
            for keyword in keywords:
                if keyword.lower() in content.lower():
                    patterns[pattern_type].append(keyword)
        
        return patterns

    def _extract_role_mentions(self, content: str) -> List[str]:
        """Extract cybersecurity role mentions from content."""
        
        roles = [
            'security analyst', 'cybersecurity analyst', 'security engineer', 'security architect',
            'incident response specialist', 'threat hunter', 'penetration tester', 'security consultant',
            'compliance officer', 'risk analyst', 'security manager', 'ciso', 'security director',
            'vulnerability assessor', 'security operations', 'soc analyst', 'security specialist'
        ]
        
        mentioned_roles = []
        for role in roles:
            if role.lower() in content.lower():
                mentioned_roles.append(role)
        
        return mentioned_roles

    def _extract_timeline_indicators(self, content: str) -> Dict[str, int]:
        """Extract transformation timeline indicators."""
        
        timeline_patterns = {
            'immediate': ['now', 'immediately', 'current', 'today', 'this year'],
            'short_term': ['next year', '2025', '2026', 'soon', 'near future'],
            'medium_term': ['2027', '2028', '2029', '2030', 'next decade', 'coming years'],
            'long_term': ['2030+', 'future', 'eventually', 'long term', 'decades']
        }
        
        timeline_intensity = defaultdict(int)
        
        for timeline, patterns in timeline_patterns.items():
            for pattern in patterns:
                timeline_intensity[timeline] += content.lower().count(pattern.lower())
        
        return dict(timeline_intensity)

    def _calculate_growth_trend(self, monthly_data: Dict[str, int]) -> float:
        """Calculate growth trend from monthly mention data."""
        
        if len(monthly_data) < 2:
            return 0.0
        
        # Sort by month
        sorted_months = sorted(monthly_data.items())
        values = [count for _, count in sorted_months]
        
        if all(v == 0 for v in values):
            return 0.0
        
        # Simple linear trend calculation
        n = len(values)
        x_values = list(range(n))
        
        # Calculate slope
        x_mean = statistics.mean(x_values)
        y_mean = statistics.mean(values)
        
        numerator = sum((x_values[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0.0
        
        slope = numerator / denominator
        
        # Normalize slope to [-1, 1] range
        max_value = max(values) if values else 1
        normalized_slope = slope / max_value if max_value > 0 else 0
        
        return max(-1, min(1, normalized_slope))

    def run_comprehensive_analysis(self) -> Dict[str, Any]:
        """Run complete AI adoption predictions analysis."""
        
        try:
            # Fetch all artifacts
            artifacts = self.db_manager.get_artifacts()
            
            if not artifacts:
                return {
                    'error': 'No artifacts found in database',
                    'total_analyzed': 0
                }
            
            self.logger.info(f"Analyzing {len(artifacts)} artifacts for AI adoption predictions")
            
            # Run all analysis components
            skill_demand = self.analyze_skill_demand_forecasting(artifacts)
            workforce_transformation = self.analyze_workforce_transformation_predictions(artifacts)
            adoption_curve = self.analyze_technology_adoption_curve(artifacts)
            
            # Generate executive summary
            executive_summary = self._generate_executive_summary(
                skill_demand, workforce_transformation, adoption_curve, len(artifacts)
            )
            
            # Calculate confidence metrics
            confidence_metrics = self._calculate_confidence_metrics(
                skill_demand, workforce_transformation, adoption_curve
            )
            
            return {
                'executive_summary': executive_summary,
                'skill_demand_forecasting': skill_demand,
                'workforce_transformation_predictions': workforce_transformation,
                'technology_adoption_curve': adoption_curve,
                'confidence_metrics': confidence_metrics,
                'total_analyzed': len(artifacts),
                'analysis_timestamp': datetime.now().isoformat(),
                'recommendations': self._generate_strategic_recommendations(
                    skill_demand, workforce_transformation, adoption_curve
                )
            }
            
        except Exception as e:
            self.logger.error(f"Error in AI adoption predictions analysis: {str(e)}")
            return {
                'error': f"Analysis failed: {str(e)}",
                'total_analyzed': 0
            }

    def _generate_executive_summary(self, skill_demand: Dict, workforce_transformation: Dict, 
                                  adoption_curve: Dict, total_articles: int) -> Dict[str, Any]:
        """Generate executive summary of AI adoption predictions."""
        
        # Top insights from each analysis
        top_skills = skill_demand.get('high_demand_skills', [])[:3]
        transformation_velocity = workforce_transformation.get('transformation_velocity', {})
        current_adoption_phase = adoption_curve.get('current_phase', 'unknown')
        
        return {
            'total_articles_analyzed': total_articles,
            'top_high_demand_skills': [skill[0] for skill in top_skills],
            'transformation_speed': transformation_velocity.get('overall_speed', 'moderate'),
            'adoption_phase': current_adoption_phase,
            'key_insights': [
                f"Analyzed {skill_demand.get('total_skills_analyzed', 0)} skills for demand forecasting",
                f"Identified {len(skill_demand.get('high_demand_skills', []))} high-demand skills",
                f"Current AI adoption phase: {current_adoption_phase}",
                f"Workforce transformation speed: {transformation_velocity.get('overall_speed', 'moderate')}"
            ]
        }

    def _calculate_confidence_metrics(self, skill_demand: Dict, workforce_transformation: Dict, 
                                    adoption_curve: Dict) -> Dict[str, str]:
        """Calculate confidence levels for predictions."""
        
        # Skill demand confidence
        skill_forecasts = skill_demand.get('skill_forecasts', {})
        avg_skill_confidence = statistics.mean([
            forecast['confidence'] for forecast in skill_forecasts.values()
        ]) if skill_forecasts else 0.0
        
        # Data volume confidence
        total_skills = skill_demand.get('total_skills_analyzed', 0)
        data_confidence = min(1.0, total_skills / 50)  # 50 skills = high confidence
        
        # Overall confidence
        overall_confidence = (avg_skill_confidence + data_confidence) / 2
        
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
            'skill_demand_confidence': confidence_level(avg_skill_confidence),
            'data_volume_confidence': confidence_level(data_confidence),
            'overall_confidence': confidence_level(overall_confidence)
        }

    def _generate_strategic_recommendations(self, skill_demand: Dict, workforce_transformation: Dict, 
                                          adoption_curve: Dict) -> List[str]:
        """Generate strategic recommendations based on analysis."""
        
        recommendations = []
        
        # Skill development recommendations
        high_demand_skills = skill_demand.get('high_demand_skills', [])
        if high_demand_skills:
            top_skill = high_demand_skills[0][0] if high_demand_skills else None
            if top_skill:
                recommendations.append(
                    f"Prioritize training in '{top_skill}' - highest predicted demand"
                )
        
        # Workforce transformation recommendations
        transformation_speed = workforce_transformation.get('transformation_velocity', {}).get('overall_speed', 'moderate')
        if transformation_speed == 'rapid':
            recommendations.append(
                "Accelerate reskilling programs due to rapid transformation pace"
            )
        elif transformation_speed == 'slow':
            recommendations.append(
                "Leverage gradual transformation pace for comprehensive skill development"
            )
        
        # Adoption curve recommendations
        current_phase = adoption_curve.get('current_phase', '')
        if 'early' in current_phase.lower():
            recommendations.append(
                "Prepare for mainstream adoption - establish AI governance frameworks"
            )
        elif 'majority' in current_phase.lower():
            recommendations.append(
                "Focus on optimization and efficiency in AI implementation"
            )
        
        return recommendations

    def generate_report(self, output_file: str = None) -> str:
        """Generate comprehensive AI adoption predictions report."""
        
        results = self.run_comprehensive_analysis()
        
        if 'error' in results:
            return f"Error generating report: {results['error']}"
        
        # Generate timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if not output_file:
            output_file = f"data/reports/ai_adoption_predictions_{timestamp}.md"
        
        # Ensure reports directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Generate markdown report
        report_content = self._generate_markdown_report(results)
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            self.logger.info(f"AI adoption predictions report saved to {output_file}")
            return output_file
            
        except Exception as e:
            self.logger.error(f"Error saving report: {str(e)}")
            return f"Error saving report: {str(e)}"

    def _generate_markdown_report(self, results: Dict[str, Any]) -> str:
        """Generate markdown report from analysis results."""
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        report = f"""# AI Adoption Rate Predictions Analysis Report

**Generated:** {timestamp}  
**Total Articles Analyzed:** {results.get('total_analyzed', 0)}  
**Analysis Confidence:** {results.get('confidence_metrics', {}).get('overall_confidence', 'Unknown')}

---

## Executive Summary

{self._format_executive_summary(results.get('executive_summary', {}))}

---

## Skill Demand Forecasting

{self._format_skill_demand_section(results.get('skill_demand_forecasting', {}))}

---

## Workforce Transformation Predictions

{self._format_workforce_transformation_section(results.get('workforce_transformation_predictions', {}))}

---

## Technology Adoption Curve Analysis

{self._format_adoption_curve_section(results.get('technology_adoption_curve', {}))}

---

## Strategic Recommendations

{self._format_recommendations_section(results.get('recommendations', []))}

---

## Confidence Metrics

{self._format_confidence_section(results.get('confidence_metrics', {}))}

---

*Report generated by AI-Horizon AI Adoption Predictions Analysis Tool*
"""
        
        return report

    def _format_executive_summary(self, summary: Dict[str, Any]) -> str:
        """Format executive summary section."""
        
        insights = summary.get('key_insights', [])
        top_skills = summary.get('top_high_demand_skills', [])
        
        content = f"""
### Key Findings

- **Articles Analyzed:** {summary.get('total_articles_analyzed', 0)}
- **Current Adoption Phase:** {summary.get('adoption_phase', 'Unknown')}
- **Transformation Speed:** {summary.get('transformation_speed', 'Unknown')}
- **Top High-Demand Skills:** {', '.join(top_skills[:3]) if top_skills else 'None identified'}

### Critical Insights

"""
        
        for insight in insights:
            content += f"- {insight}\n"
        
        return content

    def _format_skill_demand_section(self, skill_data: Dict[str, Any]) -> str:
        """Format skill demand forecasting section."""
        
        report = []
        
        # Skill demand forecasting section
        high_demand = skill_data.get('skill_analysis', {}).get('high_demand_skills', [])
        for i, skill_info in enumerate(high_demand[:10], 1):
            skill = skill_info.get('skill', 'Unknown')
            forecast = skill_info.get('forecast', {})
            confidence = forecast.get('forecast_confidence', 0)
            demand = forecast.get('demand_score', 0)
            trend = forecast.get('growth_trend', 0)
            positioning = forecast.get('market_positioning', 'Unknown')
            
            report.append(f"{i}. **{skill.title()}**")
            report.append(f"   - Demand Score: {demand:.3f}")
            report.append(f"   - Growth Trend: {trend:+.3f}")
            report.append(f"   - Market Position: {positioning}")
            report.append(f"   - Forecast Confidence: {confidence:.2f}")
            report.append("")
        
        # Emerging skills
        emerging = skill_data.get('skill_analysis', {}).get('emerging_skills', [])
        if emerging:
            report.append("### 🌟 Emerging High-Growth Skills")
            report.append("")
            for i, skill_info in enumerate(emerging[:5], 1):
                skill = skill_info.get('skill', 'Unknown')
                trend = skill_info.get('growth_trend', 0)
                report.append(f"{i}. **{skill.title()}** (Growth: {trend:+.3f})")
            report.append("")
        
        # DCWF Task Analysis
        dcwf_data = skill_data.get('dcwf_task_insights', {})
        if dcwf_data:
            report.append("## 🎯 DCWF Task Transformation Analysis")
            report.append("")
            
            task_transformations = dcwf_data.get('task_transformations', {})
            for category, data in task_transformations.items():
                if data.get('tasks_identified', 0) > 0:
                    level = data.get('transformation_level', 'Unknown')
                    count = data.get('tasks_identified', 0)
                    report.append(f"### {category.title().replace('_', ' ')} Tasks")
                    report.append(f"- **Transformation Level**: {level}")
                    report.append(f"- **Tasks Identified**: {count}")
                    
                    tasks = data.get('tasks_list', [])
                    if tasks:
                        report.append(f"- **Key Tasks**: {', '.join(tasks)}")
                    report.append("")
            
            # DCWF Strategic Insights
            insights = dcwf_data.get('dcwf_insights', [])
            if insights:
                report.append("### 📋 DCWF Strategic Insights")
                report.append("")
                for insight in insights:
                    report.append(f"- {insight}")
                report.append("")
        
        # Forecast summary
        forecast_summary = skill_data.get('forecast_summary', 'No summary available')
        report.append("### Forecast Summary")
        report.append(forecast_summary)
        report.append("")
        
        return "\n".join(report)

    def _format_workforce_transformation_section(self, workforce_data: Dict[str, Any]) -> str:
        """Format workforce transformation predictions section."""
        
        content = f"""
### Transformation Velocity

**Overall Speed:** {workforce_data.get('transformation_velocity', {}).get('overall_speed', 'Unknown')}

### Category Predictions

"""
        
        predictions = workforce_data.get('category_predictions', {})
        for category, prediction in predictions.items():
            content += f"#### {category.upper().replace('_', ' ')}\n\n"
            # Add prediction details here based on the structure
            content += f"- Transformation Pattern: {prediction.get('pattern', 'Unknown')}\n"
            content += f"- Timeline: {prediction.get('timeline', 'Unknown')}\n\n"
        
        content += f"""
### Workforce Readiness Assessment

{workforce_data.get('workforce_readiness', {}).get('summary', 'Assessment not available')}

### Transformation Summary

{workforce_data.get('transformation_summary', 'No summary available')}
"""
        
        return content

    def _format_adoption_curve_section(self, adoption_data: Dict[str, Any]) -> str:
        """Format technology adoption curve section."""
        
        content = f"""
### Current Adoption Phase

**Phase:** {adoption_data.get('current_phase', 'Unknown')}

### Adoption Distribution

"""
        
        distribution = adoption_data.get('adoption_distribution', {})
        for stage, percentage in distribution.items():
            content += f"- **{stage.replace('_', ' ').title()}:** {percentage:.1f}%\n"
        
        content += f"""

### Technology Readiness

{adoption_data.get('technology_readiness', {}).get('summary', 'Assessment not available')}

### Adoption Curve Summary

{adoption_data.get('adoption_curve_summary', 'No summary available')}
"""
        
        return content

    def _format_recommendations_section(self, recommendations: List[str]) -> str:
        """Format strategic recommendations section."""
        
        if not recommendations:
            return "No specific recommendations generated."
        
        content = ""
        for i, recommendation in enumerate(recommendations, 1):
            content += f"{i}. {recommendation}\n"
        
        return content

    def _format_confidence_section(self, confidence: Dict[str, str]) -> str:
        """Format confidence metrics section."""
        
        return f"""
- **Skill Demand Confidence:** {confidence.get('skill_demand_confidence', 'Unknown')}
- **Data Volume Confidence:** {confidence.get('data_volume_confidence', 'Unknown')}
- **Overall Analysis Confidence:** {confidence.get('overall_confidence', 'Unknown')}

*Higher confidence levels indicate more reliable predictions based on data volume and quality.*
"""

    # Additional helper methods for comprehensive analysis
    def _generate_transformation_prediction(self, category: str, transformations: Dict, 
                                          role_evolution: Dict, timeline: Dict) -> Dict[str, Any]:
        """Generate transformation prediction for a specific category."""
        
        # Analyze transformation intensity
        total_mentions = sum(len(indicators) for indicators in transformations.values())
        
        if total_mentions == 0:
            return {
                'pattern': 'insufficient_data',
                'timeline': 'unknown',
                'intensity': 0.0,
                'confidence': 0.0
            }
        
        # Determine dominant transformation pattern
        dominant_pattern = max(transformations.keys(), 
                             key=lambda k: len(transformations[k]))
        
        # Estimate timeline based on mentions
        timeline_scores = {period: sum(timeline.get(period, {}).values()) 
                          for period in ['immediate', 'short_term', 'medium_term', 'long_term']}
        
        predicted_timeline = max(timeline_scores.keys(), 
                               key=lambda k: timeline_scores[k]) if any(timeline_scores.values()) else 'unknown'
        
        return {
            'pattern': dominant_pattern,
            'timeline': predicted_timeline,
            'intensity': min(1.0, total_mentions / 10),
            'confidence': min(1.0, total_mentions / 5)
        }

    def _calculate_transformation_velocity(self, timeline_data: Dict) -> Dict[str, Any]:
        """Calculate overall transformation velocity."""
        
        immediate_score = sum(timeline_data.get('immediate', {}).values())
        short_term_score = sum(timeline_data.get('short_term', {}).values())
        medium_term_score = sum(timeline_data.get('medium_term', {}).values())
        long_term_score = sum(timeline_data.get('long_term', {}).values())
        
        total_score = immediate_score + short_term_score + medium_term_score + long_term_score
        
        if total_score == 0:
            return {'overall_speed': 'unknown', 'confidence': 0.0}
        
        # Calculate weighted velocity (immediate = highest weight)
        velocity_score = (immediate_score * 4 + short_term_score * 3 + 
                         medium_term_score * 2 + long_term_score * 1) / total_score
        
        if velocity_score >= 3.0:
            speed = 'rapid'
        elif velocity_score >= 2.0:
            speed = 'moderate'
        else:
            speed = 'gradual'
        
        return {
            'overall_speed': speed,
            'velocity_score': velocity_score,
            'confidence': min(1.0, total_score / 20)
        }

    def _identify_critical_periods(self, timeline_data: Dict) -> List[str]:
        """Identify critical transformation periods."""
        
        period_scores = {}
        for period, categories in timeline_data.items():
            period_scores[period] = sum(categories.values())
        
        # Sort periods by intensity
        sorted_periods = sorted(period_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Return top 2 critical periods
        return [period for period, score in sorted_periods[:2] if score > 0]

    def _assess_workforce_readiness(self, transformations: Dict, role_evolution: Dict) -> Dict[str, Any]:
        """Assess overall workforce readiness for transformation."""
        
        # Count reskilling mentions across all categories
        reskilling_mentions = sum(
            len(cat_data.get('reskilling', [])) 
            for cat_data in transformations.values()
        )
        
        # Count role creation vs elimination
        creation_mentions = sum(
            len(cat_data.get('role_creation', [])) 
            for cat_data in transformations.values()
        )
        
        elimination_mentions = sum(
            len(cat_data.get('role_elimination', [])) 
            for cat_data in transformations.values()
        )
        
        # Calculate readiness score
        total_transformation_mentions = reskilling_mentions + creation_mentions + elimination_mentions
        
        if total_transformation_mentions == 0:
            readiness_level = 'unknown'
            summary = 'Insufficient data to assess workforce readiness'
        else:
            reskilling_ratio = reskilling_mentions / total_transformation_mentions
            
            if reskilling_ratio >= 0.4:
                readiness_level = 'high'
                summary = 'Strong focus on reskilling indicates good workforce readiness'
            elif reskilling_ratio >= 0.2:
                readiness_level = 'moderate'
                summary = 'Moderate reskilling activity suggests developing readiness'
            else:
                readiness_level = 'low'
                summary = 'Limited reskilling mentions indicate potential readiness gaps'
        
        return {
            'readiness_level': readiness_level,
            'reskilling_ratio': reskilling_mentions / total_transformation_mentions if total_transformation_mentions > 0 else 0,
            'summary': summary
        }

    def _extract_enterprise_adoption_patterns(self, content: str) -> Dict[str, List[str]]:
        """Extract enterprise-specific adoption patterns."""
        
        patterns = {
            'enterprise_scale': [],
            'implementation_challenges': [],
            'success_factors': []
        }
        
        # Enterprise scale indicators
        scale_keywords = ['enterprise', 'large-scale', 'organization-wide', 'corporate', 'company-wide']
        for keyword in scale_keywords:
            if keyword.lower() in content.lower():
                patterns['enterprise_scale'].append(keyword)
        
        # Implementation challenges
        challenge_keywords = ['challenge', 'difficulty', 'barrier', 'obstacle', 'resistance']
        for keyword in challenge_keywords:
            if keyword.lower() in content.lower():
                patterns['implementation_challenges'].append(keyword)
        
        # Success factors
        success_keywords = ['success', 'benefit', 'advantage', 'improvement', 'efficiency']
        for keyword in success_keywords:
            if keyword.lower() in content.lower():
                patterns['success_factors'].append(keyword)
        
        return patterns

    def _determine_current_adoption_phase(self, distribution: Dict[str, float]) -> str:
        """Determine current adoption phase based on distribution."""
        
        if not distribution:
            return 'unknown'
        
        # Find dominant phase
        dominant_phase = max(distribution.keys(), key=lambda k: distribution[k])
        
        # Map to readable phase names
        phase_mapping = {
            'early_adopters': 'Early Adopters Phase',
            'early_majority': 'Early Majority Phase',
            'late_majority': 'Late Majority Phase',
            'laggards': 'Late Adopters Phase'
        }
        
        return phase_mapping.get(dominant_phase, dominant_phase.title())

    def _predict_next_phase_timeline(self, distribution: Dict, adoption_mentions: Dict) -> str:
        """Predict timeline for next adoption phase."""
        
        if not distribution:
            return 'unknown'
        
        # Simple heuristic based on current dominant phase
        dominant_phase = max(distribution.keys(), key=lambda k: distribution[k])
        
        timeline_mapping = {
            'early_adopters': '1-2 years to Early Majority',
            'early_majority': '2-3 years to Late Majority',
            'late_majority': '3-5 years to full adoption',
            'laggards': 'Full adoption achieved'
        }
        
        return timeline_mapping.get(dominant_phase, 'Timeline uncertain')

    def _assess_technology_readiness(self, adoption_mentions: Dict) -> Dict[str, Any]:
        """Assess overall technology readiness level."""
        
        total_mentions = sum(len(mentions) for mentions in adoption_mentions.values())
        
        if total_mentions == 0:
            return {
                'level': 'unknown',
                'summary': 'Insufficient data to assess technology readiness'
            }
        
        # Count implementation vs experimental mentions
        implementation_indicators = ['implementation', 'deployment', 'integration', 'automated']
        experimental_indicators = ['pilot', 'testing', 'trial', 'prototype']
        
        implementation_count = sum(
            len(adoption_mentions.get(indicator, [])) 
            for indicator in implementation_indicators
        )
        
        experimental_count = sum(
            len(adoption_mentions.get(indicator, [])) 
            for indicator in experimental_indicators
        )
        
        if implementation_count > experimental_count:
            level = 'production_ready'
            summary = 'Technology shows strong production readiness indicators'
        elif experimental_count > 0:
            level = 'experimental'
            summary = 'Technology in experimental/pilot phase'
        else:
            level = 'emerging'
            summary = 'Technology in early emergence phase'
        
        return {
            'level': level,
            'summary': summary,
            'implementation_ratio': implementation_count / total_mentions if total_mentions > 0 else 0
        }

    def _generate_forecast_summary(self, high_demand: List, emerging: List, declining: List) -> str:
        """Generate executive summary of skill forecasting."""
        return (f"Forecasting analysis identified {len(high_demand)} high-demand skills, "
                f"{len(emerging)} emerging skills with growth potential, and "
                f"{len(declining)} skills showing decline indicators. "
                f"{'Strong' if len(high_demand) > 5 else 'Moderate' if len(high_demand) > 2 else 'Limited'} "
                f"skill demand growth detected - {'positive' if len(declining) < 3 else 'mixed'} market outlook.")

    def _analyze_dcwf_task_transformation(self, artifacts: List[Dict]) -> Dict[str, Any]:
        """Analyze how DCWF tasks are being transformed by AI across categories."""
        task_transformations = {category: [] for category in self.dcwf_task_mapping.keys()}
        transformation_evidence = {}
        
        for artifact in artifacts:
            content = artifact.get('content', '').lower()
            category = artifact.get('category', 'unknown')
            
            # Look for evidence of task transformation in each category
            if category in self.dcwf_task_mapping:
                for task in self.dcwf_task_mapping[category]:
                    # Check for mentions of this task
                    task_pattern = r'\b' + re.escape(task.lower()) + r'\b'
                    if re.search(task_pattern, content):
                        task_transformations[category].append(task)
                        
                        # Extract evidence of transformation
                        context = self._extract_transformation_context(content, task)
                        if task not in transformation_evidence:
                            transformation_evidence[task] = []
                        transformation_evidence[task].append({
                            'category': category,
                            'context': context[:200] + "..." if len(context) > 200 else context
                        })
        
        # Analyze transformation patterns
        transformation_summary = {}
        for category, tasks in task_transformations.items():
            unique_tasks = list(set(tasks))
            transformation_summary[category] = {
                'tasks_identified': len(unique_tasks),
                'tasks_list': unique_tasks[:5],  # Top 5 for brevity
                'transformation_level': self._calculate_transformation_level(unique_tasks, category)
            }
        
        return {
            'task_transformations': transformation_summary,
            'evidence_examples': {k: v[:2] for k, v in transformation_evidence.items()},  # Limit examples
            'dcwf_insights': self._generate_dcwf_insights(transformation_summary)
        }
    
    def _extract_transformation_context(self, content: str, task: str) -> str:
        """Extract context around task transformation mentions."""
        task_index = content.lower().find(task.lower())
        if task_index == -1:
            return ""
        
        # Extract surrounding context (±100 characters)
        start = max(0, task_index - 100)
        end = min(len(content), task_index + len(task) + 100)
        return content[start:end]
    
    def _calculate_transformation_level(self, tasks: List[str], category: str) -> str:
        """Calculate transformation level for a category."""
        total_possible = len(self.dcwf_task_mapping.get(category, []))
        if total_possible == 0:
            return "Unknown"
        
        transformation_ratio = len(tasks) / total_possible
        
        if transformation_ratio >= 0.7:
            return "High"
        elif transformation_ratio >= 0.4:
            return "Moderate"
        elif transformation_ratio >= 0.2:
            return "Low"
        else:
            return "Minimal"
    
    def _generate_dcwf_insights(self, transformation_summary: Dict) -> List[str]:
        """Generate strategic insights about DCWF task transformation."""
        insights = []
        
        # Analyze replace category
        replace_level = transformation_summary.get('replace', {}).get('transformation_level', 'Unknown')
        if replace_level == "High":
            insights.append("High automation potential detected in routine cybersecurity tasks - prepare for workforce reskilling")
        
        # Analyze augment category  
        augment_level = transformation_summary.get('augment', {}).get('transformation_level', 'Unknown')
        if augment_level in ["High", "Moderate"]:
            insights.append("Strong AI augmentation opportunities in complex cybersecurity tasks - focus on human-AI collaboration skills")
        
        # Analyze new_tasks category
        new_tasks_level = transformation_summary.get('new_tasks', {}).get('transformation_level', 'Unknown')
        if new_tasks_level in ["High", "Moderate"]:
            insights.append("Emerging AI-driven cybersecurity roles identified - develop training for new task categories")
        
        # Analyze human_only category
        human_only_level = transformation_summary.get('human_only', {}).get('transformation_level', 'Unknown')
        if human_only_level == "High":
            insights.append("Strong demand for uniquely human cybersecurity skills - emphasize leadership and strategic thinking")
        
        if not insights:
            insights.append("DCWF task transformation patterns require further analysis - expand data collection")
            
        return insights
    
    def _calculate_forecast_confidence(self, artifact_count: int, skill_mention_count: int) -> str:
        """Calculate confidence level for forecasting based on data volume."""
        data_score = min(artifact_count / 100, 1.0)  # Normalize to 100 articles
        mention_score = min(skill_mention_count / 50, 1.0)  # Normalize to 50 skills with mentions
        
        overall_confidence = (data_score + mention_score) / 2
        
        if overall_confidence >= 0.8:
            return "High"
        elif overall_confidence >= 0.6:
            return "Medium"
        elif overall_confidence >= 0.4:
            return "Low"
        else:
            return "Very Low"

    def _generate_transformation_summary(self, predictions: Dict, transformation_velocity: Dict) -> str:
        """Generate summary of workforce transformation predictions."""
        
        speed = transformation_velocity.get('overall_speed', 'unknown')
        confidence = transformation_velocity.get('confidence', 0)
        
        summary = f"Workforce transformation proceeding at {speed} pace "
        summary += f"(confidence: {confidence:.2f}). "
        
        if predictions:
            high_intensity_categories = [cat for cat, pred in predictions.items() 
                                        if pred.get('intensity', 0) > 0.5]
            
            if high_intensity_categories:
                summary += f"Primary transformation in: {', '.join(high_intensity_categories)}. "
        
        if speed == 'rapid':
            summary += "Recommend accelerated reskilling programs."
        elif speed == 'gradual':
            summary += "Opportunity for comprehensive skill development."
        elif speed == 'moderate':
            summary += "Balanced approach to workforce development recommended."
        else:
            summary += "Monitor transformation patterns for strategic planning."
        
        return summary

    def _generate_adoption_curve_summary(self, phase: str, distribution: Dict) -> str:
        """Generate summary of adoption curve analysis."""
        
        summary = f"Current adoption phase: {phase}. "
        
        if distribution:
            total_percentage = sum(distribution.values())
            if total_percentage > 0:
                early_phases = distribution.get('early_adopters', 0) + distribution.get('early_majority', 0)
                
                if early_phases > 50:
                    summary += "Market in early adoption stages - prepare for acceleration. "
                else:
                    summary += "Market moving toward mainstream adoption. "
        
        summary += "Monitor adoption indicators for strategic positioning."
        
        return summary


def main():
    """Main function for command-line execution."""
    
    logging.basicConfig(level=logging.INFO)
    
    predictor = AIAdoptionPredictor()
    
    print("Running AI Adoption Rate Predictions Analysis...")
    print("   Focusing on skill demand forecasting and workforce transformation predictions")
    print()
    
    # Generate report
    report_file = predictor.generate_report()
    
    if report_file.startswith("Error"):
        print(f"Error: {report_file}")
        return
    
    print(f"Analysis complete! Report saved to: {report_file}")
    
    # Display quick summary
    results = predictor.run_comprehensive_analysis()
    if 'executive_summary' in results:
        summary = results['executive_summary']
        print("\nQuick Summary:")
        print(f"   • Articles analyzed: {summary.get('total_articles_analyzed', 0)}")
        print(f"   • Current adoption phase: {summary.get('adoption_phase', 'Unknown')}")
        print(f"   • Transformation speed: {summary.get('transformation_speed', 'Unknown')}")
        
        top_skills = summary.get('top_high_demand_skills', [])
        if top_skills:
            print(f"   • Top high-demand skills: {', '.join(top_skills[:3])}")


if __name__ == "__main__":
    main() 