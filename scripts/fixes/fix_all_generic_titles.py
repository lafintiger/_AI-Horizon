#!/usr/bin/env python3
"""
Fix All Generic Titles - Comprehensive title extraction for all generic entries
"""

import sys
import asyncio
import aiohttp
import json
import time
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from aih.utils.database import DatabaseManager
from aih.utils.logging import get_logger

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Please install: pip install beautifulsoup4")
    sys.exit(1)

class TitleFixer:
    """Fix generic titles by extracting real titles from URLs."""
    
    def __init__(self):
        self.logger = get_logger('title_fixer')
        self.db = DatabaseManager()
        
    async def extract_title_from_url(self, url: str) -> str:
        """Extract the actual title from a webpage URL."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            timeout = aiohttp.ClientTimeout(total=15)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        content = await response.text()
                        soup = BeautifulSoup(content, 'html.parser')
                        
                        # Try multiple title extraction methods
                        title = None
                        
                        # Method 1: <title> tag
                        title_tag = soup.find('title')
                        if title_tag and title_tag.get_text(strip=True):
                            title = title_tag.get_text(strip=True)
                        
                        # Method 2: og:title meta tag
                        if not title or len(title) < 10:
                            og_title = soup.find('meta', property='og:title')
                            if og_title and og_title.get('content'):
                                title = og_title.get('content').strip()
                        
                        # Method 3: twitter:title meta tag
                        if not title or len(title) < 10:
                            twitter_title = soup.find('meta', name='twitter:title')
                            if twitter_title and twitter_title.get('content'):
                                title = twitter_title.get('content').strip()
                        
                        # Method 4: h1 tag
                        if not title or len(title) < 10:
                            h1_tag = soup.find('h1')
                            if h1_tag and h1_tag.get_text(strip=True):
                                title = h1_tag.get_text(strip=True)
                        
                        # Method 5: article title
                        if not title or len(title) < 10:
                            for selector in ['.article-title', '.post-title', '.entry-title', '.title', 'h1.title']:
                                title_elem = soup.select_one(selector)
                                if title_elem and title_elem.get_text(strip=True):
                                    title = title_elem.get_text(strip=True)
                                    break
                        
                        # Clean up the title
                        if title:
                            # Remove common suffixes
                            suffixes_to_remove = [
                                ' | LinkedIn', ' - LinkedIn', ' | Indeed.com', ' - Indeed.com',
                                ' | McKinsey & Company', ' - McKinsey', ' | CISA', ' - CISA',
                                ' | Cybersecurity', ' - Cybersecurity', ' | HIMSS', ' - HIMSS',
                                ' | World Economic Forum', ' - WEF'
                            ]
                            
                            for suffix in suffixes_to_remove:
                                if title.endswith(suffix):
                                    title = title[:-len(suffix)].strip()
                            
                            # Remove extra whitespace and clean up
                            title = ' '.join(title.split())
                            
                            # Truncate if too long
                            if len(title) > 150:
                                title = title[:147] + "..."
                            
                            return title
                        
        except Exception as e:
            print(f"   ❌ Error extracting title: {e}")
        
        return None
    
    async def fix_generic_titles(self):
        """Fix all entries with generic titles."""
        print("🔧 Fixing All Generic Titles")
        print("=" * 60)
        
        # Get all artifacts with generic titles
        artifacts = self.db.get_artifacts()
        generic_entries = []
        
        for artifact in artifacts:
            title = artifact.get('title', '')
            if title.startswith('AI Cybersecurity Impact Analysis'):
                generic_entries.append(artifact)
        
        print(f"Found {len(generic_entries)} entries with generic titles")
        
        if not generic_entries:
            print("✅ No generic titles to fix!")
            return
        
        print(f"\n🚀 Processing {len(generic_entries)} entries...")
        
        successful = 0
        failed = 0
        
        for i, artifact in enumerate(generic_entries):
            print(f"\n📊 Processing {i+1}/{len(generic_entries)}")
            
            artifact_id = artifact['id']
            current_title = artifact.get('title', '')
            url = artifact.get('url', '')
            
            print(f"   Current: {current_title[:60]}...")
            print(f"   URL: {url[:70]}...")
            
            # Extract real title
            real_title = await self.extract_title_from_url(url)
            
            if real_title and len(real_title) > 10:
                # Update the artifact
                try:
                    metadata = json.loads(artifact.get('raw_metadata', '{}'))
                    
                    updated_artifact = {
                        'id': artifact_id,
                        'url': url,
                        'title': real_title,
                        'content': artifact.get('content', ''),
                        'source_type': artifact.get('source_type', ''),
                        'collected_at': artifact.get('collected_at'),
                        'metadata': metadata
                    }
                    
                    # Add title fixing metadata
                    updated_artifact['metadata']['title_fixed'] = True
                    updated_artifact['metadata']['original_title'] = current_title
                    updated_artifact['metadata']['title_fixed_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
                    
                    self.db.save_artifact(updated_artifact)
                    
                    print(f"   ✅ Fixed: {real_title}")
                    successful += 1
                    
                except Exception as e:
                    print(f"   ❌ Failed to save: {e}")
                    failed += 1
            else:
                print(f"   ❌ Could not extract title")
                failed += 1
            
            # Rate limiting to be nice to servers
            await asyncio.sleep(1)
        
        print(f"\n🎯 Title Fixing Complete!")
        print(f"   ✅ Successfully fixed: {successful}")
        print(f"   ❌ Failed: {failed}")
        print(f"   📊 Success rate: {(successful/(successful+failed)*100):.1f}%")
        
        # Show final status
        print(f"\n📊 Running final check...")
        self.check_remaining_generic()
    
    def check_remaining_generic(self):
        """Check how many generic titles remain."""
        artifacts = self.db.get_artifacts()
        remaining = sum(1 for artifact in artifacts if artifact.get('title', '').startswith('AI Cybersecurity Impact Analysis'))
        
        print(f"   Remaining generic titles: {remaining}")
        
        if remaining == 0:
            print("   🎉 ALL GENERIC TITLES FIXED!")
        else:
            print(f"   ⚠️  {remaining} entries still need manual attention")

async def main():
    """Main function."""
    fixer = TitleFixer()
    await fixer.fix_generic_titles()

if __name__ == "__main__":
    asyncio.run(main()) 