#!/usr/bin/env python3
"""
Comprehensive Wisdom Processor - NSF Standards

This system:
1. Audits all entries for missing wisdom
2. Enhances content where insufficient (web scraping, transcript extraction, PDF processing)
3. Extracts wisdom with quality validation
4. Ensures all results meet NSF research standards
"""

import sys
import json
import asyncio
import aiohttp
import os
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from aih.utils.database import DatabaseManager
from aih.utils.logging import get_logger
from aih.utils.cost_tracker import cost_tracker

# Import third-party libraries for content enhancement
try:
    import requests
    from bs4 import BeautifulSoup
    import openai
    import yt_dlp
    import PyPDF2
    import docx
except ImportError as e:
    print(f"Missing required libraries: {e}")
    print("Please install: pip install requests beautifulsoup4 openai yt-dlp PyPDF2 python-docx")
    sys.exit(1)

class ComprehensiveWisdomProcessor:
    """NSF-standard wisdom extraction with content enhancement."""
    
    def __init__(self, status_tracker=None):
        self.logger = get_logger('wisdom_processor')
        self.db = DatabaseManager()
        self.status_tracker = status_tracker
        
        # OpenAI setup
        self.openai_client = None
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            self.openai_client = openai.OpenAI(api_key=api_key)
        
        # Quality thresholds for NSF standards
        self.min_content_length = 500  # Minimum meaningful content
        self.min_wisdom_fields = 8     # All required wisdom fields must be present
        self.quality_checks = [
            'key_wisdom', 'career_implications', 'actionable_takeaways',
            'future_outlook', 'skill_recommendations', 'summary',
            'relevance_score', 'complexity_level'
        ]
        
    def log(self, level: str, message: str, category: str = "WISDOM"):
        """Log message to both logger and status tracker."""
        if level.upper() == "INFO":
            self.logger.info(message)
        elif level.upper() == "WARNING":
            self.logger.warning(message)
        elif level.upper() == "ERROR":
            self.logger.error(message)
            
        if self.status_tracker:
            self.status_tracker.add_log(level, message, category)
    
    async def process_all_entries(self) -> Dict[str, int]:
        """Process all entries needing wisdom extraction or content enhancement."""
        self.log("INFO", "Starting comprehensive wisdom processing with NSF standards")
        
        # Get all artifacts needing attention
        artifacts = self.db.get_artifacts()
        needs_processing = []
        
        for artifact in artifacts:
            metadata = json.loads(artifact.get('raw_metadata', '{}'))
            
            # Skip if already has quality wisdom
            if self._has_quality_wisdom(metadata):
                continue
                
            needs_processing.append(artifact)
        
        self.log("INFO", f"Found {len(needs_processing)} entries needing processing")
        
        stats = {
            'total_processed': 0,
            'content_enhanced': 0,
            'wisdom_extracted': 0,
            'failed': 0,
            'skipped_insufficient': 0
        }
        
        for i, artifact in enumerate(needs_processing):
            try:
                self.log("INFO", f"Processing {i+1}/{len(needs_processing)}: {artifact.get('title', '')[:50]}...")
                
                # Step 1: Enhance content if needed
                enhanced = await self._enhance_content(artifact)
                if enhanced:
                    stats['content_enhanced'] += 1
                    # Reload artifact after enhancement
                    artifact = self.db.get_artifact_by_id(artifact['id'])
                
                # Step 2: Extract wisdom if content is sufficient
                wisdom_result = await self._extract_quality_wisdom(artifact)
                if wisdom_result['success']:
                    stats['wisdom_extracted'] += 1
                else:
                    if wisdom_result['reason'] == 'insufficient_content':
                        stats['skipped_insufficient'] += 1
                    else:
                        stats['failed'] += 1
                
                stats['total_processed'] += 1
                
                # Rate limiting
                await asyncio.sleep(1)
                
            except Exception as e:
                self.log("ERROR", f"Failed processing {artifact.get('id')}: {e}")
                stats['failed'] += 1
        
        self.log("INFO", f"Processing complete: {stats}")
        return stats
    
    def _has_quality_wisdom(self, metadata: Dict) -> bool:
        """Check if artifact already has quality wisdom that meets NSF standards."""
        wisdom = metadata.get('extracted_wisdom')
        if not wisdom:
            return False
        
        # Check for fallback methods (these need to be redone with quality standards)
        method = wisdom.get('extraction_method', '')
        if 'fallback' in method:
            return False
        
        # Ensure all required fields are present and meaningful
        for field in self.quality_checks:
            if field not in wisdom:
                return False
            
            value = wisdom[field]
            if isinstance(value, list) and len(value) == 0:
                return False
            if isinstance(value, str) and len(value.strip()) < 10:
                return False
        
        # Check for minimum quality indicators
        if wisdom.get('relevance_score', 0) < 0.3:
            return False
        
        return True
    
    async def _enhance_content(self, artifact: Dict) -> bool:
        """Enhance content quality for NSF standards."""
        content = artifact.get('content', '')
        content_length = len(content)
        source_type = artifact.get('source_type', '')
        url = artifact.get('url', '')
        
        # Skip if content is already sufficient
        if content_length >= self.min_content_length:
            return False
        
        self.log("INFO", f"Enhancing content for {artifact['id']} (current: {content_length} chars)")
        
        enhanced_content = None
        
        try:
            if source_type == 'manual_youtube':
                enhanced_content = await self._extract_youtube_transcript(url)
            elif source_type == 'manual_url':
                enhanced_content = await self._scrape_web_content(url)
            elif source_type == 'manual_file':
                enhanced_content = await self._extract_file_content(artifact)
            elif url.startswith('http'):
                enhanced_content = await self._scrape_web_content(url)
        
            if enhanced_content and len(enhanced_content) > content_length + 100:
                # Update artifact with enhanced content
                updated_artifact = {
                    'id': artifact['id'],
                    'url': artifact.get('url', ''),
                    'title': artifact.get('title', ''),
                    'content': enhanced_content,
                    'source_type': artifact.get('source_type', ''),
                    'collected_at': artifact.get('collected_at'),
                    'metadata': json.loads(artifact.get('raw_metadata', '{}'))
                }
                
                # Add enhancement metadata
                updated_artifact['metadata']['content_enhanced'] = True
                updated_artifact['metadata']['enhancement_date'] = datetime.now().isoformat()
                updated_artifact['metadata']['original_length'] = content_length
                updated_artifact['metadata']['enhanced_length'] = len(enhanced_content)
                
                self.db.save_artifact(updated_artifact)
                self.log("INFO", f"Enhanced content: {content_length} → {len(enhanced_content)} chars")
                return True
        
        except Exception as e:
            self.log("WARNING", f"Content enhancement failed for {artifact['id']}: {e}")
        
        return False
    
    async def _extract_youtube_transcript(self, url: str) -> Optional[str]:
        """Extract transcript from YouTube video."""
        try:
            ydl_opts = {
                'writesubtitles': True,
                'writeautomaticsub': True,
                'subtitleslangs': ['en'],
                'skip_download': True,
                'quiet': True
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # Try to get subtitles
                subtitles = info.get('subtitles', {})
                auto_captions = info.get('automatic_captions', {})
                
                # Prefer manual subtitles, fallback to auto captions
                subs_data = subtitles.get('en') or auto_captions.get('en')
                
                if subs_data:
                    # Get the subtitle URL (usually first format)
                    sub_url = subs_data[0]['url']
                    
                    # Download subtitle content
                    async with aiohttp.ClientSession() as session:
                        async with session.get(sub_url) as response:
                            if response.status == 200:
                                sub_content = await response.text()
                                
                                # Parse subtitle format (usually VTT)
                                transcript = self._parse_subtitle_content(sub_content)
                                return transcript
        
        except Exception as e:
            self.log("WARNING", f"YouTube transcript extraction failed: {e}")
        
        return None
    
    def _parse_subtitle_content(self, content: str) -> str:
        """Parse subtitle content to extract clean text."""
        lines = content.split('\n')
        text_lines = []
        
        for line in lines:
            line = line.strip()
            # Skip timestamps and metadata
            if '-->' in line or line.startswith('WEBVTT') or line.isdigit():
                continue
            # Skip empty lines
            if not line:
                continue
            text_lines.append(line)
        
        return ' '.join(text_lines)
    
    async def _scrape_web_content(self, url: str) -> Optional[str]:
        """Scrape full content from web URL."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=15) as response:
                    if response.status == 200:
                        content = await response.text()
                        soup = BeautifulSoup(content, 'html.parser')
                        
                        # Remove script and style elements
                        for script in soup(["script", "style", "nav", "footer", "header"]):
                            script.decompose()
                        
                        # Try multiple content selectors
                        content_selectors = [
                            'article', '.article-content', '.post-content', '.content',
                            'main', '.story-body', '.entry-content', '.article-body',
                            '.post-body', '.blog-content', '.news-content'
                        ]
                        
                        extracted_content = ""
                        for selector in content_selectors:
                            content_elem = soup.select_one(selector)
                            if content_elem:
                                extracted_content = content_elem.get_text(separator=' ', strip=True)
                                break
                        
                        # Fallback to all paragraphs
                        if not extracted_content or len(extracted_content) < 300:
                            paragraphs = soup.find_all('p')
                            if paragraphs:
                                extracted_content = ' '.join([p.get_text(strip=True) for p in paragraphs])
                        
                        return extracted_content if len(extracted_content) > 200 else None
        
        except Exception as e:
            self.log("WARNING", f"Web scraping failed for {url}: {e}")
        
        return None
    
    async def _extract_file_content(self, artifact: Dict) -> Optional[str]:
        """Extract content from uploaded files."""
        try:
            metadata = json.loads(artifact.get('raw_metadata', '{}'))
            file_path = metadata.get('file_path')
            file_type = metadata.get('file_type', '').lower()
            
            if not file_path or not Path(file_path).exists():
                return None
            
            if file_type == 'pdf':
                return self._extract_pdf_content(file_path)
            elif file_type in ['docx', 'doc']:
                return self._extract_docx_content(file_path)
            elif file_type == 'txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
        
        except Exception as e:
            self.log("WARNING", f"File content extraction failed: {e}")
        
        return None
    
    def _extract_pdf_content(self, file_path: str) -> Optional[str]:
        """Extract text from PDF file."""
        try:
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text.strip()
        except Exception as e:
            self.log("WARNING", f"PDF extraction failed: {e}")
        return None
    
    def _extract_docx_content(self, file_path: str) -> Optional[str]:
        """Extract text from DOCX file."""
        try:
            doc = docx.Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        except Exception as e:
            self.log("WARNING", f"DOCX extraction failed: {e}")
        return None
    
    async def _extract_quality_wisdom(self, artifact: Dict) -> Dict:
        """Extract wisdom with NSF-quality standards."""
        content = artifact.get('content', '')
        content_length = len(content)
        
        # Check content sufficiency
        if content_length < self.min_content_length:
            return {
                'success': False,
                'reason': 'insufficient_content',
                'message': f'Content too short: {content_length} < {self.min_content_length} chars'
            }
        
        if not self.openai_client:
            return {
                'success': False,
                'reason': 'no_api_key',
                'message': 'OpenAI API key not configured'
            }
        
        try:
            title = artifact.get('title', 'Untitled')
            artifact_id = artifact.get('id')
            
            # Truncate content if too long
            max_content_length = 8000
            if content_length > max_content_length:
                content = content[:max_content_length] + "...[truncated for analysis]"
            
            # NSF-standard wisdom extraction prompt
            wisdom_prompt = f"""
You are an expert cybersecurity researcher conducting NSF-level analysis for career intelligence. Analyze this content with the highest academic standards.

Title: {title}

Content: {content}

Provide a comprehensive analysis as structured JSON with these REQUIRED fields:

{{
    "key_wisdom": ["5-7 most important insights with specific cybersecurity career implications"],
    "career_implications": ["3-4 detailed implications for cybersecurity career planning and development"],
    "actionable_takeaways": ["4-6 concrete, specific actions a cybersecurity professional could implement"],
    "future_outlook": "Detailed assessment of implications for cybersecurity field in 2025-2030",
    "skill_recommendations": ["3-5 specific technical and professional skills to develop"],
    "summary": "3-4 sentence executive summary capturing the core career-relevant message",
    "relevance_score": "0.0-1.0 (0.8+ for high career relevance)",
    "complexity_level": "beginner|intermediate|advanced",
    "industry_sectors": ["List of cybersecurity sectors most relevant to this content"],
    "technological_focus": ["Specific technologies, tools, or methodologies mentioned"]
}}

QUALITY REQUIREMENTS:
- Each insight must be specific and actionable
- Avoid generic advice - provide detailed, implementable guidance
- Focus on 2025 cybersecurity career landscape
- Include quantitative assessments where possible
- Cite specific skills, certifications, or technologies mentioned
- Ensure all fields are meaningful and substantial

Respond ONLY with valid JSON. No explanatory text outside the JSON structure.
"""
            
            self.log("INFO", f"Extracting wisdom for: {title[:50]}... ({content_length} chars)")
            
            response = await asyncio.to_thread(
                self.openai_client.chat.completions.create,
                model="gpt-4o",  # Use highest quality model for NSF standards
                messages=[
                    {"role": "system", "content": "You are an expert cybersecurity career research analyst. Provide detailed, research-quality analysis in valid JSON format. Ensure all insights are specific, actionable, and grounded in the content provided."},
                    {"role": "user", "content": wisdom_prompt}
                ],
                temperature=0.1,
                max_tokens=1200
            )
            
            raw_response = response.choices[0].message.content.strip()
            
            # Parse and validate response
            try:
                wisdom_data = json.loads(raw_response)
                
                # Quality validation
                validation_result = self._validate_wisdom_quality(wisdom_data, content_length)
                if not validation_result['valid']:
                    self.log("WARNING", f"Wisdom quality validation failed: {validation_result['reason']}")
                    return {
                        'success': False,
                        'reason': 'quality_validation_failed',
                        'message': validation_result['reason']
                    }
                
                # Add extraction metadata
                wisdom_data['extracted_at'] = datetime.now().isoformat()
                wisdom_data['extraction_method'] = 'openai_gpt4_nsf_quality'
                wisdom_data['content_length'] = content_length
                wisdom_data['quality_validated'] = True
                
                # Save wisdom to database
                metadata = json.loads(artifact.get('raw_metadata', '{}'))
                metadata['extracted_wisdom'] = wisdom_data
                metadata['wisdom_extracted_at'] = wisdom_data['extracted_at']
                
                updated_artifact = {
                    'id': artifact_id,
                    'url': artifact.get('url', ''),
                    'title': artifact.get('title', ''),
                    'content': artifact.get('content', ''),
                    'source_type': artifact.get('source_type', ''),
                    'collected_at': artifact.get('collected_at'),
                    'metadata': metadata
                }
                
                self.db.save_artifact(updated_artifact)
                
                # Track cost
                estimated_cost = 0.03  # GPT-4o cost estimate
                cost_tracker.track_api_call("openai", "gpt-4o", tokens=1200, custom_cost=estimated_cost)
                
                self.log("INFO", f"NSF-quality wisdom extracted for: {title[:50]}...")
                return {
                    'success': True,
                    'wisdom': wisdom_data,
                    'cost': estimated_cost
                }
                
            except json.JSONDecodeError as e:
                self.log("ERROR", f"JSON parsing failed for {artifact_id}: {e}")
                return {
                    'success': False,
                    'reason': 'json_parse_error',
                    'message': f'Invalid JSON response: {str(e)}'
                }
        
        except Exception as e:
            self.log("ERROR", f"Wisdom extraction failed for {artifact_id}: {e}")
            return {
                'success': False,
                'reason': 'extraction_error',
                'message': str(e)
            }
    
    def _validate_wisdom_quality(self, wisdom_data: Dict, content_length: int) -> Dict:
        """Validate wisdom meets NSF quality standards."""
        
        # Check all required fields are present
        for field in self.quality_checks:
            if field not in wisdom_data:
                return {'valid': False, 'reason': f'Missing required field: {field}'}
        
        # Check field quality
        key_wisdom = wisdom_data.get('key_wisdom', [])
        if not isinstance(key_wisdom, list) or len(key_wisdom) < 5:
            return {'valid': False, 'reason': 'Insufficient key wisdom insights (need 5+)'}
        
        career_implications = wisdom_data.get('career_implications', [])
        if not isinstance(career_implications, list) or len(career_implications) < 3:
            return {'valid': False, 'reason': 'Insufficient career implications (need 3+)'}
        
        actionable_takeaways = wisdom_data.get('actionable_takeaways', [])
        if not isinstance(actionable_takeaways, list) or len(actionable_takeaways) < 4:
            return {'valid': False, 'reason': 'Insufficient actionable takeaways (need 4+)'}
        
        # Check content substantiveness
        summary = wisdom_data.get('summary', '')
        if len(summary) < 100:
            return {'valid': False, 'reason': 'Summary too brief for NSF standards'}
        
        future_outlook = wisdom_data.get('future_outlook', '')
        if len(future_outlook) < 50:
            return {'valid': False, 'reason': 'Future outlook too brief'}
        
        # Check relevance score
        relevance_score = wisdom_data.get('relevance_score')
        try:
            score = float(relevance_score)
            if score < 0.5:
                return {'valid': False, 'reason': f'Relevance score too low: {score}'}
        except (ValueError, TypeError):
            return {'valid': False, 'reason': 'Invalid relevance score format'}
        
        return {'valid': True, 'reason': 'All quality checks passed'}

async def main():
    """Main processing function."""
    processor = ComprehensiveWisdomProcessor()
    
    print("🔬 Comprehensive Wisdom Processor - NSF Standards")
    print("=" * 60)
    
    try:
        # Process all entries
        stats = await processor.process_all_entries()
        
        print(f"\n✅ Processing Complete!")
        print(f"   Total processed: {stats['total_processed']}")
        print(f"   Content enhanced: {stats['content_enhanced']}")
        print(f"   Wisdom extracted: {stats['wisdom_extracted']}")
        print(f"   Failed: {stats['failed']}")
        print(f"   Insufficient content: {stats['skipped_insufficient']}")
        
        # Run final audit
        print(f"\n📊 Final Status Check:")
        os.system("python audit_wisdom_status.py")
        
    except Exception as e:
        print(f"❌ Processing failed: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 