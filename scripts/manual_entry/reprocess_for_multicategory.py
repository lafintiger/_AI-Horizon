#!/usr/bin/env python3
"""
Reprocess existing entries for multi-category analysis

This script takes existing single-category entries and reprocesses them
with the new multi-category analysis system to demonstrate the enhanced
visual indicators in the browse interface.
"""

import sys
import json
import asyncio
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from aih.utils.database import DatabaseManager
from aih.utils.logging import get_logger
from scripts.manual_entry.manual_entry_processor import ManualEntryProcessor

logger = get_logger(__name__)

async def reprocess_sample_entries(limit=5):
    """Reprocess a sample of existing entries with multi-category analysis."""
    
    db = DatabaseManager()
    processor = ManualEntryProcessor()
    
    # Get some processed entries to reprocess
    artifacts = db.get_artifacts()
    processed_entries = []
    
    for artifact in artifacts:
        metadata = json.loads(artifact['raw_metadata']) if artifact['raw_metadata'] else {}
        if metadata.get('ai_impact_category') and not metadata.get('ai_impact_categories'):
            processed_entries.append(artifact)
            if len(processed_entries) >= limit:
                break
    
    logger.info(f"Found {len(processed_entries)} entries to reprocess for multi-category analysis")
    
    results = []
    for i, entry in enumerate(processed_entries):
        try:
            logger.info(f"Reprocessing entry {i+1}/{len(processed_entries)}: {entry['title'][:50]}...")
            
            # Get current metadata
            metadata = json.loads(entry['raw_metadata']) if entry['raw_metadata'] else {}
            
            # Perform multi-category analysis
            categories, confidence, analysis_details = await processor.ai_categorize_content(
                entry['title'], 
                entry['content'][:3000]  # Limit content length
            )
            
            # Update metadata with multi-category data
            metadata['ai_impact_categories'] = categories
            metadata['multi_category_confidence'] = confidence
            metadata['multi_category_analysis'] = analysis_details
            metadata['reprocessed_at'] = str(asyncio.get_event_loop().time())
            
            # Update in database
            db.update_artifact_metadata(entry['id'], metadata)
            
            logger.info(f"✅ Reprocessed: {len(categories)} categories found")
            results.append({
                'id': entry['id'],
                'title': entry['title'][:50],
                'categories': list(categories.keys()),
                'confidence': confidence
            })
            
        except Exception as e:
            logger.error(f"Failed to reprocess entry {entry['id']}: {e}")
            results.append({
                'id': entry['id'],
                'title': entry['title'][:50],
                'error': str(e)
            })
    
    return results

async def main():
    """Main execution function."""
    logger.info("🔄 Starting multi-category reprocessing...")
    
    try:
        results = await reprocess_sample_entries(limit=10)
        
        logger.info("📊 Reprocessing Results:")
        for result in results:
            if 'error' in result:
                logger.error(f"❌ {result['title']}: {result['error']}")
            else:
                logger.info(f"✅ {result['title']}: {result['categories']} (confidence: {result['confidence']:.2f})")
        
        successful = len([r for r in results if 'error' not in r])
        logger.info(f"🎉 Successfully reprocessed {successful}/{len(results)} entries")
        
    except Exception as e:
        logger.error(f"Reprocessing failed: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 