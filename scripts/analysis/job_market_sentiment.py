#!/usr/bin/env python3
"""
Job Market Sentiment Tracking System

Provides comprehensive sentiment analysis of job market trends related to AI's impact on cybersecurity careers including:
- Sentiment analysis of job-related content
- Career opportunity vs threat tracking
- Skill demand sentiment evolution
- Employer vs employee perspective analysis
- Industry confidence indicators
- Geographic sentiment variations
- Temporal sentiment pattern analysis

Usage:
    python scripts/analysis/job_market_sentiment.py
"""

import sys
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Any
import statistics
import re

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from aih.utils.database import DatabaseManager
from scripts.analysis.implement_quality_ranking import DocumentQualityRanker

class JobMarketSentimentAnalyzer:
    """
    Advanced job market sentiment analysis system for cybersecurity AI workforce impact.
    """
    
    def __init__(self):
        self.db = DatabaseManager()
        self.quality_ranker = DocumentQualityRanker()
        self.artifacts = []
        
        # Job market sentiment lexicons
        self.positive_job_terms = [
            'opportunity', 'hiring', 'growth', 'career advancement', 'skill development',
            'new roles', 'emerging positions', 'job creation', 'expansion', 'talent demand',
            'upskilling', 'reskilling', 'career transformation', 'professional development',
            'competitive advantage', 'efficiency gains', 'productivity boost', 'innovation',
            'collaboration', 'augmentation', 'enhancement', 'empowerment'
        ]
        
        self.negative_job_terms = [
            'job loss', 'unemployment', 'displacement', 'obsolete', 'redundant',
            'elimination', 'cutbacks', 'downsizing', 'replacement', 'automation threat',
            'job insecurity', 'workforce reduction', 'layoffs', 'skill gap', 'outdated',
            'competition', 'difficult transition', 'job market shrinkage', 'career uncertainty',
            'economic disruption', 'technological unemployment', 'role elimination'
        ]
        
        self.neutral_job_terms = [
            'adaptation', 'change', 'transition', 'evolution', 'transformation',
            'adjustment', 'modification', 'shift', 'realignment', 'restructuring',
            'rebalancing', 'modernization', 'digital transformation', 'technology adoption',
            'workflow changes', 'process improvement', 'organizational change'
        ]
        
        self.skill_demand_terms = [
            'python', 'machine learning', 'ai security', 'threat detection', 'incident response',
            'vulnerability assessment', 'penetration testing', 'security architecture',
            'cloud security', 'devsecops', 'security automation', 'threat intelligence',
            'risk management', 'compliance', 'governance', 'security operations',
            'cybersecurity analyst', 'security engineer', 'security architect',
            'ai engineer', 'data scientist', 'mlops', 'security researcher'
        ]
        
    def load_all_data(self):
        """Load all artifacts for sentiment analysis."""
        print("Loading all artifacts for job market sentiment analysis...")
        self.artifacts = self.db.get_artifacts(limit=5000)
        print(f"   Loaded {len(self.artifacts)} total artifacts")
        return len(self.artifacts)
    
    def analyze_overall_sentiment(self) -> Dict[str, Any]:
        """Analyze overall job market sentiment across all content."""
        print("\n😊 Analyzing Overall Job Market Sentiment...")
        
        sentiment_scores = []
        sentiment_by_category = defaultdict(list)
        sentiment_by_month = defaultdict(list)
        
        for artifact in self.artifacts:
            try:
                # Combine title and content for analysis
                text_content = ""
                if artifact.get('title'):
                    text_content += artifact['title'] + " "
                if artifact.get('content'):
                    text_content += artifact['content']
                
                text_content = text_content.lower()
                
                # Calculate sentiment score (-1 to 1)
                positive_score = sum(1 for term in self.positive_job_terms if term in text_content)
                negative_score = sum(1 for term in self.negative_job_terms if term in text_content)
                neutral_score = sum(1 for term in self.neutral_job_terms if term in text_content)
                
                total_signals = positive_score + negative_score + neutral_score
                if total_signals > 0:
                    sentiment_score = (positive_score - negative_score) / total_signals
                    sentiment_scores.append(sentiment_score)
                    
                    # Group by category
                    try:
                        metadata = json.loads(artifact.get('raw_metadata', '{}'))
                        category = metadata.get('ai_impact_category', 'unknown')
                        sentiment_by_category[category].append(sentiment_score)
                    except:
                        sentiment_by_category['unknown'].append(sentiment_score)
                    
                    # Group by month
                    created_at = artifact.get('created_at')
                    if created_at:
                        try:
                            if isinstance(created_at, str):
                                date_obj = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                            else:
                                date_obj = created_at
                            month_key = date_obj.strftime('%Y-%m')
                            sentiment_by_month[month_key].append(sentiment_score)
                        except:
                            continue
                
            except Exception as e:
                continue
        
        # Calculate overall metrics
        overall_sentiment = {
            'overall_score': round(statistics.mean(sentiment_scores), 3) if sentiment_scores else 0,
            'sentiment_distribution': {},
            'category_sentiment': {},
            'monthly_sentiment': {},
            'confidence_level': 'high' if len(sentiment_scores) > 50 else 'medium' if len(sentiment_scores) > 20 else 'low'
        }
        
        # Sentiment distribution
        if sentiment_scores:
            positive_count = sum(1 for s in sentiment_scores if s > 0.1)
            negative_count = sum(1 for s in sentiment_scores if s < -0.1)
            neutral_count = len(sentiment_scores) - positive_count - negative_count
            
            total = len(sentiment_scores)
            overall_sentiment['sentiment_distribution'] = {
                'positive': round((positive_count / total) * 100, 1),
                'negative': round((negative_count / total) * 100, 1),
                'neutral': round((neutral_count / total) * 100, 1),
                'total_analyzed': total
            }
        
        # Category sentiment
        for category, scores in sentiment_by_category.items():
            if scores:
                overall_sentiment['category_sentiment'][category] = {
                    'average_sentiment': round(statistics.mean(scores), 3),
                    'sentiment_trend': 'positive' if statistics.mean(scores) > 0.1 else 'negative' if statistics.mean(scores) < -0.1 else 'neutral',
                    'article_count': len(scores),
                    'std_dev': round(statistics.stdev(scores), 3) if len(scores) > 1 else 0
                }
        
        # Monthly sentiment trends
        for month, scores in sorted(sentiment_by_month.items()):
            if scores:
                overall_sentiment['monthly_sentiment'][month] = {
                    'average_sentiment': round(statistics.mean(scores), 3),
                    'article_count': len(scores),
                    'dominant_sentiment': 'positive' if statistics.mean(scores) > 0.1 else 'negative' if statistics.mean(scores) < -0.1 else 'neutral'
                }
        
        print(f"   📊 Overall sentiment: {overall_sentiment['overall_score']} ({'positive' if overall_sentiment['overall_score'] > 0.1 else 'negative' if overall_sentiment['overall_score'] < -0.1 else 'neutral'})")
        print(f"   📈 Confidence level: {overall_sentiment['confidence_level']}")
        
        return overall_sentiment
    
    def analyze_career_opportunities_vs_threats(self) -> Dict[str, Any]:
        """Analyze the balance between career opportunities and threats."""
        print("\n🎯 Analyzing Career Opportunities vs Threats...")
        
        opportunity_indicators = [
            'new job roles', 'career growth', 'skill premium', 'market demand',
            'emerging opportunities', 'professional advancement', 'higher salaries',
            'job security increase', 'career prospects', 'talent shortage'
        ]
        
        threat_indicators = [
            'job displacement', 'skill obsolescence', 'market saturation',
            'wage depression', 'career uncertainty', 'professional decline',
            'employment risk', 'job market contraction', 'reduced opportunities'
        ]
        
        opportunities_by_category = defaultdict(int)
        threats_by_category = defaultdict(int)
        monthly_balance = defaultdict(lambda: {'opportunities': 0, 'threats': 0})
        
        for artifact in self.artifacts:
            try:
                text_content = ""
                if artifact.get('title'):
                    text_content += artifact['title'] + " "
                if artifact.get('content'):
                    text_content += artifact['content']
                
                text_content = text_content.lower()
                
                # Count opportunity and threat indicators
                opportunity_count = sum(1 for term in opportunity_indicators if term in text_content)
                threat_count = sum(1 for term in threat_indicators if term in text_content)
                
                if opportunity_count > 0 or threat_count > 0:
                    # Group by category
                    try:
                        metadata = json.loads(artifact.get('raw_metadata', '{}'))
                        category = metadata.get('ai_impact_category', 'unknown')
                        opportunities_by_category[category] += opportunity_count
                        threats_by_category[category] += threat_count
                    except:
                        opportunities_by_category['unknown'] += opportunity_count
                        threats_by_category['unknown'] += threat_count
                    
                    # Group by month
                    created_at = artifact.get('created_at')
                    if created_at:
                        try:
                            if isinstance(created_at, str):
                                date_obj = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                            else:
                                date_obj = created_at
                            month_key = date_obj.strftime('%Y-%m')
                            monthly_balance[month_key]['opportunities'] += opportunity_count
                            monthly_balance[month_key]['threats'] += threat_count
                        except:
                            continue
                
            except Exception as e:
                continue
        
        # Calculate balance metrics
        total_opportunities = sum(opportunities_by_category.values())
        total_threats = sum(threats_by_category.values())
        
        opportunity_threat_analysis = {
            'overall_balance': {
                'total_opportunities': total_opportunities,
                'total_threats': total_threats,
                'balance_ratio': round(total_opportunities / max(total_threats, 1), 2),
                'dominant_narrative': 'opportunity-focused' if total_opportunities > total_threats * 1.2 else 'threat-focused' if total_threats > total_opportunities * 1.2 else 'balanced'
            },
            'category_balance': {},
            'monthly_trends': {},
            'trend_direction': 'stable'
        }
        
        # Category balance
        for category in set(list(opportunities_by_category.keys()) + list(threats_by_category.keys())):
            opps = opportunities_by_category[category]
            threats = threats_by_category[category]
            total = opps + threats
            
            if total > 0:
                opportunity_threat_analysis['category_balance'][category] = {
                    'opportunities': opps,
                    'threats': threats,
                    'opportunity_percentage': round((opps / total) * 100, 1),
                    'narrative_lean': 'opportunity-focused' if opps > threats * 1.2 else 'threat-focused' if threats > opps * 1.2 else 'balanced'
                }
        
        # Monthly trends
        sorted_months = sorted(monthly_balance.keys())
        for month in sorted_months:
            data = monthly_balance[month]
            total = data['opportunities'] + data['threats']
            if total > 0:
                opportunity_threat_analysis['monthly_trends'][month] = {
                    'opportunities': data['opportunities'],
                    'threats': data['threats'],
                    'balance_ratio': round(data['opportunities'] / max(data['threats'], 1), 2),
                    'dominant_narrative': 'opportunity-focused' if data['opportunities'] > data['threats'] else 'threat-focused' if data['threats'] > data['opportunities'] else 'balanced'
                }
        
        # Determine trend direction
        if len(sorted_months) >= 3:
            recent_ratios = []
            early_ratios = []
            
            for month in sorted_months[-3:]:  # Last 3 months
                if month in opportunity_threat_analysis['monthly_trends']:
                    recent_ratios.append(opportunity_threat_analysis['monthly_trends'][month]['balance_ratio'])
            
            for month in sorted_months[:3]:   # First 3 months
                if month in opportunity_threat_analysis['monthly_trends']:
                    early_ratios.append(opportunity_threat_analysis['monthly_trends'][month]['balance_ratio'])
            
            if recent_ratios and early_ratios:
                recent_avg = statistics.mean(recent_ratios)
                early_avg = statistics.mean(early_ratios)
                
                if recent_avg > early_avg * 1.1:
                    opportunity_threat_analysis['trend_direction'] = 'becoming more opportunity-focused'
                elif early_avg > recent_avg * 1.1:
                    opportunity_threat_analysis['trend_direction'] = 'becoming more threat-focused'
        
        print(f"   ⚖️ Balance ratio: {opportunity_threat_analysis['overall_balance']['balance_ratio']} (opportunities:threats)")
        print(f"   📈 Narrative trend: {opportunity_threat_analysis['trend_direction']}")
        
        return opportunity_threat_analysis
    
    def analyze_skill_demand_sentiment(self) -> Dict[str, Any]:
        """Analyze sentiment around specific cybersecurity skills and AI integration."""
        print("\n🎓 Analyzing Skill Demand Sentiment...")
        
        skill_sentiment = defaultdict(lambda: {'positive': 0, 'negative': 0, 'mentions': 0})
        skill_trends = defaultdict(lambda: defaultdict(lambda: {'positive': 0, 'negative': 0, 'mentions': 0}))
        
        for artifact in self.artifacts:
            try:
                text_content = ""
                if artifact.get('title'):
                    text_content += artifact['title'] + " "
                if artifact.get('content'):
                    text_content += artifact['content']
                
                text_content = text_content.lower()
                
                # Check for skill mentions with sentiment context
                for skill in self.skill_demand_terms:
                    if skill in text_content:
                        skill_sentiment[skill]['mentions'] += 1
                        
                        # Analyze sentiment context around skill mention
                        skill_index = text_content.find(skill)
                        context_start = max(0, skill_index - 200)
                        context_end = min(len(text_content), skill_index + len(skill) + 200)
                        context = text_content[context_start:context_end]
                        
                        # Count positive/negative indicators in context
                        positive_context = sum(1 for term in self.positive_job_terms if term in context)
                        negative_context = sum(1 for term in self.negative_job_terms if term in context)
                        
                        skill_sentiment[skill]['positive'] += positive_context
                        skill_sentiment[skill]['negative'] += negative_context
                        
                        # Monthly tracking
                        created_at = artifact.get('created_at')
                        if created_at:
                            try:
                                if isinstance(created_at, str):
                                    date_obj = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                                else:
                                    date_obj = created_at
                                month_key = date_obj.strftime('%Y-%m')
                                skill_trends[skill][month_key]['mentions'] += 1
                                skill_trends[skill][month_key]['positive'] += positive_context
                                skill_trends[skill][month_key]['negative'] += negative_context
                            except:
                                continue
                
            except Exception as e:
                continue
        
        # Process skill sentiment analysis
        skill_demand_analysis = {
            'skill_rankings': {},
            'high_demand_skills': [],
            'emerging_skills': [],
            'declining_skills': [],
            'monthly_skill_trends': {}
        }
        
        # Rank skills by sentiment and demand
        skill_scores = []
        for skill, data in skill_sentiment.items():
            if data['mentions'] >= 3:  # Only skills with sufficient mentions
                total_sentiment_signals = data['positive'] + data['negative']
                if total_sentiment_signals > 0:
                    sentiment_score = (data['positive'] - data['negative']) / total_sentiment_signals
                    demand_score = data['mentions']
                    
                    skill_scores.append({
                        'skill': skill,
                        'sentiment_score': round(sentiment_score, 3),
                        'demand_score': demand_score,
                        'mentions': data['mentions'],
                        'positive_signals': data['positive'],
                        'negative_signals': data['negative'],
                        'overall_rating': round((sentiment_score + 1) * demand_score, 2)  # Normalize sentiment to 0-2, multiply by demand
                    })
        
        # Sort by overall rating
        skill_scores.sort(key=lambda x: x['overall_rating'], reverse=True)
        
        for i, skill_data in enumerate(skill_scores):
            skill_demand_analysis['skill_rankings'][skill_data['skill']] = {
                'rank': i + 1,
                'sentiment_score': skill_data['sentiment_score'],
                'demand_score': skill_data['demand_score'],
                'mentions': skill_data['mentions'],
                'sentiment_classification': 'highly positive' if skill_data['sentiment_score'] > 0.3 else 'positive' if skill_data['sentiment_score'] > 0.1 else 'negative' if skill_data['sentiment_score'] < -0.1 else 'neutral',
                'overall_rating': skill_data['overall_rating']
            }
        
        # Identify categories
        if skill_scores:
            # Top 5 high-demand skills
            skill_demand_analysis['high_demand_skills'] = [s['skill'] for s in skill_scores[:5]]
            
            # Skills with very positive sentiment
            positive_skills = [s for s in skill_scores if s['sentiment_score'] > 0.3]
            skill_demand_analysis['emerging_skills'] = [s['skill'] for s in positive_skills[:3]]
            
            # Skills with negative sentiment
            negative_skills = [s for s in skill_scores if s['sentiment_score'] < -0.1]
            skill_demand_analysis['declining_skills'] = [s['skill'] for s in negative_skills[:3]]
        
        # Monthly skill trends
        for skill, monthly_data in skill_trends.items():
            if sum(data['mentions'] for data in monthly_data.values()) >= 3:
                skill_demand_analysis['monthly_skill_trends'][skill] = dict(monthly_data)
        
        print(f"   🏆 Top skill: {skill_demand_analysis['high_demand_skills'][0] if skill_demand_analysis['high_demand_skills'] else 'N/A'}")
        print(f"   📈 Emerging skills: {len(skill_demand_analysis['emerging_skills'])}")
        print(f"   📉 Declining skills: {len(skill_demand_analysis['declining_skills'])}")
        
        return skill_demand_analysis
    
    def analyze_employer_vs_employee_sentiment(self) -> Dict[str, Any]:
        """Analyze different perspectives between employers and employees."""
        print("\n🏢 Analyzing Employer vs Employee Sentiment...")
        
        employer_indicators = [
            'company', 'organization', 'enterprise', 'business', 'employer',
            'hr', 'hiring', 'recruitment', 'workforce planning', 'corporate',
            'management', 'leadership', 'ceo', 'cto', 'chro'
        ]
        
        employee_indicators = [
            'worker', 'employee', 'professional', 'career', 'job seeker',
            'cybersecurity analyst', 'security engineer', 'practitioner',
            'individual', 'personal', 'worker perspective', 'employee concerns'
        ]
        
        employer_sentiment = []
        employee_sentiment = []
        mixed_perspective_sentiment = []
        
        for artifact in self.artifacts:
            try:
                text_content = ""
                if artifact.get('title'):
                    text_content += artifact['title'] + " "
                if artifact.get('content'):
                    text_content += artifact['content']
                
                text_content = text_content.lower()
                
                # Identify perspective
                employer_signals = sum(1 for term in employer_indicators if term in text_content)
                employee_signals = sum(1 for term in employee_indicators if term in text_content)
                
                # Calculate sentiment
                positive_score = sum(1 for term in self.positive_job_terms if term in text_content)
                negative_score = sum(1 for term in self.negative_job_terms if term in text_content)
                total_signals = positive_score + negative_score
                
                if total_signals > 0:
                    sentiment_score = (positive_score - negative_score) / total_signals
                    
                    if employer_signals > employee_signals * 1.5:
                        employer_sentiment.append(sentiment_score)
                    elif employee_signals > employer_signals * 1.5:
                        employee_sentiment.append(sentiment_score)
                    elif employer_signals > 0 and employee_signals > 0:
                        mixed_perspective_sentiment.append(sentiment_score)
                
            except Exception as e:
                continue
        
        perspective_analysis = {
            'employer_perspective': {
                'average_sentiment': round(statistics.mean(employer_sentiment), 3) if employer_sentiment else 0,
                'article_count': len(employer_sentiment),
                'sentiment_classification': 'positive' if employer_sentiment and statistics.mean(employer_sentiment) > 0.1 else 'negative' if employer_sentiment and statistics.mean(employer_sentiment) < -0.1 else 'neutral' if employer_sentiment else 'no data'
            },
            'employee_perspective': {
                'average_sentiment': round(statistics.mean(employee_sentiment), 3) if employee_sentiment else 0,
                'article_count': len(employee_sentiment),
                'sentiment_classification': 'positive' if employee_sentiment and statistics.mean(employee_sentiment) > 0.1 else 'negative' if employee_sentiment and statistics.mean(employee_sentiment) < -0.1 else 'neutral' if employee_sentiment else 'no data'
            },
            'mixed_perspective': {
                'average_sentiment': round(statistics.mean(mixed_perspective_sentiment), 3) if mixed_perspective_sentiment else 0,
                'article_count': len(mixed_perspective_sentiment),
                'sentiment_classification': 'positive' if mixed_perspective_sentiment and statistics.mean(mixed_perspective_sentiment) > 0.1 else 'negative' if mixed_perspective_sentiment and statistics.mean(mixed_perspective_sentiment) < -0.1 else 'neutral' if mixed_perspective_sentiment else 'no data'
            },
            'sentiment_gap': 0,
            'alignment_status': 'unknown'
        }
        
        # Calculate sentiment gap
        if employer_sentiment and employee_sentiment:
            emp_avg = statistics.mean(employer_sentiment)
            employee_avg = statistics.mean(employee_sentiment)
            perspective_analysis['sentiment_gap'] = round(emp_avg - employee_avg, 3)
            
            if abs(perspective_analysis['sentiment_gap']) < 0.1:
                perspective_analysis['alignment_status'] = 'well-aligned'
            elif perspective_analysis['sentiment_gap'] > 0.2:
                perspective_analysis['alignment_status'] = 'employers more optimistic'
            elif perspective_analysis['sentiment_gap'] < -0.2:
                perspective_analysis['alignment_status'] = 'employees more optimistic'
            else:
                perspective_analysis['alignment_status'] = 'moderate difference'
        
        print(f"   🏢 Employer sentiment: {perspective_analysis['employer_perspective']['sentiment_classification']}")
        print(f"   👨‍💼 Employee sentiment: {perspective_analysis['employee_perspective']['sentiment_classification']}")
        print(f"   🤝 Alignment: {perspective_analysis['alignment_status']}")
        
        return perspective_analysis
    
    def generate_sentiment_report(self) -> str:
        """Generate comprehensive job market sentiment analysis report."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Run all analyses
        overall_sentiment = self.analyze_overall_sentiment()
        opportunity_threat = self.analyze_career_opportunities_vs_threats()
        skill_demand = self.analyze_skill_demand_sentiment()
        perspective_analysis = self.analyze_employer_vs_employee_sentiment()
        
        # Get analysis period
        valid_dates = [a.get('created_at', '') for a in self.artifacts if a.get('created_at')]
        if valid_dates:
            min_date = min(valid_dates)
            max_date = max(valid_dates)
            analysis_period = f"{min_date} to {max_date}"
        else:
            analysis_period = "No date information available"
        
        report = f"""
