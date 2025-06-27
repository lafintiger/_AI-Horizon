"""
Artifact classification for AI-Horizon pipeline.

Classifies artifacts into the four AI impact categories using LLM analysis
enhanced with DCWF (DoD Cyber Workforce Framework) task and role mapping.
"""

import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from anthropic import Anthropic
from openai import OpenAI

# Add project root to path for DCWF indexer import
sys.path.append(str(Path(__file__).parent.parent.parent))

from aih.config import settings, AI_IMPACT_CATEGORIES
from aih.utils.logging import get_logger, log_api_call
from aih.utils.rate_limiter import rate_limiter

# Import DCWF framework indexer for enhanced classification
try:
    from scripts.analysis.dcwf_framework_indexer import DCWFFrameworkIndexer
    DCWF_AVAILABLE = True
except ImportError as e:
    logger = get_logger(__name__)
    logger.warning(f"DCWF Framework Indexer not available: {e}")
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
    dcwf_analysis: Optional[Dict[str, Any]] = None  # NEW: DCWF-specific analysis

class ArtifactClassifier:
    """
    Classifies artifacts into AI impact categories with DCWF framework integration.
    
    Enhanced with DoD Cyber Workforce Framework (DCWF) analysis to provide
    precise mapping to specific cybersecurity work roles and tasks.
    
    Categories:
    - replace: Tasks/jobs AI will replace
    - augment: Tasks requiring AI assistance
    - new_tasks: New jobs created by AI
    - human_only: Tasks remaining human-driven
    """
    
    def __init__(self, model_name: str = None):
        """
        Initialize classifier with DCWF framework integration.
        
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
        
        # Initialize DCWF framework indexer for enhanced analysis
        self.dcwf_indexer = None
        if DCWF_AVAILABLE:
            try:
                self.dcwf_indexer = DCWFFrameworkIndexer()
                logger.info(f"✅ DCWF Framework loaded: {self.dcwf_indexer.get_framework_summary()['total_work_roles']} work roles, {self.dcwf_indexer.get_framework_summary()['total_tasks']} tasks")
            except Exception as e:
                logger.warning(f"⚠️  Failed to load DCWF Framework: {e}")
                self.dcwf_indexer = None
        else:
            logger.warning("⚠️  DCWF Framework integration disabled - install dependencies")
    
    def classify_artifact(self, artifact_data: Dict[str, Any], 
                         multi_class: bool = True) -> List[Classification]:
        """
        Classify an artifact into AI impact categories with DCWF analysis.
        
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
                    logger.info(f"📊 DCWF Analysis: {len(dcwf_analysis.get('relevant_work_roles', []))} relevant work roles identified")
                except Exception as e:
                    logger.warning(f"⚠️  DCWF analysis failed: {e}")
                    dcwf_analysis = None
            
            # Step 2: Build enhanced classification prompt with DCWF context
            classification_prompt = self._build_enhanced_classification_prompt(
                artifact_data, multi_class, dcwf_analysis
            )
            
            # Step 3: Get LLM analysis
            rate_limiter.wait_if_needed(self.client_type)
            
            if self.client_type == "anthropic":
                response = self.client.messages.create(
                    model=self.model_name,
                    max_tokens=2000,  # Increased for DCWF analysis
                    temperature=0.2,  # Lower temperature for more consistent classification
                    messages=[{"role": "user", "content": classification_prompt}]
                )
                content = response.content[0].text
                tokens_used = response.usage.input_tokens + response.usage.output_tokens
            else:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": classification_prompt}],
                    max_tokens=2000,
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
            
            # Step 4: Parse classification response with DCWF integration
            classifications = self._parse_classification_response(content, multi_class, dcwf_analysis)
            
            logger.info(f"✅ Classified artifact into {len(classifications)} categories: "
                       f"{[c.category for c in classifications]}")
            
            return classifications
            
        except Exception as e:
            logger.error(f"❌ Error classifying artifact: {e}")
            # Return default classification on error
            return [Classification(
                category="human_only",
                confidence=0.1,
                rationale=f"Classification failed due to error: {str(e)}",
                supporting_evidence=[],
                model_used=self.model_name,
                classified_at=datetime.now(),
                dcwf_analysis=dcwf_analysis
            )]
    
    def _build_enhanced_classification_prompt(self, artifact_data: Dict[str, Any], 
                                            multi_class: bool, 
                                            dcwf_analysis: Optional[Dict[str, Any]]) -> str:
        """
        Build enhanced classification prompt with DCWF framework context.
        
        Args:
            artifact_data: Artifact information
            multi_class: Whether to allow multiple classifications
            dcwf_analysis: DCWF framework analysis results
            
        Returns:
            Enhanced prompt string with DCWF context
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
        
        # Build DCWF context section
        dcwf_context = ""
        if dcwf_analysis:
            dcwf_context = f"""
DCWF FRAMEWORK ANALYSIS:
The DoD Cyber Workforce Framework analysis has identified the following relevant context:

Relevant Work Roles: {', '.join(dcwf_analysis.get('relevant_work_roles', [])[:5])}

Tasks at Risk of Replacement:
{self._format_dcwf_tasks(dcwf_analysis.get('tasks_at_risk', [])[:3])}

Tasks Likely to be Augmented:
{self._format_dcwf_tasks(dcwf_analysis.get('tasks_to_augment', [])[:3])}

Human-Critical Tasks:
{self._format_dcwf_tasks(dcwf_analysis.get('human_critical_tasks', [])[:3])}

Specialty Areas Affected: {', '.join(dcwf_analysis.get('specialty_areas_affected', []))}

