#!/usr/bin/env python3
"""
Targeted High-Value Source Collection

Focuses on specific high-value sources and industry leaders to find
inference-based content about AI's impact on work and jobs.
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from aih.gather.perplexity import PerplexityConnector
from aih.utils.database import DatabaseManager
from aih.utils.logging import get_logger

# Global status tracker for web integration
status_tracker = None

def set_status_tracker(tracker):
    """Set the status tracker for web dashboard integration."""
    global status_tracker
    status_tracker = tracker

def update_progress(current: int, total: int, status: str = ""):
    """Update progress in status tracker if available."""
    if status_tracker:
        status_tracker.update_progress(current, total, status)

def add_log(level: str, message: str, category: str = "TARGETED_COLLECTION"):
    """Add log entry to status tracker if available."""
    if status_tracker:
        status_tracker.add_log(level, message, category)

async def collect_targeted_sources():
    """Run targeted collection from high-value sources."""
    logger = get_logger('targeted_collection')
    collector = PerplexityConnector()
    db = DatabaseManager()
    
    # HIGH-VALUE SOURCE-TARGETED SEARCHES
    # Focus on independent journalism, industry leaders, and unsponsored content
    
    searches = {
        'replace': [
            # CEO/Executive mandates and company policies
            'site:stratechery.com OR site:ben-evans.com OR site:platformer.news AI adoption mandate CEO employee performance 2024 2025',
            'site:axios.com OR site:theinformation.com AI transformation company productivity requirements',
            'site:substack.com "CEO memo" OR "company announcement" AI tools mandatory employee',
            'reddit.com r/programming OR r/cscareerquestions AI replacing developers jobs 2024 2025',
            'site:news.ycombinator.com "AI adoption" company policy employee productivity',
            
            # Earnings calls and business transformation
            '"earnings call" OR "quarterly results" AI automation reducing headcount 2024',
            'site:protocol.com OR site:casey.news enterprise AI implementation workforce reduction',
            'site:linkedin.com "CEO post" OR "executive update" AI productivity employee expectations',
            'youtube.com "all-in podcast" OR "lex fridman" AI job displacement automation',
            'site:techcrunch.com NOT sponsored AI startup automation replacing jobs',
            
            # Industry transformation stories
            'site:semianalysis.com OR site:deepdive.substack.com AI enterprise adoption workforce',
            '"company blog" CTO OR CEO AI automation efficiency workforce optimization',
            'site:hbr.org OR site:mit.edu AI transformation business process automation',
            'reddit.com r/MachineLearning AI replacing traditional jobs roles',
            'site:mattwillard.substack.com OR independent tech journalist AI job impact',
            
            # Specific industry transformations
            'legal industry AI automation replacing paralegals lawyers 2024 independent analysis',
            'accounting AI software replacing bookkeepers tax preparers 2024 unbiased',
            'customer service AI chatbots replacing human agents enterprise',
            'medical coding AI automation replacing medical coders 2024',
            'content creation AI tools replacing writers copywriters 2024 independent'
        ],
        
        'augment': [
            # Developer productivity and AI assistance
            'site:stackoverflow.blog OR site:github.blog developer productivity AI copilot github',
            'reddit.com r/programming AI copilot productivity developer experience 2024',
            'site:cassidoo.co OR site:swyx.io developer AI tools workflow enhancement',
            'youtube.com "developer conference" AI pair programming productivity',
            'site:increment.com OR site:a16z.com developer tools AI enhancement not replacement',
            
            # Enterprise AI assistance tools
            'site:firstround.com OR site:blog.samaltman.com enterprise AI tools employee productivity',
            'site:platformer.news OR site:stratechery.com AI assistant enterprise workflow',
            'linkedin.com CTO OR VP Engineering AI tools team productivity 2024',
            'site:stripe.com/blog OR site:shopify.engineering AI tools developer productivity',
            'site:netflix.techblog.com OR site:eng.uber.com AI enhanced workflows engineering',
            
            # Sales and marketing AI enhancement
            'site:hubspot.com/blog OR independent sales blog AI sales tools productivity',
            'reddit.com r/sales AI tools CRM enhancement productivity 2024',
            'site:gong.io/blog OR site:outreach.io/blog AI sales enhancement human oversight',
            'youtube.com sales conference AI tools enhancement not replacement',
            'site:klenty.com/blog OR sales expert substack AI sales productivity',
            
            # Creative industry AI assistance
            'site:adobe.com/blog OR independent designer blog AI creative tools enhancement',
            'reddit.com r/graphic_design AI tools creative workflow productivity',
            'youtube.com "design conference" AI creative tools human creativity',
            'site:figma.com/blog OR design leader substack AI design productivity',
            'site:behance.net OR independent artist blog AI creative assistance'
        ],
        
        'new_tasks': [
            # AI governance and ethics roles
            'site:anthropic.com/blog OR site:openai.com/blog AI safety specialist jobs',
            'reddit.com r/MachineLearning AI ethics coordinator jobs emerging 2024',
            'site:partnership.ai OR AI governance expert substack new job roles',
            'linkedin.com "AI governance" OR "AI ethics" job postings 2024',
            'youtube.com AI conference ethics governance new careers',
            
            # Prompt engineering and AI training
            'site:scale.ai/blog OR site:humanloop.com prompt engineering specialist jobs',
            'reddit.com r/ChatGPT OR r/OpenAI prompt engineering career opportunities',
            'site:promptengineering.org OR independent AI expert blog new roles',
            'linkedin.com "prompt engineer" OR "AI trainer" job market 2024',
            'youtube.com "prompt engineering" career opportunities',
            
            # MLOps and AI infrastructure
            'site:weights-biases.com/blog OR site:neptune.ai/blog MLOps engineer roles',
            'reddit.com r/MachineLearning MLOps career opportunities 2024',
            'site:mlops.community OR MLOps expert substack new job categories',
            'linkedin.com "MLOps engineer" OR "AI infrastructure" jobs 2024',
            'youtube.com MLOps conference career opportunities',
            
            # AI audit and compliance
            'site:nist.gov OR independent AI policy expert AI audit specialist roles',
            'reddit.com r/cybersecurity AI security specialist new jobs',
            'site:brookings.edu OR AI policy expert substack compliance jobs',
            'linkedin.com "AI audit" OR "AI compliance" emerging roles',
            'youtube.com AI regulation conference new job categories'
        ],
        
        'human_only': [
            # Strategic and creative leadership
            'site:stratechery.com OR site:ben-evans.com strategic planning human creativity AI limits',
            'site:hbr.org OR independent business expert strategic leadership human judgment',
            'reddit.com r/consulting OR r/strategy human expertise AI cannot replace',
            'youtube.com "business strategy" human creativity AI limitations',
            'site:mckinsey.com OR independent consultant blog strategic planning human insight',
            
            # Crisis management and leadership
            'site:axios.com OR site:politico.com crisis communication human judgment leadership',
            'reddit.com r/PublicRelations OR r/leadership crisis management human skills',
            'site:edelman.com/blog OR PR expert substack crisis communication human empathy',
            'youtube.com crisis leadership human judgment decision making',
            'linkedin.com CEO OR executive crisis management human leadership',
            
            # Relationship building and negotiation
            'site:firstround.com OR startup CEO blog relationship building human trust',
            'reddit.com r/sales OR r/negotiation human relationship building AI limits',
            'site:harvard.edu negotiation OR independent negotiation expert human skills',
            'youtube.com "negotiation masterclass" human psychology emotional intelligence',
            'linkedin.com sales leader OR executive relationship building human connection',
            
            # Innovation and breakthrough thinking
            'site:y-combinator.com OR startup founder blog innovation human creativity',
            'reddit.com r/entrepreneur OR r/startups human innovation AI limitations',
            'site:a16z.com OR VC partner blog creative problem solving human insight',
            'youtube.com innovation conference human creativity breakthrough thinking',
            'site:mit.edu OR independent researcher blog human innovation AI cannot replicate'
        ]
    }
    
    total_queries = sum(len(queries) for queries in searches.values())
    total_collected = 0
    category_stats = {}
    
    add_log("INFO", f"Starting targeted source collection: {total_queries} high-value queries", "TARGETED")
    update_progress(0, 80, "Targeting independent sources and industry leaders...")
    
    for category, queries in searches.items():
        logger.info(f'🎯 Starting targeted collection for: {category.upper()}')
        add_log("INFO", f"Targeting {category.upper()} from high-value independent sources", "TARGETED")
        
        category_count = 0
        category_stats[category] = 0
        
        for i, query in enumerate(queries):
            # Update persistent progress tracking
            if status_tracker:
                status_tracker.update_collection_progress(category, i+1, len(queries), category_count)
            
            if category_count >= 20:  # Stop once we have 20 for this category
                break
                
            try:
                status_msg = f"Targeting {category.upper()} | Source query {i+1}/{len(queries)}"
                update_progress(total_collected, 80, status_msg)
                
                logger.info(f'Source query {i+1}/{len(queries)} for {category}: {query[:80]}...')
                add_log("INFO", f"Executing targeted query {i+1}/{len(queries)}: {query[:60]}...", "TARGETED")
                
                # Use targeted search approach
                results = await collector.collect(
                    query=query,
                    max_results=5,  # More results per query since they're more targeted
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
                        'source_type': f'targeted_{category}',
                        'collected_at': artifact.collected_at,
                        'metadata': artifact.metadata
                    }
                    
                    # Add category and source targeting info
                    artifact_data['metadata']['ai_impact_category'] = category
                    artifact_data['metadata']['collection_method'] = 'targeted_sources'
                    
                    # Check if already exists
                    if not db.artifact_exists(artifact.url):
                        artifact_id = db.save_artifact(artifact_data)
                        logger.info(f'✅ Saved from targeted source: {artifact.title[:50]}...')
                        add_log("INFO", f"Saved targeted article: {artifact.title[:50]}...", "TARGETED")
                        category_count += 1
                        total_collected += 1
                        
                        # Update progress
                        update_progress(total_collected, 80, f"Collected {total_collected}/80 targeted articles")
                        
                        # Update persistent progress
                        if status_tracker:
                            status_tracker.update_collection_progress(category, i+1, len(queries), category_count)
                    else:
                        logger.info(f'⚠️  Duplicate skipped: {artifact.url}')
                        add_log("WARN", f"Duplicate skipped: {artifact.url[:50]}...", "TARGETED")
                
                # Brief pause between queries
                await asyncio.sleep(3)
                
            except Exception as e:
                logger.error(f'❌ Error in targeted query {i+1} for {category}: {e}')
                add_log("ERROR", f"Targeted query failed: {str(e)[:100]}...", "TARGETED")
                continue
        
        category_stats[category] = category_count
        logger.info(f'✅ Completed targeted {category.upper()}: {category_count} articles')
        add_log("INFO", f"Completed targeted {category.upper()}: {category_count} articles", "TARGETED")
        
        # Final category progress update
        if status_tracker:
            status_tracker.update_collection_progress(category, len(queries), len(queries), category_count)
        
        # Pause between categories
        await asyncio.sleep(5)
    
    # Final summary
    logger.info('=' * 60)
    logger.info('🎉 TARGETED COLLECTION COMPLETE!')
    logger.info('=' * 60)
    for category, count in category_stats.items():
        logger.info(f'{category.upper():>12}: {count:>3} articles')
        add_log("INFO", f"TARGETED {category.upper()}: {count} articles", "SUMMARY")
    logger.info(f'{"TOTAL":>12}: {total_collected:>3} articles')
    add_log("INFO", f"TARGETED COLLECTION COMPLETE: {total_collected} articles", "SUMMARY")
    logger.info('=' * 60)
    
    update_progress(total_collected, 80, f"Targeted collection completed: {total_collected} articles")
    
    return total_collected, category_stats

def main():
    """Main function to run targeted collection."""
    print("🎯 Starting Targeted High-Value Source Collection")
    print("=" * 60)
    print("Target: 20 articles per category from independent sources")
    print("Focus: CEO memos, independent journalism, unsponsored content")
    print("Sources: Stratechery, Reddit, Substack, company blogs, conferences")
    print("=" * 60)
    
    try:
        result, stats = asyncio.run(collect_targeted_sources())
        
        print("\n🎉 Targeted Collection Summary:")
        print("-" * 40)
        for category, count in stats.items():
            print(f"{category.capitalize():>12}: {count:>3} articles")
        print(f"{'Total':>12}: {result:>3} articles")
        print("-" * 40)
        print("✅ Targeted collection completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during targeted collection: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 