# 🎯 Job Market Sentiment Analysis Report

**Generated:** {timestamp}
**Total Articles Analyzed:** {len(self.artifacts)}
**Analysis Period:** {analysis_period}

## 📊 Executive Summary

**Overall Market Sentiment:** {overall_sentiment['overall_score']} ({'Positive' if overall_sentiment['overall_score'] > 0.1 else 'Negative' if overall_sentiment['overall_score'] < -0.1 else 'Neutral'})

**Key Findings:**
- Market sentiment is {'optimistic' if overall_sentiment['overall_score'] > 0.2 else 'pessimistic' if overall_sentiment['overall_score'] < -0.2 else 'cautiously balanced'}
- {'Opportunity-focused' if opportunity_threat['overall_balance']['balance_ratio'] > 1.2 else 'Threat-focused' if opportunity_threat['overall_balance']['balance_ratio'] < 0.8 else 'Balanced'} narrative dominates (ratio: {opportunity_threat['overall_balance']['balance_ratio']})
- Employer-employee perspectives are {perspective_analysis['alignment_status']}
- Analysis confidence: {overall_sentiment['confidence_level']}

---

## 😊 Overall Sentiment Analysis

### Sentiment Distribution
| Category | Percentage | Count |
|----------|------------|-------|"""

        if overall_sentiment['sentiment_distribution']:
            for sentiment, percentage in overall_sentiment['sentiment_distribution'].items():
                if sentiment != 'total_analyzed':
                    report += f"""
