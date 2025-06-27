#!/usr/bin/env python3
"""
Manual Entry Processor

Processes manually added content (URLs, files, YouTube videos) with:
- YouTube transcript extraction
- AI-powered categorization
- Content quality analysis
- Proper metadata enrichment
"""

import sys
import json
import time
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse, parse_qs

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from aih.utils.database import DatabaseManager
from aih.utils.logging import get_logger
from aih.utils.cost_tracker import cost_tracker

logger = get_logger(__name__)

class ManualEntryProcessor:
    """Processes manual entries with AI categorization and content analysis."""
    
    def __init__(self):
        self.db = DatabaseManager()
        
        # Initialize OpenAI client if available
        self.openai_client = None
        try:
            import openai
            import os
            from dotenv import load_dotenv
            
            # Load environment variables from config.env with override
            load_dotenv('config.env', override=True)
            
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key and not api_key.startswith('your_'):
                self.openai_client = openai.OpenAI(api_key=api_key)
                logger.info("OpenAI client initialized")
            else:
                logger.warning("OpenAI API key not found or is placeholder value")
        except ImportError:
            logger.warning("OpenAI not available - falling back to keyword classification")
        except Exception as e:
            logger.warning(f"OpenAI initialization failed: {e}")
    
    def extract_youtube_transcript(self, url: str) -> Optional[str]:
        """Extract transcript from YouTube video."""
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            
            # Extract video ID
            video_id = self._extract_youtube_id(url)
            if not video_id:
                logger.error(f"Could not extract video ID from URL: {url}")
                return None
            
            logger.info(f"Extracting transcript for video ID: {video_id}")
            
            # Try to get transcript
            try:
                transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
                
                # Combine transcript segments
                full_transcript = ' '.join([segment['text'] for segment in transcript_list])
                
                logger.info(f"Successfully extracted transcript: {len(full_transcript)} characters")
                return full_transcript
                
            except Exception as e:
                # Try auto-generated captions
                logger.warning(f"Manual transcript failed, trying auto-generated: {e}")
                transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['en-US', 'en'])
                full_transcript = ' '.join([segment['text'] for segment in transcript_list])
                
                logger.info(f"Successfully extracted auto-generated transcript: {len(full_transcript)} characters")
                return full_transcript
                
        except Exception as e:
            logger.error(f"YouTube transcript extraction failed: {e}")
            return None
    
    def _extract_youtube_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID from URL."""
        try:
            parsed = urlparse(url)
            if 'youtu.be' in parsed.netloc:
                return parsed.path[1:]
            elif 'youtube.com' in parsed.netloc:
                if 'watch' in parsed.path:
                    return parse_qs(parsed.query).get('v', [None])[0]
                elif 'embed' in parsed.path:
                    return parsed.path.split('/')[2]
        except Exception as e:
            logger.error(f"Error extracting YouTube ID: {e}")
        return None
    
    def ai_categorize_content(self, title: str, content: str) -> Tuple[Dict, float, Dict]:
        """Use AI to categorize content into multiple categories with confidence scoring."""
        if not self.openai_client:
            return self._keyword_categorize_multi(title, content)
        
        try:
            # Prepare content for analysis (truncate if too long)
            analysis_content = content[:4000] if len(content) > 4000 else content
            
            prompt = f"""
Analyze this cybersecurity content for AI workforce impact across ALL relevant categories.

Title: {title}

Content: {analysis_content}

Evaluate EACH category and provide confidence scores (0.0-1.0) with supporting evidence:

1. REPLACE: Tasks that AI can perform completely autonomously, replacing human workers
2. AUGMENT: Tasks where AI enhances human capabilities but requires human oversight  
3. NEW_TASKS: New roles and responsibilities created by AI adoption in cybersecurity
4. HUMAN_ONLY: Tasks that remain fundamentally human due to complexity or ethics

Provide comprehensive analysis as JSON:
{{
    "categories": {{
        "replace": {{
            "confidence": 0.0-1.0,
            "evidence": ["specific quote or finding 1", "specific quote or finding 2"],
            "key_tasks": ["specific task 1", "specific task 2"]
        }},
        "augment": {{
            "confidence": 0.0-1.0,
            "evidence": ["specific quote or finding 1", "specific quote or finding 2"],
            "key_tasks": ["specific task 1", "specific task 2"]
        }},
        "new_tasks": {{
            "confidence": 0.0-1.0,
            "evidence": ["specific quote or finding 1", "specific quote or finding 2"],
            "key_roles": ["specific role 1", "specific role 2"]
        }},
        "human_only": {{
            "confidence": 0.0-1.0,
            "evidence": ["specific quote or finding 1", "specific quote or finding 2"],
            "key_tasks": ["specific task 1", "specific task 2"]
        }}
    }},
    "primary_focus": "replace|augment|new_tasks|human_only",
    "overall_relevance": 0.0-1.0,
    "actionability_for_students": 0.0-1.0,
    "summary": "One sentence summary of key workforce insight"
}}

