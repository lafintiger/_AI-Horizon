#!/usr/bin/env python3
"""
Comprehensive Article Collection Script

Collects 20 articles for each AI impact category (replace, augment, new_tasks, human_only)
using diverse search queries targeting blogs, Reddit, YouTube, and other sources.
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

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

def add_log(level: str, message: str, category: str = "COLLECTION"):
    """Add log entry to status tracker if available."""
    if status_tracker:
        status_tracker.add_log(level, message, category)

async def collect_comprehensive(articles_per_category=20, custom_prompts=None, timeframe_config=None):
    """Run comprehensive collection across all categories."""
    logger = get_logger('comprehensive_collection')
    collector = PerplexityConnector()
    db = DatabaseManager()
    
    # Calculate total articles
    total_target = articles_per_category * 4
    
    # Process timeframe configuration
    timeframe_filter = None
    if timeframe_config:
        timeframe_type = timeframe_config.get('type', 'all_time')
        
        if timeframe_type == 'since_last':
            # Get the last collection date from database
            try:
                query = """
                SELECT MAX(collected_at) as last_collection_date
                FROM artifacts 
                WHERE source_type LIKE 'perplexity%'
                """
                result = db.execute_query(query)
                if result and result[0]['last_collection_date']:
                    from datetime import datetime
                    last_date = datetime.fromisoformat(result[0]['last_collection_date'].replace('Z', '+00:00'))
                    timeframe_filter = f"after:{last_date.strftime('%Y-%m-%d')}"
                    add_log("INFO", f"Using timeframe filter: articles since {last_date.strftime('%Y-%m-%d')}", "COLLECTION")
                else:
                    add_log("INFO", "No previous collections found, searching all available articles", "COLLECTION")
            except Exception as e:
                add_log("WARN", f"Could not determine last collection date: {str(e)}", "COLLECTION")
                
        elif timeframe_type == 'custom_range':
            start_date = timeframe_config.get('start_date')
            end_date = timeframe_config.get('end_date')
            if start_date and end_date:
                timeframe_filter = f"after:{start_date} before:{end_date}"
                add_log("INFO", f"Using custom date range: {start_date} to {end_date}", "COLLECTION")
                
        elif timeframe_type in ['last_7_days', 'last_30_days', 'last_3_months', 'last_6_months', 'last_year']:
            from datetime import datetime, timedelta
            days_map = {
                'last_7_days': 7,
                'last_30_days': 30,
                'last_3_months': 90,
                'last_6_months': 180,
                'last_year': 365
            }
            days_back = days_map.get(timeframe_type, 30)
            cutoff_date = datetime.now() - timedelta(days=days_back)
            timeframe_filter = f"after:{cutoff_date.strftime('%Y-%m-%d')}"
            add_log("INFO", f"Using timeframe filter: {timeframe_type} (since {cutoff_date.strftime('%Y-%m-%d')})", "COLLECTION")
            
        elif timeframe_type == 'all_time':
            add_log("INFO", "Using all-time search (no date restrictions)", "COLLECTION")
    
    # Use custom prompts if provided, otherwise use defaults
    if custom_prompts:
        searches = {}
        for category, prompts in custom_prompts.items():
            searches[category] = prompts
        add_log("INFO", f"Using custom prompts: {sum(len(p) for p in searches.values())} total queries", "COLLECTION")
    else:
        # REVISED: More inference-based search queries that capture broader AI impact patterns
        searches = {
            'replace': [
                'CEO mandates AI adoption all employees required to use AI tools 2024 2025',
                'company AI-first policy employee performance reviews AI usage',
                'AI deployment reducing headcount layoffs automation 2024',
                'enterprise AI implementation workflow automation efficiency gains',
                'AI tools mandatory employee training performance expectations',
                'company memo AI adoption requirements staff productivity',
                'automated systems replacing manual processes enterprise 2024',
                'AI transformation reducing operational staff requirements',
                'business process automation AI implementation cost savings',
                'enterprise AI mandate employee adaptation or replacement',
                'AI-driven efficiency initiatives workforce optimization 2024',
                'company-wide AI adoption traditional roles becoming obsolete',
                'AI productivity tools replacing routine tasks enterprise',
                'organizational AI transformation eliminating manual work',
                'enterprise AI strategy reducing human intervention',
                'AI automation initiatives streamlining operations 2024',
                'company AI mandate performance metrics tied to AI usage',
                'AI implementation replacing repetitive tasks workflows',
                'enterprise AI adoption reducing administrative overhead',
                'AI-first company culture traditional job functions obsolete'
            ],
            'augment': [
                'employee AI copilot tools enhancing productivity performance 2024',
                'AI assistants helping workers improve efficiency enterprise',
                'company provides AI tools to augment employee capabilities',
                'AI-enhanced workflows human oversight decision making 2024',
                'enterprise AI tools supporting employee performance goals',
                'AI collaboration platforms improving team productivity',
                'employee training AI tools to enhance job performance',
                'AI-assisted decision making human validation enterprise',
                'company AI strategy enhancing human capabilities not replacing',
                'AI tools improving employee output quality efficiency',
                'enterprise AI implementation supporting existing workforce',
                'AI-powered analytics helping employees make better decisions',
                'company AI adoption improving employee effectiveness 2024',
                'AI enhancement tools boosting individual performance metrics',
                'enterprise AI strategy augmenting human expertise',
                'AI assistants improving employee workflow efficiency',
                'company AI tools helping workers achieve higher productivity',
                'AI-enhanced capabilities improving job performance outcomes',
                'enterprise AI adoption supporting employee development',
                'AI collaboration improving team performance enterprise 2024'
            ],
            'new_tasks': [
                'AI governance officer new job roles enterprise 2024 2025',
                'prompt engineering specialist hiring demand enterprise',
                'AI ethics coordinator new positions company compliance',
                'machine learning operations engineer MLOps jobs 2024',
                'AI trainer specialist new roles enterprise hiring',
                'AI security specialist emerging jobs cybersecurity 2024',
                'AI audit specialist new compliance roles enterprise',
                'AI integration specialist emerging job market 2024',
                'prompt optimization specialist new career opportunities',
                'AI workflow designer new job categories enterprise',
                'AI performance analyst emerging roles productivity 2024',
                'AI compliance manager new positions enterprise governance',
                'AI training specialist emerging job opportunities 2024',
                'AI quality assurance specialist new roles enterprise',
                'AI transformation coordinator new job market 2024',
                'AI adoption specialist emerging career paths enterprise',
                'AI monitoring specialist new compliance roles 2024',
                'AI safety coordinator emerging job opportunities',
                'AI integration manager new enterprise positions 2024',
                'AI optimization specialist emerging job market trends'
            ],
            'human_only': [
                'cybersecurity incident command human decision making crisis leadership DCWF',
                'security architecture creative threat modeling human insight design thinking',
                'stakeholder communication CISO board reporting human trust building',
                'cybersecurity policy development ethical judgment human values compliance',
                'vulnerability assessment human pattern recognition intuitive analysis',
                'incident response coordination human judgment under pressure crisis management',
                'security awareness training human psychology behavioral change',
                'vendor security assessment human relationship management negotiation',
                'regulatory compliance interpretation human legal judgment ethics',
                'penetration testing creative attack simulation human intuition',
                'security risk communication executive briefing human storytelling',
                'crisis communication public relations human empathy messaging',
                'security team leadership human motivation conflict resolution',
                'business continuity planning human strategic thinking scenarios',
                'security culture development human psychology organizational change',
                'forensic investigation human analytical reasoning evidence interpretation',
                'security program strategy human vision long-term planning',
                'third-party risk assessment human judgment relationship evaluation',
                'security awareness campaign design human creativity behavioral psychology',
                'cybersecurity ethics artificial intelligence human moral reasoning'
            ]
        }
    
    # Calculate total queries for progress tracking
    total_queries = sum(len(queries) for queries in searches.values())
    current_query = 0
    
    total_collected = 0
    category_stats = {}
    
    add_log("INFO", f"Starting comprehensive collection: {total_queries} total queries, target {total_target} articles", "COLLECTION")
    update_progress(0, total_target, "Initializing collection across all categories...")
    
    for category, queries in searches.items():
        logger.info(f'🎯 Starting collection for category: {category.upper()}')
        add_log("INFO", f"Starting collection for category: {category.upper()}", "COLLECTION")
        
        category_count = 0
        category_stats[category] = 0
        
        for i, query in enumerate(queries):
            current_query += 1
            
            # Update persistent progress tracking
            if status_tracker:
                status_tracker.update_collection_progress(category, i+1, len(queries), category_count)
            
            if category_count >= articles_per_category:  # Stop once we have target for this category
                break
                
            try:
                status_msg = f"Category: {category.upper()} | Query {i+1}/{len(queries)}: {query[:40]}..."
                update_progress(total_collected, total_target, status_msg)
                
                logger.info(f'Query {i+1}/{len(queries)} for {category}: {query[:60]}...')
                add_log("INFO", f"Executing query {i+1}/{len(queries)} for {category}: {query[:50]}...", "COLLECTION")
                
                # Collect articles for this query using the correct method
                results = await collector.collect(
                    query=query,
                    max_results=3,  # Get a few per query to ensure variety
                    category=category,
                    timeframe=timeframe_filter
                )
                
                # Save results
                for artifact in results:
                    if category_count >= articles_per_category:
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
                        add_log("INFO", f"Saved article: {artifact.title[:50]}...", "COLLECTION")
                        category_count += 1
                        total_collected += 1
                        
                        # Update progress
                        update_progress(total_collected, total_target, f"Collected {total_collected}/{total_target} articles")
                        
                        # Update persistent progress
                        if status_tracker:
                            status_tracker.update_collection_progress(category, i+1, len(queries), category_count)
                    else:
                        logger.info(f'⚠️  Duplicate skipped: {artifact.url}')
                        add_log("WARN", f"Duplicate skipped: {artifact.url[:50]}...", "COLLECTION")
                
                # Brief pause between queries to avoid rate limits
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f'❌ Error in query {i+1} for {category}: {e}')
                add_log("ERROR", f"Query failed for {category}: {str(e)[:100]}...", "COLLECTION")
                continue
        
        category_stats[category] = category_count
        logger.info(f'✅ Completed {category.upper()}: collected {category_count} articles')
        add_log("INFO", f"Completed {category.upper()}: {category_count} articles collected", "COLLECTION")
        
        # Final category progress update
        if status_tracker:
            status_tracker.update_collection_progress(category, len(queries), len(queries), category_count)
        
        # Pause between categories
        await asyncio.sleep(3)
    
    # Final summary
    logger.info('=' * 60)
    logger.info('🎉 COLLECTION COMPLETE!')
    logger.info('=' * 60)
    for category, count in category_stats.items():
        logger.info(f'{category.upper():>12}: {count:>3} articles')
        add_log("INFO", f"{category.upper()}: {count} articles", "SUMMARY")
    logger.info(f'{"TOTAL":>12}: {total_collected:>3} articles')
    add_log("INFO", f"TOTAL COLLECTION COMPLETE: {total_collected} articles", "SUMMARY")
    logger.info('=' * 60)
    
    update_progress(total_collected, total_target, f"Collection completed: {total_collected} articles")
    
    return total_collected, category_stats

def main():
    """Main function to run the collection."""
    import sys
    
    # Check for command line arguments for custom article count
    articles_per_category = 20  # default
    if len(sys.argv) > 1:
        try:
            articles_per_category = int(sys.argv[1])
        except ValueError:
            print("Invalid article count argument. Using default of 20 per category.")
    
    total_target = articles_per_category * 4
    
    print("🚀 Starting Comprehensive AI-Horizon Article Collection")
    print("=" * 60)
    print(f"Target: {articles_per_category} articles per category ({total_target} total)")
    print("Sources: Blogs, Reddit, YouTube, News, Academic")
    print("Categories: Replace, Augment, New Tasks, Human-Only")
    print("=" * 60)
    
    try:
        result, stats = asyncio.run(collect_comprehensive(articles_per_category))
        
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