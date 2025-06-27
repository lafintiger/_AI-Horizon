"""
Local artifact classification using Ollama models.

Replaces external API dependencies with local Ollama models,
providing the same interface as the original classifier.
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from aih.config import settings, AI_IMPACT_CATEGORIES
from aih.utils.logging import get_logger
from aih.utils.ollama_client import OllamaClient, OllamaResponse

# Import DCWF framework indexer for enhanced classification
try:
    from scripts.analysis.dcwf_framework_indexer import DCWFFrameworkIndexer
    DCWF_AVAILABLE = True
except ImportError as e:
    DCWF_AVAILABLE = False

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
    dcwf_analysis: Optional[Dict[str, Any]] = None

class LocalArtifactClassifier:
    """
    Classifies artifacts into AI impact categories using local Ollama models.
    
    Provides the same interface as ArtifactClassifier but uses local models
    instead of external APIs. Enhanced with DCWF framework integration.
    
    Categories:
    - replace: Tasks/jobs AI will replace
    - augment: Tasks requiring AI assistance
    - new_tasks: New jobs created by AI
    - human_only: Tasks remaining human-driven
    """
    
    def __init__(self, model_name: str = None, ollama_client: OllamaClient = None):
        """
        Initialize local classifier with Ollama models.
        
        Args:
            model_name: Specific model to use (overrides config)
            ollama_client: Pre-configured Ollama client (optional)
        """
        self.model_name = model_name or settings.local_classification_model
        self.client = ollama_client or OllamaClient()
        
        # Validate Ollama connection
        if not self.client.validate_connection():
            logger.warning("⚠️  Ollama connection failed - classifier may not work properly")
        
        # Initialize DCWF framework indexer for enhanced analysis
        self.dcwf_indexer = None
        if DCWF_AVAILABLE:
            try:
                self.dcwf_indexer = DCWFFrameworkIndexer()
                stats = self.dcwf_indexer.get_framework_stats()
                logger.info(f"✅ DCWF Framework loaded: {stats['total_work_roles']} work roles")
            except Exception as e:
                logger.warning(f"⚠️  Failed to load DCWF Framework: {e}")
                self.dcwf_indexer = None
        else:
            logger.warning("⚠️  DCWF Framework integration disabled")
        
        logger.info(f"🤖 Local classifier initialized with model: {self.model_name}")
    
    def classify_artifact(self, artifact_data: Dict[str, Any], 
                         multi_class: bool = True) -> List[Classification]:
        """
        Classify an artifact into AI impact categories using local models.
        
        Args:
            artifact_data: Artifact dictionary with content and metadata
            multi_class: If True, allows multiple classifications per artifact
            
        Returns:
            List of Classification objects with DCWF analysis included
        """
        logger.info(f"🔍 Classifying artifact: {artifact_data.get('title', 'Untitled')[:50]}...")
        
        try:
            # Step 1: Perform DCWF analysis if available
            dcwf_analysis = None
            if self.dcwf_indexer:
                try:
                    content = artifact_data.get('content', '')
                    dcwf_analysis = self.dcwf_indexer.infer_dcwf_impacts(content)
                    logger.info(f"📊 DCWF Analysis: {len(dcwf_analysis.get('relevant_work_roles', []))} relevant work roles")
                except Exception as e:
                    logger.warning(f"⚠️  DCWF analysis failed: {e}")
                    dcwf_analysis = None
            
            # Step 2: Use Ollama for classification
            response = self.client.classify_artifact(
                content=artifact_data.get('content', ''),
                title=artifact_data.get('title', ''),
                dcwf_context=self._format_dcwf_context(dcwf_analysis) if dcwf_analysis else ""
            )
            
            if not response.success:
                logger.error(f"❌ Classification failed: {response.error}")
                return self._create_fallback_classification(dcwf_analysis)
            
            # Step 3: Parse the response
            classifications = self._parse_classification_response(
                response.content, multi_class, dcwf_analysis
            )
            
            logger.info(f"✅ Classified artifact into {len(classifications)} categories: "
                       f"{[c.category for c in classifications]}")
            
            return classifications
            
        except Exception as e:
            logger.error(f"❌ Error classifying artifact: {e}")
            return self._create_fallback_classification(dcwf_analysis)
    
    def _format_dcwf_context(self, dcwf_analysis: Dict[str, Any]) -> str:
        """Format DCWF analysis for inclusion in prompt."""
        if not dcwf_analysis:
            return ""
        
        context_parts = []
        
        if dcwf_analysis.get('relevant_work_roles'):
            roles = ', '.join(dcwf_analysis['relevant_work_roles'])
            context_parts.append(f"Relevant DoD work roles: {roles}")
        
        if dcwf_analysis.get('tasks_at_risk'):
            tasks = len(dcwf_analysis['tasks_at_risk'])
            context_parts.append(f"Tasks potentially at risk: {tasks}")
        
        if dcwf_analysis.get('tasks_to_augment'):
            tasks = len(dcwf_analysis['tasks_to_augment'])
            context_parts.append(f"Tasks likely to be augmented: {tasks}")
        
        return "; ".join(context_parts)
    
    def _parse_classification_response(self, response: str, 
                                     multi_class: bool,
                                     dcwf_analysis: Optional[Dict[str, Any]]) -> List[Classification]:
        """
        Parse Ollama classification response into Classification objects.
        
        Args:
            response: Raw response from Ollama
            multi_class: Whether to allow multiple classifications
            dcwf_analysis: DCWF framework analysis results
            
        Returns:
            List of Classification objects
        """
        classifications = []
        
        try:
            # Clean the response to extract JSON
            cleaned_response = self._clean_json_response(response)
            
            # Try to parse as JSON
            try:
                result = json.loads(cleaned_response)
            except json.JSONDecodeError:
                logger.warning("⚠️  Failed to parse JSON response, attempting regex extraction")
                result = self._extract_classification_data(response)
            
            # Handle both single classification and multi-classification
            if isinstance(result, list):
                # Multiple classifications
                for item in result:
                    classification = self._create_classification_from_dict(item, dcwf_analysis)
                    if classification:
                        classifications.append(classification)
            else:
                # Single classification
                classification = self._create_classification_from_dict(result, dcwf_analysis)
                if classification:
                    classifications.append(classification)
            
            # If multi_class is False, return only the highest confidence classification
            if not multi_class and len(classifications) > 1:
                classifications = [max(classifications, key=lambda x: x.confidence)]
            
        except Exception as e:
            logger.error(f"❌ Error parsing classification response: {e}")
            logger.debug(f"Raw response: {response}")
            classifications = [self._create_fallback_classification(dcwf_analysis)[0]]
        
        return classifications
    
    def _clean_json_response(self, response: str) -> str:
        """Clean response text to extract valid JSON."""
        # Remove common prefixes/suffixes
        response = response.strip()
        
        # Look for JSON block
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json_match.group(0)
        
        # If no JSON block found, return original
        return response
    
    def _extract_classification_data(self, response: str) -> Dict[str, Any]:
        """Extract classification data using regex if JSON parsing fails."""
        extracted_data = {}
        
        # Extract category
        category_match = re.search(r'"?category"?\s*:\s*"?(\w+)"?', response, re.IGNORECASE)
        if category_match:
            extracted_data['category'] = category_match.group(1).lower()
        
        # Extract confidence
        confidence_match = re.search(r'"?confidence"?\s*:\s*([0-9.]+)', response, re.IGNORECASE)
        if confidence_match:
            extracted_data['confidence'] = float(confidence_match.group(1))
        
        # Extract rationale
        rationale_match = re.search(r'"?rationale"?\s*:\s*"([^"]+)"', response, re.IGNORECASE)
        if rationale_match:
            extracted_data['rationale'] = rationale_match.group(1)
        
        # Extract supporting evidence
        evidence_match = re.search(r'"?supporting_evidence"?\s*:\s*\[(.*?)\]', response, re.DOTALL | re.IGNORECASE)
        if evidence_match:
            evidence_text = evidence_match.group(1)
            evidence_items = re.findall(r'"([^"]+)"', evidence_text)
            extracted_data['supporting_evidence'] = evidence_items
        
        # Set defaults if not found
        extracted_data.setdefault('category', 'human_only')
        extracted_data.setdefault('confidence', 0.3)
        extracted_data.setdefault('rationale', 'Extracted from unstructured response')
        extracted_data.setdefault('supporting_evidence', [])
        
        return extracted_data
    
    def _create_classification_from_dict(self, data: Dict[str, Any], 
                                       dcwf_analysis: Optional[Dict[str, Any]]) -> Optional[Classification]:
        """Create Classification object from parsed data."""
        try:
            category = data.get('category', '').lower()
            
            # Validate category
            if category not in AI_IMPACT_CATEGORIES:
                logger.warning(f"⚠️  Unknown category '{category}', defaulting to 'human_only'")
                category = 'human_only'
            
            confidence = float(data.get('confidence', 0.5))
            confidence = max(0.0, min(1.0, confidence))  # Clamp to [0,1]
            
            rationale = data.get('rationale', 'No rationale provided')
            supporting_evidence = data.get('supporting_evidence', [])
            
            # Ensure supporting_evidence is a list
            if isinstance(supporting_evidence, str):
                supporting_evidence = [supporting_evidence]
            
            return Classification(
                category=category,
                confidence=confidence,
                rationale=rationale,
                supporting_evidence=supporting_evidence,
                model_used=self.model_name,
                classified_at=datetime.now(),
                dcwf_analysis=dcwf_analysis
            )
            
        except Exception as e:
            logger.error(f"❌ Error creating classification: {e}")
            return None
    
    def _create_fallback_classification(self, dcwf_analysis: Optional[Dict[str, Any]]) -> List[Classification]:
        """Create fallback classification when parsing fails."""
        return [Classification(
            category="human_only",
            confidence=0.2,
            rationale="Classification failed - defaulting to human-only tasks",
            supporting_evidence=["Local model classification error"],
            model_used=self.model_name,
            classified_at=datetime.now(),
            dcwf_analysis=dcwf_analysis
        )]
    
    def batch_classify(self, artifacts: List[Dict[str, Any]], 
                      multi_class: bool = True) -> Dict[str, List[Classification]]:
        """
        Classify multiple artifacts efficiently.
        
        Args:
            artifacts: List of artifact dictionaries
            multi_class: Whether to allow multiple classifications
            
        Returns:
            Dictionary mapping artifact IDs to classifications
        """
        results = {}
        
        logger.info(f"🔄 Batch classifying {len(artifacts)} artifacts...")
        
        for i, artifact in enumerate(artifacts):
            artifact_id = artifact.get('id', f'artifact_{i}')
            
            try:
                classifications = self.classify_artifact(artifact, multi_class)
                results[artifact_id] = classifications
                
                if (i + 1) % 10 == 0:
                    logger.info(f"   Processed {i + 1}/{len(artifacts)} artifacts")
                    
            except Exception as e:
                logger.error(f"❌ Failed to classify artifact {artifact_id}: {e}")
                results[artifact_id] = self._create_fallback_classification(None)
        
        logger.info(f"✅ Batch classification complete: {len(results)} artifacts processed")
        return results 