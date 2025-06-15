#!/usr/bin/env python3
"""
AI-Horizon Detailed Category Analysis
Shows both primary categories and multi-category analysis with confidence scores.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from aih.utils.database import DatabaseManager
import json
from collections import defaultdict, Counter
from datetime import datetime
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

class DetailedCategoryAnalyzer:
    def __init__(self):
        self.db = DatabaseManager()
        self.categories = {
            'replace': 'AI REPLACE - Tasks completely automated by AI',
            'augment': 'AI AUGMENT - Human-AI collaboration enhancing capabilities',
            'new_tasks': 'AI NEW TASKS - Jobs created due to AI technology',
            'human_only': 'AI HUMAN-ONLY - Tasks requiring uniquely human expertise',
            'unknown': 'UNCATEGORIZED - Not yet classified'
        }
        
    def get_all_articles_with_multicategory(self):
        """Retrieve all articles with their multi-category analysis."""
        try:
            articles = []
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                query = """
                SELECT id, title, content, url, source_type, collected_at, raw_metadata
                FROM artifacts
                ORDER BY collected_at DESC
                """
                
                cursor.execute(query)
                results = cursor.fetchall()
                
                for row in results:
                    metadata = json.loads(row[6]) if row[6] else {}
                    
                    # Get primary category
                    primary_category = metadata.get('ai_impact_category', 'unknown')
                    
                    # Get multi-category analysis
                    multicategory = metadata.get('ai_impact_categories', {})
                    primary_from_multi = metadata.get('primary_category', 'unknown')
                    
                    # Get wisdom data
                    wisdom = metadata.get('extracted_wisdom', {})
                    
                    articles.append({
                        'id': row[0],
                        'title': row[1] or '',
                        'content': row[2] or '',
                        'url': row[3] or '',
                        'primary_category': primary_category,
                        'primary_from_multi': primary_from_multi,
                        'multicategory': multicategory,
                        'metadata': metadata,
                        'created_at': row[5],
                        'quality_score': metadata.get('quality_score', 0),
                        'wisdom': wisdom,
                        'source_type': row[4] or 'unknown',
                        'has_wisdom': bool(wisdom.get('key_wisdom'))
                    })
            
            logger.info(f"Retrieved {len(articles)} articles with multi-category analysis")
            return articles
            
        except Exception as e:
            logger.error(f"Error retrieving articles: {e}")
            return []
    
    def analyze_multicategory_distribution(self, articles):
        """Analyze the distribution across multi-categories."""
        category_stats = defaultdict(lambda: {'count': 0, 'total_confidence': 0, 'articles': []})
        
        for article in articles:
            multicategory = article.get('multicategory', {})
            
            for category, data in multicategory.items():
                confidence = data.get('confidence', 0)
                if confidence > 0:  # Only count categories with positive confidence
                    category_stats[category]['count'] += 1
                    category_stats[category]['total_confidence'] += confidence
                    category_stats[category]['articles'].append({
                        'title': article['title'],
                        'confidence': confidence,
                        'quality_score': article['quality_score'],
                        'evidence': data.get('evidence', []),
                        'url': article['url']
                    })
        
        # Calculate averages and sort
        for category in category_stats:
            stats = category_stats[category]
            stats['avg_confidence'] = stats['total_confidence'] / stats['count'] if stats['count'] > 0 else 0
            stats['articles'].sort(key=lambda x: x['confidence'], reverse=True)
        
        return dict(category_stats)
    
    def get_top_articles_by_category(self, articles, category, limit=10):
        """Get top articles for a specific category based on confidence."""
        category_articles = []
        
        for article in articles:
            multicategory = article.get('multicategory', {})
            if category in multicategory:
                confidence = multicategory[category].get('confidence', 0)
                if confidence > 0:
                    category_articles.append({
                        'title': article['title'],
                        'confidence': confidence,
                        'quality_score': article['quality_score'],
                        'evidence': multicategory[category].get('evidence', []),
                        'url': article['url'],
                        'wisdom_summary': article['wisdom'].get('summary', '') if article['wisdom'] else '',
                        'key_insights': article['wisdom'].get('key_wisdom', []) if article['wisdom'] else []
                    })
        
        return sorted(category_articles, key=lambda x: (x['confidence'], x['quality_score']), reverse=True)[:limit]
    
    def extract_category_themes(self, articles, category):
        """Extract themes and evidence for a specific category."""
        all_evidence = []
        keyword_counts = Counter()
        
        for article in articles:
            multicategory = article.get('multicategory', {})
            if category in multicategory:
                evidence = multicategory[category].get('evidence', [])
                all_evidence.extend(evidence)
                for keyword in evidence:
                    keyword_counts[keyword] += 1
        
        return {
            'top_evidence': keyword_counts.most_common(10),
            'total_evidence_items': len(all_evidence),
            'unique_evidence_items': len(set(all_evidence))
        }
    
    def generate_comprehensive_analysis(self):
        """Generate comprehensive multi-category analysis."""
        logger.info("Starting detailed multi-category analysis...")
        
        articles = self.get_all_articles_with_multicategory()
        if not articles:
            logger.error("No articles found")
            return None
        
        # Analyze multi-category distribution
        multicategory_stats = self.analyze_multicategory_distribution(articles)
        
        # Generate report
        report = {
            'generated_at': datetime.now().isoformat(),
            'total_articles': len(articles),
            'articles_with_wisdom': len([a for a in articles if a['has_wisdom']]),
            'multicategory_analysis': {},
            'category_summaries': {},
            'overall_stats': {
                'avg_quality_score': sum(a['quality_score'] for a in articles) / len(articles) if articles else 0,
                'high_quality_articles': len([a for a in articles if a['quality_score'] >= 0.8]),
                'articles_with_multicategory': len([a for a in articles if a['multicategory']])
            }
        }
        
        # Analyze each category
        for category in ['replace', 'augment', 'new_tasks', 'human_only']:
            if category in multicategory_stats:
                stats = multicategory_stats[category]
                top_articles = self.get_top_articles_by_category(articles, category, 10)
                themes = self.extract_category_themes(articles, category)
                
                report['category_summaries'][category] = {
                    'description': self.categories[category],
                    'article_count': stats['count'],
                    'avg_confidence': stats['avg_confidence'],
                    'total_confidence': stats['total_confidence'],
                    'top_articles': top_articles,
                    'themes': themes
                }
        
        report['multicategory_analysis'] = multicategory_stats
        
        return report
    
    def print_detailed_analysis(self, report):
        """Print detailed analysis to console."""
        print("\n" + "="*100)
        print("🎯 AI-HORIZON DETAILED MULTI-CATEGORY ANALYSIS")
        print("="*100)
        print(f"📊 Generated: {report['generated_at']}")
        print(f"📄 Total Articles: {report['total_articles']}")
        print(f"🧠 Articles with Wisdom: {report['articles_with_wisdom']}")
        print(f"⭐ High Quality Articles: {report['overall_stats']['high_quality_articles']}")
        print(f"📈 Average Quality Score: {report['overall_stats']['avg_quality_score']:.3f}")
        print(f"🎯 Articles with Multi-Category Analysis: {report['overall_stats']['articles_with_multicategory']}")
        
        print("\n" + "="*100)
        print("📊 MULTI-CATEGORY DISTRIBUTION ANALYSIS")
        print("="*100)
        
        for category, summary in report['category_summaries'].items():
            print(f"\n🏷️  {summary['description']}")
            print("-" * 80)
            print(f"📊 Articles with this category: {summary['article_count']}")
            print(f"📈 Average Confidence: {summary['avg_confidence']:.3f}")
            print(f"📊 Total Confidence Score: {summary['total_confidence']:.2f}")
            
            print(f"\n🔍 Top Evidence Keywords:")
            for evidence, count in summary['themes']['top_evidence'][:5]:
                print(f"   • {evidence}: {count} articles")
            
            print(f"\n📑 Top Articles by Confidence:")
            for i, article in enumerate(summary['top_articles'][:5], 1):
                print(f"   {i}. {article['title'][:70]}...")
                print(f"      Confidence: {article['confidence']:.3f} | Quality: {article['quality_score']:.3f}")
                if article['key_insights']:
                    print(f"      Key Insight: {article['key_insights'][0][:100]}...")
                print()
        
        print("\n" + "="*100)
        print("🎯 CATEGORY OVERLAP ANALYSIS")
        print("="*100)
        
        # Show articles that appear in multiple categories
        multicategory_articles = []
        for article_data in report['multicategory_analysis'].values():
            for article in article_data['articles']:
                if article not in multicategory_articles:
                    multicategory_articles.append(article)
        
        # Find articles with high confidence in multiple categories
        print("📊 Articles with strong presence in multiple categories:")
        category_counts = Counter()
        for category_name, category_data in report['multicategory_analysis'].items():
            for article in category_data['articles']:
                if article['confidence'] > 0.5:  # High confidence threshold
                    category_counts[article['title']] += 1
        
        multi_category_articles = [(title, count) for title, count in category_counts.items() if count > 1]
        multi_category_articles.sort(key=lambda x: x[1], reverse=True)
        
        for title, count in multi_category_articles[:10]:
            print(f"   • {title[:70]}... ({count} categories)")
        
        print("\n" + "="*100)

def main():
    """Main execution function."""
    try:
        analyzer = DetailedCategoryAnalyzer()
        
        # Generate comprehensive analysis
        report = analyzer.generate_comprehensive_analysis()
        
        if report:
            # Print detailed analysis
            analyzer.print_detailed_analysis(report)
            
            # Save to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data/detailed_category_analysis_{timestamp}.json"
            
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 Full detailed analysis saved to: {filename}")
            print("🎉 Detailed category analysis completed successfully!")
            
        else:
            print("❌ Failed to generate analysis")
            
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        print(f"❌ Error generating analysis: {e}")

if __name__ == "__main__":
    main() 