| {sentiment.title()} | {percentage}% | {int(percentage * overall_sentiment['sentiment_distribution']['total_analyzed'] / 100)} |"""

        report += f"""

### Sentiment by AI Impact Category
| Category | Average Sentiment | Classification | Articles | Std Dev |
|----------|------------------|----------------|----------|---------|"""

        for category, data in overall_sentiment['category_sentiment'].items():
            report += f"""
| {category} | {data['average_sentiment']} | {data['sentiment_trend'].title()} | {data['article_count']} | {data['std_dev']} |"""

        report += f"""

### Monthly Sentiment Trends
| Month | Average Sentiment | Dominant Sentiment | Articles |
|-------|------------------|-------------------|----------|"""

        for month, data in sorted(overall_sentiment['monthly_sentiment'].items()):
            report += f"""
| {month} | {data['average_sentiment']} | {data['dominant_sentiment'].title()} | {data['article_count']} |"""

        report += f"""

---

## ⚖️ Career Opportunities vs Threats Analysis

**Overall Balance Ratio:** {opportunity_threat['overall_balance']['balance_ratio']} (opportunities:threats)
**Dominant Narrative:** {opportunity_threat['overall_balance']['dominant_narrative'].title()}
**Trend Direction:** {opportunity_threat['trend_direction'].title()}

