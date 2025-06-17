#!/usr/bin/env python3
"""
Test script for local Ollama models.
Verifies connectivity and basic functionality before migration.
"""

import json
import requests
import time
from typing import Dict, Any, List

class OllamaTestClient:
    """Test client for Ollama API."""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def test_connection(self) -> bool:
        """Test if Ollama is running and accessible."""
        try:
            response = self.session.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get('models', [])
                print(f"✅ Ollama connected! Available models: {len(models)}")
                for model in models:
                    print(f"   - {model['name']} ({model.get('size', 'unknown size')})")
                return True
            else:
                print(f"❌ Ollama connection failed: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Ollama connection error: {e}")
            return False
    
    def test_model(self, model_name: str, prompt: str) -> Dict[str, Any]:
        """Test a specific model with a prompt."""
        try:
            print(f"\n🧠 Testing model: {model_name}")
            print(f"📝 Prompt: {prompt}")
            
            start_time = time.time()
            
            response = self.session.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "top_p": 0.9
                    }
                },
                timeout=120  # 2 minute timeout
            )
            
            elapsed_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', '')
                
                print(f"✅ Response ({elapsed_time:.2f}s): {response_text[:200]}...")
                
                return {
                    'success': True,
                    'response': response_text,
                    'elapsed_time': elapsed_time,
                    'model': model_name
                }
            else:
                print(f"❌ Model test failed: HTTP {response.status_code}")
                print(f"   Response: {response.text}")
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}",
                    'elapsed_time': elapsed_time
                }
                
        except Exception as e:
            print(f"❌ Model test error: {e}")
            return {
                'success': False,
                'error': str(e),
                'elapsed_time': time.time() - start_time if 'start_time' in locals() else 0
            }
    
    def test_classification(self, model_name: str) -> Dict[str, Any]:
        """Test AI classification task."""
        prompt = """You are a cybersecurity workforce analyst. Classify this content into one of four categories:

Categories:
- replace: Tasks completely automated by AI
- augment: Tasks requiring AI assistance to perform effectively  
- new_tasks: Jobs/tasks created because of AI developments
- human_only: Tasks remaining predominantly human-driven

Content: "AI-powered vulnerability scanners can now automatically identify, prioritize, and even patch common security vulnerabilities without human intervention. The system learns from previous security incidents and can predict attack patterns."

Respond with only a JSON object like this:
{
    "category": "replace",
    "confidence": 0.85,
    "reasoning": "Brief explanation"
}"""
        
        return self.test_model(model_name, prompt)
    
    def test_wisdom_extraction(self, model_name: str) -> Dict[str, Any]:
        """Test wisdom extraction task."""
        prompt = """Extract key insights from this cybersecurity workforce content. Return a JSON object with the structure below:

Content: "The integration of AI in cybersecurity operations is creating a new class of professionals who specialize in human-AI collaboration. These 'AI-augmented analysts' combine traditional security skills with AI tool proficiency, enabling them to process 10x more security events while maintaining high accuracy in threat detection."

Return JSON:
{
    "key_insights": ["insight 1", "insight 2"],
    "ai_impact": "brief summary of AI's role",
    "workforce_implications": "how this affects cybersecurity jobs"
}"""
        
        return self.test_model(model_name, prompt)

def main():
    """Run comprehensive local model tests."""
    print("🚀 AI-Horizon Local Model Testing")
    print("=" * 50)
    
    # Test Ollama connectivity
    client = OllamaTestClient()
    if not client.test_connection():
        print("\n❌ Cannot connect to Ollama. Please ensure:")
        print("   1. Ollama is installed and running")
        print("   2. Ollama is accessible on http://localhost:11434")
        print("   3. At least one model is installed (e.g., 'ollama pull llama3.1:8b')")
        return
    
    # Recommended models for different tasks
    test_models = [
        "llama3:latest",      # Fast, good for classification (user has this)
        "qwen3:latest",       # Better reasoning, good for analysis (user has this)
        "mistral:latest",     # Good for structured tasks (user has this)
    ]
    
    results = []
    
    for model in test_models:
        print(f"\n{'='*50}")
        print(f"Testing Model: {model}")
        print(f"{'='*50}")
        
        # Test basic functionality
        basic_result = client.test_model(
            model, 
            "Hello! Can you help me analyze cybersecurity workforce trends?"
        )
        
        if basic_result['success']:
            # Test classification task
            print(f"\n📊 Classification Test:")
            classification_result = client.test_classification(model)
            
            # Test wisdom extraction
            print(f"\n🧠 Wisdom Extraction Test:")
            wisdom_result = client.test_wisdom_extraction(model)
            
            results.append({
                'model': model,
                'basic_test': basic_result,
                'classification_test': classification_result,
                'wisdom_test': wisdom_result
            })
        else:
            print(f"⚠️  Skipping advanced tests for {model} due to basic test failure")
            results.append({
                'model': model,
                'basic_test': basic_result,
                'classification_test': {'success': False, 'error': 'Basic test failed'},
                'wisdom_test': {'success': False, 'error': 'Basic test failed'}
            })
    
    # Summary report
    print(f"\n{'='*50}")
    print("SUMMARY REPORT")
    print(f"{'='*50}")
    
    working_models = []
    for result in results:
        model = result['model']
        basic_ok = result['basic_test']['success']
        classification_ok = result['classification_test']['success']
        wisdom_ok = result['wisdom_test']['success']
        
        status = "✅" if all([basic_ok, classification_ok, wisdom_ok]) else "⚠️" if basic_ok else "❌"
        print(f"{status} {model}")
        print(f"   Basic: {'✅' if basic_ok else '❌'}")
        print(f"   Classification: {'✅' if classification_ok else '❌'}")
        print(f"   Wisdom: {'✅' if wisdom_ok else '❌'}")
        
        if basic_ok and classification_ok and wisdom_ok:
            working_models.append(model)
    
    if working_models:
        print(f"\n🎉 SUCCESS! Working models for AI-Horizon:")
        for model in working_models:
            print(f"   ✅ {model}")
        print(f"\n📋 Next Steps:")
        print(f"   1. These models are ready for AI-Horizon integration")
        print(f"   2. Run the next script to set up local connectors")
        print(f"   3. Test the full system with local models")
    else:
        print(f"\n❌ No fully working models found. Please:")
        print(f"   1. Install recommended models: ollama pull llama3.1:8b")
        print(f"   2. Ensure sufficient RAM/VRAM for models")
        print(f"   3. Check Ollama logs for errors")
        
    return len(working_models) > 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 