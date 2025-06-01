"""
NID-based source scoring for AI-Horizon pipeline.

Implements NATO Intelligence Doctrine (NID) source reliability and information 
credibility assessment for collected artifacts.
"""

import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

from anthropic import Anthropic
from openai import OpenAI

from aih.config import (settings, SOURCE_RELIABILITY_SCALE, INFO_CREDIBILITY_SCALE)
from aih.utils.logging import get_logger, log_api_call
from aih.utils.rate_limiter import rate_limiter

logger = get_logger(__name__)

@dataclass
class SourceScore:
    """Data structure for source scoring results."""
    source_reliability: str  # A-F scale
    info_credibility: str    # 1-6 scale
    specificity_score: float     # 0-1
    recency_score: float         # 0-1
    evidence_score: float        # 0-1
    expert_score: float          # 0-1
    overall_score: float         # 0-1 composite
    rationale: str

class SourceScorer:
    """
    Scores artifacts using NID (NATO Intelligence Doctrine) methodology.
    
    Evaluates source reliability (A-F) and information credibility (1-6)
    along with additional factors for cybersecurity/AI context.
    """
    
    def __init__(self, model_name: str = None):
        """
        Initialize source scorer.
        
        Args:
            model_name: LLM model to use for scoring
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
    
    async def score_artifact(self, artifact_data: Dict[str, Any]) -> SourceScore:
        """
        Score an artifact using NID methodology.
        
        Args:
            artifact_data: Artifact dictionary containing url, title, content, metadata
            
        Returns:
            SourceScore object with detailed scoring
        """
        logger.info(f"Scoring artifact: {artifact_data.get('title', 'Untitled')[:50]}...")
        
        try:
            # Build scoring prompt
            scoring_prompt = self._build_scoring_prompt(artifact_data)
            
            # Get LLM assessment
            rate_limiter.wait_if_needed(self.client_type)
            
            if self.client_type == "anthropic":
                response = self.client.messages.create(
                    model=self.model_name,
                    max_tokens=1000,
                    temperature=0.3,
                    messages=[{"role": "user", "content": scoring_prompt}]
                )
                content = response.content[0].text
                tokens_used = response.usage.input_tokens + response.usage.output_tokens
            else:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": scoring_prompt}],
                    max_tokens=1000,
                    temperature=0.3
                )
                content = response.choices[0].message.content
                tokens_used = response.usage.total_tokens
            
            # Log API call
            estimated_cost = self._estimate_cost(tokens_used)
            log_api_call(
                api_type=self.client_type,
                prompt=scoring_prompt[:100],
                response=content[:100],
                tokens=tokens_used,
                cost=estimated_cost
            )
            
            # Parse LLM response
            score = self._parse_scoring_response(content, artifact_data)
            
            logger.info(f"Scored artifact: {score.source_reliability}{score.info_credibility} "
                       f"(overall: {score.overall_score:.2f})")
            
            return score
            
        except Exception as e:
            logger.error(f"Error scoring artifact: {e}")
            # Return default low scores on error
            return SourceScore(
                source_reliability="F",
                info_credibility="6",
                specificity_score=0.0,
                recency_score=0.0,
                evidence_score=0.0,
                expert_score=0.0,
                overall_score=0.1,
                rationale=f"Scoring failed due to error: {str(e)}"
            )
    
    def _build_scoring_prompt(self, artifact_data: Dict[str, Any]) -> str:
        """
        Build detailed scoring prompt for LLM.
        
        Args:
            artifact_data: Artifact information
            
        Returns:
            Formatted prompt string
        """
        url = artifact_data.get('url', '')
        title = artifact_data.get('title', '')
        content = artifact_data.get('content', '')
        source_type = artifact_data.get('source_type', '')
        
        # Truncate content for prompt efficiency
        content_excerpt = content[:1500] + "..." if len(content) > 1500 else content
        
        prompt = f"""You are an intelligence analyst tasked with evaluating source reliability and information credibility using NATO Intelligence Doctrine (NID) standards for a cybersecurity workforce research project.

ARTIFACT TO EVALUATE:
URL: {url}
Title: {title}
Source Type: {source_type}
Content: {content_excerpt}

EVALUATION CRITERIA:

1. SOURCE RELIABILITY (A-F Scale):
A = Reliable: No doubt about authenticity, trustworthiness, competency
B = Usually reliable: Minor doubts, mostly valid information history  
C = Fairly reliable: Some doubts, provided valid information in past
D = Not usually reliable: Significant doubts about reliability
E = Unreliable: Lacks authenticity, history of invalid information
F = Cannot be judged: Insufficient information to evaluate reliability

2. INFORMATION CREDIBILITY (1-6 Scale):
1 = Confirmed: Logical, consistent, confirmed by independent sources
2 = Probably true: Logical, consistent, not confirmed
3 = Possibly true: Reasonably logical, agrees with some information
4 = Doubtfully true: Not logical but possible, not confirmed
5 = Improbable: Not logical, contradicted by other information
6 = Cannot be judged: Validity cannot be determined

