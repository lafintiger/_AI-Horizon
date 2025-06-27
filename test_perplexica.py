#!/usr/bin/env python3
"""
Test Perplexica integration with AI-Horizon.

This script tests the connection to Perplexica running on localhost:3000
and validates that our connector can successfully interact with it.
"""

import asyncio
import json
import time
from datetime import datetime

import requests
from aih.config import validate_model_configuration
from aih.gather.perplexica import PerplexicaConnector
from aih.utils.logging import get_logger

logger = get_logger(__name__)

def test_perplexica_connectivity():
    """Test basic connectivity to Perplexica API."""
    print("🔍 Testing Perplexica connectivity...")
    
    try:
        # Test basic API endpoint
        response = requests.get("http://localhost:3000/api/search", timeout=10)
        
        # Expect 400 for GET without query (means API is working)
        if response.status_code == 400:
            print("✅ Perplexica API responding correctly")
            return True
        elif response.status_code == 200:
            print("✅ Perplexica API accessible")
            return True
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Perplexica at localhost:3000")
        print("   Ensure Perplexica is running: cd Perplexica && docker compose up -d")
        return False
    except Exception as e:
        print(f"❌ Error testing connectivity: {e}")
        return False

def test_perplexica_search():
    """Test a simple search request to Perplexica."""
    print("🔍 Testing Perplexica search API...")
    
    try:
        search_payload = {
            "query": "AI impact on cybersecurity jobs 2024",
            "history": [],
            "focus": "webSearch",
            "source": "web"
        }
        
        start_time = time.time()
        response = requests.post(
            "http://localhost:3000/api/search",
            json=search_payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"✅ Search completed in {elapsed:.2f}s")
            print(f"   Message length: {len(result.get('message', ''))}")
            print(f"   Sources: {len(result.get('sources', []))}")
            
            # Show preview of response
            message = result.get('message', '')
            if message:
                preview = message[:200] + "..." if len(message) > 200 else message
                print(f"   Preview: {preview}")
            
            return True
        else:
            print(f"❌ Search failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing search: {e}")
        return False

async def test_connector_integration():
    """Test our PerplexicaConnector class."""
    print("🔍 Testing PerplexicaConnector integration...")
    
    try:
        # Initialize connector
        connector = PerplexicaConnector()
        
        # Test validation
        if not connector.validate_config():
            print("❌ Connector validation failed")
            return False
        
        print("✅ Connector validation passed")
        
        # Test artifact collection
        print("   Collecting test artifacts...")
        start_time = time.time()
        
        artifacts = await connector.collect(
            query="cybersecurity workforce automation",
            max_results=3,
            category="replace",
            timeframe="2024"
        )
        
        elapsed = time.time() - start_time
        
        print(f"✅ Collected {len(artifacts)} artifacts in {elapsed:.2f}s")
        
        # Show artifact details
        for i, artifact in enumerate(artifacts[:2]):
            print(f"   Artifact {i+1}:")
            print(f"     Title: {artifact.title[:60]}...")
            print(f"     Source: {artifact.source}")
            print(f"     URL: {artifact.url}")
            print(f"     Content: {len(artifact.content)} chars")
            print(f"     Relevance: {artifact.relevance_score}")
        
        return True
        
    except Exception as e:
        print(f"❌ Connector integration failed: {e}")
        return False

async def test_multi_query():
    """Test multi-query functionality."""
    print("🔍 Testing multi-query collection...")
    
    try:
        connector = PerplexicaConnector()
        
        start_time = time.time()
        artifacts = await connector.collect_multi_query(
            category="augment",
            max_results=5,
            timeframe="2024"
        )
        elapsed = time.time() - start_time
        
        print(f"✅ Multi-query collected {len(artifacts)} artifacts in {elapsed:.2f}s")
        
        # Show unique sources
        sources = set(artifact.source for artifact in artifacts)
        print(f"   Unique sources: {sources}")
        
        return True
        
    except Exception as e:
        print(f"❌ Multi-query test failed: {e}")
        return False

def main():
    """Run all Perplexica tests."""
    print("🚀 AI-Horizon Perplexica Integration Test")
    print("=" * 50)
    
    # Check system status
    print("\n📊 System Status:")
    status = validate_model_configuration()
    print(f"   Use Local Models: {status['use_local_models']}")
    print(f"   Perplexica Available: {status.get('perplexica_available', 'Unknown')}")
    print(f"   Ollama Available: {status['ollama_available']}")
    
    if status.get('warnings'):
        print("   Warnings:")
        for warning in status['warnings']:
            print(f"     ⚠️ {warning}")
    
    # Run tests
    tests = [
        ("Connectivity", test_perplexica_connectivity),
        ("Search API", test_perplexica_search),
        ("Connector Integration", test_connector_integration),
        ("Multi-query", test_multi_query)
    ]
    
    results = {}
    
    print("\n🧪 Running Tests:")
    print("-" * 30)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = asyncio.run(test_func())
            else:
                result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print("\n📈 Test Results Summary:")
    print("=" * 50)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name:<20} {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Perplexica integration is working correctly.")
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
        
        # Provide helpful troubleshooting
        if not results.get("Connectivity", False):
            print("\n🔧 Troubleshooting:")
            print("   1. Ensure Perplexica is running:")
            print("      cd Perplexica && docker compose up -d")
            print("   2. Check if port 3000 is accessible:")
            print("      curl http://localhost:3000/api/search")
            print("   3. Verify Perplexica configuration includes Ollama URL")

if __name__ == "__main__":
    main() 