#!/usr/bin/env python3
"""
AI-Horizon Batch Wisdom Extraction

Extract wisdom and insights from all existing articles using AI.
This will process all articles that don't already have extracted wisdom.
"""

import sys
import json
import asyncio
import os
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from aih.utils.database import DatabaseManager
from aih.utils.logging import get_logger
from aih.utils.cost_tracker import cost_tracker
from fix_wisdom_extraction import RobustWisdomExtractor

async def extract_wisdom_for_article(artifact_id, title, content, db, logger):
    """Extract wisdom for a single article."""
    try:
        import openai
        
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            logger.error("OpenAI API key not configured")
            return None
        
        client = openai.OpenAI(api_key=api_key)
        
        # Truncate content if too long (keep within token limits)
        max_content_length = 6000
        if len(content) > max_content_length:
            content = content[:max_content_length] + "...[truncated]"
        
        wisdom_prompt = f"""
You are an expert cybersecurity career advisor analyzing content for 2025 graduates. Extract the most valuable, actionable wisdom from this article.

Title: {title}

Content: {content}

Provide your analysis as a structured JSON response with:

{{
    "key_wisdom": ["3-5 most important insights that would help a cybersecurity professional"],
    "career_implications": ["2-3 specific implications for career planning and development"],
    "actionable_takeaways": ["3-4 concrete actions someone could take based on this content"],
    "future_outlook": "Brief assessment of what this means for the cybersecurity field in 2025-2030",
    "skill_recommendations": ["2-3 specific skills to focus on based on this analysis"],
    "summary": "2-3 sentence executive summary of the core message",
    "relevance_score": 0.0-1.0,
    "complexity_level": "beginner|intermediate|advanced"
}}

Focus on practical, actionable insights that would genuinely help someone navigate their cybersecurity career. Avoid generic advice - be specific and forward-looking.
"""
        
        logger.info(f"Extracting wisdom from: {title[:50]}...")
        
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert cybersecurity career strategist. Provide deep, actionable insights that help professionals make informed career decisions."},
                {"role": "user", "content": wisdom_prompt}
            ],
            temperature=0.1,
            max_tokens=800
        )
        
        # Parse the AI response
        try:
            response_content = response.choices[0].message.content.strip()
            
            # Handle cases where AI response isn't pure JSON
            if not response_content:
                logger.error(f"❌ Empty response for {title[:50]}...")
                return None
            
            # Try to extract JSON if it's wrapped in markdown
            if "```json" in response_content:
                start = response_content.find("```json") + 7
                end = response_content.find("```", start)
                if end > start:
                    response_content = response_content[start:end].strip()
            elif "```" in response_content:
                start = response_content.find("```") + 3
                end = response_content.find("```", start)
                if end > start:
                    response_content = response_content[start:end].strip()
            
            # Clean up common JSON formatting issues
            response_content = response_content.replace("'", '"')  # Replace single quotes
            
            try:
                wisdom_data = json.loads(response_content)
            except json.JSONDecodeError:
                # If still can't parse, log the response for debugging
                logger.error(f"❌ JSON parse failed for {title[:50]}...")
                logger.error(f"Raw response: {response_content[:200]}...")
                
                # Create a fallback wisdom structure
                wisdom_data = {
                    "key_wisdom": ["Analysis failed - content may be too complex or unstructured"],
                    "career_implications": ["Manual review recommended"],
                    "actionable_takeaways": ["Consider source credibility and relevance"],
                    "future_outlook": "Analysis could not be completed automatically",
                    "skill_recommendations": ["Critical thinking", "Source evaluation"],
                    "summary": f"Automated analysis failed for this content: {title[:100]}",
                    "relevance_score": 0.1,
                    "complexity_level": "unknown",
                    "extraction_error": "JSON parsing failed",
                    "raw_response": response_content[:500]  # Store partial response for debugging
                }
            
            # Add extraction metadata
            wisdom_data['extracted_at'] = datetime.now().isoformat()
            wisdom_data['extraction_method'] = 'openai_gpt4_wisdom_batch'
            wisdom_data['content_length'] = len(content)
            
            # Get artifact and update metadata
            artifact = db.get_artifact_by_id(artifact_id)
            if artifact:
                metadata = json.loads(artifact.get('raw_metadata', '{}'))
                metadata['extracted_wisdom'] = wisdom_data
                metadata['wisdom_extracted_at'] = wisdom_data['extracted_at']
                
                # Update artifact with new metadata
                artifact['metadata'] = metadata
                artifact['raw_metadata'] = json.dumps(metadata)
                db.save_artifact(artifact)
                
                # Track cost
                estimated_cost = 0.015  # Rough estimate for GPT-4o-mini with this prompt
                cost_tracker.track_api_call("openai", "gpt-4o-mini", tokens=800, custom_cost=estimated_cost)
                
                if wisdom_data.get('extraction_error'):
                    logger.warning(f"⚠️ Partial wisdom extracted for: {title[:50]}... (Cost: ${estimated_cost:.4f})")
                else:
                    logger.info(f"✅ Wisdom extracted for: {title[:50]}... (Cost: ${estimated_cost:.4f})")
                return wisdom_data
            else:
                logger.error(f"❌ Could not find artifact: {artifact_id}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Failed to process wisdom response for {title[:50]}...: {e}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Wisdom extraction failed for {title[:50]}...: {e}")
        return None

