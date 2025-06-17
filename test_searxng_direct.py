#!/usr/bin/env python3
"""
Test SearXNG Direct connector
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from aih.gather.searxng_direct import SearXNGDirectConnector
from aih.utils.logging import get_logger

logger = get_logger(__name__)

async def test_searxng_direct():
    """Test SearXNG Direct collection."""
    print("🧪 Testing SearXNG Direct Collection")
    print("=" * 50)
    
    try:
        # Initialize connector
        connector = SearXNGDirectConnector()
        print("✅ SearXNG Direct connector initialized")
        
        # Validate config
        if connector.validate_config():
            print("✅ SearXNG Direct configuration valid")
        else:
            print("❌ SearXNG Direct configuration invalid")
            return
        
        # Test collection
        print("\n🔍 Testing collection...")
        artifacts = await connector.collect(
            query="cybersecurity AI automation workforce",
            max_results=5,
            category="replace",
            timeframe="2024"
        )
        
        print(f"✅ Collection completed: {len(artifacts)} artifacts")
        
        # Display results
        for i, artifact in enumerate(artifacts):
            print(f"\n📄 Artifact {i+1}:")
            print(f"   Title: {artifact.title[:80]}...")
            print(f"   URL: {artifact.url}")
            print(f"   Source Type: {artifact.source_type}")
            print(f"   Content: {artifact.content[:200]}...")
        
        print(f"\n🎉 SearXNG Direct test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_searxng_direct()) 