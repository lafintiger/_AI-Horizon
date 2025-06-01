"""
Artifact classification for AI-Horizon pipeline.

Classifies artifacts into the four AI impact categories using LLM analysis.
"""

import re
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from anthropic import Anthropic
from openai import OpenAI

from aih.config import settings, AI_IMPACT_CATEGORIES
from aih.utils.logging import get_logger, log_api_call
from aih.utils.rate_limiter import rate_limiter

logger = get_logger(__name__)

@dataclass
class Classification:
    """Data structure for classification results."""
    category: str
    confidence: float
    rationale: str
    supporting_evidence: List[str]
    model_used: str
    classified_at: datetime

class ArtifactClassifier:
    """
    Classifies artifacts into AI impact categories.
    
    Categories:
    - replace: Tasks/jobs AI will replace
    - augment: Tasks requiring AI assistance
    - new_tasks: New jobs created by AI
    - human_only: Tasks remaining human-driven
    """
    
    def __init__(self, model_name: str = None):
        """
        Initialize classifier.
        
        Args:
            model_name: LLM model to use for classification
        """
        self.model_name = model_name or settings.default_llm_model
        
        # Initialize LLM client based on model
        if "claude" in self.model_name.lower():
            if not settings.anthropic_api_key:
                raise ValueError("Anthropic API key required for Claude models")
            self.client = Anthropic(api_key=settings.anthropic_api_key)
            self.client_type = "anthropic"
        else:
            if not settings.openai_api_key:
                raise ValueError("OpenAI API key required for GPT models")
            self.client = OpenAI(api_key=settings.openai_api_key)
            self.client_type = "openai"
    
    async def classify_artifact(self, artifact_data: Dict[str, Any], 
                              multi_class: bool = True) -> List[Classification]:
        """
        Classify an artifact into AI impact categories.
        
        Args:
            artifact_data: Artifact dictionary with content and metadata
            multi_class: If True, allows multiple classifications per artifact
            
        Returns:
            List of Classification objects (single item if multi_class=False)
        """
        logger.info(f"Classifying artifact: {artifact_data.get('title', 'Untitled')[:50]}...")
        
        try:
            # Build classification prompt
            classification_prompt = self._build_classification_prompt(
                artifact_data, multi_class
            )
            
            # Get LLM analysis
            rate_limiter.wait_if_needed(self.client_type)
            
            if self.client_type == "anthropic":
                response = self.client.messages.create(
                    model=self.model_name,
                    max_tokens=1500,
                    temperature=0.2,  # Lower temperature for more consistent classification
                    messages=[{"role": "user", "content": classification_prompt}]
                )
                content = response.content[0].text
                tokens_used = response.usage.input_tokens + response.usage.output_tokens
            else:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": classification_prompt}],
                    max_tokens=1500,
                    temperature=0.2
                )
                content = response.choices[0].message.content
                tokens_used = response.usage.total_tokens
            
            # Log API call
            estimated_cost = self._estimate_cost(tokens_used)
            log_api_call(
                api_type=self.client_type,
                prompt=classification_prompt[:100],
                response=content[:100],
                tokens=tokens_used,
                cost=estimated_cost
            )
            
            # Parse classification response
            classifications = self._parse_classification_response(content, multi_class)
            
            logger.info(f"Classified artifact into {len(classifications)} categories: "
                       f"{[c.category for c in classifications]}")
            
            return classifications
            
        except Exception as e:
            logger.error(f"Error classifying artifact: {e}")
            # Return default classification on error
            return [Classification(
                category="human_only",
                confidence=0.1,
                rationale=f"Classification failed due to error: {str(e)}",
                supporting_evidence=[],
                model_used=self.model_name,
                classified_at=datetime.now()
            )]
    
    def _build_classification_prompt(self, artifact_data: Dict[str, Any], 
                                   multi_class: bool) -> str:
        """
        Build classification prompt for LLM.
        
        Args:
            artifact_data: Artifact information
            multi_class: Whether to allow multiple classifications
            
        Returns:
            Formatted prompt string
        """
        url = artifact_data.get('url', '')
        title = artifact_data.get('title', '')
        content = artifact_data.get('content', '')
        source_type = artifact_data.get('source_type', '')
        
        # Truncate content for prompt efficiency
        content_excerpt = content[:2000] + "..." if len(content) > 2000 else content
        
        multi_class_instruction = """
You may assign the artifact to MULTIPLE categories if it discusses multiple types of AI impact. 
For each applicable category, provide a separate analysis.
""" if multi_class else """
Choose the SINGLE MOST PROMINENT category that best fits the primary focus of this artifact.
"""
        
        categories_desc = "\n".join([
            f"- {cat_id}: {cat_info['name']} - {cat_info['description']}"
            for cat_id, cat_info in AI_IMPACT_CATEGORIES.items()
        ])
        
        prompt = f"""You are an AI research analyst tasked with classifying content about AI's impact on cybersecurity workforce roles and tasks.

ARTIFACT TO CLASSIFY:
URL: {url}
Title: {title}
Source Type: {source_type}
Content: {content_excerpt}

CLASSIFICATION CATEGORIES:
{categories_desc}

CLASSIFICATION INSTRUCTIONS:
{multi_class_instruction}

For each category you assign, analyze:
1. What specific cybersecurity tasks or roles are mentioned?
2. How is AI expected to impact these tasks/roles?
3. What evidence supports this classification?
4. What is your confidence level (0.0-1.0)?

ANALYSIS CRITERIA:
- Replace: Look for evidence that AI will fully automate tasks, eliminate roles, or replace human decision-making
- Augment: Look for evidence that AI will assist, enhance, or require integration with human work
- New Tasks: Look for evidence of emerging roles, new skill requirements, or jobs that exist because of AI
- Human Only: Look for evidence that certain tasks will remain human-driven due to complexity, ethics, judgment, or other factors

Provide your classification(s) in this EXACT format:

CLASSIFICATION_1:
CATEGORY: [replace/augment/new_tasks/human_only]
CONFIDENCE: [0.0-1.0]
SUPPORTING_EVIDENCE: [Specific quotes or examples from the content that support this classification]
RATIONALE: [Detailed explanation of why this category fits, including specific cybersecurity tasks/roles mentioned and how AI impacts them]

[If multiple classifications, repeat with CLASSIFICATION_2, CLASSIFICATION_3, etc.]

IMPORTANT: Only classify if there is clear evidence in the content. If the artifact doesn't clearly discuss AI's impact on cybersecurity work, respond with:
NO_CLASSIFICATION: Content does not clearly address AI impact on cybersecurity workforce
"""
        
        return prompt
    
    def _parse_classification_response(self, response: str, 
                                     multi_class: bool) -> List[Classification]:
        """
        Parse LLM classification response.
        
        Args:
            response: LLM response text
            multi_class: Whether multiple classifications were requested
            
        Returns:
            List of Classification objects
        """
        classifications = []
        
        # Check for no classification case
        if "NO_CLASSIFICATION:" in response:
            return [Classification(
                category="human_only",
                confidence=0.0,
                rationale="Content does not clearly address AI impact on cybersecurity workforce",
                supporting_evidence=[],
                model_used=self.model_name,
                classified_at=datetime.now()
            )]
        
        # Find all classification blocks
        classification_pattern = r'CLASSIFICATION_\d+:\s*\n(.*?)(?=CLASSIFICATION_\d+:|$)'
        classification_blocks = re.findall(classification_pattern, response, re.DOTALL)
        
        # If no numbered classifications found, try to parse as single classification
        if not classification_blocks:
            classification_blocks = [response]
        
        for block in classification_blocks:
            try:
                # Extract components from each block
                category_match = re.search(r'CATEGORY:\s*(\w+)', block)
                confidence_match = re.search(r'CONFIDENCE:\s*([\d.]+)', block)
                evidence_match = re.search(r'SUPPORTING_EVIDENCE:\s*(.+?)(?=RATIONALE:)', 
                                         block, re.DOTALL)
                rationale_match = re.search(r'RATIONALE:\s*(.+)', block, re.DOTALL)
                
                if category_match:
                    category = category_match.group(1).lower()
                    
                    # Validate category
                    if category not in AI_IMPACT_CATEGORIES:
                        logger.warning(f"Invalid category '{category}', defaulting to 'human_only'")
                        category = "human_only"
                    
                    confidence = float(confidence_match.group(1)) if confidence_match else 0.5
                    confidence = min(1.0, max(0.0, confidence))  # Clamp to valid range
                    
                    evidence_text = evidence_match.group(1).strip() if evidence_match else ""
                    evidence_list = [e.strip() for e in evidence_text.split('\n') 
                                   if e.strip() and not e.strip().startswith('-')]
                    
                    rationale = rationale_match.group(1).strip() if rationale_match else "No rationale provided"
                    
                    classification = Classification(
                        category=category,
                        confidence=confidence,
                        rationale=rationale,
                        supporting_evidence=evidence_list,
                        model_used=self.model_name,
                        classified_at=datetime.now()
                    )
                    
                    classifications.append(classification)
                    
            except Exception as e:
                logger.warning(f"Error parsing classification block: {e}")
                continue
        
        # If no valid classifications found, return default
        if not classifications:
            classifications = [Classification(
                category="human_only",
                confidence=0.1,
                rationale="Failed to parse classification from response",
                supporting_evidence=[],
                model_used=self.model_name,
                classified_at=datetime.now()
            )]
        
        # If single classification requested, return only the highest confidence one
        if not multi_class and len(classifications) > 1:
            classifications = [max(classifications, key=lambda c: c.confidence)]
        
        return classifications
    
    def _estimate_cost(self, tokens: int) -> float:
        """
        Estimate cost of API call.
        
        Args:
            tokens: Number of tokens used
            
        Returns:
            Estimated cost in USD
        """
        if self.client_type == "anthropic":
            # Claude pricing (approximate)
            cost_per_1k_tokens = 0.008  # Blended input/output for Claude-3.5-Sonnet
        else:
            # OpenAI pricing (approximate)
            cost_per_1k_tokens = 0.0015  # GPT-4 pricing
        
        return (tokens / 1000) * cost_per_1k_tokens 