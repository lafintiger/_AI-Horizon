#!/usr/bin/env python3
"""
Add Multi-Category Data to Existing Entries

This script adds multi-category AI impact data to existing entries using
keyword-based analysis instead of requiring API calls.
"""

import sys
import json
import re
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from aih.utils.database import DatabaseManager
from aih.utils.logging import get_logger

logger = get_logger(__name__)

def analyze_content_keywords(title, content):
    """
    Analyze content using keyword patterns to determine AI impact categories.
    
    Returns:
        dict: Categories with confidence scores and evidence
    """
    text = f"{title} {content}".lower()
    categories = {}
    
    # Replace category keywords and patterns
    replace_keywords = [
        'automat', 'replac', 'eliminat', 'ai will', 'machine learning will',
        'ai can', 'ai does', 'ai performs', 'ai handles', 'ai processes',
        'fully automated', 'complete automation', 'ai-driven', 'ai-powered automation'
    ]
    
    # Augment category keywords
    augment_keywords = [
        'assist', 'enhance', 'support', 'help', 'aid', 'augment', 'collaborate',
        'human-ai', 'ai-assisted', 'ai-enhanced', 'ai tools', 'ai helps',
        'working with ai', 'ai collaboration', 'ai integration'
    ]
    
    # New tasks category keywords
    new_tasks_keywords = [
        'new role', 'new job', 'emerging role', 'ai specialist', 'ai engineer',
        'ai governance', 'ai ethics', 'ai security', 'ml engineer', 'mlsecops',
        'ai coordinator', 'ai trainer', 'ai oversight', 'ai compliance'
    ]
    
    # Human-only category keywords
    human_only_keywords = [
        'human judgment', 'human decision', 'human creativity', 'human intuition',
        'strategic thinking', 'leadership', 'communication', 'empathy',
        'human-only', 'uniquely human', 'human expertise', 'human insight',
        'cannot be automated', 'requires human', 'human element'
    ]
    
    # Count keyword matches and calculate confidence
    replace_matches = sum(1 for keyword in replace_keywords if keyword in text)
    augment_matches = sum(1 for keyword in augment_keywords if keyword in text)
    new_tasks_matches = sum(1 for keyword in new_tasks_keywords if keyword in text)
    human_only_matches = sum(1 for keyword in human_only_keywords if keyword in text)
    
    # Calculate confidence based on keyword density and matches
    total_words = len(text.split())
    
    if replace_matches > 0:
        confidence = min(0.9, 0.3 + (replace_matches / 10))
        categories['replace'] = {
            'confidence': confidence,
            'evidence': [f"Found {replace_matches} automation/replacement indicators"],
            'rationale': f"Content discusses AI automation and replacement of human tasks"
        }
    
    if augment_matches > 0:
        confidence = min(0.9, 0.3 + (augment_matches / 10))
        categories['augment'] = {
            'confidence': confidence,
            'evidence': [f"Found {augment_matches} human-AI collaboration indicators"],
            'rationale': f"Content discusses AI assisting and enhancing human capabilities"
        }
    
    if new_tasks_matches > 0:
        confidence = min(0.9, 0.4 + (new_tasks_matches / 8))
        categories['new_tasks'] = {
            'confidence': confidence,
            'evidence': [f"Found {new_tasks_matches} new role/job indicators"],
            'rationale': f"Content discusses new roles and jobs created by AI"
        }
    
    if human_only_matches > 0:
        confidence = min(0.9, 0.4 + (human_only_matches / 8))
        categories['human_only'] = {
            'confidence': confidence,
            'evidence': [f"Found {human_only_matches} human-only task indicators"],
            'rationale': f"Content discusses tasks that remain uniquely human"
        }
    
    # If no specific categories found, assign based on general content
    if not categories:
        if 'cybersecurity' in text and 'ai' in text:
            categories['augment'] = {
                'confidence': 0.5,
                'evidence': ["General cybersecurity and AI content"],
                'rationale': "General discussion of AI in cybersecurity context"
            }
    
    return categories

def add_multicategory_data():
    """Add multi-category data to all entries."""
    db = DatabaseManager()
    
    logger.info("🔄 Adding multi-category data to all entries...")
    
    # Get all artifacts
    all_artifacts = db.get_artifacts()
    logger.info(f"Found {len(all_artifacts)} entries to process")
    
    processed_count = 0
    updated_count = 0
    skipped_count = 0
    
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
                skipped_count += 1
                processed_count += 1
                continue
            
            # Analyze content with keyword-based approach
            title = artifact.get('title', '')
            content = artifact.get('content', '')
            
            categories = analyze_content_keywords(title, content)
            
            if not categories:
                logger.info(f"  ⚠️  No categories detected, skipping")
                skipped_count += 1
                processed_count += 1
                continue
            
            # Update metadata with multi-category data
            metadata['ai_impact_categories'] = categories
            metadata['reprocessed_at'] = datetime.now().isoformat()
            metadata['processing_method'] = 'keyword_multicategory'
            
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
            
            category_list = ', '.join([f"{cat}({data['confidence']:.1f})" for cat, data in categories.items()])
            logger.info(f"  ✅ Updated with categories: {category_list}")
            updated_count += 1
            processed_count += 1
            
        except Exception as e:
            logger.error(f"  ❌ Error processing {artifact.get('id', 'unknown')}: {e}")
            processed_count += 1
    
    logger.info(f"🎉 Multi-category processing complete!")
    logger.info(f"  📊 Total processed: {processed_count}")
    logger.info(f"  ✅ Updated: {updated_count}")
    logger.info(f"  ⏭️  Skipped: {skipped_count}")

def verify_results():
    """Verify the multi-category data addition results."""
    db = DatabaseManager()
    
    logger.info("🔍 Verifying multi-category results...")
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        # Check total entries
        cursor.execute("SELECT COUNT(*) FROM artifacts")
        total_count = cursor.fetchone()[0]
        logger.info(f"📊 Total entries in database: {total_count}")
        
        # Check entries with multi-category data
        cursor.execute("SELECT COUNT(*) FROM artifacts WHERE raw_metadata LIKE '%ai_impact_categories%'")
        multi_category_count = cursor.fetchone()[0]
        logger.info(f"🎯 Entries with multi-category data: {multi_category_count}")
        
        # Show some examples
        cursor.execute("""
            SELECT id, title, raw_metadata 
            FROM artifacts 
            WHERE raw_metadata LIKE '%ai_impact_categories%' 
            LIMIT 3
        """)
        examples = cursor.fetchall()
        
        logger.info("📝 Example multi-category entries:")
        for entry_id, title, metadata_json in examples:
            try:
                metadata = json.loads(metadata_json)
                categories = metadata.get('ai_impact_categories', {})
                category_summary = ', '.join([f"{cat}({data['confidence']:.1f})" for cat, data in categories.items()])
                logger.info(f"  • {title[:40]}... → {category_summary}")
            except Exception as e:
                logger.info(f"  • {title[:40]}... → Error parsing metadata")

def main():
    """Main execution function."""
    logger.info("🚀 Starting multi-category data addition...")
    
    try:
        # Add multi-category data
        add_multicategory_data()
        
        # Verify results
        verify_results()
        
        logger.info("🎉 Multi-category data addition completed successfully!")
        logger.info("💡 You can now browse entries to see the multi-category visual indicators")
        
    except Exception as e:
        logger.error(f"❌ Error during multi-category processing: {e}")
        raise

if __name__ == "__main__":
    main() 