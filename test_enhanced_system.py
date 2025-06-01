#!/usr/bin/env python3
"""
Test script for the enhanced AI-Horizon system with:
- Task-focused queries
- Multi-query collection
- Duplicate detection
- Real source URLs
"""

import asyncio
from aih.gather.perplexity import PerplexityConnector
from aih.utils.database import DatabaseManager

async def test_enhanced_system():
    print("🚀 Testing Enhanced AI-Horizon System")
    print("=" * 60)
    
    # Initialize components
    db = DatabaseManager()
    connector = PerplexityConnector()
    
    # Get existing URLs to test duplicate detection
    existing_urls = db.get_existing_urls()
    print(f"📚 Existing articles in database: {len(existing_urls)}")
    
    # Test 1: Single category multi-query collection
    print(f"\n🔍 Test 1: Multi-query collection for 'replace' category")
    
    artifacts = await connector.collect_multi_query(
        category="replace",
        max_results=15,
        timeframe="2024",
        existing_urls=existing_urls
    )
    
    print(f"✅ Multi-query collection results:")
    print(f"   📊 Total unique articles: {len(artifacts)}")
    print(f"   🔗 Real source URLs: {sum(1 for a in artifacts if not a.url.startswith('perplexity://'))}")
    
    # Show sample results
    print(f"\n📄 Sample articles:")
    for i, artifact in enumerate(artifacts[:5], 1):
        print(f"  {i}. {artifact.title[:60]}...")
        print(f"     URL: {artifact.url}")
        print(f"     Date: {artifact.metadata.get('date', 'N/A')}")
        print()
    
    # Test 2: Check for duplicates
    print(f"\n🔍 Test 2: Duplicate detection")
    
    # Run same collection again to test duplicate filtering
    artifacts_2 = await connector.collect_multi_query(
        category="replace",
        max_results=10,
        timeframe="2024",
        existing_urls={a.url for a in artifacts}  # Use first batch as existing
    )
    
    print(f"✅ Second collection with duplicate filtering:")
    print(f"   📊 New unique articles: {len(artifacts_2)}")
    
    # Test 3: Verify URL quality
    print(f"\n🔍 Test 3: Source URL quality assessment")
    
    all_artifacts = artifacts + artifacts_2
    real_urls = [a for a in all_artifacts if not a.url.startswith('perplexity://')]
    fake_urls = [a for a in all_artifacts if a.url.startswith('perplexity://')]
    
    print(f"✅ URL Quality Results:")
    print(f"   ✅ Real source URLs: {len(real_urls)} ({len(real_urls)/len(all_artifacts)*100:.1f}%)")
    print(f"   ❌ Fake URLs: {len(fake_urls)} ({len(fake_urls)/len(all_artifacts)*100:.1f}%)")
    
    # Test 4: Source diversity
    print(f"\n🔍 Test 4: Source diversity analysis")
    
    domains = set()
    for artifact in real_urls:
        try:
            from urllib.parse import urlparse
            domain = urlparse(artifact.url).netloc
            domains.add(domain)
        except:
            pass
    
    print(f"✅ Source Diversity:")
    print(f"   🌐 Unique domains: {len(domains)}")
    print(f"   📰 Sample domains: {list(domains)[:5]}")
    
    # Summary
    print(f"\n🎉 ENHANCEMENT TEST SUMMARY:")
    print(f"=" * 60)
    print(f"✅ Multi-query collection: {'WORKING' if len(artifacts) > 5 else 'NEEDS IMPROVEMENT'}")
    print(f"✅ Real source URLs: {'WORKING' if len(real_urls) > len(fake_urls) else 'NEEDS IMPROVEMENT'}")
    print(f"✅ Duplicate detection: {'WORKING' if len(set(a.url for a in all_artifacts)) == len(all_artifacts) else 'NEEDS IMPROVEMENT'}")
    print(f"✅ Source diversity: {'WORKING' if len(domains) > 3 else 'NEEDS IMPROVEMENT'}")
    
    return all_artifacts

if __name__ == "__main__":
    artifacts = asyncio.run(test_enhanced_system()) 