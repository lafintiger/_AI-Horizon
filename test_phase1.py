#!/usr/bin/env python3
"""
Test script for AI-Horizon Phase 1 implementation.

This script validates the core components without requiring API keys.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all core modules can be imported."""
    print("🧪 Testing imports...")
    
    try:
        from aih.config import settings, AI_IMPACT_CATEGORIES
        print("  ✅ Config module imported")
        
        from aih.utils.logging import get_logger
        from aih.utils.database import DatabaseManager
        from aih.utils.rate_limiter import RateLimiter
        print("  ✅ Utils modules imported")
        
        from aih.gather.base import BaseConnector, Artifact
        from aih.gather.perplexity import PerplexityConnector
        print("  ✅ Gather modules imported")
        
        from aih.classify.classifier import ArtifactClassifier
        from aih.classify.scorer import SourceScorer
        print("  ✅ Classify modules imported")
        
        from aih.cli import main
        print("  ✅ CLI module imported")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Import failed: {e}")
        return False

def test_database():
    """Test database functionality."""
    print("\n🗄️  Testing database...")
    
    try:
        from aih.utils.database import DatabaseManager
        from datetime import datetime
        
        # Create test database in memory
        db = DatabaseManager(db_path=":memory:")
        print("  ✅ Database initialized")
        
        # Test artifact insertion
        test_artifact = {
            'id': 'test_artifact_1',
            'url': 'https://example.com/test',
            'title': 'Test AI Cybersecurity Article',
            'content': 'This is a test article about AI impact on cybersecurity jobs.',
            'source_type': 'test',
            'collected_at': datetime.now(),
            'metadata': {'test': True}
        }
        
        artifact_id = db.save_artifact(test_artifact)
        print("  ✅ Artifact saved")
        
        # Test artifact retrieval
        retrieved = db.get_artifact_by_id(artifact_id)
        if retrieved is None:
            print("  ❌ Failed to retrieve artifact")
            return False
            
        if retrieved['title'] != test_artifact['title']:
            print("  ❌ Retrieved artifact has wrong title")
            return False
            
        print("  ✅ Artifact retrieved")
        
        # Test getting all artifacts
        all_artifacts = db.get_artifacts()
        if len(all_artifacts) != 1:
            print("  ❌ Wrong number of artifacts retrieved")
            return False
            
        print("  ✅ Artifact listing works")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config():
    """Test configuration system."""
    print("\n⚙️  Testing configuration...")
    
    try:
        from aih.config import settings, get_data_path, AI_IMPACT_CATEGORIES
        
        # Test path creation
        data_path = get_data_path("test")
        if not data_path.exists():
            print("  ❌ Data path was not created")
            return False
        print("  ✅ Data path creation works")
        
        # Test categories
        if len(AI_IMPACT_CATEGORIES) != 4:
            print("  ❌ Wrong number of AI impact categories")
            return False
            
        required_categories = ['replace', 'augment', 'new_tasks', 'human_only']
        for cat in required_categories:
            if cat not in AI_IMPACT_CATEGORIES:
                print(f"  ❌ Missing category: {cat}")
                return False
                
        print("  ✅ AI impact categories defined")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Config test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 AI-Horizon Phase 1 Implementation Test")
    print("=" * 50)
    
    tests = [test_imports, test_config, test_database]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Phase 1 implementation is working correctly.")
        print("\n📋 Next steps:")
        print("1. Copy env.example to .env and add your API keys")
        print("2. Install in development mode: pip install -e .")
        print("3. Test data collection: aih collect --query 'AI cybersecurity jobs' --max-results 3")
        print("4. Test classification: aih classify --limit 3")
        print("5. Check status: aih status")
    else:
        print("❌ Some tests failed. Please check the errors above.")

if __name__ == "__main__":
    main() 