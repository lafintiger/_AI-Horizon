"""
Comprehensive Multi-Category Test

Tests strategic data collection for all four AI impact categories:
- Replace: Tasks AI will replace entirely
- Augment: Tasks requiring AI assistance  
- New Tasks: Jobs created by AI developments
- Human-Only: Tasks remaining human-driven

Generates detailed results for web reporting.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from aih.gather.perplexity import PerplexityConnector
from aih.config import settings, get_data_path

async def test_all_categories():
    """Test strategic data collection across all AI impact categories."""
    
    print("🚀 AI-Horizon Comprehensive Category Test")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Strategic queries for each category
    category_queries = {
        "replace": {
            "name": "AI REPLACING Cybersecurity Jobs",
            "query": """
            CYBERSECURITY WORKFORCE AUTOMATION 2024-2025:
            
            Find authoritative sources on AI COMPLETELY REPLACING cybersecurity professionals:
            
            KEY INDICATORS:
            • SIEM/log analysis fully automated (no human analysts)
            • AI threat detection replacing SOC analysts entirely
            • Autonomous incident response eliminating human responders
            • Job displacement studies showing workforce reduction
            • "Lights-out" security operations centers
            • AI taking over vulnerability management completely
            
            PRIORITY SOURCES: Gartner, Forrester, SANS, academic studies, government workforce reports
            """,
            "indicators": ["replacing", "automation", "autonomous", "job displacement", "workforce reduction", "eliminating", "lights-out"]
        },
        
        "augment": {
            "name": "AI AUGMENTING Cybersecurity Professionals", 
            "query": """
            CYBERSECURITY AI-HUMAN COLLABORATION 2024-2025:
            
            Find sources on AI ASSISTING and ENHANCING cybersecurity professionals:
            
            KEY INDICATORS:
            • AI copilots for security analysts
            • ML-enhanced threat analysis requiring human oversight
            • AI-assisted incident response with human decision-making
            • Analyst productivity improvements through AI tools
            • Human-AI collaboration in security operations
            • AI augmentation improving analyst capabilities
            
            PRIORITY SOURCES: SANS surveys, vendor case studies, practitioner reports, industry analysis
            """,
            "indicators": ["augmenting", "assisting", "collaboration", "copilot", "enhanced", "productivity", "human-ai"]
        },
        
        "new_tasks": {
            "name": "NEW JOBS Created by AI",
            "query": """
            EMERGING CYBERSECURITY ROLES 2024-2025:
            
            Find sources on NEW cybersecurity jobs created by AI technology:
            
            KEY INDICATORS:
            • AI security engineers and ML security specialists
            • AI model security and bias testing roles
            • AI governance and ethics positions in cybersecurity
            • Prompt engineering for security applications
            • AI red team and adversarial testing specialists
            • New skill requirements for AI-integrated security
            
            PRIORITY SOURCES: Job market reports, LinkedIn workforce insights, recruitment studies, career surveys
            """,
            "indicators": ["new roles", "emerging", "ai security engineer", "ml specialist", "governance", "skill requirements", "created by ai"]
        },
        
        "human_only": {
            "name": "HUMAN-ONLY Cybersecurity Tasks",
            "query": """
            HUMAN-ESSENTIAL CYBERSECURITY 2024-2025:
            
            Find sources on cybersecurity tasks that REMAIN human-driven:
            
            KEY INDICATORS:
            • Strategic security planning requiring human judgment
            • Crisis communication and stakeholder management
            • Legal/compliance decisions in security incidents
            • Ethical considerations in security policies
            • Creative threat modeling and red team planning
            • Complex investigations requiring human intuition
            
            PRIORITY SOURCES: CISO perspectives, security leadership studies, policy research, ethics papers
            """,
            "indicators": ["human judgment", "strategic", "ethics", "compliance", "creative", "intuition", "human-driven", "human-only"]
        }
    }
    
    try:
        # Initialize connector
        connector = PerplexityConnector()
        print("✅ Perplexity connector initialized")
        print()
        
        # Results storage
        all_results = {}
        
        # Test each category
        for category, config in category_queries.items():
            print(f"🎯 Testing Category: {config['name']}")
            print("-" * 50)
            print(f"Key Indicators: {', '.join(config['indicators'][:4])}...")
            
            try:
                # Collect artifacts for this category
                artifacts = await connector.collect(
                    query=config["query"],
                    max_results=10,  # Increased to 10 for comprehensive analysis
                    category=category,
                    timeframe="2024"
                )
                
                print(f"📊 Collected {len(artifacts)} artifacts")
                
                # Analyze artifacts for this category
                category_analysis = {
                    "name": config["name"],
                    "total_articles": len(artifacts),
                    "artifacts": [],
                    "indicators_found": {},
                    "content_quality": {
                        "avg_length": 0,
                        "total_content": 0
                    },
                    "source_analysis": {
                        "domains": [],
                        "credible_sources": 0
                    }
                }
                
                total_length = 0
                indicator_counts = {ind: 0 for ind in config["indicators"]}
                
                for i, artifact in enumerate(artifacts, 1):
                    # Basic artifact info
                    artifact_info = {
                        "title": artifact.title,
                        "url": artifact.url,
                        "collected_at": artifact.collected_at.strftime('%Y-%m-%d %H:%M:%S'),
                        "content_length": len(artifact.content),
                        "content_preview": artifact.content[:250] + "..." if len(artifact.content) > 250 else artifact.content,
                        "indicators_found": []
                    }
                    
                    # Check for key indicators
                    content_lower = artifact.content.lower()
                    for indicator in config["indicators"]:
                        if indicator.lower() in content_lower:
                            indicator_counts[indicator] += 1
                            artifact_info["indicators_found"].append(indicator)
                    
                    # Source analysis
                    if artifact.url:
                        domain = artifact.url.split('/')[2] if len(artifact.url.split('/')) > 2 else "unknown"
                        category_analysis["source_analysis"]["domains"].append(domain)
                        
                        # Check credibility
                        credible_domains = [
                            'gartner.com', 'forrester.com', 'mckinsey.com', 'sans.org', 
                            'nist.gov', 'ieee.org', 'acm.org', 'arxiv.org'
                        ]
                        if any(cd in domain.lower() for cd in credible_domains):
                            category_analysis["source_analysis"]["credible_sources"] += 1
                    
                    total_length += len(artifact.content)
                    category_analysis["artifacts"].append(artifact_info)
                    
                    print(f"  📄 Article {i}: {len(artifact_info['indicators_found'])} indicators found")
                
                # Calculate summary stats
                if artifacts:
                    category_analysis["content_quality"]["avg_length"] = total_length // len(artifacts)
                    category_analysis["content_quality"]["total_content"] = total_length
                
                category_analysis["indicators_found"] = indicator_counts
                
                # Summary for this category
                total_indicators = sum(indicator_counts.values())
                print(f"  🎯 Total indicator matches: {total_indicators}")
                print(f"  📊 Average content length: {category_analysis['content_quality']['avg_length']} chars")
                print(f"  🏆 Credible sources: {category_analysis['source_analysis']['credible_sources']}/{len(artifacts)}")
                print()
                
                all_results[category] = category_analysis
                
            except Exception as e:
                print(f"❌ Error processing category {category}: {e}")
                all_results[category] = {
                    "name": config["name"],
                    "total_articles": 0,
                    "error": str(e),
                    "artifacts": [],
                    "indicators_found": {},
                    "content_quality": {"avg_length": 0, "total_content": 0},
                    "source_analysis": {"domains": [], "credible_sources": 0}
                }
        
        # Save results to JSON for web report
        results_file = get_data_path("reports") / "category_analysis_results.json"
        
        # Add metadata
        results_with_metadata = {
            "test_timestamp": datetime.now().isoformat(),
            "test_type": "comprehensive_category_analysis",
            "perplexity_api_used": True,
            "categories_tested": list(category_queries.keys()),
            "results": all_results
        }
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results_with_metadata, f, indent=2, ensure_ascii=False)
        
        print("📈 COMPREHENSIVE ANALYSIS SUMMARY")
        print("=" * 60)
        
        total_articles = sum(r.get("total_articles", 0) for r in all_results.values())
        successful_categories = sum(1 for r in all_results.values() if r.get("total_articles", 0) > 0)
        
        print(f"Total articles collected: {total_articles}")
        print(f"Successful categories: {successful_categories}/{len(category_queries)}")
        print(f"Results saved to: {results_file}")
        
        for category, results in all_results.items():
            if results.get("total_articles", 0) > 0:
                total_indicators = sum(results.get("indicators_found", {}).values())
                print(f"  {category.upper()}: {results['total_articles']} articles, {total_indicators} indicator matches")
        
        print(f"\n✅ Results saved for web report generation")
        return all_results
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return {}

if __name__ == "__main__":
    results = asyncio.run(test_all_categories()) 