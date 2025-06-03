#!/usr/bin/env python3
"""
Trend Analysis System

Provides comprehensive temporal analysis of collected articles including:
- Article sentiment trends over time
- Quality trends by category and overall
- Topic evolution and emergence tracking
- AI impact category distribution trends
- Source coverage and reliability trends
- Keyword frequency evolution
- Collection velocity and pattern analysis

Usage:
    python scripts/analysis/trend_analysis.py
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

class TrendAnalyzer:
    """
    Advanced trend analysis system for analyzing temporal patterns in collected cybersecurity AI data.
    """
    
    def __init__(self):
        self.db = DatabaseManager()
        self.quality_ranker = DocumentQualityRanker()
        self.artifacts = []
        self.trend_data = {}
        
    def load_all_data(self):
        """Load all artifacts for comprehensive trend analysis."""
        print("Loading all artifacts for trend analysis...")
        self.artifacts = self.db.get_artifacts(limit=5000)  # Get more for better trends
        print(f"   Loaded {len(self.artifacts)} total artifacts")
        return len(self.artifacts)
    
    def analyze_quality_trends(self) -> Dict[str, Any]:
        """Analyze quality trends over time across categories."""
        print("\n📈 Analyzing Quality Trends Over Time...")
        
        # Group by month for quality trends
        monthly_quality = defaultdict(lambda: {'scores': [], 'count': 0})
        category_monthly_quality = defaultdict(lambda: defaultdict(lambda: {'scores': [], 'count': 0}))
        
        for artifact in self.artifacts:
            try:
                # Calculate quality score
                quality_score, _ = self.quality_ranker.calculate_document_score(artifact)
                
                # Parse date
                created_at = artifact.get('created_at')
                if not created_at:
                    continue
                    
                if isinstance(created_at, str):
                    date_obj = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                else:
                    date_obj = created_at
                
                month_key = date_obj.strftime('%Y-%m')
                
                # Overall quality trend
                monthly_quality[month_key]['scores'].append(quality_score)
                monthly_quality[month_key]['count'] += 1
                
                # Category-specific trends
                try:
                    metadata = json.loads(artifact.get('raw_metadata', '{}'))
                    category = metadata.get('ai_impact_category', 'unknown')
                    category_monthly_quality[category][month_key]['scores'].append(quality_score)
                    category_monthly_quality[category][month_key]['count'] += 1
                except:
                    continue
                    
            except Exception as e:
                continue
        
        # Calculate trend statistics
        quality_trends = {
            'overall_monthly': {},
            'category_trends': {},
            'trend_direction': 'stable',
            'quality_improvement': 0.0
        }
        
        # Process overall monthly trends
        sorted_months = sorted(monthly_quality.keys())
        for month in sorted_months:
            if monthly_quality[month]['scores']:
                avg_quality = statistics.mean(monthly_quality[month]['scores'])
                quality_trends['overall_monthly'][month] = {
                    'avg_quality': round(avg_quality, 3),
                    'count': monthly_quality[month]['count'],
                    'std_dev': round(statistics.stdev(monthly_quality[month]['scores']) if len(monthly_quality[month]['scores']) > 1 else 0, 3)
                }
        
        # Calculate overall trend direction
        if len(sorted_months) >= 2:
            recent_months = sorted_months[-3:]  # Last 3 months
            early_months = sorted_months[:3]    # First 3 months
            
            if len(recent_months) >= 2 and len(early_months) >= 2:
                recent_avg = statistics.mean([
                    quality_trends['overall_monthly'][m]['avg_quality'] 
                    for m in recent_months 
                    if m in quality_trends['overall_monthly']
                ])
                early_avg = statistics.mean([
                    quality_trends['overall_monthly'][m]['avg_quality'] 
                    for m in early_months 
                    if m in quality_trends['overall_monthly']
                ])
                
                improvement = recent_avg - early_avg
                quality_trends['quality_improvement'] = round(improvement, 3)
                
                if improvement > 0.05:
                    quality_trends['trend_direction'] = 'improving'
                elif improvement < -0.05:
                    quality_trends['trend_direction'] = 'declining'
        
        # Process category trends
        for category, monthly_data in category_monthly_quality.items():
            category_trend = {}
            sorted_cat_months = sorted(monthly_data.keys())
            
            for month in sorted_cat_months:
                if monthly_data[month]['scores']:
                    avg_quality = statistics.mean(monthly_data[month]['scores'])
                    category_trend[month] = {
                        'avg_quality': round(avg_quality, 3),
                        'count': monthly_data[month]['count']
                    }
            
            if category_trend:
                quality_trends['category_trends'][category] = category_trend
        
        print(f"   📊 Quality Trend: {quality_trends['trend_direction'].title()}")
        if quality_trends['quality_improvement'] != 0:
            print(f"   📈 Improvement: {quality_trends['quality_improvement']:+.3f}")
        
        return quality_trends
    
    def analyze_topic_evolution(self) -> Dict[str, Any]:
        """Analyze how topics and keywords evolve over time."""
        print("\n🔍 Analyzing Topic Evolution...")
        
        # Extract keywords from titles and content
        monthly_keywords = defaultdict(lambda: Counter())
        monthly_topics = defaultdict(lambda: Counter())
        
        # Common AI/cybersecurity keywords to track
        key_terms = [
            'artificial intelligence', 'machine learning', 'ai', 'automation',
            'cybersecurity', 'security', 'threat detection', 'incident response',
            'vulnerability', 'risk', 'compliance', 'governance', 'ethics',
            'workforce', 'jobs', 'skills', 'training', 'career', 'employment',
            'llm', 'generative ai', 'chatgpt', 'gpt', 'claude', 'neural network'
        ]
        
        for artifact in self.artifacts:
            try:
                # Parse date
                created_at = artifact.get('created_at')
                if not created_at:
                    continue
                    
                if isinstance(created_at, str):
                    date_obj = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                else:
                    date_obj = created_at
                
                month_key = date_obj.strftime('%Y-%m')
                
                # Combine title and content for analysis
                text_content = ""
                if artifact.get('title'):
                    text_content += artifact['title'] + " "
                if artifact.get('content'):
                    text_content += artifact['content'][:1000]  # First 1000 chars
                
                text_content = text_content.lower()
                
                # Count key terms
                for term in key_terms:
                    if term in text_content:
                        monthly_keywords[month_key][term] += 1
                
                # Extract potential topics from metadata
                try:
                    metadata = json.loads(artifact.get('raw_metadata', '{}'))
                    category = metadata.get('ai_impact_category', 'unknown')
                    monthly_topics[month_key][category] += 1
                except:
                    continue
                    
            except Exception as e:
                continue
        
        # Calculate topic trends
        topic_evolution = {
            'keyword_trends': {},
            'topic_distribution': {},
            'emerging_terms': [],
            'declining_terms': []
        }
        
        sorted_months = sorted(monthly_keywords.keys())
        
        # Process keyword trends
        for term in key_terms:
            term_trend = {}
            for month in sorted_months:
                count = monthly_keywords[month][term]
                total_articles = sum(monthly_topics[month].values())
                frequency = count / max(total_articles, 1)
                term_trend[month] = {
                    'count': count,
                    'frequency': round(frequency, 4)
                }
            topic_evolution['keyword_trends'][term] = term_trend
        
        # Process topic distribution trends
        for month in sorted_months:
            total = sum(monthly_topics[month].values())
            if total > 0:
                distribution = {}
                for topic, count in monthly_topics[month].items():
                    distribution[topic] = {
                        'count': count,
                        'percentage': round((count / total) * 100, 1)
                    }
                topic_evolution['topic_distribution'][month] = distribution
        
        # Identify emerging and declining terms
        if len(sorted_months) >= 6:  # Need at least 6 months of data
            recent_months = sorted_months[-3:]
            early_months = sorted_months[:3]
            
            for term in key_terms:
                recent_freq = statistics.mean([
                    topic_evolution['keyword_trends'][term].get(m, {}).get('frequency', 0)
                    for m in recent_months
                ])
                early_freq = statistics.mean([
                    topic_evolution['keyword_trends'][term].get(m, {}).get('frequency', 0)
                    for m in early_months
                ])
                
                change = recent_freq - early_freq
                if change > 0.01:  # Threshold for emergence
                    topic_evolution['emerging_terms'].append({
                        'term': term,
                        'change': round(change, 4),
                        'recent_frequency': round(recent_freq, 4)
                    })
                elif change < -0.01:  # Threshold for decline
                    topic_evolution['declining_terms'].append({
                        'term': term,
                        'change': round(change, 4),
                        'recent_frequency': round(recent_freq, 4)
                    })
        
        # Sort by magnitude of change
        topic_evolution['emerging_terms'].sort(key=lambda x: x['change'], reverse=True)
        topic_evolution['declining_terms'].sort(key=lambda x: x['change'])
        
        print(f"   🔥 Emerging terms: {len(topic_evolution['emerging_terms'])}")
        print(f"   📉 Declining terms: {len(topic_evolution['declining_terms'])}")
        
        return topic_evolution
    
    def analyze_collection_patterns(self) -> Dict[str, Any]:
        """Analyze collection velocity and pattern trends."""
        print("\n📅 Analyzing Collection Patterns...")
        
        daily_collections = defaultdict(int)
        monthly_collections = defaultdict(int)
        weekly_collections = defaultdict(int)
        source_monthly = defaultdict(lambda: defaultdict(int))
        
        for artifact in self.artifacts:
            try:
                created_at = artifact.get('created_at')
                if not created_at:
                    continue
                    
                if isinstance(created_at, str):
                    date_obj = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                else:
                    date_obj = created_at
                
                # Date keys
                day_key = date_obj.strftime('%Y-%m-%d')
                month_key = date_obj.strftime('%Y-%m')
                week_key = date_obj.strftime('%Y-W%U')
                
                daily_collections[day_key] += 1
                monthly_collections[month_key] += 1
                weekly_collections[week_key] += 1
                
                # Source patterns
                if artifact.get('url'):
                    from urllib.parse import urlparse
                    domain = urlparse(artifact['url']).netloc.lower()
                    source_monthly[domain][month_key] += 1
                    
            except Exception as e:
                continue
        
        collection_patterns = {
            'daily_stats': {},
            'monthly_stats': {},
            'weekly_stats': {},
            'collection_velocity': {},
            'source_patterns': {},
            'consistency_score': 0.0
        }
        
        # Process daily patterns
        sorted_days = sorted(daily_collections.keys())
        if sorted_days:
            collection_patterns['daily_stats'] = {
                'total_days': len(sorted_days),
                'avg_per_day': round(statistics.mean(daily_collections.values()), 2),
                'max_day': max(daily_collections.values()),
                'min_day': min(daily_collections.values()),
                'std_dev': round(statistics.stdev(daily_collections.values()) if len(daily_collections) > 1 else 0, 2)
            }
        
        # Process monthly patterns
        sorted_months = sorted(monthly_collections.keys())
        for month in sorted_months:
            collection_patterns['monthly_stats'][month] = {
                'count': monthly_collections[month],
                'daily_avg': round(monthly_collections[month] / 30, 2)  # Approximate
            }
        
        # Calculate collection velocity trends
        if len(sorted_months) >= 2:
            recent_month = monthly_collections[sorted_months[-1]]
            previous_month = monthly_collections[sorted_months[-2]]
            velocity_change = recent_month - previous_month
            
            collection_patterns['collection_velocity'] = {
                'recent_month': recent_month,
                'previous_month': previous_month,
                'change': velocity_change,
                'trend': 'increasing' if velocity_change > 0 else 'decreasing' if velocity_change < 0 else 'stable'
            }
        
        # Analyze source patterns
        for domain, monthly_data in source_monthly.items():
            if sum(monthly_data.values()) >= 3:  # Only sources with 3+ articles
                collection_patterns['source_patterns'][domain] = {
                    'total_articles': sum(monthly_data.values()),
                    'active_months': len(monthly_data),
                    'avg_per_month': round(statistics.mean(monthly_data.values()), 2),
                    'monthly_distribution': dict(monthly_data)
                }
        
        # Calculate consistency score (0-1)
        if daily_collections:
            daily_values = list(daily_collections.values())
            if len(daily_values) > 1:
                cv = statistics.stdev(daily_values) / statistics.mean(daily_values) if statistics.mean(daily_values) > 0 else 1
                consistency_score = max(0, 1 - cv)  # Higher consistency = lower coefficient of variation
                collection_patterns['consistency_score'] = round(consistency_score, 3)
        
        print(f"   📊 Collection consistency: {collection_patterns['consistency_score']:.3f}")
        print(f"   📈 Monthly trend: {collection_patterns.get('collection_velocity', {}).get('trend', 'unknown')}")
        
        return collection_patterns
    
    def analyze_sentiment_trends(self) -> Dict[str, Any]:
        """Analyze sentiment trends in article content over time."""
        print("\n😊 Analyzing Sentiment Trends...")
        
        # Simple sentiment analysis based on keywords
        positive_keywords = ['opportunity', 'growth', 'improve', 'benefit', 'enhance', 'advance', 'efficient', 'effective']
        negative_keywords = ['threat', 'risk', 'danger', 'replace', 'eliminate', 'concern', 'challenge', 'difficult']
        neutral_keywords = ['change', 'shift', 'adapt', 'transform', 'evolve', 'develop', 'implement']
        
        monthly_sentiment = defaultdict(lambda: {'positive': 0, 'negative': 0, 'neutral': 0, 'total': 0})
        category_sentiment = defaultdict(lambda: defaultdict(lambda: {'positive': 0, 'negative': 0, 'neutral': 0, 'total': 0}))
        
        for artifact in self.artifacts:
            try:
                created_at = artifact.get('created_at')
                if not created_at:
                    continue
                    
                if isinstance(created_at, str):
                    date_obj = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                else:
                    date_obj = created_at
                
                month_key = date_obj.strftime('%Y-%m')
                
                # Analyze sentiment in title and content
                text_content = ""
                if artifact.get('title'):
                    text_content += artifact['title'] + " "
                if artifact.get('content'):
                    text_content += artifact['content'][:2000]  # First 2000 chars
                
                text_content = text_content.lower()
                
                # Count sentiment indicators
                pos_count = sum(1 for word in positive_keywords if word in text_content)
                neg_count = sum(1 for word in negative_keywords if word in text_content)
                neu_count = sum(1 for word in neutral_keywords if word in text_content)
                
                # Classify overall sentiment
                if pos_count > neg_count and pos_count > neu_count:
                    sentiment = 'positive'
                elif neg_count > pos_count and neg_count > neu_count:
                    sentiment = 'negative'
                else:
                    sentiment = 'neutral'
                
                monthly_sentiment[month_key][sentiment] += 1
                monthly_sentiment[month_key]['total'] += 1
                
                # Category sentiment
                try:
                    metadata = json.loads(artifact.get('raw_metadata', '{}'))
                    category = metadata.get('ai_impact_category', 'unknown')
                    category_sentiment[category][month_key][sentiment] += 1
                    category_sentiment[category][month_key]['total'] += 1
                except:
                    continue
                    
            except Exception as e:
                continue
        
        sentiment_trends = {
            'monthly_sentiment': {},
            'category_sentiment': {},
            'overall_sentiment': {'positive': 0, 'negative': 0, 'neutral': 0}
        }
        
        # Process monthly sentiment
        sorted_months = sorted(monthly_sentiment.keys())
        for month in sorted_months:
            data = monthly_sentiment[month]
            if data['total'] > 0:
                sentiment_trends['monthly_sentiment'][month] = {
                    'positive': round((data['positive'] / data['total']) * 100, 1),
                    'negative': round((data['negative'] / data['total']) * 100, 1),
                    'neutral': round((data['neutral'] / data['total']) * 100, 1),
                    'total_articles': data['total']
                }
        
        # Calculate overall sentiment
        total_pos = sum(data['positive'] for data in monthly_sentiment.values())
        total_neg = sum(data['negative'] for data in monthly_sentiment.values())
        total_neu = sum(data['neutral'] for data in monthly_sentiment.values())
        total_all = total_pos + total_neg + total_neu
        
        if total_all > 0:
            sentiment_trends['overall_sentiment'] = {
                'positive': round((total_pos / total_all) * 100, 1),
                'negative': round((total_neg / total_all) * 100, 1),
                'neutral': round((total_neu / total_all) * 100, 1)
            }
        
        # Process category sentiment
        for category, monthly_data in category_sentiment.items():
            category_data = {}
            for month, data in monthly_data.items():
                if data['total'] > 0:
                    category_data[month] = {
                        'positive': round((data['positive'] / data['total']) * 100, 1),
                        'negative': round((data['negative'] / data['total']) * 100, 1),
                        'neutral': round((data['neutral'] / data['total']) * 100, 1),
                        'total': data['total']
                    }
            if category_data:
                sentiment_trends['category_sentiment'][category] = category_data
        
        print(f"   😊 Overall sentiment: {sentiment_trends['overall_sentiment']['positive']}% positive, {sentiment_trends['overall_sentiment']['negative']}% negative")
        
        return sentiment_trends
    
    def generate_trend_report(self) -> str:
        """Generate comprehensive trend analysis report."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Run all analyses
        quality_trends = self.analyze_quality_trends()
        topic_evolution = self.analyze_topic_evolution()
        collection_patterns = self.analyze_collection_patterns()
        sentiment_trends = self.analyze_sentiment_trends()
        
        # Get analysis period safely
        valid_dates = [a.get('created_at', '') for a in self.artifacts if a.get('created_at')]
        if valid_dates:
            min_date = min(valid_dates)
            max_date = max(valid_dates)
            analysis_period = f"{min_date} to {max_date}"
        else:
            analysis_period = "No date information available"
        
        report = f"""
# 📊 Comprehensive Trend Analysis Report

**Generated:** {timestamp}
**Total Articles Analyzed:** {len(self.artifacts)}
**Analysis Period:** {analysis_period}

## 📈 Quality Trends Analysis

**Overall Trend:** {quality_trends['trend_direction'].title()}
**Quality Improvement:** {quality_trends['quality_improvement']:+.3f}

### Monthly Quality Evolution
| Month | Avg Quality | Articles | Std Dev |
|-------|-------------|----------|---------|"""

        for month, data in sorted(quality_trends['overall_monthly'].items()):
            report += f"""
| {month} | {data['avg_quality']:.3f} | {data['count']} | {data['std_dev']:.3f} |"""

        report += f"""

### Quality Trends by Category
"""
        for category, monthly_data in quality_trends['category_trends'].items():
            if monthly_data:
                recent_quality = list(monthly_data.values())[-1]['avg_quality'] if monthly_data else 0
                article_count = sum(data['count'] for data in monthly_data.values())
                report += f"- **{category}**: {recent_quality:.3f} average ({article_count} articles)\n"

        report += f"""

## 🔍 Topic Evolution Analysis

### Emerging Terms (Increasing Frequency)
"""
        if topic_evolution['emerging_terms']:
            for term_data in topic_evolution['emerging_terms'][:5]:
                report += f"- **{term_data['term']}**: +{term_data['change']:.4f} frequency increase\n"
        else:
            report += "- No significant emerging terms detected\n"

        report += f"""
### Declining Terms (Decreasing Frequency)
"""
        if topic_evolution['declining_terms']:
            for term_data in topic_evolution['declining_terms'][:5]:
                report += f"- **{term_data['term']}**: {term_data['change']:.4f} frequency decrease\n"
        else:
            report += "- No significant declining terms detected\n"

        report += f"""

## 📅 Collection Pattern Analysis

**Collection Consistency Score:** {collection_patterns['consistency_score']:.3f}/1.0
**Recent Trend:** {collection_patterns.get('collection_velocity', {}).get('trend', 'Unknown').title()}

### Monthly Collection Statistics
| Month | Articles | Daily Avg |
|-------|----------|-----------|"""

        for month, data in sorted(collection_patterns['monthly_stats'].items()):
            report += f"""
| {month} | {data['count']} | {data['daily_avg']:.1f} |"""

        report += f"""

### Top Performing Sources
| Source | Total Articles | Active Months | Avg/Month |
|--------|----------------|---------------|-----------|"""

        sorted_sources = sorted(
            collection_patterns['source_patterns'].items(),
            key=lambda x: x[1]['total_articles'],
            reverse=True
        )
        
        if sorted_sources:
            for domain, data in sorted_sources[:10]:
                report += f"""
| {domain} | {data['total_articles']} | {data['active_months']} | {data['avg_per_month']:.1f} |"""
        else:
            report += """
| No source data available | - | - | - |"""

        report += f"""

## 😊 Sentiment Trends Analysis

**Overall Sentiment Distribution:**
- Positive: {sentiment_trends['overall_sentiment']['positive']}%
- Neutral: {sentiment_trends['overall_sentiment']['neutral']}%  
- Negative: {sentiment_trends['overall_sentiment']['negative']}%

### Monthly Sentiment Evolution
| Month | Positive % | Neutral % | Negative % | Articles |
|-------|------------|-----------|------------|----------|"""

        for month, data in sorted(sentiment_trends['monthly_sentiment'].items()):
            report += f"""
| {month} | {data['positive']}% | {data['neutral']}% | {data['negative']}% | {data['total_articles']} |"""

        report += f"""

## 🎯 Key Insights & Recommendations

### Quality Insights
"""
        if quality_trends['trend_direction'] == 'improving':
            report += "- ✅ Content quality is improving over time\n"
            report += f"- 📈 Quality improvement of {quality_trends['quality_improvement']:+.3f} detected\n"
        elif quality_trends['trend_direction'] == 'declining':
            report += "- ⚠️ Content quality showing decline\n"
            report += f"- 📉 Quality decline of {quality_trends['quality_improvement']:.3f} detected\n"
            report += "- 🎯 Recommend focusing on higher-quality sources\n"
        else:
            report += "- 📊 Content quality remains stable\n"

        report += f"""
### Collection Insights
"""
        if collection_patterns['consistency_score'] > 0.7:
            report += "- ✅ Collection patterns are highly consistent\n"
        elif collection_patterns['consistency_score'] > 0.5:
            report += "- 📊 Collection patterns show moderate consistency\n"
        else:
            report += "- ⚠️ Collection patterns are inconsistent\n"
            report += "- 🎯 Recommend establishing regular collection schedule\n"

        velocity_trend = collection_patterns.get('collection_velocity', {}).get('trend')
        if velocity_trend == 'increasing':
            report += "- 📈 Collection velocity is increasing\n"
        elif velocity_trend == 'decreasing':
            report += "- 📉 Collection velocity is decreasing\n"
            report += "- 🎯 Consider expanding source coverage\n"

        report += f"""
### Topic Insights
"""
        if topic_evolution['emerging_terms']:
            report += f"- 🔥 {len(topic_evolution['emerging_terms'])} emerging topics identified\n"
            top_emerging = topic_evolution['emerging_terms'][0]
            report += f"- 📈 Fastest growing topic: '{top_emerging['term']}'\n"
        else:
            report += "- 📊 No significant topic emergence detected\n"
        
        if topic_evolution['declining_terms']:
            report += f"- 📉 {len(topic_evolution['declining_terms'])} declining topics identified\n"
        else:
            report += "- 📊 No significant topic decline detected\n"

        report += f"""
### Sentiment Insights
"""
        pos_pct = sentiment_trends['overall_sentiment']['positive']
        neg_pct = sentiment_trends['overall_sentiment']['negative']
        
        if pos_pct > neg_pct * 1.5:
            report += "- 😊 Overall sentiment is predominantly positive\n"
        elif neg_pct > pos_pct * 1.5:
            report += "- 😟 Overall sentiment leans negative\n"
            report += "- 🎯 Consider balancing with more opportunity-focused content\n"
        else:
            report += "- 📊 Sentiment is well-balanced across positive/negative spectrum\n"

        report += f"""

---

*This trend analysis provides insights into temporal patterns across content quality, topics, collection patterns, and sentiment. Use these insights to optimize collection strategies and understand evolving landscape trends.*
"""

        return report