3. ADDITIONAL FACTORS (0.0-1.0 Scale):
- Specificity: How specific and detailed are the claims?
- Recency: How current is the information?
- Evidence: Are claims supported by data, studies, or concrete examples?
- Expertise: Does the author/source have relevant credentials?

ANALYSIS INSTRUCTIONS:
1. Analyze the source URL and determine its credibility level
2. Evaluate the author's expertise and credentials if available
3. Assess whether claims are supported by evidence
4. Check for logical consistency and factual accuracy
5. Consider potential bias or motivation

Provide your assessment in this EXACT format:
SOURCE_RELIABILITY: [A/B/C/D/E/F]
INFO_CREDIBILITY: [1/2/3/4/5/6]
SPECIFICITY_SCORE: [0.0-1.0]
RECENCY_SCORE: [0.0-1.0]
EVIDENCE_SCORE: [0.0-1.0]
EXPERT_SCORE: [0.0-1.0]
RATIONALE: [Detailed explanation of your scoring rationale, including specific observations about source credibility, content quality, evidence provided, and any concerns or strengths identified]
"""
        
        return prompt
    
    def _parse_scoring_response(self, response: str, artifact_data: Dict[str, Any]) -> SourceScore:
        """
        Parse LLM scoring response into SourceScore object.
        
        Args:
            response: LLM response text
            artifact_data: Original artifact data
            
        Returns:
            SourceScore object
        """
        # Extract scores using regex patterns
        reliability_match = re.search(r'SOURCE_RELIABILITY:\s*([A-F])', response)
        credibility_match = re.search(r'INFO_CREDIBILITY:\s*([1-6])', response)
        specificity_match = re.search(r'SPECIFICITY_SCORE:\s*([\d.]+)', response)
        recency_match = re.search(r'RECENCY_SCORE:\s*([\d.]+)', response)
        evidence_match = re.search(r'EVIDENCE_SCORE:\s*([\d.]+)', response)
        expert_match = re.search(r'EXPERT_SCORE:\s*([\d.]+)', response)
        rationale_match = re.search(r'RATIONALE:\s*(.+)', response, re.DOTALL)
        
        # Default values if parsing fails
        source_reliability = reliability_match.group(1) if reliability_match else "F"
        info_credibility = credibility_match.group(1) if credibility_match else "6"
        specificity_score = float(specificity_match.group(1)) if specificity_match else 0.0
        recency_score = float(recency_match.group(1)) if recency_match else 0.0
        evidence_score = float(evidence_match.group(1)) if evidence_match else 0.0
        expert_score = float(expert_match.group(1)) if expert_match else 0.0
        rationale = rationale_match.group(1).strip() if rationale_match else "Unable to parse scoring rationale"
        
        # Calculate overall score
        overall_score = self._calculate_overall_score(
            source_reliability, info_credibility, specificity_score,
            recency_score, evidence_score, expert_score
        )
        
        return SourceScore(
            source_reliability=source_reliability,
            info_credibility=info_credibility,
            specificity_score=min(1.0, max(0.0, specificity_score)),
            recency_score=min(1.0, max(0.0, recency_score)),
            evidence_score=min(1.0, max(0.0, evidence_score)),
            expert_score=min(1.0, max(0.0, expert_score)),
            overall_score=overall_score,
            rationale=rationale
        )
    
    def _calculate_overall_score(self, source_reliability: str, info_credibility: str,
                               specificity: float, recency: float, evidence: float, 
                               expert: float) -> float:
        """
        Calculate composite overall score from individual components.
        
        Args:
            source_reliability: A-F reliability score
            info_credibility: 1-6 credibility score
            specificity: Specificity score (0-1)
            recency: Recency score (0-1)
            evidence: Evidence score (0-1)
            expert: Expert score (0-1)
            
        Returns:
            Overall score (0-1)
        """
        # Convert letter grade to numeric (A=1.0, B=0.8, C=0.6, D=0.4, E=0.2, F=0.0)
        reliability_numeric = {
            'A': 1.0, 'B': 0.8, 'C': 0.6, 'D': 0.4, 'E': 0.2, 'F': 0.0
        }.get(source_reliability, 0.0)
        
        # Convert credibility to numeric (1=1.0, 2=0.8, 3=0.6, 4=0.4, 5=0.2, 6=0.0)
        credibility_numeric = {
            '1': 1.0, '2': 0.8, '3': 0.6, '4': 0.4, '5': 0.2, '6': 0.0
        }.get(info_credibility, 0.0)
        
        # Weighted average with emphasis on reliability and credibility
        weights = {
            'reliability': 0.3,
            'credibility': 0.3,
            'evidence': 0.2,
            'expert': 0.1,
            'specificity': 0.05,
            'recency': 0.05
        }
        
        overall = (
            reliability_numeric * weights['reliability'] +
            credibility_numeric * weights['credibility'] +
            evidence * weights['evidence'] +
            expert * weights['expert'] +
            specificity * weights['specificity'] +
            recency * weights['recency']
        )
        
        return round(overall, 3)
    
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