Use this DCWF analysis to inform your classification and provide specific references to DoD cybersecurity work roles and tasks in your rationale.
"""
        
        prompt = f"""You are an AI research analyst tasked with classifying content about AI's impact on cybersecurity workforce roles and tasks, with specific focus on the DoD Cyber Workforce Framework (DCWF).

ARTIFACT TO CLASSIFY:
URL: {url}
Title: {title}
Source Type: {source_type}
Content: {content_excerpt}

{dcwf_context}

CLASSIFICATION CATEGORIES:
{categories_desc}

CLASSIFICATION INSTRUCTIONS:
{multi_class_instruction}

For each category you assign, analyze:
1. What specific cybersecurity tasks or roles are mentioned (reference DCWF roles when applicable)?
2. How is AI expected to impact these tasks/roles?
3. What evidence supports this classification?
4. What is your confidence level (0.0-1.0)?
5. Which specific DCWF work roles and tasks are most relevant?

ANALYSIS CRITERIA:
- Replace: Look for evidence that AI will fully automate tasks, eliminate roles, or replace human decision-making
- Augment: Look for evidence that AI will assist, enhance, or require integration with human work
- New Tasks: Look for evidence of emerging roles, new skill requirements, or jobs that exist because of AI
- Human Only: Look for evidence that certain tasks will remain human-driven due to complexity, ethics, judgment, or other factors

Provide your classification(s) in this EXACT format:

CLASSIFICATION_1:
CATEGORY: [replace/augment/new_tasks/human_only]
CONFIDENCE: [0.0-1.0]
DCWF_ROLES: [List specific DCWF work roles mentioned or relevant]
DCWF_TASKS: [List specific DCWF tasks that are impacted]
SUPPORTING_EVIDENCE: [Specific quotes or examples from the content that support this classification]
RATIONALE: [Detailed explanation of why this category fits, including specific cybersecurity tasks/roles mentioned and how AI impacts them, with DCWF context]

"""
        
        return prompt
    
    def _format_dcwf_tasks(self, tasks: List[Dict[str, Any]]) -> str:
        """Format DCWF tasks for prompt inclusion."""
        if not tasks:
            return "None identified"
        
        formatted = []
        for task in tasks:
            work_role = task.get('work_role', 'Unknown Role')
            description = task.get('description', 'No description')[:100]
            formatted.append(f"  • {work_role}: {description}...")
        
        return "\n".join(formatted)
    
    def _parse_classification_response(self, response: str, 
                                     multi_class: bool,
                                     dcwf_analysis: Optional[Dict[str, Any]]) -> List[Classification]:
        """
        Parse LLM classification response with DCWF integration.
        
        Args:
            response: LLM response text
            multi_class: Whether multiple classifications are expected
            dcwf_analysis: DCWF framework analysis results
            
        Returns:
            List of Classification objects with DCWF data
        """
        classifications = []
        
        # Split response into individual classifications
        classification_blocks = re.split(r'CLASSIFICATION_\d+:', response)
        
        for block in classification_blocks[1:]:  # Skip first empty split
            try:
                # Extract classification components
                category_match = re.search(r'CATEGORY:\s*(\w+)', block)
                confidence_match = re.search(r'CONFIDENCE:\s*([\d.]+)', block)
                dcwf_roles_match = re.search(r'DCWF_ROLES:\s*([^\n]+)', block)
                dcwf_tasks_match = re.search(r'DCWF_TASKS:\s*([^\n]+)', block)
                evidence_match = re.search(r'SUPPORTING_EVIDENCE:\s*([^\n]+(?:\n(?!RATIONALE:)[^\n]+)*)', block, re.MULTILINE)
                rationale_match = re.search(r'RATIONALE:\s*(.+)', block, re.DOTALL)
                
                if category_match and confidence_match:
                    category = category_match.group(1).lower()
                    confidence = float(confidence_match.group(1))
                    
                    # Extract DCWF-specific information
                    dcwf_roles = dcwf_roles_match.group(1).strip() if dcwf_roles_match else ""
                    dcwf_tasks = dcwf_tasks_match.group(1).strip() if dcwf_tasks_match else ""
                    
                    evidence = evidence_match.group(1).strip() if evidence_match else ""
                    rationale = rationale_match.group(1).strip() if rationale_match else ""
                    
                    # Enhance DCWF analysis with LLM insights
                    enhanced_dcwf_analysis = dcwf_analysis.copy() if dcwf_analysis else {}
                    if dcwf_roles or dcwf_tasks:
                        enhanced_dcwf_analysis.update({
                            'llm_identified_roles': dcwf_roles,
                            'llm_identified_tasks': dcwf_tasks,
                            'classification_category': category,
                            'classification_confidence': confidence
                        })
                    
                    classification = Classification(
                        category=category,
                        confidence=confidence,
                        rationale=rationale,
                        supporting_evidence=[evidence] if evidence else [],
                        model_used=self.model_name,
                        classified_at=datetime.now(),
                        dcwf_analysis=enhanced_dcwf_analysis
                    )
                    
                    classifications.append(classification)
                    
            except Exception as e:
                logger.warning(f"⚠️  Error parsing classification block: {e}")
                continue
        
        # Fallback if no classifications parsed
        if not classifications:
            logger.warning("⚠️  No valid classifications parsed, using fallback")
            classifications = [Classification(
                category="human_only",
                confidence=0.5,
                rationale="Unable to parse classification response",
                supporting_evidence=[],
                model_used=self.model_name,
                classified_at=datetime.now(),
                dcwf_analysis=dcwf_analysis
            )]
        
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