Only include categories with confidence >= 0.3. Focus on specific, actionable insights for cybersecurity students.
"""
            
            logger.info("Sending content to OpenAI for multi-category analysis")
            start_time = time.time()
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert cybersecurity workforce analyst specializing in AI impact assessment. Provide detailed, evidence-based analysis for career planning."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=800
            )
            
            # Track cost
            duration = time.time() - start_time
            estimated_cost = 0.015  # Slightly higher for more detailed analysis
            cost_tracker.track_api_call("openai", "gpt-4o-mini", tokens=1200, custom_cost=estimated_cost)
            
            # Parse response
            try:
                result = json.loads(response.choices[0].message.content)
                categories = result.get('categories', {})
                
                # Filter categories by confidence threshold
                filtered_categories = {
                    cat: data for cat, data in categories.items() 
                    if data.get('confidence', 0) >= 0.3
                }
                
                # Calculate overall confidence (average of significant categories)
                if filtered_categories:
                    overall_confidence = sum(data['confidence'] for data in filtered_categories.values()) / len(filtered_categories)
                else:
                    overall_confidence = 0.3
                
                analysis_details = {
                    'primary_focus': result.get('primary_focus', 'augment'),
                    'overall_relevance': result.get('overall_relevance', 0.5),
                    'actionability_for_students': result.get('actionability_for_students', 0.5),
                    'summary': result.get('summary', 'Cybersecurity workforce analysis'),
                    'processing_method': 'openai_gpt4_multi',
                    'processing_time': duration,
                    'categories_analyzed': len(categories),
                    'significant_categories': len(filtered_categories)
                }
                
                logger.info(f"Multi-category analysis complete: {len(filtered_categories)} significant categories found")
                return filtered_categories, overall_confidence, analysis_details
                
            except json.JSONDecodeError:
                logger.error("Failed to parse AI response as JSON")
                return self._keyword_categorize_multi(title, content)
                
        except Exception as e:
            logger.error(f"AI categorization failed: {e}")
            return self._keyword_categorize_multi(title, content)
    
    def _keyword_categorize_multi(self, title: str, content: str) -> Tuple[Dict, float, Dict]:
        """Fallback keyword-based multi-category categorization."""
        combined_text = f"{title.lower()} {content.lower()}"
        
        category_keywords = {
            'replace': ['replace', 'automat', 'eliminat', 'job loss', 'redundant', 'obsolete', 'displaced'],
            'augment': ['assist', 'enhance', 'tool', 'help', 'support', 'improve', 'augment', 'collaboration'],
            'new_tasks': ['new job', 'opportunit', 'creat', 'emergi', 'novel', 'demand', 'ai engineer', 'mlsecops'],
            'human_only': ['human only', 'expert', 'judgment', 'creativ', 'oversight', 'strategy', 'ethics', 'leadership']
        }
        
        categories = {}
        for category, keywords in category_keywords.items():
            matches = [keyword for keyword in keywords if keyword in combined_text]
            if matches:
                confidence = min(len(matches) / 5, 1.0)  # Normalize confidence
                categories[category] = {
                    'confidence': confidence,
                    'evidence': [f'Contains keyword: {match}' for match in matches[:3]],
                    'key_tasks': [f'Tasks related to {match}' for match in matches[:2]]
                }
        
        # Ensure at least one category
        if not categories:
            categories['augment'] = {
                'confidence': 0.4,
                'evidence': ['General cybersecurity content'],
                'key_tasks': ['General cybersecurity tasks']
            }
        
        overall_confidence = max(cat['confidence'] for cat in categories.values())
        
        analysis_details = {
            'primary_focus': max(categories.keys(), key=lambda k: categories[k]['confidence']),
            'overall_relevance': 0.6,
            'actionability_for_students': 0.5,
            'summary': f'Keyword-based analysis found {len(categories)} relevant categories',
            'processing_method': 'keyword_fallback_multi',
            'categories_analyzed': len(category_keywords),
            'significant_categories': len(categories)
        }
        
        return categories, overall_confidence, analysis_details
    
    def analyze_content_quality(self, content: str, source_type: str) -> Dict:
        """Analyze content quality and generate quality metrics."""
        
        # Basic quality metrics
        word_count = len(content.split())
        char_count = len(content)
        
        # Content quality scoring
        quality_score = 0.0
        
        # Length scoring (optimal 300-3000 words)
        if 300 <= word_count <= 3000:
            length_score = 1.0
        elif word_count < 300:
            length_score = word_count / 300
        else:
            length_score = max(0.5, 3000 / word_count)
        
        quality_score += length_score * 0.4
        
        # Technical depth (cybersecurity keywords)
        tech_keywords = [
            'security', 'cybersecurity', 'vulnerability', 'threat', 'attack', 'defense',
            'firewall', 'encryption', 'malware', 'phishing', 'siem', 'soc', 'incident',
            'compliance', 'risk', 'penetration', 'authentication', 'authorization'
        ]
        
        content_lower = content.lower()
        tech_density = sum(1 for keyword in tech_keywords if keyword in content_lower) / len(tech_keywords)
        quality_score += min(tech_density * 2, 1.0) * 0.3
        
        # Source type bonus
        source_bonus = {
            'manual_youtube': 0.8,  # Video content
            'manual_url': 0.9,      # Web articles
            'manual_file': 1.0      # Documents
        }.get(source_type, 0.7)
        
        quality_score += source_bonus * 0.3
        
        return {
            'quality_score': min(quality_score, 1.0),
            'word_count': word_count,
            'char_count': char_count,
            'length_score': length_score,
            'tech_density': tech_density,
            'source_bonus': source_bonus,
            'content_metrics': {
                'has_substantial_content': word_count >= 100,
                'technical_relevance': tech_density > 0.1,
                'appropriate_length': 100 <= word_count <= 5000
            }
        }
    
    def process_entry(self, artifact_id: str, status_tracker=None) -> Dict:
        """Process a single manual entry with full AI analysis."""
        try:
            if status_tracker:
                status_tracker.add_log("INFO", f"Processing entry: {artifact_id}", "PROCESSING")
            
            # Get artifact from database
            artifact = self.db.get_artifact_by_id(artifact_id)
            if not artifact:
                raise ValueError(f"Artifact not found: {artifact_id}")
            
            # Check if already processed
            metadata = json.loads(artifact.get('raw_metadata', '{}'))
            if metadata.get('ai_impact_category'):
                return {
                    'status': 'already_processed',
                    'category': metadata['ai_impact_category'],
                    'processed_at': metadata.get('processed_at')
                }
            
            original_content = artifact.get('content', '')
            title = artifact.get('title', '')
            source_type = artifact.get('source_type', '')
            
            # Enhanced content extraction
            enhanced_content = original_content
            
            # YouTube transcript extraction
            if source_type == 'manual_youtube' and artifact.get('url'):
                if status_tracker:
                    status_tracker.add_log("INFO", f"Extracting YouTube transcript for {artifact_id}", "PROCESSING")
                
                transcript = self.extract_youtube_transcript(artifact['url'])
                if transcript:
                    enhanced_content = f"{original_content}\n\nTranscript:\n{transcript}"
                    if status_tracker:
                        status_tracker.add_log("INFO", f"Transcript extracted: {len(transcript)} characters", "PROCESSING")
                else:
                    if status_tracker:
                        status_tracker.add_log("WARNING", f"Could not extract transcript for {artifact_id}", "PROCESSING")
            
            # AI categorization
            if status_tracker:
                status_tracker.add_log("INFO", f"Running AI categorization for {artifact_id}", "PROCESSING")
            
            categories, overall_confidence, analysis_details = self.ai_categorize_content(title, enhanced_content)
            
            # Content quality analysis
            quality_metrics = self.analyze_content_quality(enhanced_content, source_type)
            
            # Update metadata with multi-category AI analysis
            # For backward compatibility, set primary category as ai_impact_category
            primary_category = analysis_details.get('primary_focus', 'augment')
            
            updated_metadata = {
                **metadata,  # Preserve existing metadata
                'ai_impact_category': primary_category,  # Backward compatibility
                'ai_impact_categories': categories,      # NEW: Multi-category data
                'confidence_score': overall_confidence,
                'processed_at': datetime.now().isoformat(),
                'processing_method': analysis_details.get('processing_method', 'unknown'),
                'analysis_details': analysis_details,
                'quality_metrics': quality_metrics,
                'enhanced_content': len(enhanced_content) > len(original_content)
            }
            
            # Update artifact with enhanced content and metadata
            updated_artifact = {
                **artifact,
                'content': enhanced_content,
                'metadata': updated_metadata
            }
            
            # Save updated artifact
            self.db.save_artifact(updated_artifact)
            
            if status_tracker:
                status_tracker.add_log("INFO", f"Successfully processed {artifact_id} -> {categories.get('replace', 'AUGMENT')} (confidence: {overall_confidence:.2f})", "PROCESSING")
            
            return {
                'status': 'processed',
                'artifact_id': artifact_id,
                'category': categories.get('replace', 'AUGMENT'),
                'confidence': overall_confidence,
                'quality_score': quality_metrics['quality_score'],
                'word_count': quality_metrics['word_count'],
                'processing_method': analysis_details.get('processing_method'),
                'key_insights': analysis_details.get('key_tasks', [])
            }
            
        except Exception as e:
            logger.error(f"Error processing entry {artifact_id}: {e}")
            if status_tracker:
                status_tracker.add_log("ERROR", f"Failed to process {artifact_id}: {e}", "PROCESSING")
            raise
    
    def process_multiple_entries(self, artifact_ids: List[str], status_tracker=None) -> Dict:
        """Process multiple entries with progress tracking."""
        total_count = len(artifact_ids)
        processed_results = []
        failed_count = 0
        
        if status_tracker:
            status_tracker.add_log("INFO", f"Starting batch processing of {total_count} entries", "PROCESSING")
        
        for i, artifact_id in enumerate(artifact_ids):
            try:
                if status_tracker:
                    status_tracker.update_progress(i, total_count, f"Processing {artifact_id}")
                
                result = self.process_entry(artifact_id, status_tracker)
                processed_results.append(result)
                
                # Small delay to prevent overwhelming APIs
                import time
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Failed to process {artifact_id}: {e}")
                failed_count += 1
                processed_results.append({
                    'status': 'failed',
                    'artifact_id': artifact_id,
                    'error': str(e)
                })
        
        if status_tracker:
            status_tracker.update_progress(total_count, total_count, "Processing complete")
            status_tracker.add_log("INFO", f"Batch processing complete: {len(processed_results) - failed_count} successful, {failed_count} failed", "PROCESSING")
        
        return {
            'total_processed': len(processed_results),
            'successful': len(processed_results) - failed_count,
            'failed': failed_count,
            'results': processed_results
        }

# Main functions for API integration
def process_single_entry(artifact_id: str, status_tracker=None) -> Dict:
    """Process a single manual entry."""
    processor = ManualEntryProcessor()
    return processor.process_entry(artifact_id, status_tracker)

def process_multiple_entries(artifact_ids: List[str], status_tracker=None) -> Dict:
    """Process multiple manual entries."""
    processor = ManualEntryProcessor()
    return processor.process_multiple_entries(artifact_ids, status_tracker)

def process_all_unprocessed_entries(status_tracker=None) -> Dict:
    """Process all unprocessed manual entries."""
    try:
        db = DatabaseManager()
        artifacts = db.get_artifacts(limit=500)
        
        # Find unprocessed manual entries
        unprocessed_ids = []
        for artifact in artifacts:
            if artifact.get('source_type', '').startswith('manual_'):
                metadata = json.loads(artifact.get('raw_metadata', '{}'))
                if not metadata.get('ai_impact_category'):
                    unprocessed_ids.append(artifact['id'])
        
        if not unprocessed_ids:
            return {
                'total_processed': 0,
                'successful': 0,
                'failed': 0,
                'message': 'No unprocessed entries found'
            }
        
        return process_multiple_entries(unprocessed_ids, status_tracker)
        
    except Exception as e:
        logger.error(f"Error in process_all_unprocessed_entries: {e}")
        raise

# Synchronous versions for Flask background threads (now just aliases since main functions are synchronous)
def process_single_entry_sync(artifact_id: str, status_tracker=None) -> Dict:
    """Process a single manual entry (synchronous version)."""
    return process_single_entry(artifact_id, status_tracker)

def process_multiple_entries_sync(artifact_ids: List[str], status_tracker=None) -> Dict:
    """Process multiple manual entries (synchronous version)."""
    return process_multiple_entries(artifact_ids, status_tracker)

def process_all_unprocessed_entries_sync(status_tracker=None) -> Dict:
    """Process all unprocessed manual entries (synchronous version)."""
    return process_all_unprocessed_entries(status_tracker)

if __name__ == "__main__":
    # Test processing
    processor = ManualEntryProcessor()
    
    # Test YouTube transcript extraction
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Roll for testing
    transcript = processor.extract_youtube_transcript(test_url)
    print(f"Transcript extracted: {len(transcript) if transcript else 0} characters")
    
    # Test AI categorization
    test_title = "AI-Powered Cybersecurity Tools"
    test_content = "This video discusses how artificial intelligence is transforming cybersecurity by automating threat detection and enhancing analyst capabilities."
    
    categories, overall_confidence, details = processor.ai_categorize_content(test_title, test_content)
    print(f"Categorization: {categories.get('replace', 'AUGMENT')} (confidence: {overall_confidence})")
    print(f"Details: {details}") 