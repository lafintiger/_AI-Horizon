#!/usr/bin/env python3
"""
AI Skills Collection - Using the PROVEN working collection system
Just different search queries focused on AI skills instead of general cybersecurity
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from aih.utils.database import DatabaseManager
from aih.gather.perplexity import PerplexityConnector
from aih.utils.logging import get_logger

logger = get_logger(__name__)

class AISkillsCollector:
    """
    AI Skills Collector - Uses the EXACT same pattern as the working collection system
    """
    
    def __init__(self, status_tracker=None):
        self.status_tracker = status_tracker
        self.db = DatabaseManager()
        self.collector = PerplexityConnector()
        
    async def collect_ai_skills(self, skills_per_category: int = 10, timeframe: str = "6months") -> Dict[str, Any]:
        """
        Collect AI skills using the EXACT same pattern as the working system.
        Just different search queries focused on AI skills.
        """
        
        # AI Skills search queries - focused on emerging skills
        ai_skills_queries = {
            "new_tasks": [
                f"emerging AI tools cybersecurity professionals 2024 new technologies",
                f"latest AI security tools threat detection {timeframe}",
                f"new artificial intelligence cybersecurity capabilities 2024",
                f"emerging AI-powered security solutions {timeframe}",
                f"cutting-edge AI cybersecurity technologies 2024"
            ],
            "augment": [
                f"AI-assisted cybersecurity human analyst tools {timeframe}",
                f"AI augmented threat hunting security operations 2024",
                f"machine learning enhanced cybersecurity workflows",
                f"AI-powered security analyst productivity tools {timeframe}",
                f"human-AI collaboration cybersecurity defense 2024"
            ],
            "human_only": [
                f"cybersecurity skills that require human expertise 2024",
                f"AI-resistant cybersecurity capabilities human judgment",
                f"cybersecurity roles requiring human creativity ethics {timeframe}",
                f"human-only cybersecurity leadership communication skills",
                f"cybersecurity expertise that AI cannot replace 2024"
            ]
        }
        
        total_collected = 0
        total_target = len(ai_skills_queries) * skills_per_category
        category_stats = {}
        
        self.add_log("INFO", f"Starting AI Skills Collection - Target: {total_target} skills", "COLLECTION")
        
        for category, queries in ai_skills_queries.items():
            category_count = 0
            self.add_log("INFO", f"Collecting {category} AI skills...", "COLLECTION")
            
            for i, query in enumerate(queries):
                if category_count >= skills_per_category:
                    break
                    
                try:
                    self.update_progress(
                        total_collected, total_target,
                        f"Searching {category} skills - Query {i+1}/{len(queries)}"
                    )
                    
                    # Use the EXACT same collector as the working system
                    artifacts = await self.collector.collect(
                        query=query,
                        max_results=3,  # Smaller batches
                        category=category,
                        timeframe=timeframe
                    )
                    
                    # Save using the EXACT same pattern as the working system
                    for artifact in artifacts:
                        if category_count >= skills_per_category:
                            break
                        
                        # Convert artifact to database format - EXACT same structure
                        artifact_data = {
                            'id': artifact.id,
                            'url': artifact.url,
                            'title': artifact.title,
                            'content': artifact.content,
                            'source_type': f'ai_skills_{category}',
                            'collected_at': artifact.collected_at,
                            'metadata': artifact.metadata
                        }
                        
                        # Add AI skills category to metadata - SAME as working system
                        artifact_data['metadata']['ai_impact_category'] = category
                        artifact_data['metadata']['collection_method'] = 'ai_skills_focused'
                        artifact_data['metadata']['skill_search_query'] = query
                        
                        # Check if already exists - SAME as working system
                        if not self.db.artifact_exists(artifact.url):
                            artifact_id = self.db.save_artifact(artifact_data)
                            logger.info(f'✅ Saved AI skill: {artifact.title[:50]}...')
                            self.add_log("INFO", f"Saved AI skill: {artifact.title[:50]}...", "COLLECTION")
                            category_count += 1
                            total_collected += 1
                            
                            # Update progress
                            self.update_progress(
                                total_collected, total_target,
                                f"Collected {total_collected}/{total_target} AI skills"
                            )
                        else:
                            logger.info(f'⚠️  Duplicate skipped: {artifact.url}')
                            self.add_log("WARN", f"Duplicate skipped: {artifact.url[:50]}...", "COLLECTION")
                    
                    # Brief pause between queries
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    logger.error(f'❌ Error in AI skills query {i+1} for {category}: {e}')
                    self.add_log("ERROR", f"AI skills query failed: {str(e)[:100]}...", "COLLECTION")
                    continue
            
            category_stats[category] = category_count
            logger.info(f'✅ {category.upper()} AI skills: {category_count} collected')
            self.add_log("INFO", f"{category.upper()} AI skills complete: {category_count} collected", "COLLECTION")
            
            # Pause between categories
            await asyncio.sleep(3)
        
        # Complete collection
        self.add_log("INFO", f"AI Skills Collection Complete! Total: {total_collected} skills", "COLLECTION")
        
        return {
            'success': True,
            'total_collected': total_collected,
            'category_stats': category_stats,
            'collection_method': 'proven_system_pattern',
            'timestamp': datetime.now().isoformat()
        }
    
    def add_log(self, level: str, message: str, category: str = "SYSTEM"):
        """Add log message - same pattern as working system"""
        if self.status_tracker:
            self.status_tracker.add_log(level, message, category)
        logger.info(f"{level}: {message}")
    
    def update_progress(self, current: int, total: int, status: str = ""):
        """Update progress - same pattern as working system"""
        if self.status_tracker:
            self.status_tracker.update_progress(current, total, status)

async def main():
    """Test the AI skills collection"""
    collector = AISkillsCollector()
    
    print("🔍 Starting AI Skills Collection using proven system pattern...")
    results = await collector.collect_ai_skills(skills_per_category=5, timeframe="6months")
    
    print(f"\n✅ Collection Results:")
    print(f"Total AI skills collected: {results['total_collected']}")
    print(f"Category breakdown: {results['category_stats']}")
    print(f"Collection method: {results['collection_method']}")
    
    return results

if __name__ == "__main__":
    asyncio.run(main()) 