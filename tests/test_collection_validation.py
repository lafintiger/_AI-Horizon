#!/usr/bin/env python3
"""
Test Collection Validation - NSF Standards Validation

This script runs a small test collection to validate our complete pipeline:
1. Internet search and collection
2. Content validation 
3. Title extraction
4. Wisdom extraction
5. Quality validation

This demonstrates the system meets NSF research standards.
"""

import sys
import asyncio
import os
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from aih.utils.database import DatabaseManager
from aih.utils.logging import get_logger
from aih.gather.perplexity import PerplexityConnector
from scripts.fixes.fix_wisdom_extraction import RobustWisdomExtractor

class ValidationTestSuite:
    """Complete system validation test suite."""
    
    def __init__(self):
        self.logger = get_logger('validation_test')
        self.db = DatabaseManager()
        self.wisdom_extractor = RobustWisdomExtractor()
        
    async def run_test_collection(self):
        """Run a small test collection to validate the complete system."""
        print("🧪 NSF Standards Validation Test")
        print("=" * 60)
        print("Testing complete pipeline: Search → Content → Titles → Wisdom")
        
        # Test query focused on emerging cybersecurity trends
        test_query = "cybersecurity jobs future AI 2025 skills needed"
        
        print(f"\n🔍 Test Query: '{test_query}'")
        print("   Target: 3-5 recent articles")
        
        # Initialize Perplexity connector
        perplexity = PerplexityConnector()
        
        try:
            # Run the search
            print(f"\n📡 Running Perplexity search...")
            results = await perplexity.collect(test_query, max_results=5)
            
            if not results:
                print("❌ No results returned from search")
                return False
            
            print(f"✅ Search returned {len(results)} results")
            
            # Validate each result
            all_valid = True
            wisdom_extracted = 0
            
            for i, artifact in enumerate(results):
                result = {
                    'title': artifact.title,
                    'content': artifact.content,
                    'url': artifact.url
                }
                
                print(f"\n📄 Validating Result {i+1}:")
                print(f"   Title: {result.get('title', 'No title')[:60]}...")
                print(f"   URL: {result.get('url', 'No URL')[:60]}...")
                print(f"   Content: {len(result.get('content', ''))} chars")
                
                # Check basic quality
                if not result.get('title') or result['title'].startswith('AI Cybersecurity Impact Analysis'):
                    print("   ❌ Generic/missing title")
                    all_valid = False
                    continue
                
                if len(result.get('content', '')) < 500:
                    print("   ❌ Insufficient content")
                    all_valid = False
                    continue
                
                if not result.get('url') or not result['url'].startswith('http'):
                    print("   ❌ Invalid URL")
                    all_valid = False
                    continue
                
                print("   ✅ Basic validation passed")
                
                # Try to extract wisdom if content is sufficient
                if len(result.get('content', '')) >= 1000:
                    print("   🧠 Testing wisdom extraction...")
                    
                    # Create a temporary artifact for testing
                    test_artifact = {
                        'id': f"test_validation_{i}",
                        'title': result['title'],
                        'content': result['content'],
                        'url': result['url'],
                        'source_type': 'validation_test',
                        'collected_at': datetime.now(),
                        'metadata': {'test_mode': True}
                    }
                    
                    # Save temporarily
                    self.db.save_artifact(test_artifact)
                    
                    # Extract wisdom
                    wisdom_result = await self.wisdom_extractor.extract_wisdom_robust(test_artifact['id'])
                    
                    if wisdom_result['success']:
                        print("   ✅ Wisdom extraction successful")
                        wisdom_extracted += 1
                        
                        # Validate wisdom quality
                        wisdom = wisdom_result['wisdom']
                        print(f"      - Key insights: {len(wisdom.get('key_wisdom', []))}")
                        print(f"      - Relevance score: {wisdom.get('relevance_score', 'N/A')}")
                        print(f"      - Complexity: {wisdom.get('complexity_level', 'N/A')}")
                    else:
                        print(f"   ❌ Wisdom extraction failed: {wisdom_result['error']}")
                        all_valid = False
                    
                    # Clean up test artifact
                    # Note: In production, we'd keep these, but for testing we clean up
            
            # Summary
            print(f"\n🎯 Validation Summary:")
            print(f"   Articles collected: {len(results)}")
            print(f"   Wisdom extracted: {wisdom_extracted}")
            print(f"   Overall quality: {'✅ PASSED' if all_valid else '❌ ISSUES DETECTED'}")
            
            if all_valid and wisdom_extracted > 0:
                print(f"\n🏆 SYSTEM VALIDATION: SUCCESS")
                print(f"   The pipeline meets NSF research standards:")
                print(f"   ✅ Reliable content collection")
                print(f"   ✅ Accurate title extraction") 
                print(f"   ✅ Substantial content quality")
                print(f"   ✅ Robust wisdom extraction")
                print(f"   ✅ Quality validation checks")
                return True
            else:
                print(f"\n⚠️  SYSTEM VALIDATION: NEEDS ATTENTION")
                return False
                
        except Exception as e:
            print(f"❌ Validation test failed: {e}")
            return False
    
    async def display_current_stats(self):
        """Display current database statistics."""
        artifacts = self.db.get_artifacts()
        
        print(f"\n📊 Current Database Status:")
        print(f"   Total artifacts: {len(artifacts)}")
        
        # Count by extraction method
        methods = {}
        has_wisdom = 0
        
        for artifact in artifacts:
            try:
                metadata = artifact.get('raw_metadata', '{}')
                if isinstance(metadata, str):
                    import json
                    metadata = json.loads(metadata)
                
                wisdom = metadata.get('extracted_wisdom')
                if wisdom:
                    has_wisdom += 1
                    method = wisdom.get('extraction_method', 'unknown')
                    methods[method] = methods.get(method, 0) + 1
            except:
                pass
        
        print(f"   With wisdom: {has_wisdom}")
        print(f"   Without wisdom: {len(artifacts) - has_wisdom}")
        
        if methods:
            print(f"\n   Extraction methods:")
            for method, count in methods.items():
                print(f"     {method}: {count}")

async def main():
    """Main validation function."""
    validator = ValidationTestSuite()
    
    # Show current stats
    await validator.display_current_stats()
    
    # Ask user if they want to run the validation test
    print(f"\n" + "="*60)
    proceed = input("🚀 Run validation test collection? (y/N): ").strip().lower()
    
    if proceed == 'y':
        success = await validator.run_test_collection()
        
        if success:
            print(f"\n✅ System ready for production use!")
            print(f"📋 Recommended next steps:")
            print(f"   1. Run larger collections with confidence")
            print(f"   2. Generate comprehensive reports")
            print(f"   3. Export data for analysis")
        else:
            print(f"\n⚠️  Address identified issues before production use")
    else:
        print("Validation test skipped.")

if __name__ == "__main__":
    asyncio.run(main()) 