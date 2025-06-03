#!/usr/bin/env python3
"""
Fix Remaining Entries - Handle the last few problematic entries
"""

import sys
import json
import asyncio
import aiohttp
import os
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from aih.utils.database import DatabaseManager
from aih.utils.logging import get_logger
from fix_wisdom_extraction import RobustWisdomExtractor

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Please install: pip install requests beautifulsoup4")
    sys.exit(1)

async def enhance_url_content(artifact):
    """Attempt to scrape full content from URL."""
    url = artifact.get('url', '')
    if not url.startswith('http'):
        return None
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=15) as response:
                if response.status == 200:
                    content = await response.text()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Remove unwanted elements
                    for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
                        script.decompose()
                    
                    # Try multiple content selectors
                    content_selectors = [
                        'article', '.article-content', '.post-content', '.content',
                        'main', '.story-body', '.entry-content', '.article-body',
                        '.post-body', '.blog-content', '.news-content', '.text-content',
                        '[role="main"]', '.main-content', '#content'
                    ]
                    
                    extracted_content = ""
                    for selector in content_selectors:
                        content_elem = soup.select_one(selector)
                        if content_elem:
                            extracted_content = content_elem.get_text(separator=' ', strip=True)
                            if len(extracted_content) > 500:
                                break
                    
                    # Fallback to all paragraphs
                    if not extracted_content or len(extracted_content) < 300:
                        paragraphs = soup.find_all('p')
                        if paragraphs:
                            extracted_content = ' '.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 20])
                    
                    # Final fallback to body text
                    if not extracted_content or len(extracted_content) < 200:
                        body = soup.find('body')
                        if body:
                            extracted_content = body.get_text(separator=' ', strip=True)
                    
                    return extracted_content if len(extracted_content) > 100 else None
    
    except Exception as e:
        print(f"   ❌ Scraping failed: {e}")
        return None

async def fix_minimal_entry(artifact):
    """Fix an entry with minimal content."""
    entry_id = artifact['id']
    title = artifact.get('title', 'Untitled')
    content = artifact.get('content', '')
    url = artifact.get('url', '')
    source_type = artifact.get('source_type', '')
    
    print(f"\n🔧 Fixing: {title[:60]}...")
    print(f"   Current content: {len(content)} chars")
    print(f"   URL: {url[:70]}...")
    
    # Try to enhance content
    enhanced_content = None
    
    if source_type == 'manual_url' and url:
        print("   🔗 Attempting web scraping...")
        enhanced_content = await enhance_url_content(artifact)
    
    if enhanced_content and len(enhanced_content) > 500:
        print(f"   ✅ Content enhanced: {len(content)} → {len(enhanced_content)} chars")
        
        # Update artifact
        metadata = json.loads(artifact.get('raw_metadata', '{}'))
        
        updated_artifact = {
            'id': entry_id,
            'url': url,
            'title': title,
            'content': enhanced_content,
            'source_type': source_type,
            'collected_at': artifact.get('collected_at'),
            'metadata': metadata
        }
        
        # Add enhancement metadata
        updated_artifact['metadata']['content_enhanced'] = True
        updated_artifact['metadata']['enhancement_date'] = datetime.now().isoformat()
        updated_artifact['metadata']['original_length'] = len(content)
        updated_artifact['metadata']['enhanced_length'] = len(enhanced_content)
        
        # Save enhanced content
        db = DatabaseManager()
        db.save_artifact(updated_artifact)
        
        # Now extract wisdom
        print("   🧠 Extracting wisdom from enhanced content...")
        extractor = RobustWisdomExtractor()
        result = await extractor.extract_wisdom_robust(entry_id)
        
        if result['success']:
            wisdom = result['wisdom']
            print(f"   ✅ Wisdom extracted! Relevance: {wisdom.get('relevance_score', 'N/A')}")
            return True
        else:
            print(f"   ❌ Wisdom extraction failed: {result['error']}")
            return False
    else:
        print(f"   ❌ Could not enhance content sufficiently")
        return False

async def main():
    """Fix all remaining problematic entries."""
    print("🔧 Fixing Remaining Entries")
    print("=" * 50)
    
    db = DatabaseManager()
    artifacts = db.get_artifacts()
    
    # Find entries with minimal content
    minimal_entries = []
    for artifact in artifacts:
        content = artifact.get('content', '')
        metadata = json.loads(artifact.get('raw_metadata', '{}'))
        wisdom = metadata.get('extracted_wisdom')
        
        # Skip if already has quality wisdom
        if wisdom and 'fallback' not in wisdom.get('extraction_method', ''):
            continue
        
        # Target entries with very little content
        if len(content) < 100:
            minimal_entries.append(artifact)
    
    print(f"Found {len(minimal_entries)} entries with minimal content")
    
    if not minimal_entries:
        print("✅ No entries need fixing!")
        return
    
    # Show what we'll fix
    for i, artifact in enumerate(minimal_entries):
        title = artifact.get('title', 'Untitled')[:50]
        content_len = len(artifact.get('content', ''))
        source_type = artifact.get('source_type', '')
        print(f"{i+1:2d}. {title}... ({content_len} chars, {source_type})")
    
    proceed = input(f"\n🚀 Fix {len(minimal_entries)} entries? (y/N): ").strip().lower()
    if proceed != 'y':
        print("Cancelled.")
        return
    
    # Fix entries
    successful = 0
    failed = 0
    
    for i, artifact in enumerate(minimal_entries):
        print(f"\n📊 Processing {i+1}/{len(minimal_entries)}")
        
        success = await fix_minimal_entry(artifact)
        
        if success:
            successful += 1
        else:
            failed += 1
        
        # Rate limiting
        await asyncio.sleep(2)
    
    print(f"\n🎯 Fixing Complete!")
    print(f"   ✅ Successful: {successful}")
    print(f"   ❌ Failed: {failed}")
    
    # Final status check
    print(f"\n📊 Running final status check...")
    os.system("python audit_wisdom_status.py")

if __name__ == "__main__":
    asyncio.run(main()) 