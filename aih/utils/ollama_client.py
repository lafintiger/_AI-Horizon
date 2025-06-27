"""
Ollama client wrapper for local LLM integration.

Replaces OpenAI and Anthropic API calls with local Ollama models,
providing the same interface for seamless migration.
"""

import json
import time
import requests
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from aih.config import settings
from aih.utils.logging import get_logger, log_api_call
from aih.utils.cost_tracker import cost_tracker

logger = logging.getLogger(__name__)

@dataclass
class OllamaResponse:
    """Standardized response format matching OpenAI/Anthropic patterns."""
    content: str
    model: str
    tokens_used: int
    elapsed_time: float
    success: bool
    error: Optional[str] = None

class OllamaClient:
    """
    Unified client for Ollama models replacing OpenAI/Anthropic APIs.
    
    Provides the same interface as external APIs but routes to local models
    running on Ollama. Supports multiple models optimized for different tasks
    with intelligent model loading/unloading for memory management.
    
    Optimized Model Selection Based on Available Models:
    - Classification: llama3:latest (fast, lightweight, accurate)
    - Wisdom Extraction: qwen3:32b-q8_0 (superior reasoning, worth the load time)
    - Chat/RAG: mistral-nemo:12b-instruct-2407-q6_K (excellent for structured responses)
    - Analysis: llama3.3:70b-instruct-q5_K_M (top-tier analysis, managed loading)
    - Coding: qwen2.5-coder:32b-instruct-fp16 (specialized for code analysis)
    - Heavy Analysis: nemotron:70b-instruct-q5_K_M (alternative to llama3.3)
    """
    
    def __init__(self, base_url: str = None):
        """
        Initialize Ollama client with optimized model selection.
        
        Args:
            base_url: Ollama server URL (defaults to config setting)
        """
        self.base_url = base_url or getattr(settings, 'ollama_url', 'http://localhost:11434')
        self.session = requests.Session()
        self.current_loaded_model = None
        self.model_load_timeout = 180  # 3 minutes for large models
        
        # Optimized model assignments based on available high-quality models
        self.models = {
            # Fast tasks - keep lightweight
            "classification": getattr(settings, 'local_classification_model', 'llama3:latest'),
            
            # Reasoning tasks - use powerful models
            "wisdom": getattr(settings, 'local_wisdom_model', 'qwen3:32b-q8_0'),
            
            # Structured responses - balanced performance
            "chat": getattr(settings, 'local_chat_model', 'mistral-nemo:12b-instruct-2407-q6_K'),
            
            # Deep analysis - top-tier models
            "analysis": getattr(settings, 'local_analysis_model', 'llama3.3:70b-instruct-q5_K_M'),
            
            # Code analysis - specialized model
            "coding": getattr(settings, 'local_coding_model', 'qwen2.5-coder:32b-instruct-fp16'),
            
            # Alternative heavy analysis
            "heavy_analysis": getattr(settings, 'local_heavy_analysis_model', 'nemotron:70b-instruct-q5_K_M')
        }
        
        # Model memory requirements (approximate GB)
        self.model_memory_requirements = {
            'llama3:latest': 4,
            'mistral:latest': 4,
            'qwen3:latest': 5,
            'mistral-nemo:12b-instruct-2407-q6_K': 12,
            'qwen3:32b-q8_0': 32,
            'gemma3:27b-it-q8_0': 27,
            'llama3.3:70b-instruct-q5_K_M': 45,
            'nemotron:70b-instruct-q5_K_M': 45,
            'cogito:70b': 45,
            'qwen2.5-coder:32b-instruct-fp16': 32,
            'meditron:70b-q5_1': 45,
            'aya-expanse:32b-fp16': 32
        }
        
        logger.info(f"🤖 Ollama client initialized: {self.base_url}")
        logger.info(f"   Optimized models configured: {self.models}")
    
    def validate_connection(self) -> bool:
        """Test Ollama connectivity."""
        try:
            response = self.session.get(f"{self.base_url}/api/tags", timeout=10)
            if response.status_code == 200:
                models = response.json().get('models', [])
                available_models = [m['name'] for m in models]
                logger.info(f"✅ Ollama connected with {len(available_models)} models")
                
                # Check if our configured models are available
                missing_models = []
                for task, model in self.models.items():
                    if model not in available_models:
                        missing_models.append(f"{task}: {model}")
                
                if missing_models:
                    logger.warning(f"⚠️  Missing models: {missing_models}")
                    logger.warning("   Install with: ollama pull <model_name>")
                
                return True
            else:
                logger.error(f"❌ Ollama connection failed: HTTP {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Ollama connection error: {e}")
            return False
    
    def _unload_model(self, model_name: str) -> bool:
        """
        Unload a model from memory to free up resources.
        
        Args:
            model_name: Name of model to unload
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"🔄 Unloading model: {model_name}")
            response = self.session.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model_name,
                    "keep_alive": 0  # Unload immediately
                },
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Model {model_name} unloaded successfully")
                if self.current_loaded_model == model_name:
                    self.current_loaded_model = None
                return True
            else:
                logger.warning(f"⚠️  Failed to unload {model_name}: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error unloading model {model_name}: {e}")
            return False

    def _load_model(self, model_name: str, wait_for_load: bool = True) -> bool:
        """
        Load a model into memory.
        
        Args:
            model_name: Name of model to load
            wait_for_load: Whether to wait for model to fully load
            
        Returns:
            True if successful, False otherwise
        """
        try:
            memory_req = self.model_memory_requirements.get(model_name, 10)
            logger.info(f"🚀 Loading model: {model_name} (~{memory_req}GB)")
            
            # Send a simple prompt to trigger model loading
            start_time = time.time()
            response = self.session.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model_name,
                    "prompt": "Hello",
                    "stream": False,
                    "options": {"num_predict": 1}
                },
                timeout=self.model_load_timeout
            )
            
            load_time = time.time() - start_time
            
            if response.status_code == 200:
                self.current_loaded_model = model_name
                logger.info(f"✅ Model {model_name} loaded in {load_time:.1f}s")
                return True
            else:
                logger.error(f"❌ Failed to load {model_name}: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error loading model {model_name}: {e}")
            return False

    def _smart_model_switch(self, target_model: str) -> bool:
        """
        Intelligently switch models, unloading heavy models when needed.
        
        Args:
            target_model: Model to switch to
            
        Returns:
            True if switch successful, False otherwise
        """
        if self.current_loaded_model == target_model:
            logger.debug(f"✅ Model {target_model} already loaded")
            return True
        
        # Unload current model if it's a heavy one (>20GB)
        if self.current_loaded_model:
            current_memory = self.model_memory_requirements.get(self.current_loaded_model, 10)
            target_memory = self.model_memory_requirements.get(target_model, 10)
            
            # Unload if current model is heavy OR if we need a different heavy model
            if current_memory > 20 or (target_memory > 20 and current_memory > 10):
                logger.info(f"🔄 Switching from {self.current_loaded_model} ({current_memory}GB) to {target_model} ({target_memory}GB)")
                self._unload_model(self.current_loaded_model)
                # Wait a moment for unloading to complete
                time.sleep(2)
        
        # Load the target model
        return self._load_model(target_model)

    def generate(self, prompt: str, model: str = None, task_type: str = "general", 
                 max_tokens: int = 2000, temperature: float = 0.3) -> OllamaResponse:
        """
        Generate response using Ollama model with intelligent model management.
        
        Args:
            prompt: Input prompt
            model: Specific model name (overrides task_type selection)
            task_type: Task type for automatic model selection
            max_tokens: Maximum tokens (not strictly enforced by Ollama)
            temperature: Sampling temperature
            
        Returns:
            OllamaResponse object with standardized format
        """
        # Select model based on task type if not specified
        if not model:
            model = self.models.get(task_type, self.models["classification"])
        
        # Smart model switching
        if not self._smart_model_switch(model):
            logger.warning(f"⚠️  Failed to load {model}, trying fallback")
            # Fallback to lightweight model
            fallback_model = "llama3:latest"
            if not self._smart_model_switch(fallback_model):
                logger.error(f"❌ Failed to load fallback model {fallback_model}")
                return OllamaResponse(
                    content="",
                    model=model,
                    tokens_used=0,
                    elapsed_time=0,
                    success=False,
                    error="Failed to load any model"
                )
            model = fallback_model
        
        logger.debug(f"🧠 Generating with {model}: {prompt[:100]}...")
        
        start_time = time.time()
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "top_p": 0.9,
                        "num_predict": max_tokens
                    }
                },
                timeout=300  # 5 minute timeout for long responses
            )
            
            elapsed_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                content = result.get('response', '')
                
                # Estimate tokens (rough approximation)
                estimated_tokens = len(prompt.split()) + len(content.split())
                
                # Log the API call (no cost for local models)
                log_api_call(
                    api_type="ollama",
                    prompt=prompt[:100],
                    response=content[:100],
                    tokens=estimated_tokens,
                    cost=0.0  # Local models are free!
                )
                
                # Track usage (no cost but still track for analytics)
                cost_tracker.track_api_call("ollama", model, estimated_tokens, custom_cost=0.0)
                
                logger.debug(f"✅ Generated response in {elapsed_time:.2f}s ({estimated_tokens} tokens)")
                
                return OllamaResponse(
                    content=content,
                    model=model,
                    tokens_used=estimated_tokens,
                    elapsed_time=elapsed_time,
                    success=True
                )
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                logger.error(f"❌ Ollama generation failed: {error_msg}")
                
                return OllamaResponse(
                    content="",
                    model=model,
                    tokens_used=0,
                    elapsed_time=time.time() - start_time,
                    success=False,
                    error=error_msg
                )
                
        except Exception as e:
            error_msg = str(e)
            elapsed_time = time.time() - start_time
            logger.error(f"❌ Ollama generation error: {error_msg}")
            
            return OllamaResponse(
                content="",
                model=model or "unknown",
                tokens_used=0,
                elapsed_time=elapsed_time,
                success=False,
                error=error_msg
            )
    
    def classify_artifact(self, content: str, title: str = "", 
                         dcwf_context: str = "") -> OllamaResponse:
        """
        Classify content into AI impact categories.
        
        Args:
            content: Content to classify
            title: Optional title
            dcwf_context: Optional DCWF framework context
            
        Returns:
            OllamaResponse with classification JSON
        """
        prompt = f"""You are a cybersecurity workforce analyst. Classify this content into one of four AI impact categories:

