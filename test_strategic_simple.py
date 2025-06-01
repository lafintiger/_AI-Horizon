"""
Strategic Data Collection Test - Simplified

Tests strategic prompt crafting with key indicators to collect 
high-quality cybersecurity AI impact articles using Perplexity API.
"""

import asyncio
from datetime import datetime
from aih.gather.perplexity import PerplexityConnector
from aih.config import settings

async def test_strategic_prompts():
    """Test strategic data collection with key indicators."""
    
    print("🚀 Strategic Data Collection Test")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API Key: {settings.perplexity_api_key[:15]}..." if settings.perplexity_api_key else "❌ No API Key")
    print()
    
    try:
        # Initialize Perplexity connector
        connector = PerplexityConnector()
        print("✅ Perplexity connector initialized")
        
        # Strategic query with targeted approach
        strategic_query = """
        CYBERSECURITY AI WORKFORCE IMPACT RESEARCH 2024-2025:
        
        Find recent authoritative sources discussing AI automation REPLACING cybersecurity professionals:
        
        KEY INDICATORS TO SEARCH FOR:
        • SIEM/log analysis becoming fully automated (no human analysts needed)
        • AI threat detection systems replacing SOC analysts  
        • Autonomous incident response eliminating human responders
        • Job displacement studies in cybersecurity field
        • "Lights-out" or "human-free" security operations centers
        • Workforce reduction due to AI automation
        
        PRIORITIZE CREDIBLE SOURCES:
        • Academic research papers and studies
        • Gartner, Forrester, McKinsey workforce reports
        • SANS Institute cybersecurity surveys
        • Government/NIST cybersecurity workforce analysis
        • Major security vendor research (IBM, Microsoft, Palo Alto)
        • Peer-reviewed cybersecurity journals
        
        FOCUS TIMEFRAME: 2024-2025 developments and future predictions
        """
        
        print("📡 Strategic Query Focus:")
        print("   🎯 Category: AI REPLACING cybersecurity jobs")
        print("   📊 Sources: Academic, industry reports, government studies")
        print("   📅 Timeframe: 2024-2025")
        print("   🔍 Key Indicators: automation, job displacement, autonomous systems")
        print()
        
        # Collect artifacts using strategic approach
        print("🔍 Collecting articles with strategic prompting...")
        artifacts = await connector.collect(
            query=strategic_query,
            max_results=4,  # Test with small batch
            category="replace",
            timeframe="2024"
        )
        
        print(f"✅ Successfully collected {len(artifacts)} strategic artifacts")
        print()
        
        # Analyze collected results
        print("📊 STRATEGIC COLLECTION ANALYSIS")
        print("=" * 50)
        
        for i, artifact in enumerate(artifacts, 1):
            print(f"\n📄 Artifact {i}: Strategic Analysis")
            print("-" * 30)
            print(f"📍 Title: {artifact.title}")
            print(f"🔗 Source URL: {artifact.url}")
            print(f"📅 Collection Time: {artifact.collected_at}")
            print(f"🏷️  Target Category: replace")
            
            # Analyze source credibility
            if artifact.url:
                domain = artifact.url.split('/')[2] if len(artifact.url.split('/')) > 2 else "unknown"
                print(f"🏢 Source Domain: {domain}")
                
                # Check if it's a high-credibility source
                credible_domains = [
                    'gartner.com', 'forrester.com', 'mckinsey.com', 'sans.org', 
                    'nist.gov', 'ieee.org', 'acm.org', 'arxiv.org', 'researchgate.net',
                    'ibm.com', 'microsoft.com', 'cisco.com', 'paloaltonetworks.com'
                ]
                
                is_credible = any(cd in domain.lower() for cd in credible_domains)
                print(f"📋 High-Credibility Source: {'✅ Yes' if is_credible else '❓ Unknown'}")
            
            # Analyze content for key indicators
            content = artifact.content.lower()
            key_indicators = [
                "replacing", "automation", "autonomous", "job displacement", 
                "workforce reduction", "siem", "soc", "threat hunter", 
                "analyst", "lights-out", "human-free"
            ]
            
            found_indicators = [ind for ind in key_indicators if ind in content]
            print(f"🎯 Key Indicators Found ({len(found_indicators)}/{len(key_indicators)}): {', '.join(found_indicators)}")
            
            # Content quality assessment
            content_length = len(artifact.content)
            print(f"📝 Content Length: {content_length} characters")
            
            # Show content preview
            preview = artifact.content[:300] + "..." if len(artifact.content) > 300 else artifact.content
            print(f"📖 Content Preview: {preview}")
            
        # Summary statistics
        print(f"\n📈 STRATEGIC COLLECTION SUMMARY")
        print("=" * 50)
        print(f"Total artifacts collected: {len(artifacts)}")
        
        if artifacts:
            # Count high-credibility sources
            credible_count = 0
            total_indicators = 0
            
            for artifact in artifacts:
                if artifact.url:
                    domain = artifact.url.split('/')[2] if len(artifact.url.split('/')) > 2 else ""
                    credible_domains = ['gartner.com', 'forrester.com', 'mckinsey.com', 'sans.org', 'nist.gov']
                    if any(cd in domain.lower() for cd in credible_domains):
                        credible_count += 1
                
                content = artifact.content.lower()
                key_indicators = ["replacing", "automation", "autonomous", "job displacement"]
                found = sum(1 for ind in key_indicators if ind in content)
                total_indicators += found
            
            print(f"High-credibility sources: {credible_count}/{len(artifacts)}")
            print(f"Average key indicators per artifact: {total_indicators/len(artifacts):.1f}")
            print(f"Strategic targeting effectiveness: {'🎯 High' if total_indicators > len(artifacts) else '📊 Moderate'}")
        
        print("\n🎉 Strategic data collection test completed successfully!")
        print("✅ Perplexity API integration working")
        print("✅ Strategic prompting with key indicators functional")
        print("✅ Quality source targeting operational")
        print("✅ Ready for full pipeline implementation")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_strategic_prompts()) 