def main():
    """Run comprehensive trend analysis."""
    print("Starting Comprehensive Trend Analysis...")
    print("=" * 60)
    
    analyzer = TrendAnalyzer()
    
    # Load all data
    data_count = analyzer.load_all_data()
    
    if data_count == 0:
        print("No data available for trend analysis")
        return
    
    # Generate comprehensive trend report
    report = analyzer.generate_trend_report()
    
    # Save report
    report_dir = Path('data/reports')
    report_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = report_dir / f'trend_analysis_{timestamp}.md'
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\nTrend analysis complete!")
    print(f"Report saved to: {report_file}")
    print(f"Analyzed {data_count} articles")
    
    # Print summary
    print("\n" + "=" * 60)
    print("TREND ANALYSIS SUMMARY")
    print("=" * 60)
    
    # Quick summary
    quality_trends = analyzer.analyze_quality_trends()
    collection_patterns = analyzer.analyze_collection_patterns()
    sentiment_trends = analyzer.analyze_sentiment_trends()
    
    print(f"Quality Trend: {quality_trends['trend_direction'].title()}")
    print(f"Collection Consistency: {collection_patterns['consistency_score']:.3f}")
    print(f"Sentiment Balance: {sentiment_trends['overall_sentiment']['positive']}% positive")
    print(f"Analysis Period: Full dataset temporal coverage")

if __name__ == "__main__":
    main() 