async def extract_wisdom_batch(limit=None):
    """Extract wisdom for all articles that don't already have it."""
    logger = get_logger('wisdom_batch')
    logger.info("🧠 Starting batch wisdom extraction for all articles")
    
    try:
        db = DatabaseManager()
        artifacts = db.get_artifacts(limit=1000)  # Get all artifacts
        
        # Filter for articles that don't have extracted wisdom
        articles_to_process = []
        for artifact in artifacts:
            metadata = json.loads(artifact.get('raw_metadata', '{}'))
            if not metadata.get('extracted_wisdom'):
                # Only process articles with substantial content
                content = artifact.get('content', '')
                if len(content.strip()) > 100:  # At least 100 characters
                    articles_to_process.append(artifact)
        
        # Apply limit if specified
        if limit and limit < len(articles_to_process):
            articles_to_process = articles_to_process[:limit]
            logger.info(f"📊 Limited to {limit} articles for testing")
        
        logger.info(f"📊 Found {len(articles_to_process)} articles to process (out of {len(artifacts)} total)")
        
        if not articles_to_process:
            logger.info("✅ All articles already have extracted wisdom!")
            return 0, 0
        
        # Process articles with rate limiting
        successful = 0
        failed = 0
        total_cost = 0.0
        
        for i, artifact in enumerate(articles_to_process, 1):
            logger.info(f"🔄 Processing {i}/{len(articles_to_process)}: {artifact.get('title', 'Untitled')[:50]}...")
            
            wisdom = await extract_wisdom_for_article(
                artifact['id'],
                artifact.get('title', 'Untitled'),
                artifact.get('content', ''),
                db,
                logger
            )
            
            if wisdom:
                successful += 1
                total_cost += 0.015
            else:
                failed += 1
            
            # Rate limiting - wait 2 seconds between requests to avoid overwhelming API
            if i < len(articles_to_process):
                await asyncio.sleep(2)
        
        logger.info(f"🎉 Batch wisdom extraction completed!")
        logger.info(f"✅ Successful: {successful}")
        logger.info(f"❌ Failed: {failed}")
        logger.info(f"💰 Total estimated cost: ${total_cost:.2f}")
        
        return successful, failed
        
    except Exception as e:
        logger.error(f"❌ Batch wisdom extraction failed: {e}")
        return 0, 0

async def fix_specific_entry(entry_id: str):
    """Fix a specific entry by attempting content enhancement and wisdom extraction."""
    db = DatabaseManager()
    extractor = RobustWisdomExtractor()
    
    print(f"🔍 Checking entry: {entry_id}")
    
    # Get the artifact
    artifact = db.get_artifact_by_id(entry_id)
    if not artifact:
        print(f"❌ Entry not found: {entry_id}")
        return False
    
    title = artifact.get('title', 'Untitled')
    content = artifact.get('content', '')
    url = artifact.get('url', '')
    source_type = artifact.get('source_type', '')
    
    print(f"📄 Title: {title}")
    print(f"🔗 URL: {url}")
    print(f"📝 Current content length: {len(content)} chars")
    print(f"📂 Source type: {source_type}")
    
    # Check current metadata
    metadata = json.loads(artifact.get('raw_metadata', '{}'))
    current_wisdom = metadata.get('extracted_wisdom')
    
    if current_wisdom:
        method = current_wisdom.get('extraction_method', 'unknown')
        print(f"🧠 Current wisdom method: {method}")
        
        # Check if it's a fallback method that needs redoing
        if 'fallback' in method:
            print("⚠️  Has fallback wisdom - needs enhancement")
        else:
            print("✅ Already has quality wisdom")
            return True
    else:
        print("❌ No wisdom extracted yet")
    
    # Try to enhance content if it's YouTube and content is minimal
    if source_type == 'manual_youtube' and len(content) < 1000:
        print("🎥 Attempting YouTube transcript extraction...")
        
        try:
            # Try different transcript extraction methods
            transcript = await attempt_youtube_transcript(url)
            
            if transcript and len(transcript) > 500:
                # Update content
                new_content = f"{content}\n\nTranscript:\n{transcript}"
                
                # Update artifact
                updated_artifact = {
                    'id': entry_id,
                    'url': url,
                    'title': title,
                    'content': new_content,
                    'source_type': source_type,
                    'collected_at': artifact.get('collected_at'),
                    'metadata': metadata
                }
                
                # Add enhancement metadata
                updated_artifact['metadata']['content_enhanced'] = True
                updated_artifact['metadata']['enhancement_date'] = datetime.now().isoformat()
                updated_artifact['metadata']['original_length'] = len(content)
                updated_artifact['metadata']['enhanced_length'] = len(new_content)
                
                db.save_artifact(updated_artifact)
                print(f"✅ Content enhanced: {len(content)} → {len(new_content)} chars")
                
                # Reload artifact
                artifact = db.get_artifact_by_id(entry_id)
            else:
                print("❌ Could not extract transcript")
        
        except Exception as e:
            print(f"❌ Transcript extraction failed: {e}")
    
    # Extract wisdom regardless
    print("🧠 Attempting wisdom extraction...")
    
    result = await extractor.extract_wisdom_robust(entry_id)
    
    if result['success']:
        print("✅ Wisdom extraction successful!")
        
        # Show summary
        wisdom = result['wisdom']
        print(f"   📊 Key insights: {len(wisdom.get('key_wisdom', []))}")
        print(f"   🎯 Career implications: {len(wisdom.get('career_implications', []))}")
        print(f"   ✅ Relevance score: {wisdom.get('relevance_score', 'N/A')}")
        return True
    else:
        print(f"❌ Wisdom extraction failed: {result['error']}")
        return False

