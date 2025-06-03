#!/usr/bin/env python3
"""
Cleanup Failed Entries - Remove entries that can't be processed
"""

import sys
import json
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from aih.utils.database import DatabaseManager
from aih.utils.logging import get_logger

def cleanup_failed_entries():
    """Remove entries with insufficient content that can't be enhanced."""
    logger = get_logger('cleanup')
    
    print("🧹 Cleaning Up Failed Entries")
    print("=" * 50)
    
    db = DatabaseManager()
    artifacts = db.get_artifacts()
    
    # Find entries with minimal content and no wisdom
    failed_entries = []
    for artifact in artifacts:
        content = artifact.get('content', '')
        metadata = json.loads(artifact.get('raw_metadata', '{}'))
        wisdom = metadata.get('extracted_wisdom')
        
        # Target entries with very little content and no quality wisdom
        if len(content) < 100 and (not wisdom or 'fallback' in wisdom.get('extraction_method', '')):
            failed_entries.append(artifact)
    
    print(f"Found {len(failed_entries)} entries to remove:")
    
    for i, artifact in enumerate(failed_entries):
        title = artifact.get('title', 'Untitled')[:60]
        content_len = len(artifact.get('content', ''))
        url = artifact.get('url', '')[:70]
        print(f"{i+1:2d}. {title}...")
        print(f"     Content: {content_len} chars")
        print(f"     URL: {url}...")
        print()
    
    if not failed_entries:
        print("✅ No failed entries to remove!")
        return
    
    proceed = input(f"🗑️  Delete {len(failed_entries)} failed entries? (y/N): ").strip().lower()
    if proceed != 'y':
        print("Cancelled.")
        return
    
    # Delete entries using the proper database connection
    deleted_count = 0
    for artifact in failed_entries:
        try:
            artifact_id = artifact['id']
            
            # Use the database manager's connection context
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM artifacts WHERE id = ?", (artifact_id,))
                conn.commit()
            
            print(f"🗑️  Deleted: {artifact.get('title', 'Untitled')[:50]}...")
            deleted_count += 1
            
        except Exception as e:
            print(f"❌ Failed to delete {artifact_id}: {e}")
    
    print(f"\n✅ Cleanup Complete!")
    print(f"   🗑️  Deleted: {deleted_count} entries")
    
    # Final status check
    print(f"\n📊 Running final status check...")
    os.system("python audit_wisdom_status.py")

if __name__ == "__main__":
    cleanup_failed_entries() 