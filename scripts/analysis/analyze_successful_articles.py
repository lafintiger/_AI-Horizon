#!/usr/bin/env python3
"""
Analyze Successful Articles

Examines the successful "replace" and "augment" articles to understand
what content patterns and sources worked best for developing new search strategies.
"""

import sys
import json
from pathlib import Path
from typing import List, Dict

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from aih.utils.database import DatabaseManager

def analyze_articles_by_category(category: str) -> List[Dict]:
    """Get articles for a specific category and analyze them."""
    db = DatabaseManager()
    artifacts = db.get_artifacts()
    
    category_articles = []
    for artifact in artifacts:
        metadata = json.loads(artifact.get('raw_metadata', '{}'))
        if metadata.get('ai_impact_category') == category:
            category_articles.append({
                'title': artifact.get('title', 'No title'),
                'url': artifact.get('url', 'No URL'),
                'content': artifact.get('content', 'No content')[:500] + '...',
                'source_type': artifact.get('source_type', 'Unknown'),
                'collected_at': artifact.get('collected_at', 'Unknown')
            })
    
    return category_articles

def extract_content_patterns(articles: List[Dict]) -> Dict:
    """Analyze content patterns in successful articles."""
    patterns = {
        'common_keywords': [],
        'source_domains': [],
        'content_themes': [],
        'title_patterns': []
    }
    
    for article in articles:
        # Extract domain from URL
        if 'url' in article and article['url'] != 'No URL':
            try:
                from urllib.parse import urlparse
                domain = urlparse(article['url']).netloc
                patterns['source_domains'].append(domain)
            except:
                pass
        
        # Analyze title patterns
        title = article.get('title', '').lower()
        if 'ai' in title:
            patterns['title_patterns'].append('Contains "AI"')
        if 'automation' in title:
            patterns['title_patterns'].append('Contains "automation"')
        if 'job' in title or 'career' in title:
            patterns['title_patterns'].append('Job/career related')
        if 'company' in title or 'enterprise' in title:
            patterns['title_patterns'].append('Enterprise focused')
        
        # Analyze content themes (first 500 chars)
        content = article.get('content', '').lower()
        if 'ceo' in content or 'executive' in content:
            patterns['content_themes'].append('Executive leadership')
        if 'mandate' in content or 'require' in content:
            patterns['content_themes'].append('Mandates/requirements')
        if 'performance' in content:
            patterns['content_themes'].append('Performance metrics')
        if 'efficiency' in content or 'productivity' in content:
            patterns['content_themes'].append('Efficiency/productivity')
        if 'transformation' in content:
            patterns['content_themes'].append('Digital transformation')
    
    return patterns

def main():
    """Analyze successful articles and provide insights."""
    print("🔍 Analyzing Successful Articles for Pattern Recognition")
    print("=" * 60)
    
    # Analyze Replace category
    replace_articles = analyze_articles_by_category('replace')
    print(f"\n📊 REPLACE Category Analysis ({len(replace_articles)} articles)")
    print("-" * 40)
    
    if replace_articles:
        for i, article in enumerate(replace_articles, 1):
            print(f"\n{i}. {article['title']}")
            print(f"   URL: {article['url']}")
            print(f"   Source: {article['source_type']}")
            print(f"   Content preview: {article['content'][:200]}...")
        
        replace_patterns = extract_content_patterns(replace_articles)
        print(f"\n🎯 Replace Category Patterns:")
        print(f"   Domains: {set(replace_patterns['source_domains'])}")
        print(f"   Title patterns: {set(replace_patterns['title_patterns'])}")
        print(f"   Content themes: {set(replace_patterns['content_themes'])}")
    else:
        print("   No replace articles found")
    
    # Analyze Augment category
    augment_articles = analyze_articles_by_category('augment')
    print(f"\n📊 AUGMENT Category Analysis ({len(augment_articles)} articles)")
    print("-" * 40)
    
    if augment_articles:
        for i, article in enumerate(augment_articles, 1):
            print(f"\n{i}. {article['title']}")
            print(f"   URL: {article['url']}")
            print(f"   Source: {article['source_type']}")
            print(f"   Content preview: {article['content'][:200]}...")
        
        augment_patterns = extract_content_patterns(augment_articles)
        print(f"\n🎯 Augment Category Patterns:")
        print(f"   Domains: {set(augment_patterns['source_domains'])}")
        print(f"   Title patterns: {set(augment_patterns['title_patterns'])}")
        print(f"   Content themes: {set(augment_patterns['content_themes'])}")
    else:
        print("   No augment articles found")
    
    # High-value source recommendations
    print(f"\n💡 HIGH-VALUE SOURCE RECOMMENDATIONS")
    print("-" * 40)
    print("Based on analysis, focus on:")
    print("📰 Independent Tech Journalism:")
    print("   - Stratechery, Benedict Evans, Casey Newton")
    print("   - The Information, Protocol, Axios (tech section)")
    print("   - Individual tech reporters on Substack")
    
    print("\n🏢 Industry Leader Content:")
    print("   - Company blog posts by CEOs/CTOs")
    print("   - Earnings call transcripts")
    print("   - Internal company memos (when public)")
    
    print("\n💬 Community Sources:")
    print("   - Reddit: r/programming, r/MachineLearning, r/cscareerquestions")
    print("   - Hacker News discussions")
    print("   - LinkedIn posts by industry leaders")
    
    print("\n🎥 Video Content:")
    print("   - YouTube: All-In Podcast, Lex Fridman, tech conference talks")
    print("   - Podcast transcripts from industry shows")
    
    return replace_articles, augment_articles

if __name__ == "__main__":
    main() 