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

def add_log(level: str, message: str, category: str = "COLLECTION"):
    """Add log entry to status tracker if available."""
    if status_tracker:
        status_tracker.add_log(level, message, category)

async def collect_comprehensive():
    """Run comprehensive collection across all categories."""
    logger = get_logger('comprehensive_collection')
    collector = PerplexityConnector()
    db = DatabaseManager()
    
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
            'strategic planning requires human creativity AI cannot replace',
            'crisis management human judgment leadership skills essential',
            'stakeholder relationship building human trust empathy required',
            'complex negotiations human intuition emotional intelligence',
            'ethical decision making human values moral reasoning',
            'creative problem solving human innovation breakthrough thinking',
            'team leadership human motivation inspiration management',
            'customer relationship building human connection trust',
            'complex communication human empathy understanding context',
            'strategic vision human insight long-term planning',
            'crisis communication human judgment sensitive messaging',
            'organizational culture building human leadership values',
            'complex conflict resolution human mediation skills',
            'innovative thinking human creativity breakthrough solutions',
            'relationship management human trust building networks',
            'executive decision making human judgment risk assessment',
            'team building human psychology motivation dynamics',
            'strategic partnerships human relationship trust building',
            'crisis leadership human judgment under pressure',
            'organizational change management human psychology adaptation'
        ]
    }
    
    # Calculate total queries for progress tracking
    total_queries = sum(len(queries) for queries in searches.values())
    current_query = 0
    
    total_collected = 0
    category_stats = {}
    
    add_log("INFO", f"Starting comprehensive collection: {total_queries} total queries", "COLLECTION")
    update_progress(0, 80, "Initializing collection across all categories...")
    
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
            
            if category_count >= 20:  # Stop once we have 20 for this category
                break
                
            try:
                status_msg = f"Category: {category.upper()} | Query {i+1}/{len(queries)}: {query[:40]}..."
                update_progress(total_collected, 80, status_msg)
                
                logger.info(f'Query {i+1}/{len(queries)} for {category}: {query[:60]}...')
                add_log("INFO", f"Executing query {i+1}/{len(queries)} for {category}: {query[:50]}...", "COLLECTION")
                
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
                        add_log("INFO", f"Saved article: {artifact.title[:50]}...", "COLLECTION")
                        category_count += 1
                        total_collected += 1
                        
                        # Update progress
                        update_progress(total_collected, 80, f"Collected {total_collected}/80 articles")
                        
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
    
    update_progress(total_collected, 80, f"Collection completed: {total_collected} articles")
    
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