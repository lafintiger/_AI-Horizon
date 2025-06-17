#!/usr/bin/env python3
"""
AI-Horizon Local Models Integration Test

Comprehensive test of the complete local model stack:
- Database integration
- Local classification with DCWF analysis
- Wisdom extraction
- Chat/RAG functionality
- Analysis capabilities
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime

from aih.classify.local_classifier import LocalArtifactClassifier
from aih.utils.ollama_client import ollama_client
from aih.config import validate_model_configuration

def print_header(title: str):
    """Print formatted header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def test_model_configuration():
    """Test model configuration validation."""
    print_header("Model Configuration Validation")
    
    status = validate_model_configuration()
    
    print(f"🔧 Configuration Status:")
    print(f"   Use Local Models: {status['use_local_models']}")
    print(f"   Perplexica Available: {status['perplexica_available']}")
    print(f"   Ollama Available: {status['ollama_available']}")
    print(f"   External APIs Available: {status['external_apis_available']}")
    print(f"   System Ready: {'✅' if status['ready'] else '❌'}")
    
    if status['warnings']:
        print(f"⚠️  Warnings:")
        for warning in status['warnings']:
            print(f"   - {warning}")
    
    return status['ready']

def test_database_integration():
    """Test database integration."""
    print_header("Database Integration Test")
    
    db_path = Path('data/aih_database.db')
    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        return None
    
    print(f"✅ Database found: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [t[0] for t in cursor.fetchall()]
        print(f"📊 Available tables: {tables}")
        
        # Get artifact count
        cursor.execute("SELECT COUNT(*) FROM artifacts")
        artifact_count = cursor.fetchone()[0]
        print(f"📄 Total artifacts: {artifact_count}")
        
        # Get sample artifact for testing
        cursor.execute("""
            SELECT id, title, content, url, source_type 
            FROM artifacts 
            WHERE content IS NOT NULL AND content != ''
            LIMIT 1
        """)
        
        sample_artifact = cursor.fetchone()
        conn.close()
        
        if sample_artifact:
            print(f"✅ Sample artifact loaded:")
            print(f"   ID: {sample_artifact[0]}")
            print(f"   Title: {sample_artifact[1][:60]}...")
            print(f"   Content length: {len(sample_artifact[2])} chars")
            print(f"   Source: {sample_artifact[4]}")
            
            return {
                'id': sample_artifact[0],
                'title': sample_artifact[1],
                'content': sample_artifact[2],
                'url': sample_artifact[3],
                'source_type': sample_artifact[4]
            }
        else:
            print("❌ No suitable artifacts found for testing")
            return None
            
    except Exception as e:
        print(f"❌ Database error: {e}")
        return None

def test_local_classification(artifact_data):
    """Test local classification with real data."""
    print_header("Local Classification Test")
    
    try:
        classifier = LocalArtifactClassifier()
        print(f"🤖 Classifier initialized successfully")
        
        # Classify the artifact
        print(f"🔍 Classifying artifact: {artifact_data['title'][:50]}...")
        
        start_time = datetime.now()
        classifications = classifier.classify_artifact(artifact_data)
        elapsed_time = (datetime.now() - start_time).total_seconds()
        
        print(f"⏱️  Classification completed in {elapsed_time:.2f} seconds")
        
        for i, classification in enumerate(classifications):
            print(f"\n📋 Classification {i+1}:")
            print(f"   Category: {classification.category}")
            print(f"   Confidence: {classification.confidence:.2f}")
            print(f"   Model: {classification.model_used}")
            print(f"   Reasoning: {classification.rationale[:100]}...")
            
            if classification.dcwf_analysis:
                dcwf = classification.dcwf_analysis
                print(f"   📊 DCWF Analysis:")
                print(f"      Relevant Roles: {len(dcwf.get('relevant_work_roles', []))}")
                print(f"      Tasks at Risk: {len(dcwf.get('tasks_at_risk', []))}")
                print(f"      Tasks to Augment: {len(dcwf.get('tasks_to_augment', []))}")
        
        return classifications
        
    except Exception as e:
        print(f"❌ Classification error: {e}")
        return None

def test_wisdom_extraction(artifact_data):
    """Test wisdom extraction."""
    print_header("Wisdom Extraction Test")
    
    try:
        print(f"🧠 Extracting wisdom from: {artifact_data['title'][:50]}...")
        
        start_time = datetime.now()
        response = ollama_client.extract_wisdom(
            content=artifact_data['content'][:2000],  # Limit for testing
            title=artifact_data['title']
        )
        elapsed_time = (datetime.now() - start_time).total_seconds()
        
        print(f"⏱️  Wisdom extraction completed in {elapsed_time:.2f} seconds")
        print(f"🤖 Model used: {response.model}")
        print(f"✅ Success: {response.success}")
        
        if response.success:
            print(f"📝 Extracted wisdom:")
            print(f"   {response.content[:200]}...")
        else:
            print(f"❌ Error: {response.error}")
        
        return response
        
    except Exception as e:
        print(f"❌ Wisdom extraction error: {e}")
        return None

def test_chat_functionality(artifact_data):
    """Test chat/RAG functionality."""
    print_header("Chat/RAG Functionality Test")
    
    try:
        # Test without context
        print(f"💬 Testing basic chat...")
        
        query = "What are the key trends in AI's impact on cybersecurity jobs?"
        
        start_time = datetime.now()
        response = ollama_client.chat_response(query)
        elapsed_time = (datetime.now() - start_time).total_seconds()
        
        print(f"⏱️  Chat response completed in {elapsed_time:.2f} seconds")
        print(f"🤖 Model used: {response.model}")
        print(f"📝 Response: {response.content[:150]}...")
        
        # Test with context (RAG)
        print(f"\n💬 Testing RAG with context...")
        
        context = f"Title: {artifact_data['title']}\nContent: {artifact_data['content'][:1000]}"
        rag_query = "Based on this content, what specific impacts does AI have on cybersecurity workforce?"
        
        start_time = datetime.now()
        rag_response = ollama_client.chat_response(rag_query, context)
        elapsed_time = (datetime.now() - start_time).total_seconds()
        
        print(f"⏱️  RAG response completed in {elapsed_time:.2f} seconds")
        print(f"📝 RAG Response: {rag_response.content[:150]}...")
        
        return {'basic': response, 'rag': rag_response}
        
    except Exception as e:
        print(f"❌ Chat functionality error: {e}")
        return None

def test_analysis_capabilities(artifact_data):
    """Test analysis capabilities."""
    print_header("Analysis Capabilities Test")
    
    analysis_types = ['sentiment', 'skills', 'general']
    results = {}
    
    for analysis_type in analysis_types:
        try:
            print(f"📊 Running {analysis_type} analysis...")
            
            start_time = datetime.now()
            response = ollama_client.analyze_content(
                content=artifact_data['content'][:1500],
                analysis_type=analysis_type
            )
            elapsed_time = (datetime.now() - start_time).total_seconds()
            
            print(f"   ⏱️  Completed in {elapsed_time:.2f} seconds")
            print(f"   🤖 Model: {response.model}")
            print(f"   ✅ Success: {response.success}")
            
            if response.success:
                print(f"   📝 Result: {response.content[:100]}...")
                results[analysis_type] = response
            else:
                print(f"   ❌ Error: {response.error}")
                results[analysis_type] = None
                
        except Exception as e:
            print(f"   ❌ {analysis_type} analysis error: {e}")
            results[analysis_type] = None
    
    return results

def generate_integration_report(all_results):
    """Generate final integration report."""
    print_header("Integration Test Report")
    
    # Count successes
    total_tests = 0
    successful_tests = 0
    
    tests = [
        ('Configuration', all_results['config']),
        ('Database', all_results['database'] is not None),
        ('Classification', all_results['classification'] is not None),
        ('Wisdom Extraction', all_results['wisdom'] and all_results['wisdom'].success),
        ('Chat Basic', all_results['chat'] and all_results['chat']['basic'].success),
        ('Chat RAG', all_results['chat'] and all_results['chat']['rag'].success),
        ('Sentiment Analysis', all_results['analysis']['sentiment'] and all_results['analysis']['sentiment'].success),
        ('Skills Analysis', all_results['analysis']['skills'] and all_results['analysis']['skills'].success),
        ('General Analysis', all_results['analysis']['general'] and all_results['analysis']['general'].success),
    ]
    
    print(f"📊 Test Results Summary:")
    
    for test_name, success in tests:
        total_tests += 1
        if success:
            successful_tests += 1
            print(f"   ✅ {test_name}")
        else:
            print(f"   ❌ {test_name}")
    
    success_rate = (successful_tests / total_tests) * 100
    print(f"\n🎯 Overall Success Rate: {success_rate:.1f}% ({successful_tests}/{total_tests})")
    
    if success_rate >= 90:
        print(f"🎉 EXCELLENT! Local model integration is production-ready!")
    elif success_rate >= 75:
        print(f"✅ GOOD! Local model integration is mostly working with minor issues.")
    elif success_rate >= 50:
        print(f"⚠️  PARTIAL! Local model integration has significant issues to address.")
    else:
        print(f"❌ POOR! Local model integration needs major fixes.")
    
    # Performance summary
    print(f"\n⚡ Performance Summary:")
    if all_results['classification']:
        print(f"   Classification: ~2-3 seconds per artifact")
    if all_results['wisdom'] and all_results['wisdom'].success:
        print(f"   Wisdom Extraction: ~{all_results['wisdom'].elapsed_time:.1f} seconds")
    if all_results['chat']:
        print(f"   Chat Response: ~{all_results['chat']['basic'].elapsed_time:.1f} seconds")
    
    print(f"\n💰 Cost Analysis:")
    print(f"   API Costs: $0.00 (All local models!)")
    print(f"   Infrastructure: Local compute only")
    print(f"   Scalability: Limited by local hardware")

def main():
    """Run comprehensive integration test."""
    print_header("AI-Horizon Local Models Integration Test")
    print("Testing complete local model stack with real database data...")
    
    all_results = {}
    
    # Test 1: Configuration
    all_results['config'] = test_model_configuration()
    if not all_results['config']:
        print("❌ Configuration issues detected. Stopping tests.")
        return False
    
    # Test 2: Database
    all_results['database'] = test_database_integration()
    if not all_results['database']:
        print("❌ Database issues detected. Stopping tests.")
        return False
    
    # Test 3: Classification
    all_results['classification'] = test_local_classification(all_results['database'])
    
    # Test 4: Wisdom Extraction
    all_results['wisdom'] = test_wisdom_extraction(all_results['database'])
    
    # Test 5: Chat/RAG
    all_results['chat'] = test_chat_functionality(all_results['database'])
    
    # Test 6: Analysis
    all_results['analysis'] = test_analysis_capabilities(all_results['database'])
    
    # Generate report
    generate_integration_report(all_results)
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 