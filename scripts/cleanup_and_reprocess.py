#!/usr/bin/env python3
"""
Cleanup and Reprocess All Entries

This script:
1. Removes demo entries (source_type = 'demo')
2. Reprocesses all remaining entries to ensure they have proper multi-category data
3. Updates the database with enhanced categorization
"""

import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from aih.utils.database import DatabaseManager
from aih.utils.logging import get_logger
from aih.classify.classifier import ArtifactClassifier

logger = get_logger(__name__)

def remove_demo_entries():
    """Remove all demo entries from the database."""
    db = DatabaseManager()
    
    logger.info("🧹 Removing demo entries...")
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        # First, count demo entries
        cursor.execute("SELECT COUNT(*) FROM artifacts WHERE source_type = 'demo'")
        demo_count = cursor.fetchone()[0]
        
        if demo_count == 0:
            logger.info("✅ No demo entries found to remove")
            return
        
        logger.info(f"Found {demo_count} demo entries to remove")
        
        # Get demo entry IDs for logging
        cursor.execute("SELECT id, title FROM artifacts WHERE source_type = 'demo'")
        demo_entries = cursor.fetchall()
        
        for entry_id, title in demo_entries:
            logger.info(f"🗑️  Removing: {title[:50]}... (ID: {entry_id})")
        
        # Remove demo entries
        cursor.execute("DELETE FROM artifacts WHERE source_type = 'demo'")
        conn.commit()
        
        logger.info(f"✅ Successfully removed {demo_count} demo entries")

async def reprocess_all_entries():
    """Reprocess all entries to ensure proper multi-category data."""
    db = DatabaseManager()
    classifier = ArtifactClassifier()
    
    logger.info("🔄 Starting reprocessing of all entries...")
    
    # Get all artifacts
    all_artifacts = db.get_artifacts()
    logger.info(f"Found {len(all_artifacts)} entries to process")
    
    processed_count = 0
    updated_count = 0
    error_count = 0
    
    for artifact in all_artifacts:
        try:
            logger.info(f"Processing: {artifact['title'][:50]}...")
            
            # Check if artifact already has multi-category data
            metadata = artifact.get('raw_metadata', '{}')
            if isinstance(metadata, str):
                try:
                    metadata = json.loads(metadata)
                except json.JSONDecodeError:
                    metadata = {}
            
            # Check if it already has ai_impact_categories (multi-category data)
            has_multi_category = 'ai_impact_categories' in metadata
            
            if has_multi_category:
                logger.info(f"  ✅ Already has multi-category data")
                processed_count += 1
                continue
            
            # Reprocess with classifier to get multi-category data
            # Use the classifier to get enhanced categorization
            classifications = classifier.classify_artifact(artifact, multi_class=True)
            
            # Convert classifications to categories format
            categories = {}
            for classification in classifications:
                categories[classification.category] = {
                    'confidence': classification.confidence,
                    'evidence': classification.supporting_evidence,
                    'rationale': classification.rationale
                }
            
            # Update metadata with multi-category data
            metadata['ai_impact_categories'] = categories
            metadata['reprocessed_at'] = datetime.now().isoformat()
            metadata['processing_method'] = 'enhanced_multicategory'
            
            # Determine primary category (highest confidence)
            primary_category = 'unknown'
            max_confidence = 0
            for category, data in categories.items():
                if isinstance(data, dict) and data.get('confidence', 0) > max_confidence:
                    max_confidence = data['confidence']
                    primary_category = category
            
            metadata['primary_category'] = primary_category
            metadata['overall_confidence'] = max_confidence
            
            # Update the artifact in database
            updated_artifact = artifact.copy()
            updated_artifact['raw_metadata'] = json.dumps(metadata)
            
            # Save updated artifact
            db.save_artifact(updated_artifact)
            
            logger.info(f"  ✅ Updated with categories: {', '.join(categories.keys())}")
            updated_count += 1
            processed_count += 1
            
        except Exception as e:
            logger.error(f"  ❌ Error processing {artifact.get('id', 'unknown')}: {e}")
            error_count += 1
            processed_count += 1
    
    logger.info(f"🎉 Reprocessing complete!")
    logger.info(f"  📊 Total processed: {processed_count}")
    logger.info(f"  ✅ Updated: {updated_count}")
    logger.info(f"  ❌ Errors: {error_count}")

def verify_cleanup():
    """Verify the cleanup and reprocessing results."""
    db = DatabaseManager()
    
    logger.info("🔍 Verifying cleanup results...")
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        # Check for remaining demo entries
        cursor.execute("SELECT COUNT(*) FROM artifacts WHERE source_type = 'demo'")
        demo_count = cursor.fetchone()[0]
        
        if demo_count > 0:
            logger.warning(f"⚠️  Still found {demo_count} demo entries!")
        else:
            logger.info("✅ No demo entries remaining")
        
        # Check total entries
        cursor.execute("SELECT COUNT(*) FROM artifacts")
        total_count = cursor.fetchone()[0]
        logger.info(f"📊 Total entries in database: {total_count}")
        
        # Check entries with multi-category data
        cursor.execute("SELECT COUNT(*) FROM artifacts WHERE raw_metadata LIKE '%ai_impact_categories%'")
        multi_category_count = cursor.fetchone()[0]
        logger.info(f"🎯 Entries with multi-category data: {multi_category_count}")
        
        # Show source type breakdown
        cursor.execute("SELECT source_type, COUNT(*) FROM artifacts GROUP BY source_type")
        source_breakdown = cursor.fetchall()
        
        logger.info("📈 Source type breakdown:")
        for source_type, count in source_breakdown:
            logger.info(f"  {source_type}: {count}")

async def main():
    """Main execution function."""
    logger.info("🚀 Starting cleanup and reprocessing...")
    
    try:
        # Step 1: Remove demo entries
        remove_demo_entries()
        
        # Step 2: Reprocess all entries
        await reprocess_all_entries()
        
        # Step 3: Verify results
        verify_cleanup()
        
        logger.info("🎉 Cleanup and reprocessing completed successfully!")
        logger.info("💡 You can now browse entries to see the enhanced multi-category data")
        
    except Exception as e:
        logger.error(f"❌ Error during cleanup and reprocessing: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 