Categories:
- replace: Tasks completely automated by AI
- augment: Tasks requiring AI assistance to perform effectively  
- new_tasks: Jobs/tasks created because of AI developments
- human_only: Tasks remaining predominantly human-driven

{f"Title: {title}" if title else ""}

Content: {content[:2000]}...

{f"DCWF Context: {dcwf_context}" if dcwf_context else ""}

Respond with ONLY a JSON object in this exact format:
{{
    "category": "replace|augment|new_tasks|human_only",
    "confidence": 0.85,
    "rationale": "Brief explanation of why this content fits the category",
    "supporting_evidence": ["specific quote or fact 1", "specific quote or fact 2"]
}}"""
        
        return self.generate(prompt, task_type="classification", temperature=0.2)
    
    def extract_wisdom(self, content: str, title: str = "") -> OllamaResponse:
        """
        Extract key insights and wisdom from content.
        
        Args:
            content: Content to analyze
            title: Optional title
            
        Returns:
            OllamaResponse with wisdom extraction JSON
        """
        prompt = f"""Extract key insights from this cybersecurity workforce content for research purposes.

{f"Title: {title}" if title else ""}

Content: {content[:3000]}...

Return a JSON object with this exact structure:
{{
    "key_insights": [
        "Specific insight about AI impact on cybersecurity workforce",
        "Another concrete finding or trend",
        "Third key takeaway"
    ],
    "ai_impact_summary": "2-3 sentence summary of how AI affects cybersecurity work",
    "workforce_implications": "How this affects cybersecurity professionals and career paths",
    "future_predictions": "What this suggests about the future of cybersecurity jobs",
    "confidence_level": 0.8,
    "evidence_quality": "high|medium|low"
}}"""
        
        return self.generate(prompt, task_type="wisdom", temperature=0.3)
    
    def chat_response(self, query: str, context: str = "") -> OllamaResponse:
        """
        Generate chat response with optional context (RAG).
        
        Args:
            query: User query
            context: Optional context for RAG
            
        Returns:
            OllamaResponse with chat response
        """
        if context:
            prompt = f"""You are a cybersecurity workforce intelligence assistant. Answer the user's query based on the provided context.