### Balance by AI Impact Category
| Category | Opportunities | Threats | Opportunity % | Narrative Lean |
|----------|---------------|---------|---------------|----------------|"""

        for category, data in opportunity_threat['category_balance'].items():
            report += f"""
| {category} | {data['opportunities']} | {data['threats']} | {data['opportunity_percentage']}% | {data['narrative_lean'].title()} |"""

        report += f"""

### Monthly Opportunity-Threat Balance
| Month | Opportunities | Threats | Balance Ratio | Dominant Narrative |
|-------|---------------|---------|---------------|-------------------|"""

        for month, data in sorted(opportunity_threat['monthly_trends'].items()):
            report += f"""
| {month} | {data['opportunities']} | {data['threats']} | {data['balance_ratio']} | {data['dominant_narrative'].title()} |"""

        report += f"""

---

## 🎓 Skill Demand Sentiment Analysis

### Top High-Demand Skills
"""
        for i, skill in enumerate(skill_demand['high_demand_skills'][:5], 1):
            if skill in skill_demand['skill_rankings']:
                data = skill_demand['skill_rankings'][skill]
                report += f"{i}. **{skill}** - Sentiment: {data['sentiment_score']} ({data['sentiment_classification']}), Mentions: {data['mentions']}\n"

        report += f"""
