#!/usr/bin/env python3
"""
Comprehensive Article Collection Script

Collects 20 articles for each AI impact category (replace, augment, new_tasks, human_only)
using diverse search queries targeting blogs, Reddit, YouTube, and other sources.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from aih.gather.perplexity import PerplexityConnector
from aih.utils.database import DatabaseManager
from aih.utils.logging import get_logger

async def collect_comprehensive():
    """Run comprehensive collection across all categories."""
    logger = get_logger('comprehensive_collection')
    collector = PerplexityConnector()
    db = DatabaseManager()
    
    # Comprehensive search queries for each category
    searches = {
        'replace': [
            'AI completely replacing cybersecurity analysts SOC automation 2024 2025',
            'automated threat detection replacing human analysts blog reddit',
            'SIEM automation eliminating cybersecurity jobs reddit discussion',
            'vulnerability scanning automated AI no human needed',
            'incident response automation replacing analysts YouTube',
            'lights-out security operations AI takeover blog posts',
            'malware analysis automated AI replacing experts',
            'log analysis SIEM fully automated no analysts needed',
            'compliance checking automated AI replacing humans reddit',
            'penetration testing automated AI replacing pentesters blog',
            'network monitoring AI automation no human oversight',
            'security orchestration fully automated SOAR replacing analysts',
            'threat hunting automated AI replacing hunters blog reddit',
            'forensics analysis AI automation replacing investigators',
            'patch management fully automated no human intervention',
            'risk assessment automated AI eliminating analysts',
            'security awareness training AI replacing human trainers',
            'access control management fully automated AI',
            'backup security automated AI no human management',
            'endpoint protection automated AI replacing admins blog'
        ],
        'augment': [
            'cybersecurity AI copilots assisting analysts 2024 2025',
            'AI-enhanced threat hunting human oversight blog reddit',
            'machine learning assisted log analysis SOC analysts',
            'AI-powered incident investigation human decision making',
            'cybersecurity AI tools enhancing analyst performance',
            'human-AI collaboration threat detection blog posts',
            'AI-assisted vulnerability assessment security teams',
            'SOC analysts using AI tools better efficiency reddit',
            'AI-enhanced penetration testing human expertise YouTube',
            'machine learning compliance monitoring human review',
            'AI-assisted forensics investigation analyst workflow',
            'threat intelligence AI augmenting human analysis',
            'AI-powered risk assessment human validation blog',
            'cybersecurity AI dashboard enhancing analyst insight',
            'AI-assisted security awareness training programs',
            'machine learning network monitoring human oversight',
            'AI-enhanced security orchestration analyst control',
            'cybersecurity AI recommendations human approval reddit',
            'AI-assisted patch management security teams',
            'human-guided AI security automation best practices'
        ],
        'new_tasks': [
            'AI security engineer jobs cybersecurity 2024 2025',
            'MLSecOps machine learning security operations jobs',
            'prompt injection security specialist new roles',
            'AI governance cybersecurity positions blog reddit',
            'algorithm auditing security jobs emerging',
            'AI red team cybersecurity specialist YouTube',
            'machine learning model security validation jobs',
            'AI bias detection cybersecurity roles blog',
            'adversarial AI testing security positions',
            'AI ethics cybersecurity compliance jobs reddit',
            'prompt engineering cybersecurity applications',
            'AI model monitoring security operations',
            'synthetic data security specialist jobs blog',
            'AI explainability cybersecurity analyst roles',
            'machine learning pipeline security jobs',
            'AI training data security specialist',
            'generative AI security engineer positions',
            'AI incident response specialist new roles reddit',
            'machine learning privacy engineer cybersecurity',
            'AI security architecture specialist jobs YouTube'
        ],
        'human_only': [
            'strategic cybersecurity planning human expertise 2024',
            'crisis communication cybersecurity incidents human judgment',
            'regulatory compliance human decision making blog reddit',
            'stakeholder management cybersecurity leadership roles',
            'ethical cybersecurity decisions human intuition',
            'business strategy cybersecurity alignment human insight',
            'cybersecurity budget planning human expertise',
            'vendor negotiations cybersecurity human skills',
            'team leadership cybersecurity management blog',
            'cybersecurity policy development human judgment reddit',
            'executive briefings cybersecurity human communication',
            'legal cybersecurity decisions human expertise',
            'cybersecurity culture building human leadership',
            'cross-functional collaboration security teams',
            'cybersecurity training design human creativity blog',
            'security architecture vision human insight',
            'cybersecurity mergers acquisitions human expertise',
            'board reporting cybersecurity human communication reddit',
            'cybersecurity innovation human creativity YouTube',
            'complex forensics investigation human intuition blog'
        ]
    }
    
    total_collected = 0
    category_stats = {}
    
    for category, queries in searches.items():
        logger.info(f'🎯 Starting collection for category: {category.upper()}')
        category_count = 0
        category_stats[category] = 0
        
        for i, query in enumerate(queries):
            if category_count >= 20:  # Stop once we have 20 for this category
                break
                
            try:
                logger.info(f'Query {i+1}/{len(queries)} for {category}: {query[:60]}...')
                
                # Collect articles for this query using the correct method
                results = await collector.collect(
                    query=query,
                    max_results=3,  # Get a few per query to ensure variety
                    category=category,
                    timeframe="2024-2025"
                )
                
                # Save results
                for artifact in results:
                    if category_count >= 20:
                        break
                    
                    # Convert artifact to database format
                    artifact_data = {
                        'id': artifact.id,
                        'url': artifact.url,
                        'title': artifact.title,
                        'content': artifact.content,
                        'source_type': f'perplexity_{category}',
                        'collected_at': artifact.collected_at,
                        'metadata': artifact.metadata
                    }
                    
                    # Add category to metadata
                    artifact_data['metadata']['ai_impact_category'] = category
                    
                    # Check if already exists
                    if not db.artifact_exists(artifact.url):
                        artifact_id = db.save_artifact(artifact_data)
                        logger.info(f'✅ Saved: {artifact.title[:50]}...')
                        category_count += 1
                        total_collected += 1
                    else:
                        logger.info(f'⚠️  Duplicate skipped: {artifact.url}')
                
                # Brief pause between queries to avoid rate limits
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f'❌ Error in query {i+1} for {category}: {e}')
                continue
        
        category_stats[category] = category_count
        logger.info(f'✅ Completed {category.upper()}: collected {category_count} articles')
        
        # Pause between categories
        await asyncio.sleep(3)
    
    # Final summary
    logger.info('=' * 60)
    logger.info('🎉 COLLECTION COMPLETE!')
    logger.info('=' * 60)
    for category, count in category_stats.items():
        logger.info(f'{category.upper():>12}: {count:>3} articles')
    logger.info(f'{"TOTAL":>12}: {total_collected:>3} articles')
    logger.info('=' * 60)
    
    return total_collected, category_stats

def main():
    """Main function to run the collection."""
    print("🚀 Starting Comprehensive AI-Horizon Article Collection")
    print("=" * 60)
    print("Target: 20 articles per category (80 total)")
    print("Sources: Blogs, Reddit, YouTube, News, Academic")
    print("Categories: Replace, Augment, New Tasks, Human-Only")
    print("=" * 60)
    
    try:
        result, stats = asyncio.run(collect_comprehensive())
        
        print("\n🎉 Collection Summary:")
        print("-" * 40)
        for category, count in stats.items():
            print(f"{category.capitalize():>12}: {count:>3} articles")
        print(f"{'Total':>12}: {result:>3} articles")
        print("-" * 40)
        print("✅ Collection completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during collection: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 