Context:
{context[:4000]}...

User Query: {query}

Provide a helpful, accurate response based on the context. If the context doesn't contain relevant information, say so clearly."""
        else:
            prompt = f"""You are a cybersecurity workforce intelligence assistant. Answer this query:

{query}

Provide a helpful, accurate response about AI's impact on cybersecurity careers and workforce trends."""
        
        return self.generate(prompt, task_type="chat", temperature=0.4)
    
    def analyze_content(self, content: str, analysis_type: str = "general") -> OllamaResponse:
        """
        Perform detailed content analysis.
        
        Args:
            content: Content to analyze
            analysis_type: Type of analysis to perform
            
        Returns:
            OllamaResponse with analysis results
        """
        if analysis_type == "sentiment":
            prompt = f"""Analyze the sentiment and tone of this cybersecurity workforce content:

Content: {content[:2000]}...

Return JSON:
{{
    "sentiment": "positive|negative|neutral",
    "confidence": 0.85,
    "key_themes": ["theme1", "theme2", "theme3"],
    "tone_analysis": "Professional description of the tone and perspective"
}}"""
        
        elif analysis_type == "skills":
            prompt = f"""Extract cybersecurity skills and competencies mentioned in this content:

Content: {content[:2000]}...

Return JSON:
{{
    "technical_skills": ["skill1", "skill2"],
    "soft_skills": ["skill1", "skill2"],
    "ai_related_skills": ["ai skill1", "ai skill2"],
    "skill_demand_level": "high|medium|low",
    "future_skills_needed": ["emerging skill1", "emerging skill2"]
}}"""
        
        else:  # general analysis
            prompt = f"""Provide a comprehensive analysis of this cybersecurity workforce content:

Content: {content[:2000]}...

Return JSON:
{{
    "main_topics": ["topic1", "topic2", "topic3"],
    "key_findings": ["finding1", "finding2"],
    "implications": "What this means for cybersecurity workforce",
    "credibility": "Assessment of source credibility and evidence quality"
}}"""
        
        return self.generate(prompt, task_type="analysis", temperature=0.3)

    def get_available_models(self) -> List[str]:
        """Get list of available models from Ollama."""
        try:
            response = self.session.get(f"{self.base_url}/api/tags", timeout=10)
            if response.status_code == 200:
                models = response.json().get('models', [])
                return [m['name'] for m in models]
            return []
        except Exception as e:
            logger.error(f"❌ Failed to get available models: {e}")
            return []

    def cleanup_models(self):
        """Unload all models to free memory."""
        if self.current_loaded_model:
            logger.info("🧹 Cleaning up loaded models...")
            self._unload_model(self.current_loaded_model)

# Global instance for easy access
ollama_client = OllamaClient() 