async def attempt_youtube_transcript(url: str) -> str:
    """Try multiple methods to extract YouTube transcript."""
    try:
        # Method 1: youtube-transcript-api
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            import re
            
            # Extract video ID
            video_id_match = re.search(r'(?:v=|/)([0-9A-Za-z_-]{11}).*', url)
            if video_id_match:
                video_id = video_id_match.group(1)
                print(f"   Video ID: {video_id}")
                
                # Try multiple language codes
                for lang_codes in [['en'], ['en-US'], ['en-GB'], ['a.en']]:
                    try:
                        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=lang_codes)
                        transcript = ' '.join([item['text'] for item in transcript_list])
                        if len(transcript) > 100:
                            print(f"   ✅ Transcript extracted with language: {lang_codes}")
                            return transcript
                    except Exception as e:
                        print(f"   ⚠️  Language {lang_codes} failed: {e}")
                        continue
        
        except ImportError:
            print("   ⚠️  youtube-transcript-api not available")
        except Exception as e:
            print(f"   ❌ youtube-transcript-api failed: {e}")
        
        # Method 2: yt-dlp with subtitle extraction
        try:
            import yt_dlp
            
            ydl_opts = {
                'writesubtitles': True,
                'writeautomaticsub': True,
                'subtitleslangs': ['en', 'en-US'],
                'skip_download': True,
                'quiet': True,
                'no_warnings': True
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # Check for subtitles
                subtitles = info.get('subtitles', {})
                auto_captions = info.get('automatic_captions', {})
                
                # Try to get subtitle text
                for lang in ['en', 'en-US']:
                    subs = subtitles.get(lang) or auto_captions.get(lang)
                    if subs:
                        # This would need subtitle file parsing
                        print(f"   ✅ Found subtitles for language: {lang}")
                        return f"Subtitles available but parsing not implemented. Video: {info.get('title', 'Unknown')}"
        
        except ImportError:
            print("   ⚠️  yt-dlp not available")
        except Exception as e:
            print(f"   ❌ yt-dlp failed: {e}")
        
        print("   ❌ No transcript extraction method succeeded")
        return ""
    
    except Exception as e:
        print(f"   ❌ All transcript methods failed: {e}")
        return ""

async def main():
    """Main function to fix specific problematic entries."""
    print("🔧 Targeted Entry Fix")
    print("=" * 50)
    
    # The specific problematic entry
    problematic_entry = "manual_youtube_20250601_155345"
    
    print(f"\n🎯 Fixing problematic entry: {problematic_entry}")
    
    success = await fix_specific_entry(problematic_entry)
    
    if success:
        print(f"\n✅ Entry fixed successfully!")
    else:
        print(f"\n❌ Entry still has issues")
    
    # Also check a few other entries
    print(f"\n📊 Checking status of recent entries...")
    
    db = DatabaseManager()
    artifacts = db.get_artifacts()
    
    # Find entries without wisdom
    no_wisdom = []
    for artifact in artifacts:
        metadata = json.loads(artifact.get('raw_metadata', '{}'))
        wisdom = metadata.get('extracted_wisdom')
        
        if not wisdom or 'fallback' in wisdom.get('extraction_method', ''):
            no_wisdom.append(artifact)
    
    print(f"Found {len(no_wisdom)} entries needing attention:")
    for i, artifact in enumerate(no_wisdom[:5]):
        title = artifact.get('title', 'Untitled')[:50]
        content_len = len(artifact.get('content', ''))
        source_type = artifact.get('source_type', '')
        print(f"{i+1}. {title}... ({content_len} chars, {source_type})")
    
    if len(no_wisdom) > 5:
        print(f"   ... and {len(no_wisdom) - 5} more")

if __name__ == "__main__":
    asyncio.run(main()) 