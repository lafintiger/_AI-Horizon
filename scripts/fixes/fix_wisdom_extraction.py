#!/usr/bin/env python3
"""
Fix Wisdom Extraction - Robust JSON handling and API debugging

This script diagnoses and fixes the JSON parsing issues with OpenAI API responses.
"""

import sys
import json
import asyncio
import os
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from aih.utils.database import DatabaseManager
from aih.utils.logging import get_logger
from aih.utils.cost_tracker import cost_tracker
import openai

class RobustWisdomExtractor:
    """Robust wisdom extraction with enhanced error handling."""
    
    def __init__(self):
        self.logger = get_logger('wisdom_fix')
        self.db = DatabaseManager()
        
        # OpenAI setup with error handling
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        self.client = openai.OpenAI(api_key=api_key)
        
    async def test_openai_connection(self):
        """Test OpenAI API connection and response format."""
        print("🔧 Testing OpenAI API Connection...")
        
        try:
            # Simple test query
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant. Respond with valid JSON only."},
                    {"role": "user", "content": 'Respond with this exact JSON: {"test": "success", "status": "working"}'}
                ],
                temperature=0,
                max_tokens=100
            )
            
            raw_response = response.choices[0].message.content.strip()
            print(f"Raw API Response: '{raw_response}'")
            
            # Try to parse JSON
            try:
                parsed = json.loads(raw_response)
                print(f"✅ JSON Parsing Success: {parsed}")
                return True
            except json.JSONDecodeError as e:
                print(f"❌ JSON Parsing Failed: {e}")
                print(f"Response length: {len(raw_response)}")
                print(f"First 200 chars: {repr(raw_response[:200])}")
                return False
                
        except Exception as e:
            print(f"❌ OpenAI API Error: {e}")
            return False
    
    def clean_json_response(self, response: str) -> str:
        """Clean and extract JSON from OpenAI response."""
        # Remove common prefixes/suffixes
        response = response.strip()
        
        # Remove markdown code blocks
        if response.startswith('```json'):
            response = response[7:]
        if response.startswith('```'):
            response = response[3:]
        if response.endswith('```'):
            response = response[:-3]
        
        # Find JSON content between braces
        start = response.find('{')
        end = response.rfind('}')
        
        if start != -1 and end != -1 and end > start:
            response = response[start:end+1]
        
        return response.strip()
    
    async def extract_wisdom_robust(self, artifact_id: str) -> dict:
        """Extract wisdom with robust error handling and JSON parsing."""
        artifact = self.db.get_artifact_by_id(artifact_id)
        if not artifact:
            return {'success': False, 'error': 'Artifact not found'}
        
        content = artifact.get('content', '')
        title = artifact.get('title', 'Untitled')
        
        if len(content) < 500:
            return {'success': False, 'error': 'Content too short for analysis'}
        
        # Truncate content if too long
        max_length = 6000
        if len(content) > max_length:
            content = content[:max_length] + "...[truncated]"
        
        print(f"\n🧠 Extracting wisdom for: {title[:60]}...")
        print(f"   Content length: {len(content)} characters")
        
        # Simple, reliable prompt that focuses on JSON structure
        prompt = f"""
Analyze this cybersecurity content for career intelligence. Respond with ONLY valid JSON.

Title: {title}
Content: {content}

Required JSON structure:
{{
    "key_wisdom": ["insight 1", "insight 2", "insight 3", "insight 4", "insight 5"],
    "career_implications": ["implication 1", "implication 2", "implication 3"],
    "actionable_takeaways": ["action 1", "action 2", "action 3", "action 4"],
    "future_outlook": "Assessment of cybersecurity field trends and implications",
    "skill_recommendations": ["skill 1", "skill 2", "skill 3"],
    "summary": "Executive summary of key career-relevant insights",
    "relevance_score": 0.8,
    "complexity_level": "intermediate"
}}

CRITICAL: Respond ONLY with the JSON object. No explanatory text before or after.
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a cybersecurity career analyst. Always respond with valid JSON only. Never include explanatory text outside the JSON structure."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=800
            )
            
            raw_response = response.choices[0].message.content.strip()
            print(f"   Raw response length: {len(raw_response)}")
            print(f"   First 100 chars: {repr(raw_response[:100])}")
            
            # Clean and parse JSON
            cleaned_response = self.clean_json_response(raw_response)
            print(f"   Cleaned response length: {len(cleaned_response)}")
            
            try:
                wisdom_data = json.loads(cleaned_response)
                
                # Validate required fields
                required_fields = ['key_wisdom', 'career_implications', 'actionable_takeaways', 
                                 'future_outlook', 'skill_recommendations', 'summary', 
                                 'relevance_score', 'complexity_level']
                
                for field in required_fields:
                    if field not in wisdom_data:
                        return {'success': False, 'error': f'Missing field: {field}'}
                
                # Add metadata
                wisdom_data['extracted_at'] = datetime.now().isoformat()
                wisdom_data['extraction_method'] = 'openai_gpt4_robust_fixed'
                wisdom_data['content_length'] = len(content)
                
                # Save to database
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
                
                print(f"   ✅ Wisdom extracted successfully!")
                return {'success': True, 'wisdom': wisdom_data}
                
            except json.JSONDecodeError as e:
                print(f"   ❌ JSON parsing failed: {e}")
                print(f"   Raw response: {repr(raw_response)}")
                print(f"   Cleaned response: {repr(cleaned_response)}")
                return {'success': False, 'error': f'JSON parsing failed: {e}', 'raw_response': raw_response}
                
        except Exception as e:
            print(f"   ❌ API call failed: {e}")
            return {'success': False, 'error': f'API call failed: {e}'}
    
    async def process_entries_needing_wisdom(self):
        """Process all entries that need wisdom extraction."""
        # Get entries with sufficient content but no wisdom
        artifacts = self.db.get_artifacts()
        
        needs_wisdom = []
        for artifact in artifacts:
            metadata = json.loads(artifact.get('raw_metadata', '{}'))
            content = artifact.get('content', '')
            
            # Skip if already has wisdom
            if metadata.get('extracted_wisdom'):
                continue
            
            # Only process entries with sufficient content
            if len(content) >= 500:
                needs_wisdom.append(artifact)
        
        print(f"\n📋 Found {len(needs_wisdom)} entries needing wisdom extraction")
        
        if not needs_wisdom:
            print("✅ All entries already have wisdom extracted!")
            return
        
        # Show what we'll process
        for i, artifact in enumerate(needs_wisdom[:10]):
            title = artifact.get('title', 'Untitled')[:50]
            content_len = len(artifact.get('content', ''))
            print(f"{i+1:2d}. {title}... ({content_len:,} chars)")
        
        if len(needs_wisdom) > 10:
            print(f"    ... and {len(needs_wisdom) - 10} more")
        
        proceed = input(f"\n🚀 Process {len(needs_wisdom)} entries? (y/N): ").strip().lower()
        if proceed != 'y':
            print("Cancelled.")
            return
        
        # Process entries
        successful = 0
        failed = 0
        
        for i, artifact in enumerate(needs_wisdom):
            print(f"\n📊 Processing {i+1}/{len(needs_wisdom)}")
            
            result = await self.extract_wisdom_robust(artifact['id'])
            
            if result['success']:
                successful += 1
            else:
                failed += 1
                print(f"   ❌ Failed: {result['error']}")
            
            # Rate limiting
            await asyncio.sleep(2)
        
        print(f"\n🎯 Processing Complete!")
        print(f"   ✅ Successful: {successful}")
        print(f"   ❌ Failed: {failed}")
        
        # Final audit
        print(f"\n📊 Running final audit...")
        os.system("python audit_wisdom_status.py")

async def main():
    """Main function."""
    extractor = RobustWisdomExtractor()
    
    print("🔬 Robust Wisdom Extraction Fix")
    print("=" * 50)
    
    # First test the API connection
    api_working = await extractor.test_openai_connection()
    
    if not api_working:
        print("\n❌ OpenAI API issues detected. Please check your API key and connection.")
        return
    
    # Process entries needing wisdom
    await extractor.process_entries_needing_wisdom()

if __name__ == "__main__":
    asyncio.run(main()) 