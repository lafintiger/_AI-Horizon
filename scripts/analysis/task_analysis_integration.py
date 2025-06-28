#!/usr/bin/env python3
"""
Task-Centric Analysis Integration Script

This script integrates the enhanced task extraction functionality into the AI-Horizon pipeline.
It processes existing articles to extract specific DCWF tasks, AI tools, and example prompts,
populating the new task-centric database tables.

Usage:
    python task_analysis_integration.py [--reprocess-all] [--limit N]
"""

import sys
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from aih.utils.database import DatabaseManager
from aih.utils.logging import get_logger
from aih.classify.task_extractor import EnhancedTaskExtractor

logger = get_logger(__name__)

class TaskAnalysisIntegrator:
    """
    Integrates task-centric analysis into the AI-Horizon pipeline.
    
    This class:
    1. Processes existing articles to extract tasks
    2. Populates the new task-centric database tables
    3. Provides methods to reprocess articles when needed
    4. Generates task analysis summaries
    """
    
    def __init__(self, model_name: str = None):
        """Initialize the task analysis integrator."""
        self.db = DatabaseManager()
        self.task_extractor = EnhancedTaskExtractor(model_name)
        logger.info("✅ Task Analysis Integrator initialized")
    
    def process_unanalyzed_articles(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Process articles that haven't been analyzed for task extraction.
        
        Args:
            limit: Maximum number of articles to process (None for all)
            
        Returns:
            Dictionary with processing results
        """
        logger.info("🔍 Finding unanalyzed articles for task extraction...")
        
        try:
            # Get articles that haven't been processed for task extraction
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                query = """
                    SELECT a.id, a.title, a.content, a.url, a.source_type, a.collected_at
                    FROM artifacts a
                    LEFT JOIN article_task_mappings atm ON a.id = atm.artifact_id
                    WHERE atm.artifact_id IS NULL
                    AND LENGTH(a.content) > 500  -- Only process articles with substantial content
                    ORDER BY a.collected_at DESC
                """
                
                if limit:
                    query += f" LIMIT {limit}"
                
                cursor.execute(query)
                unanalyzed_articles = [dict(row) for row in cursor.fetchall()]
            
            logger.info(f"📊 Found {len(unanalyzed_articles)} unanalyzed articles")
            
            if not unanalyzed_articles:
                return {
                    'processed_count': 0,
                    'task_extractions': 0,
                    'ai_tools_found': 0,
                    'errors': []
                }
            
            # Process each article
            results = {
                'processed_count': 0,
                'task_extractions': 0,
                'ai_tools_found': 0,
                'errors': []
            }
            
            for i, article in enumerate(unanalyzed_articles, 1):
                logger.info(f"🔍 Processing article {i}/{len(unanalyzed_articles)}: {article['title'][:50]}...")
                
                try:
                    # Extract tasks from article
                    task_extractions = self.task_extractor.extract_tasks_from_article(article)
                    
                    if task_extractions:
                        # Save task extractions to database
                        success = self.task_extractor.save_task_extractions_to_db(
                            task_extractions, article['id']
                        )
                        
                        if success:
                            results['task_extractions'] += len(task_extractions)
                            logger.info(f"✅ Processed {len(task_extractions)} task extractions")
                        else:
                            results['errors'].append(f"Failed to save extractions for {article['title']}")
                    
                    results['processed_count'] += 1
                    
                    # Add a small delay to avoid rate limiting
                    import time
                    time.sleep(1)
                    
                except Exception as e:
                    error_msg = f"Error processing article {article['title']}: {str(e)}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
                    continue
            
            logger.info(f"✅ Task extraction completed: {results['processed_count']} articles processed, "
                       f"{results['task_extractions']} tasks extracted")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Error in task extraction processing: {e}")
            return {
                'processed_count': 0,
                'task_extractions': 0,
                'ai_tools_found': 0,
                'errors': [str(e)]
            }
    
    def reprocess_all_articles(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Reprocess all articles for task extraction (useful for updates).
        
        Args:
            limit: Maximum number of articles to process (None for all)
            
        Returns:
            Dictionary with processing results
        """
        logger.info("🔄 Reprocessing all articles for task extraction...")
        
        try:
            # Clear existing task mappings (optional - you might want to keep them)
            # This depends on whether you want to completely reprocess or just add new extractions
            
            # Get all articles
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                query = """
                    SELECT id, title, content, url, source_type, collected_at
                    FROM artifacts
                    WHERE LENGTH(content) > 500
                    ORDER BY collected_at DESC
                """
                
                if limit:
                    query += f" LIMIT {limit}"
                
                cursor.execute(query)
                all_articles = [dict(row) for row in cursor.fetchall()]
            
            logger.info(f"📊 Reprocessing {len(all_articles)} articles")
            
            # Process each article (similar to process_unanalyzed_articles)
            results = {
                'processed_count': 0,
                'task_extractions': 0,
                'ai_tools_found': 0,
                'errors': []
            }
            
            for i, article in enumerate(all_articles, 1):
                logger.info(f"🔄 Reprocessing article {i}/{len(all_articles)}: {article['title'][:50]}...")
                
                try:
                    # Extract tasks from article
                    task_extractions = self.task_extractor.extract_tasks_from_article(article)
                    
                    if task_extractions:
                        # Save task extractions to database
                        success = self.task_extractor.save_task_extractions_to_db(
                            task_extractions, article['id']
                        )
                        
                        if success:
                            results['task_extractions'] += len(task_extractions)
                    
                    results['processed_count'] += 1
                    
                    # Add a small delay to avoid rate limiting
                    import time
                    time.sleep(1)
                    
                except Exception as e:
                    error_msg = f"Error reprocessing article {article['title']}: {str(e)}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
                    continue
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Error in reprocessing: {e}")
            return {
                'processed_count': 0,
                'task_extractions': 0,
                'ai_tools_found': 0,
                'errors': [str(e)]
            }
    
    def generate_task_analysis_summaries(self) -> Dict[str, Any]:
        """
        Generate analysis summaries for all tasks in the database.
        
        Returns:
            Dictionary with summary generation results
        """
        logger.info("📊 Generating task analysis summaries...")
        
        try:
            # Get all tasks that need summary updates
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT dt.id, dt.task_name, COUNT(atm.artifact_id) as article_count
                    FROM dcwf_tasks dt
                    LEFT JOIN article_task_mappings atm ON dt.id = atm.task_id
                    GROUP BY dt.id, dt.task_name
                    HAVING article_count > 0
                """)
                
                tasks_to_summarize = [dict(row) for row in cursor.fetchall()]
            
            logger.info(f"📊 Generating summaries for {len(tasks_to_summarize)} tasks")
            
            summaries_generated = 0
            
            for task in tasks_to_summarize:
                try:
                    # Get all article mappings for this task
                    task_mappings = []
                    with self.db.get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("""
                            SELECT ai_impact_mentioned, confidence_level, relevance_score
                            FROM article_task_mappings
                            WHERE task_id = ?
                        """, (task['id'],))
                        task_mappings = [dict(row) for row in cursor.fetchall()]
                    
                    # Calculate confidence scores for each category
                    impact_categories = {
                        'replace': [],
                        'augment': [],
                        'new_tasks': [],
                        'human_only': []
                    }
                    
                    for mapping in task_mappings:
                        category = mapping['ai_impact_mentioned'] or 'human_only'
                        if category in impact_categories:
                            impact_categories[category].append(mapping['confidence_level'] or 0.5)
                    
                    # Calculate average confidence for each category
                    def avg_or_zero(values):
                        return sum(values) / len(values) if values else 0.0
                    
                    replace_confidence = avg_or_zero(impact_categories['replace'])
                    augment_confidence = avg_or_zero(impact_categories['augment'])
                    new_tasks_confidence = avg_or_zero(impact_categories['new_tasks'])
                    human_only_confidence = avg_or_zero(impact_categories['human_only'])
                    
                    # Determine primary AI impact
                    confidence_scores = {
                        'replace': replace_confidence,
                        'augment': augment_confidence,
                        'new_tasks': new_tasks_confidence,
                        'human_only': human_only_confidence
                    }
                    
                    primary_ai_impact = max(confidence_scores, key=confidence_scores.get)
                    
                    # Get recommended tools for this task
                    recommended_tools = []
                    with self.db.get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("""
                            SELECT at.tool_name
                            FROM ai_tools at
                            JOIN task_tool_recommendations ttr ON at.id = ttr.tool_id
                            WHERE ttr.task_id = ?
                            ORDER BY ttr.effectiveness_rating DESC
                            LIMIT 5
                        """, (task['id'],))
                        recommended_tools = [row[0] for row in cursor.fetchall()]
                    
                    # Create summary data
                    analysis_data = {
                        'total_articles_analyzed': task['article_count'],
                        'replace_confidence': replace_confidence,
                        'augment_confidence': augment_confidence,
                        'new_tasks_confidence': new_tasks_confidence,
                        'human_only_confidence': human_only_confidence,
                        'primary_ai_impact': primary_ai_impact,
                        'recommended_tools': recommended_tools,
                        'key_insights': [
                            f"Analyzed in {task['article_count']} articles",
                            f"Primary AI impact: {primary_ai_impact} ({confidence_scores[primary_ai_impact]:.2f} confidence)",
                            f"Tools recommended: {len(recommended_tools)}"
                        ],
                        'example_prompts': []  # Could be enhanced to collect actual prompts
                    }
                    
                    # Save summary to database
                    success = self.db.update_task_analysis_summary(task['id'], analysis_data)
                    if success:
                        summaries_generated += 1
                    
                except Exception as e:
                    logger.error(f"Error generating summary for task {task['task_name']}: {e}")
                    continue
            
            logger.info(f"✅ Generated {summaries_generated} task analysis summaries")
            
            return {
                'summaries_generated': summaries_generated,
                'total_tasks': len(tasks_to_summarize)
            }
            
        except Exception as e:
            logger.error(f"❌ Error generating task analysis summaries: {e}")
            return {
                'summaries_generated': 0,
                'total_tasks': 0,
                'error': str(e)
            }
    
    def get_integration_status(self) -> Dict[str, Any]:
        """Get the current status of task-centric integration."""
        try:
            stats = self.db.get_task_statistics()
            
            # Add some additional status information
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get total articles
                cursor.execute("SELECT COUNT(*) FROM artifacts")
                total_articles = cursor.fetchone()[0]
                
                # Get articles with task mappings
                cursor.execute("SELECT COUNT(DISTINCT artifact_id) FROM article_task_mappings")
                articles_with_tasks = cursor.fetchone()[0]
                
                # Get processing percentage
                processing_percentage = (articles_with_tasks / total_articles * 100) if total_articles > 0 else 0
            
            status = {
                'database_stats': stats,
                'total_articles': total_articles,
                'articles_with_task_extractions': articles_with_tasks,
                'processing_percentage': round(processing_percentage, 2),
                'integration_complete': processing_percentage > 90,
                'generated_at': datetime.now().isoformat()
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting integration status: {e}")
            return {
                'error': str(e),
                'generated_at': datetime.now().isoformat()
            }

def main():
    """Main function to run task analysis integration."""
    parser = argparse.ArgumentParser(description="Task-Centric Analysis Integration")
    parser.add_argument('--reprocess-all', action='store_true', 
                       help='Reprocess all articles (not just unanalyzed ones)')
    parser.add_argument('--limit', type=int, default=None,
                       help='Limit number of articles to process')
    parser.add_argument('--generate-summaries', action='store_true',
                       help='Generate task analysis summaries')
    parser.add_argument('--status', action='store_true',
                       help='Show integration status')
    
    args = parser.parse_args()
    
    integrator = TaskAnalysisIntegrator()
    
    if args.status:
        logger.info("📊 Getting integration status...")
        status = integrator.get_integration_status()
        print("\n=== TASK-CENTRIC INTEGRATION STATUS ===")
        print(f"Total Articles: {status.get('total_articles', 'Unknown')}")
        print(f"Articles with Task Extractions: {status.get('articles_with_task_extractions', 'Unknown')}")
        print(f"Processing Percentage: {status.get('processing_percentage', 'Unknown')}%")
        print(f"Integration Complete: {status.get('integration_complete', False)}")
        print(f"Total Tasks: {status.get('database_stats', {}).get('total_tasks', 'Unknown')}")
        print(f"Total AI Tools: {status.get('database_stats', {}).get('total_tools', 'Unknown')}")
        print(f"Total Recommendations: {status.get('database_stats', {}).get('total_recommendations', 'Unknown')}")
        
    elif args.generate_summaries:
        logger.info("📊 Generating task analysis summaries...")
        results = integrator.generate_task_analysis_summaries()
        print(f"\n✅ Generated {results['summaries_generated']} summaries for {results['total_tasks']} tasks")
        
    elif args.reprocess_all:
        logger.info("🔄 Reprocessing all articles...")
        results = integrator.reprocess_all_articles(limit=args.limit)
        print(f"\n✅ Reprocessed {results['processed_count']} articles")
        print(f"📊 Extracted {results['task_extractions']} tasks")
        if results['errors']:
            print(f"⚠️  Errors: {len(results['errors'])}")
        
    else:
        logger.info("🔍 Processing unanalyzed articles...")
        results = integrator.process_unanalyzed_articles(limit=args.limit)
        print(f"\n✅ Processed {results['processed_count']} articles")
        print(f"📊 Extracted {results['task_extractions']} tasks")
        if results['errors']:
            print(f"⚠️  Errors: {len(results['errors'])}")

if __name__ == "__main__":
    main() 