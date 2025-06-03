#!/usr/bin/env python3
"""
Audit Wisdom Status - Check current state of wisdom extraction across all entries
"""

import sys
import json
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from aih.utils.database import DatabaseManager
from aih.utils.logging import get_logger

def audit_wisdom_status():
    """Audit the current wisdom extraction status across all entries."""
    logger = get_logger('audit_wisdom')
    
    try:
        db = DatabaseManager()
        artifacts = db.get_artifacts()
        
        print(f"\n=== WISDOM EXTRACTION AUDIT ===")
        print(f"Total artifacts: {len(artifacts)}")
        
        # Categorize entries
        has_wisdom = []
        no_wisdom = []
        insufficient_content = []
        youtube_no_transcript = []
        good_content_no_wisdom = []
        
        for artifact in artifacts:
            metadata = json.loads(artifact.get('raw_metadata', '{}'))
            content = artifact.get('content', '')
            content_length = len(content)
            source_type = artifact.get('source_type', '')
            title = artifact.get('title', 'Untitled')[:50]
            
            if metadata.get('extracted_wisdom'):
                has_wisdom.append({
                    'id': artifact.get('id'),
                    'title': title,
                    'content_length': content_length,
                    'extraction_method': metadata['extracted_wisdom'].get('extraction_method', 'unknown')
                })
            else:
                no_wisdom.append(artifact)
                
                if source_type == 'manual_youtube' and content_length < 200:
                    youtube_no_transcript.append({
                        'id': artifact.get('id'),
                        'title': title,
                        'url': artifact.get('url', ''),
                        'content_length': content_length
                    })
                elif content_length < 200:
                    insufficient_content.append({
                        'id': artifact.get('id'),
                        'title': title,
                        'url': artifact.get('url', ''),
                        'content_length': content_length,
                        'source_type': source_type
                    })
                else:
                    good_content_no_wisdom.append({
                        'id': artifact.get('id'),
                        'title': title,
                        'url': artifact.get('url', ''),
                        'content_length': content_length,
                        'source_type': source_type
                    })
        
        print(f"\n--- STATUS BREAKDOWN ---")
        print(f"✅ Has wisdom extracted: {len(has_wisdom)}")
        print(f"❌ Missing wisdom: {len(no_wisdom)}")
        print(f"   📄 Good content, ready to process: {len(good_content_no_wisdom)}")
        print(f"   🎥 YouTube without transcript: {len(youtube_no_transcript)}")
        print(f"   ⚠️  Insufficient content: {len(insufficient_content)}")
        
        # Show extraction methods used
        if has_wisdom:
            methods = {}
            for entry in has_wisdom:
                method = entry['extraction_method']
                methods[method] = methods.get(method, 0) + 1
            
            print(f"\n--- EXTRACTION METHODS USED ---")
            for method, count in methods.items():
                print(f"   {method}: {count}")
        
        # Show entries ready for processing
        if good_content_no_wisdom:
            print(f"\n--- ENTRIES READY FOR WISDOM EXTRACTION ---")
            for i, entry in enumerate(good_content_no_wisdom[:10]):  # Show first 10
                print(f"{i+1:2d}. {entry['title']} ({entry['content_length']} chars)")
            if len(good_content_no_wisdom) > 10:
                print(f"    ... and {len(good_content_no_wisdom) - 10} more")
        
        # Show problematic entries that need content enhancement
        print(f"\n--- ENTRIES NEEDING CONTENT ENHANCEMENT ---")
        
        if youtube_no_transcript:
            print(f"\nYouTube videos without transcripts ({len(youtube_no_transcript)}):")
            for entry in youtube_no_transcript[:5]:
                print(f"   - {entry['title']} ({entry['content_length']} chars)")
                print(f"     URL: {entry['url']}")
            if len(youtube_no_transcript) > 5:
                print(f"   ... and {len(youtube_no_transcript) - 5} more")
        
        if insufficient_content:
            print(f"\nEntries with insufficient content ({len(insufficient_content)}):")
            for entry in insufficient_content[:5]:
                print(f"   - {entry['title']} ({entry['content_length']} chars)")
                print(f"     Type: {entry['source_type']}, URL: {entry['url'][:60]}...")
            if len(insufficient_content) > 5:
                print(f"   ... and {len(insufficient_content) - 5} more")
        
        return {
            'total': len(artifacts),
            'has_wisdom': len(has_wisdom),
            'ready_to_process': len(good_content_no_wisdom),
            'youtube_needs_transcript': len(youtube_no_transcript),
            'insufficient_content': len(insufficient_content),
            'ready_entries': good_content_no_wisdom,
            'youtube_entries': youtube_no_transcript,
            'insufficient_entries': insufficient_content
        }
        
    except Exception as e:
        logger.error(f"Audit failed: {e}")
        return None

if __name__ == "__main__":
    audit_wisdom_status() 