### Emerging Skills (Positive Sentiment)
"""
        for skill in skill_demand['emerging_skills'][:3]:
            if skill in skill_demand['skill_rankings']:
                data = skill_demand['skill_rankings'][skill]
                report += f"- **{skill}** - Sentiment: {data['sentiment_score']} ({data['sentiment_classification']})\n"

        if skill_demand['declining_skills']:
            report += f"""
### Skills Under Pressure (Negative Sentiment)
"""
            for skill in skill_demand['declining_skills'][:3]:
                if skill in skill_demand['skill_rankings']:
                    data = skill_demand['skill_rankings'][skill]
                    report += f"- **{skill}** - Sentiment: {data['sentiment_score']} ({data['sentiment_classification']})\n"

        report += f"""

---

## 🏢 Employer vs Employee Perspective Analysis

| Perspective | Average Sentiment | Classification | Articles | 
|-------------|------------------|----------------|----------|
| Employer | {perspective_analysis['employer_perspective']['average_sentiment']} | {perspective_analysis['employer_perspective']['sentiment_classification'].title()} | {perspective_analysis['employer_perspective']['article_count']} |
| Employee | {perspective_analysis['employee_perspective']['average_sentiment']} | {perspective_analysis['employee_perspective']['sentiment_classification'].title()} | {perspective_analysis['employee_perspective']['article_count']} |
| Mixed Perspective | {perspective_analysis['mixed_perspective']['average_sentiment']} | {perspective_analysis['mixed_perspective']['sentiment_classification'].title()} | {perspective_analysis['mixed_perspective']['article_count']} |

