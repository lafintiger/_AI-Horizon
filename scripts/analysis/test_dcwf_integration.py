#!/usr/bin/env python3
"""
DCWF Integration Test & Verification Script

This script tests and demonstrates the DCWF framework integration in AI-Horizon.
Use this to verify that the DCWF framework is properly loaded and integrated
into the classification system.

Usage:
    python scripts/analysis/test_dcwf_integration.py
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from aih.utils.logging import get_logger
from aih.classify.classifier import ArtifactClassifier

logger = get_logger(__name__)

def test_dcwf_framework_loading():
    """Test DCWF framework loading and basic functionality."""
    print("🔍 Testing DCWF Framework Loading...")
    
    try:
        from scripts.analysis.dcwf_framework_indexer import DCWFFrameworkIndexer
        
        # Initialize indexer
        indexer = DCWFFrameworkIndexer()
        
        # Get framework summary
        summary = indexer.get_framework_summary()
        
        print(f"✅ DCWF Framework loaded successfully!")
        print(f"   📊 Work Roles: {summary['total_work_roles']}")
        print(f"   📋 Tasks: {summary['total_tasks']}")
        print(f"   🏷️  Keywords: {summary['keyword_index_size']}")
        print(f"   📁 Specialty Areas: {len(summary['specialty_areas'])}")
        
        return indexer, True
        
    except Exception as e:
        print(f"❌ DCWF Framework loading failed: {e}")
        return None, False

def test_dcwf_analysis():
    """Test DCWF content analysis functionality."""
    print("\n🔍 Testing DCWF Content Analysis...")
    
    try:
        from scripts.analysis.dcwf_framework_indexer import DCWFFrameworkIndexer
        indexer = DCWFFrameworkIndexer()
        
        # Test content for analysis
        test_content = """
        AI-powered code generation tools are revolutionizing software development.
        These tools can automatically generate secure code, perform code reviews,
        and assist with debugging. Software developers will need to adapt their
        workflows to incorporate AI assistance while maintaining code quality
        and security standards.
        """
        
        # Perform DCWF analysis
        analysis = indexer.infer_dcwf_impacts(test_content)
        
        print(f"✅ DCWF Analysis completed!")
        print(f"   🎯 Relevant Work Roles: {len(analysis.get('relevant_work_roles', []))}")
        print(f"      {', '.join(analysis.get('relevant_work_roles', [])[:3])}")
        print(f"   ⚠️  Tasks at Risk: {len(analysis.get('tasks_at_risk', []))}")
        print(f"   🤝 Tasks to Augment: {len(analysis.get('tasks_to_augment', []))}")
        print(f"   👤 Human-Critical Tasks: {len(analysis.get('human_critical_tasks', []))}")
        print(f"   📊 Confidence: {analysis.get('inference_confidence', 0):.2f}")
        
        return analysis, True
        
    except Exception as e:
        print(f"❌ DCWF Analysis failed: {e}")
        return None, False

def test_enhanced_classification():
    """Test enhanced classification with DCWF integration."""
    print("\n🔍 Testing Enhanced Classification with DCWF...")
    
    try:
        # Initialize classifier
        classifier = ArtifactClassifier()
        
        # Test artifact data
        test_artifact = {
            "title": "AI-Powered Cybersecurity Tools Transform Software Development",
            "content": """
            Artificial intelligence is transforming how cybersecurity professionals approach
            software development and security testing. New AI tools can automatically:
            
            - Generate secure code following best practices
            - Perform automated security code reviews
            - Detect vulnerabilities in real-time
            - Suggest security improvements
            - Automate penetration testing
            
            Software developers and security architects will need to integrate these tools
            into their workflows while maintaining human oversight for critical decisions.
            Database administrators will also benefit from AI-powered security monitoring
            and threat detection capabilities.
            """,
            "url": "https://example.com/ai-cybersecurity-tools",
            "source_type": "article"
        }
        
        # Perform classification
        classifications = classifier.classify_artifact(test_artifact)
        
        print(f"✅ Enhanced Classification completed!")
        print(f"   📊 Classifications: {len(classifications)}")
        
        for i, classification in enumerate(classifications, 1):
            print(f"\n   📋 Classification {i}:")
            print(f"      Category: {classification.category}")
            print(f"      Confidence: {classification.confidence:.2f}")
            print(f"      Model: {classification.model_used}")
            
            if classification.dcwf_analysis:
                dcwf = classification.dcwf_analysis
                print(f"      🎯 DCWF Work Roles: {len(dcwf.get('relevant_work_roles', []))}")
                print(f"         {', '.join(dcwf.get('relevant_work_roles', [])[:3])}")
                print(f"      📋 LLM Identified Roles: {dcwf.get('llm_identified_roles', 'None')}")
                print(f"      🔧 LLM Identified Tasks: {dcwf.get('llm_identified_tasks', 'None')}")
            else:
                print(f"      ⚠️  No DCWF analysis available")
            
            print(f"      💭 Rationale: {classification.rationale[:150]}...")
        
        return classifications, True
        
    except Exception as e:
        print(f"❌ Enhanced Classification failed: {e}")
        import traceback
        traceback.print_exc()
        return None, False

def test_work_role_exploration():
    """Test work role exploration functionality."""
    print("\n🔍 Testing Work Role Exploration...")
    
    try:
        from scripts.analysis.dcwf_framework_indexer import DCWFFrameworkIndexer
        indexer = DCWFFrameworkIndexer()
        
        # Test work role details
        role_name = "Software Developer"
        role_details = indexer.get_work_role_details(role_name)
        
        if role_details:
            print(f"✅ Work Role Details retrieved!")
            print(f"   🎯 Role: {role_details['role_name']}")
            print(f"   🆔 ID: {role_details['role_id']}")
            print(f"   📋 Tasks: {role_details['task_count']}")
            print(f"   🏷️  Specialty: {role_details['specialty_area']}")
            print(f"   📝 Description: {role_details['role_description'][:100]}...")
            
            # Show sample tasks
            print(f"\n   📋 Sample Tasks:")
            for i, task in enumerate(role_details['tasks'][:3], 1):
                print(f"      {i}. {task.task_description[:80]}...")
        else:
            print(f"⚠️  No details found for role: {role_name}")
        
        # Test keyword search
        print(f"\n   🔍 Testing Keyword Search...")
        coding_tasks = indexer.find_relevant_tasks(["coding", "programming", "development"])
        
        print(f"   ✅ Found {len(coding_tasks)} tasks matching coding keywords:")
        for i, task in enumerate(coding_tasks[:3], 1):
            print(f"      {i}. {task['work_role']}: {task['description'][:60]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Work Role Exploration failed: {e}")
        return False

def test_framework_cache():
    """Test framework cache functionality."""
    print("\n🔍 Testing Framework Cache...")
    
    try:
        cache_file = Path("data/dcwf_framework_index.json")
        
        if cache_file.exists():
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
            
            metadata = cache_data.get('metadata', {})
            work_roles = cache_data.get('work_roles', {})
            tasks = cache_data.get('tasks', {})
            
            print(f"✅ Framework Cache loaded!")
            print(f"   📁 Cache File: {cache_file}")
            print(f"   📊 Work Roles: {len(work_roles)}")
            print(f"   📋 Tasks: {len(tasks)}")
            print(f"   🕒 Last Updated: {metadata.get('loaded_at', 'Unknown')}")
            print(f"   📂 Source: {Path(metadata.get('framework_source', '')).name}")
            
            return True
        else:
            print(f"⚠️  Framework cache not found: {cache_file}")
            return False
            
    except Exception as e:
        print(f"❌ Framework Cache test failed: {e}")
        return False

def generate_integration_report():
    """Generate comprehensive integration status report."""
    print("\n📊 Generating DCWF Integration Report...")
    
    report = {
        "test_timestamp": datetime.now().isoformat(),
        "dcwf_framework_status": "unknown",
        "classification_integration": "unknown",
        "analysis_capabilities": "unknown",
        "cache_status": "unknown",
        "overall_status": "unknown"
    }
    
    # Test framework loading
    indexer, framework_ok = test_dcwf_framework_loading()
    report["dcwf_framework_status"] = "operational" if framework_ok else "failed"
    
    # Test analysis
    analysis, analysis_ok = test_dcwf_analysis()
    report["analysis_capabilities"] = "operational" if analysis_ok else "failed"
    
    # Test classification
    classifications, classification_ok = test_enhanced_classification()
    report["classification_integration"] = "operational" if classification_ok else "failed"
    
    # Test work role exploration
    exploration_ok = test_work_role_exploration()
    report["work_role_exploration"] = "operational" if exploration_ok else "failed"
    
    # Test cache
    cache_ok = test_framework_cache()
    report["cache_status"] = "operational" if cache_ok else "failed"
    
    # Overall status
    all_tests = [framework_ok, analysis_ok, classification_ok, exploration_ok, cache_ok]
    if all(all_tests):
        report["overall_status"] = "fully_operational"
    elif any(all_tests):
        report["overall_status"] = "partially_operational"
    else:
        report["overall_status"] = "failed"
    
    return report

def main():
    """Main test execution."""
    print("🚀 AI-Horizon DCWF Integration Test Suite")
    print("=" * 50)
    
    # Generate comprehensive report
    report = generate_integration_report()
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 DCWF INTEGRATION TEST SUMMARY")
    print("=" * 50)
    
    status_emoji = {
        "operational": "✅",
        "failed": "❌",
        "unknown": "❓",
        "fully_operational": "🟢",
        "partially_operational": "🟡"
    }
    
    print(f"Framework Loading:     {status_emoji.get(report['dcwf_framework_status'], '❓')} {report['dcwf_framework_status']}")
    print(f"Analysis Capabilities: {status_emoji.get(report['analysis_capabilities'], '❓')} {report['analysis_capabilities']}")
    print(f"Classification:        {status_emoji.get(report['classification_integration'], '❓')} {report['classification_integration']}")
    print(f"Work Role Exploration: {status_emoji.get(report.get('work_role_exploration', 'unknown'), '❓')} {report.get('work_role_exploration', 'unknown')}")
    print(f"Framework Cache:       {status_emoji.get(report['cache_status'], '❓')} {report['cache_status']}")
    print(f"\nOVERALL STATUS:        {status_emoji.get(report['overall_status'], '❓')} {report['overall_status'].upper()}")
    
    # Save report
    report_file = Path("data/dcwf_integration_test_report.json")
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Detailed report saved: {report_file}")
    
    if report['overall_status'] == 'fully_operational':
        print("\n🎉 DCWF Integration is fully operational!")
        print("   The system is ready for DoD cybersecurity workforce analysis.")
    elif report['overall_status'] == 'partially_operational':
        print("\n⚠️  DCWF Integration is partially operational.")
        print("   Some features may not work as expected. Check individual test results.")
    else:
        print("\n❌ DCWF Integration has failed.")
        print("   Please check the DCWF_INTEGRATION_GUIDE.md for troubleshooting.")
    
    return report['overall_status'] == 'fully_operational'

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 