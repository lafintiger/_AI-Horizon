#!/usr/bin/env python3
"""
AI-Horizon Category Summary Report Generator
Generates comprehensive summaries of all articles organized by AI impact category.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from aih.utils.database import DatabaseManager
import json
from collections import defaultdict, Counter
from datetime import datetime
import re
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

class CategorySummaryReporter:
    def __init__(self):
        self.db = DatabaseManager()
        self.categories = {
            'replace': 'AI REPLACE - Tasks completely automated by AI',
            'augment': 'AI AUGMENT - Human-AI collaboration enhancing capabilities',
            'new_tasks': 'AI NEW TASKS - Jobs created due to AI technology',
            'human_only': 'AI HUMAN-ONLY - Tasks requiring uniquely human expertise',
            'unknown': 'UNCATEGORIZED - Not yet classified'
        }
        
    def get_all_articles(self):
        """Retrieve all articles from the database."""
        try:
            articles = []
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get all artifacts
                query = """
                SELECT id, title, content, url, source_type, collected_at, raw_metadata
                FROM artifacts
                ORDER BY collected_at DESC
                """
                
                cursor.execute(query)
                results = cursor.fetchall()
                
                for row in results:
                    # Parse metadata
                    metadata = json.loads(row[6]) if row[6] else {}
                    
                    # Get category from metadata (where it's actually stored)
                    category = metadata.get('ai_impact_category', 'unknown')
                    confidence = metadata.get('classification_confidence', 0)
                    
                    articles.append({
                        'id': row[0],
                        'title': row[1] or '',
                        'content': row[2] or '',
                        'url': row[3] or '',
                        'category': category,
                        'metadata': metadata,
                        'created_at': row[5],
                        'quality_score': metadata.get('quality_score', 0),
                        'wisdom': metadata.get('extracted_wisdom', {}),
                        'source_type': row[4] or 'unknown',
                        'confidence': confidence
                    })
            
            logger.info(f"Retrieved {len(articles)} articles from database")
            return articles
            
        except Exception as e:
            logger.error(f"Error retrieving articles: {e}")
            return []
    
    def categorize_articles(self, articles):
        """Organize articles by category."""
        categorized = defaultdict(list)
        
        for article in articles:
            category = article['category']
            categorized[category].append(article)
        
        return categorized
    
    def extract_key_insights(self, article):
        """Extract key insights from an article."""
        insights = {
            'title': article['title'],
            'quality_score': article['quality_score'],
            'source_type': article['source_type'],
            'url': article['url']
        }
        
        # Extract wisdom insights if available
        wisdom = article.get('wisdom', {})
        if wisdom:
            insights['key_insights'] = wisdom.get('key_insights', [])
            insights['implications'] = wisdom.get('implications', [])
            insights['recommendations'] = wisdom.get('recommendations', [])
        
        # Extract content summary (first 200 chars)
        content = article.get('content', '')
        if content:
            insights['summary'] = content[:200] + "..." if len(content) > 200 else content
        
        return insights
    
    def analyze_category_themes(self, articles):
        """Analyze common themes within a category."""
        themes = Counter()
        skills_mentioned = Counter()
        technologies = Counter()
        
        # Common cybersecurity terms to look for
        cyber_terms = [
            'threat detection', 'incident response', 'vulnerability', 'penetration testing',
            'security analyst', 'SIEM', 'SOC', 'malware', 'phishing', 'ransomware',
            'compliance', 'risk assessment', 'firewall', 'encryption', 'authentication',
            'zero trust', 'cloud security', 'endpoint security', 'network security'
        ]
        
        ai_terms = [
            'machine learning', 'artificial intelligence', 'automation', 'neural networks',
            'deep learning', 'natural language processing', 'computer vision', 'predictive analytics',
            'anomaly detection', 'behavioral analysis', 'AI-powered', 'intelligent automation'
        ]
        
        for article in articles:
            content = (article.get('content', '') + ' ' + article.get('title', '')).lower()
            
            # Count cybersecurity terms
            for term in cyber_terms:
                if term in content:
                    skills_mentioned[term] += 1
            
            # Count AI terms
            for term in ai_terms:
                if term in content:
                    technologies[term] += 1
        
        return {
            'top_skills': skills_mentioned.most_common(10),
            'top_technologies': technologies.most_common(10),
            'article_count': len(articles)
        }
    
    def generate_category_summary(self, category, articles):
        """Generate a comprehensive summary for a category."""
        if not articles:
            return {
                'category': category,
                'description': self.categories.get(category, 'Unknown category'),
                'article_count': 0,
                'articles': [],
                'themes': {},
                'quality_stats': {}
            }
        
        # Quality statistics
        quality_scores = [a['quality_score'] for a in articles if a['quality_score']]
        quality_stats = {
            'average_quality': sum(quality_scores) / len(quality_scores) if quality_scores else 0,
            'high_quality_count': len([q for q in quality_scores if q >= 0.8]),
            'medium_quality_count': len([q for q in quality_scores if 0.6 <= q < 0.8]),
            'low_quality_count': len([q for q in quality_scores if q < 0.6])
        }
        
        # Source type distribution
        source_types = Counter(a['source_type'] for a in articles)
        
        # Extract insights from top articles
        top_articles = sorted(articles, key=lambda x: x['quality_score'], reverse=True)[:10]
        article_insights = [self.extract_key_insights(a) for a in top_articles]
        
        # Analyze themes
        themes = self.analyze_category_themes(articles)
        
        return {
            'category': category,
            'description': self.categories.get(category, 'Unknown category'),
            'article_count': len(articles),
            'quality_stats': quality_stats,
            'source_distribution': dict(source_types),
            'themes': themes,
            'top_articles': article_insights,
            'recent_articles': [self.extract_key_insights(a) for a in articles[:5]]
        }
    
    def generate_comprehensive_report(self):
        """Generate the complete category summary report."""
        logger.info("Starting comprehensive category summary report generation...")
        
        # Get all articles
        articles = self.get_all_articles()
        if not articles:
            logger.error("No articles found in database")
            return None
        
        # Categorize articles
        categorized = self.categorize_articles(articles)
        
        # Generate report
        report = {
            'generated_at': datetime.now().isoformat(),
            'total_articles': len(articles),
            'categories': {},
            'overall_stats': {
                'category_distribution': {cat: len(arts) for cat, arts in categorized.items()},
                'total_quality_articles': len([a for a in articles if a['quality_score'] >= 0.8]),
                'average_quality': sum(a['quality_score'] for a in articles if a['quality_score']) / len([a for a in articles if a['quality_score']]) if articles else 0
            }
        }
        
        # Generate summary for each category
        for category in ['replace', 'augment', 'new_tasks', 'human_only', 'unknown']:
            articles_in_category = categorized.get(category, [])
            category_summary = self.generate_category_summary(category, articles_in_category)
            report['categories'][category] = category_summary
            
            logger.info(f"Generated summary for {category}: {len(articles_in_category)} articles")
        
        return report
    
    def save_report(self, report, filename=None):
        """Save the report to a file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data/category_summary_report_{timestamp}.json"
        
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Report saved to: {filename}")
            return filename
        except Exception as e:
            logger.error(f"Error saving report: {e}")
            return None
    
    def print_summary(self, report):
        """Print a formatted summary to console."""
        print("\n" + "="*80)
        print("🎯 AI-HORIZON CATEGORY SUMMARY REPORT")
        print("="*80)
        print(f"📊 Generated: {report['generated_at']}")
        print(f"📄 Total Articles: {report['total_articles']}")
        print(f"⭐ High Quality Articles: {report['overall_stats']['total_quality_articles']}")
        print(f"📈 Average Quality Score: {report['overall_stats']['average_quality']:.3f}")
        
        print("\n📋 CATEGORY DISTRIBUTION:")
        for category, count in report['overall_stats']['category_distribution'].items():
            percentage = (count / report['total_articles']) * 100
            print(f"   {category.upper()}: {count} articles ({percentage:.1f}%)")
        
        print("\n" + "="*80)
        print("📚 DETAILED CATEGORY SUMMARIES")
        print("="*80)
        
        for category, summary in report['categories'].items():
            if summary['article_count'] == 0:
                continue
                
            print(f"\n🏷️  {summary['description']}")
            print("-" * 60)
            print(f"📊 Articles: {summary['article_count']}")
            print(f"⭐ Average Quality: {summary['quality_stats']['average_quality']:.3f}")
            print(f"🟢 High Quality: {summary['quality_stats']['high_quality_count']}")
            print(f"🟡 Medium Quality: {summary['quality_stats']['medium_quality_count']}")
            print(f"🔴 Low Quality: {summary['quality_stats']['low_quality_count']}")
            
            print(f"\n📈 Top Skills/Topics:")
            for skill, count in summary['themes']['top_skills'][:5]:
                print(f"   • {skill}: {count} mentions")
            
            print(f"\n🤖 Top Technologies:")
            for tech, count in summary['themes']['top_technologies'][:5]:
                print(f"   • {tech}: {count} mentions")
            
            print(f"\n📑 Top Quality Articles:")
            for i, article in enumerate(summary['top_articles'][:3], 1):
                print(f"   {i}. {article['title'][:60]}... (Quality: {article['quality_score']:.3f})")
        
        print("\n" + "="*80)

def main():
    """Main execution function."""
    try:
        reporter = CategorySummaryReporter()
        
        # Generate comprehensive report
        report = reporter.generate_comprehensive_report()
        
        if report:
            # Save to file
            filename = reporter.save_report(report)
            
            # Print summary to console
            reporter.print_summary(report)
            
            print(f"\n💾 Full detailed report saved to: {filename}")
            print("🎉 Category summary report generation completed successfully!")
            
        else:
            print("❌ Failed to generate report")
            
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        print(f"❌ Error generating report: {e}")

if __name__ == "__main__":
    main() 