**Sentiment Gap:** {perspective_analysis['sentiment_gap']} ({'Employers more optimistic' if perspective_analysis['sentiment_gap'] > 0 else 'Employees more optimistic' if perspective_analysis['sentiment_gap'] < 0 else 'Well aligned'})

**Alignment Status:** {perspective_analysis['alignment_status'].title()}

---

## 🎯 Key Insights & Recommendations

### Market Sentiment Insights
"""
        if overall_sentiment['overall_score'] > 0.2:
            report += "- ✅ **Strong Positive Market Sentiment**: The cybersecurity job market shows robust optimism about AI integration\n"
        elif overall_sentiment['overall_score'] > 0:
            report += "- 📊 **Cautiously Optimistic**: Market sentiment leans positive but remains measured\n"
        elif overall_sentiment['overall_score'] > -0.2:
            report += "- ⚠️ **Mixed Sentiment**: Market shows balanced concerns and opportunities\n"
        else:
            report += "- 🚨 **Negative Market Sentiment**: Significant concerns about AI's impact on cybersecurity careers\n"

        if opportunity_threat['overall_balance']['balance_ratio'] > 1.5:
            report += "- 🚀 **Opportunity-Dominant Narrative**: Strong focus on career growth and new roles\n"
        elif opportunity_threat['overall_balance']['balance_ratio'] < 0.7:
            report += "- ⚠️ **Threat-Focused Narrative**: Significant concern about job displacement\n"
        else:
            report += "- ⚖️ **Balanced Narrative**: Equal attention to opportunities and threats\n"

        report += f"""
