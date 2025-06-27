#!/usr/bin/env python3
"""
Test script for optimized model management and article processing.

This script tests:
1. Model loading/unloading functionality 
2. Intelligent model switching
3. Complete article processing pipeline
4. Performance monitoring with different models
"""

import asyncio
import time
import logging
from typing import List, Dict, Any

from aih.utils.ollama_client import OllamaClient
from aih.gather.searxng_direct import SearXNGDirectConnector
from aih.classify.local_classifier import LocalArtifactClassifier
from aih.utils.database import DatabaseManager
from aih.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s'
)
logger = logging.getLogger(__name__)

class ModelManagementTester:
    """Test suite for model management and article processing."""
    
    def __init__(self):
        self.ollama_client = OllamaClient()
        self.collector = SearXNGDirectConnector()
        self.classifier = LocalArtifactClassifier()
        self.database = DatabaseManager()
        
    def test_model_availability(self) -> Dict[str, bool]:
        """Test which configured models are actually available."""
        logger.info("🔍 Testing model availability...")
        
        available_models = self.ollama_client.get_available_models()
        configured_models = self.ollama_client.models
        
        results = {}
        for task, model_name in configured_models.items():
            is_available = model_name in available_models
            results[f"{task} ({model_name})"] = is_available
            
            if is_available:
                logger.info(f"✅ {task}: {model_name}")
            else:
                logger.warning(f"❌ {task}: {model_name} - NOT AVAILABLE")
        
        return results
    
    def test_model_loading_performance(self) -> Dict[str, float]:
        """Test loading performance for different model sizes."""
        logger.info("⚡ Testing model loading performance...")
        
        # Test models of different sizes
        test_models = [
            ("lightweight", "llama3:latest"),
            ("medium", "mistral-nemo:12b-instruct-2407-q6_K"), 
            ("large", "qwen3:32b-q8_0"),
            ("xlarge", "llama3.3:70b-instruct-q5_K_M")
        ]
        
        results = {}
        
        for category, model_name in test_models:
            if model_name in self.ollama_client.get_available_models():
                logger.info(f"🚀 Testing load time for {category} model: {model_name}")
                
                # Unload any current model first
                if self.ollama_client.current_loaded_model:
                    self.ollama_client._unload_model(self.ollama_client.current_loaded_model)
                    time.sleep(2)
                
                # Time the loading
                start_time = time.time()
                success = self.ollama_client._load_model(model_name)
                load_time = time.time() - start_time
                
                if success:
                    results[f"{category} ({model_name})"] = load_time
                    logger.info(f"✅ {category} loaded in {load_time:.1f}s")
                else:
                    results[f"{category} ({model_name})"] = -1
                    logger.error(f"❌ Failed to load {category}")
            else:
                logger.warning(f"⚠️  Skipping {category} - model not available")
                results[f"{category} ({model_name})"] = -1
        
        return results
    
    def test_intelligent_switching(self) -> bool:
        """Test intelligent model switching functionality."""
        logger.info("🔄 Testing intelligent model switching...")
        
        try:
            # Test switching between different model sizes
            models_to_test = [
                ("classification", "llama3:latest"),
                ("wisdom", "qwen3:32b-q8_0"),
                ("analysis", "llama3.3:70b-instruct-q5_K_M"),
                ("classification", "llama3:latest")  # Back to lightweight
            ]
            
            for task_type, expected_model in models_to_test:
                logger.info(f"🎯 Switching to {task_type} task ({expected_model})")
                
                # Test a simple generation to trigger model switching
                response = self.ollama_client.generate(
                    "Test prompt",
                    task_type=task_type,
                    max_tokens=10
                )
                
                if response.success:
                    logger.info(f"✅ Successfully used {response.model}")
                else:
                    logger.error(f"❌ Failed to generate with {expected_model}: {response.error}")
                    return False
                
                # Small delay between switches
                time.sleep(1)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Model switching test failed: {e}")
            return False
    
    async def test_complete_processing_pipeline(self) -> Dict[str, Any]:
        """Test the complete article processing pipeline with optimized models."""
        logger.info("🔄 Testing complete processing pipeline...")
        
        try:
            # Step 1: Collect articles using SearXNG Direct
            logger.info("📡 Step 1: Collecting articles...")
            start_time = time.time()
            
            artifacts = await self.collector.collect(
                query="AI cybersecurity automation 2024",
                max_results=3,  # Small test batch
                category="replace",
                timeframe="2024"
            )
            
            collection_time = time.time() - start_time
            logger.info(f"✅ Collected {len(artifacts)} artifacts in {collection_time:.1f}s")
            
            if not artifacts:
                logger.error("❌ No artifacts collected")
                return {"success": False, "error": "No artifacts collected"}
            
            # Step 2: Process each artifact with different models
            processing_results = []
            
            for i, artifact in enumerate(artifacts):
                logger.info(f"🔬 Step 2.{i+1}: Processing artifact '{artifact.title[:50]}...'")
                
                # Classification (lightweight model)
                logger.info("   🏷️  Classifying...")
                class_start = time.time()
                artifact_data = {
                    'content': artifact.content,
                    'title': artifact.title,
                    'source_url': getattr(artifact, 'source_url', artifact.url)
                }
                classifications = self.classifier.classify_artifact(artifact_data)
                classification = classifications[0] if classifications else None
                class_time = time.time() - class_start
                
                # Wisdom extraction (powerful reasoning model)
                logger.info("   🧠 Extracting wisdom...")
                wisdom_start = time.time()
                wisdom_response = self.ollama_client.extract_wisdom(
                    content=artifact.content,
                    title=artifact.title
                )
                wisdom_time = time.time() - wisdom_start
                
                # Analysis (top-tier model)
                logger.info("   📊 Performing analysis...")
                analysis_start = time.time()
                analysis_response = self.ollama_client.analyze_content(
                    content=artifact.content,
                    analysis_type="comprehensive"
                )
                analysis_time = time.time() - analysis_start
                
                processing_results.append({
                    "title": artifact.title,
                    "classification": {
                        "success": classification is not None,
                        "category": classification.category if classification else 'unknown',
                        "time": class_time
                    },
                    "wisdom": {
                        "success": wisdom_response.success,
                        "model": wisdom_response.model,
                        "time": wisdom_time
                    },
                    "analysis": {
                        "success": analysis_response.success,
                        "model": analysis_response.model,
                        "time": analysis_time
                    }
                })
                
                logger.info(f"   ✅ Processed in {class_time + wisdom_time + analysis_time:.1f}s")
            
            # Step 3: Database storage test
            logger.info("💾 Step 3: Testing database storage...")
            try:
                # Test database connection
                stats = self.database.get_database_stats()
                logger.info(f"✅ Database accessible: {stats['total_artifacts']} total artifacts")
                db_success = True
            except Exception as e:
                logger.error(f"❌ Database error: {e}")
                db_success = False
            
            total_time = time.time() - start_time
            
            return {
                "success": True,
                "collection": {
                    "artifacts_collected": len(artifacts),
                    "time": collection_time
                },
                "processing": processing_results,
                "database": {"success": db_success},
                "total_time": total_time,
                "performance_summary": {
                    "avg_classification_time": sum(r["classification"]["time"] for r in processing_results) / len(processing_results),
                    "avg_wisdom_time": sum(r["wisdom"]["time"] for r in processing_results) / len(processing_results),
                    "avg_analysis_time": sum(r["analysis"]["time"] for r in processing_results) / len(processing_results)
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Complete pipeline test failed: {e}")
            return {"success": False, "error": str(e)}
    
    def cleanup(self):
        """Clean up resources."""
        logger.info("🧹 Cleaning up...")
        self.ollama_client.cleanup_models()

async def main():
    """Run the comprehensive model management test suite."""
    logger.info("🚀 Starting Model Management Test Suite")
    logger.info("=" * 60)
    
    tester = ModelManagementTester()
    
    try:
        # Test 1: Model Availability
        logger.info("\n📋 TEST 1: Model Availability")
        availability = tester.test_model_availability()
        available_count = sum(1 for available in availability.values() if available)
        logger.info(f"✅ {available_count}/{len(availability)} models available")
        
        # Test 2: Loading Performance
        logger.info("\n⚡ TEST 2: Model Loading Performance")
        load_times = tester.test_model_loading_performance()
        for model, time_taken in load_times.items():
            if time_taken > 0:
                logger.info(f"   {model}: {time_taken:.1f}s")
        
        # Test 3: Intelligent Switching
        logger.info("\n🔄 TEST 3: Intelligent Model Switching")
        switching_success = tester.test_intelligent_switching()
        if switching_success:
            logger.info("✅ Model switching working correctly")
        else:
            logger.error("❌ Model switching failed")
        
        # Test 4: Complete Pipeline
        logger.info("\n🔄 TEST 4: Complete Processing Pipeline")
        pipeline_results = await tester.test_complete_processing_pipeline()
        
        if pipeline_results["success"]:
            logger.info("✅ Complete pipeline test successful!")
            logger.info(f"   📊 Performance Summary:")
            perf = pipeline_results["performance_summary"]
            logger.info(f"      Classification: {perf['avg_classification_time']:.1f}s avg")
            logger.info(f"      Wisdom: {perf['avg_wisdom_time']:.1f}s avg")
            logger.info(f"      Analysis: {perf['avg_analysis_time']:.1f}s avg")
            logger.info(f"      Total Pipeline: {pipeline_results['total_time']:.1f}s")
        else:
            logger.error(f"❌ Pipeline test failed: {pipeline_results.get('error', 'Unknown error')}")
        
        logger.info("\n🎉 Test Suite Complete!")
        logger.info("=" * 60)
        
        # Summary
        total_tests = 4
        passed_tests = sum([
            available_count > 0,
            len([t for t in load_times.values() if t > 0]) > 0,
            switching_success,
            pipeline_results["success"]
        ])
        
        logger.info(f"📊 SUMMARY: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            logger.info("🎯 ALL SYSTEMS OPERATIONAL! Your AI-Horizon is ready for production.")
        else:
            logger.warning(f"⚠️  {total_tests - passed_tests} tests failed. Check logs above.")
    
    finally:
        tester.cleanup()

if __name__ == "__main__":
    asyncio.run(main()) 