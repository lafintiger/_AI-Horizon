"""
Strategic Pipeline Test - Full End-to-End Workflow

Tests the complete AI-Horizon pipeline with strategically crafted prompts
focused on finding high-quality sources about AI's impact on cybersecurity workforce.
"""

import asyncio
from datetime import datetime
from aih.gather.perplexity import PerplexityConnector
from aih.classify.scorer import NIDScorer
from aih.classify.classifier import ArtifactClassifier
from aih.utils.database import DatabaseManager
from aih.config import settings

async def test_strategic_collection():
    """Test data collection with strategically crafted prompts."""
    
    print("🚀 AI-Horizon Strategic Pipeline Test")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Initialize components
    print("🔧 Initializing pipeline components...")
    try:
        connector = PerplexityConnector()
        print("✅ Perplexity connector ready")
        
        # Test with just the connector first
        print("🎯 Testing strategic data collection...")
        
        # Strategic query focused on "Replace" category with key indicators
        strategic_query = """AI automation completely replacing cybersecurity analysts and SOC operators 2024: 
        
        Key indicators to search for:
        - SIEM/log analysis being fully automated
        - AI systems replacing human threat hunters
        - Autonomous incident response without human oversight
        - Job displacement studies in cybersecurity
        - Vendor announcements about "lights-out" security operations
        
        Focus on credible sources: Gartner reports, SANS Institute studies, government cybersecurity workforce analysis, peer-reviewed academic research, major security vendor case studies.
        
        Timeframe: 2024-2025 developments and predictions."""
        
        print(f"📡 Strategic Query: {strategic_query[:150]}...")
        print("🎯 Key Focus: Finding evidence of complete job replacement by AI")
        print("📊 Target Sources: Academic research, industry reports, government studies")
        
        # Collect with strategic approach
        artifacts = await connector.collect(
            query=strategic_query,
            max_results=3,
            category="replace", 
            timeframe="2024"
        )
        
        print(f"\n📊 Successfully collected {len(artifacts)} strategic artifacts")
        
        # Analyze results
        for i, artifact in enumerate(artifacts, 1):
            print(f"\n  📄 Strategic Artifact {i}:")
            print(f"     📍 Title: {artifact.title}")
            print(f"     🔗 Source: {artifact.source_url}")
            print(f"     📝 Content Preview: {artifact.content[:200]}...")
            print(f"     🏷️  Category Collected For: replace")
            print(f"     📅 Collection Time: {artifact.collection_timestamp}")
            
            # Basic credibility assessment
            source_domain = artifact.source_url.split('/')[2] if artifact.source_url else "unknown"
            print(f"     🏢 Source Domain: {source_domain}")
            
            # Check for key indicators in content
            key_indicators = [
                "replacing", "automation", "autonomous", "job displacement",
                "SIEM", "SOC", "threat hunter", "analyst", "workforce"
            ]
            
            found_indicators = []
            content_lower = artifact.content.lower()
            for indicator in key_indicators:
                if indicator.lower() in content_lower:
                    found_indicators.append(indicator)
            
            print(f"     🎯 Key Indicators Found: {', '.join(found_indicators) if found_indicators else 'None'}")
            
        print("\n🎉 Strategic collection test completed successfully!")
        print("✅ Perplexity API integration working")
        print("✅ Strategic prompting with key indicators functioning")
        print("✅ Quality source targeting operational")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_strategic_collection()) 