### Stakeholder Alignment
"""
        if perspective_analysis['alignment_status'] == 'well-aligned':
            report += "- 🤝 **Strong Alignment**: Employers and employees share similar sentiment about AI's impact\n"
        elif 'optimistic' in perspective_analysis['alignment_status']:
            optimistic_group = 'employers' if 'employers' in perspective_analysis['alignment_status'] else 'employees'
            report += f"- 📈 **Perspective Gap**: {optimistic_group.title()} show more optimistic outlook than counterparts\n"
        else:
            report += "- 🔄 **Moderate Misalignment**: Some difference in perspective between employers and employees\n"

        report += f"""
### Skill Development Recommendations
"""
        if skill_demand['high_demand_skills']:
            top_skill = skill_demand['high_demand_skills'][0]
            report += f"- 🎯 **Priority Skill**: Focus on {top_skill} development (highest demand with positive sentiment)\n"
        
        if skill_demand['emerging_skills']:
            report += f"- 📈 **Emerging Opportunities**: Invest in {', '.join(skill_demand['emerging_skills'][:2])} for future growth\n"
        
        if skill_demand['declining_skills']:
            report += f"- 🔄 **Skills Transition**: Consider pivoting from {', '.join(skill_demand['declining_skills'][:2])} to growth areas\n"

        report += f"""
### Strategic Recommendations
"""
        if overall_sentiment['overall_score'] > 0.1:
            report += "- ✅ **Leverage Positive Momentum**: Use current optimism to drive skill development initiatives\n"
        else:
            report += "- 🎯 **Address Concerns**: Focus on communication about AI as augmentation rather than replacement\n"

        if opportunity_threat['trend_direction'] != 'stable':
            report += f"- 📊 **Monitor Trend**: Market narrative is {opportunity_threat['trend_direction']} - adjust strategies accordingly\n"

        report += f"""

---

*This job market sentiment analysis provides insights into how the cybersecurity community perceives AI's impact on careers, opportunities, and workforce transformation. Use these insights to guide career development, hiring strategies, and workforce planning.*
"""

        return report

def main():
    """Run comprehensive job market sentiment analysis."""
    print("Starting Job Market Sentiment Analysis...")
    print("=" * 60)
    
    analyzer = JobMarketSentimentAnalyzer()
    
    # Load all data
    data_count = analyzer.load_all_data()
    
    if data_count == 0:
        print("No data available for sentiment analysis")
        return
    
    # Generate comprehensive sentiment report
    report = analyzer.generate_sentiment_report()
    
    # Save report
    report_dir = Path('data/reports')
    report_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = report_dir / f'job_market_sentiment_{timestamp}.md'
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\nJob market sentiment analysis complete!")
    print(f"Report saved to: {report_file}")
    print(f"Analyzed {data_count} articles")
    
    # Print summary
    print("\n" + "=" * 60)
    print("SENTIMENT ANALYSIS SUMMARY")
    print("=" * 60)
    
    # Quick summary
    overall_sentiment = analyzer.analyze_overall_sentiment()
    opportunity_threat = analyzer.analyze_career_opportunities_vs_threats()
    
    print(f"Overall Sentiment: {overall_sentiment['overall_score']} ({'Positive' if overall_sentiment['overall_score'] > 0.1 else 'Negative' if overall_sentiment['overall_score'] < -0.1 else 'Neutral'})")
    print(f"Opportunity/Threat Ratio: {opportunity_threat['overall_balance']['balance_ratio']}")
    print(f"Market Narrative: {opportunity_threat['overall_balance']['dominant_narrative'].title()}")
    print(f"Confidence Level: {overall_sentiment['confidence_level'].title()}")

if __name__ == "__main__":
    main() 