"""
Enhanced Task Extraction for AI-Horizon pipeline.

Extracts specific DCWF tasks, AI tools, and example prompts from articles
to build a comprehensive task-centric database.
"""

import re
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

from anthropic import Anthropic
from openai import OpenAI

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from aih.config import settings
from aih.utils.logging import get_logger, log_api_call
from aih.utils.rate_limiter import rate_limiter
from aih.utils.database import DatabaseManager

# Import DCWF framework indexer
try:
    from scripts.analysis.dcwf_framework_indexer import DCWFFrameworkIndexer
    DCWF_AVAILABLE = True
except ImportError as e:
    logger = get_logger(__name__)
    logger.warning(f"DCWF Framework Indexer not available: {e}")
    DCWF_AVAILABLE = False

logger = get_logger(__name__)

@dataclass
class TaskExtraction:
    """Data structure for task extraction results."""
    dcwf_task_id: str
    task_name: str
    task_description: str
    work_role_id: str
    work_role_name: str
    ai_impact_category: str
    confidence_score: float
    ai_tools_mentioned: List[str]
    example_prompts: List[str]
    context_snippets: List[str]
    rationale: str
    extracted_at: datetime

@dataclass
class AIToolExtraction:
    """Data structure for AI tool extraction results."""
    tool_name: str
    tool_category: str
    vendor: str
    description: str
    capabilities: List[str]
    target_tasks: List[str]
    pricing_model: str
    website_url: str
    example_prompts: List[str]
    effectiveness_claims: List[str]

class EnhancedTaskExtractor:
    """
    Enhanced task extractor that identifies specific DCWF tasks and AI tools from articles.
    
    This classifier extends the basic classification to:
    1. Extract specific DCWF tasks mentioned in articles
    2. Identify AI tools and their capabilities
    3. Capture example prompts and use cases
    4. Map tasks to AI impact categories with high precision
    """
    
    def __init__(self, model_name: str = None):
        """Initialize the enhanced task extractor."""
        self.model_name = model_name or settings.default_llm_model
        self.db = DatabaseManager()
        
        # Initialize LLM client
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
        
        # Initialize DCWF framework indexer
        self.dcwf_indexer = None
        if DCWF_AVAILABLE:
            try:
                self.dcwf_indexer = DCWFFrameworkIndexer()
                logger.info(f"✅ DCWF Framework loaded for task extraction")
            except Exception as e:
                logger.warning(f"⚠️  Failed to load DCWF Framework: {e}")
                self.dcwf_indexer = None
        
        # Load known AI tools for better extraction
        self._load_known_ai_tools()
    
    def _load_known_ai_tools(self):
        """Load known AI tools from database or create initial set."""
        self.known_ai_tools = [
            "Cursor", "Windsurf", "ChatGPT", "Claude", "Gemini", "Copilot",
            "Codex", "Tabnine", "Kite", "Replit", "Aider", "Continue",
            "Codeium", "IntelliCode", "CodeWhisperer", "Bard", "DeepCode",
            "SonarQube", "Snyk", "Checkmarx", "Veracode", "Semgrep",
            "Burp Suite", "OWASP ZAP", "Nessus", "Nmap", "Metasploit",
            "Wireshark", "Kali Linux", "Splunk", "ELK Stack", "Suricata"
        ]
    
    def extract_tasks_from_article(self, artifact_data: Dict[str, Any]) -> List[TaskExtraction]:
        """
        Extract specific DCWF tasks mentioned in an article.
        
        Args:
            artifact_data: Article data with content and metadata
            
        Returns:
            List of TaskExtraction objects
        """
        logger.info(f"🔍 Extracting tasks from: {artifact_data.get('title', 'Untitled')[:50]}...")
        
        try:
            # Step 1: Build task extraction prompt
            prompt = self._build_task_extraction_prompt(artifact_data)
            
            # Step 2: Get LLM analysis
            rate_limiter.wait_if_needed(self.client_type)
            
            if self.client_type == "anthropic":
                response = self.client.messages.create(
                    model=self.model_name,
                    max_tokens=3000,
                    temperature=0.1,  # Very low temperature for precise extraction
                    messages=[{"role": "user", "content": prompt}]
                )
                content = response.content[0].text
                tokens_used = response.usage.input_tokens + response.usage.output_tokens
            else:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=3000,
                    temperature=0.1
                )
                content = response.choices[0].message.content
                tokens_used = response.usage.total_tokens
            
            # Log API call
            estimated_cost = self._estimate_cost(tokens_used)
            log_api_call(
                api_type=self.client_type,
                prompt=prompt[:100],
                response=content[:100],
                tokens=tokens_used,
                cost=estimated_cost
            )
            
            # Step 3: Parse task extraction response
            task_extractions = self._parse_task_extraction_response(content, artifact_data)
            
            logger.info(f"✅ Extracted {len(task_extractions)} tasks from article")
            
            return task_extractions
            
        except Exception as e:
            logger.error(f"❌ Error extracting tasks: {e}")
            return []
    
    def _build_task_extraction_prompt(self, artifact_data: Dict[str, Any]) -> str:
        """Build prompt for extracting specific DCWF tasks from article."""
        content = artifact_data.get('content', '')[:3000]  # Limit content length
        title = artifact_data.get('title', '')
        
        # Get DCWF context if available
        dcwf_context = ""
        if self.dcwf_indexer:
            try:
                dcwf_analysis = self.dcwf_indexer.infer_dcwf_impacts(content)
                if dcwf_analysis and 'relevant_work_roles' in dcwf_analysis:
                    dcwf_context = f"""
DCWF Framework Context:
{json.dumps(dcwf_analysis, indent=2)}
"""
            except Exception as e:
                logger.warning(f"Failed to get DCWF context: {e}")
        
        return f"""
You are an expert at analyzing cybersecurity articles and extracting specific tasks that are mentioned in relation to AI impact. 

ARTICLE TITLE: {title}

ARTICLE CONTENT:
{content}

{dcwf_context}

TASK EXTRACTION INSTRUCTIONS:
1. Identify specific cybersecurity tasks mentioned in this article
2. For each task, determine:
   - The specific task name and description
   - Which DCWF work role it belongs to (if mentioned or can be inferred)
   - How AI impacts this task (replace/augment/new_tasks/human_only)
   - What AI tools are mentioned for this task
   - Any example prompts or use cases provided
   - Your confidence level in this analysis

3. Focus on concrete, actionable tasks like:
   - "Develop secure code and error handling"
   - "Conduct vulnerability assessments"
   - "Analyze security logs"
   - "Implement access controls"
   - "Perform incident response"

4. Avoid vague or overly broad tasks.

RESPONSE FORMAT:
Please respond with a JSON array of task extractions. Each extraction should have this structure:

[
  {{
    "dcwf_task_id": "DCWF_XXX",  // Use actual DCWF ID if known, or "INFERRED_XXX"
    "task_name": "Specific task name",
    "task_description": "Detailed description of what this task involves",
    "work_role_id": "DCWF_XXX",  // DCWF work role ID if known
    "work_role_name": "Work role name (e.g., Software Developer, Security Analyst)",
    "ai_impact_category": "replace|augment|new_tasks|human_only",
    "confidence_score": 0.85,  // 0.0 to 1.0
    "ai_tools_mentioned": ["Tool1", "Tool2"],
    "example_prompts": ["Example prompt 1", "Example prompt 2"],
    "context_snippets": ["Relevant quote from article", "Another relevant quote"],
    "rationale": "Why you classified this task this way"
  }}
]

IMPORTANT:
- Only extract tasks that are explicitly mentioned or clearly implied in the article
- Be specific about task names and descriptions
- Include actual quotes from the article in context_snippets
- If you're not confident about a task (confidence < 0.6), include it but mark the low confidence
- Return valid JSON only, no additional text

EXTRACT TASKS:
"""
    
    def _parse_task_extraction_response(self, response: str, artifact_data: Dict[str, Any]) -> List[TaskExtraction]:
        """Parse LLM response for task extractions."""
        try:
            # Extract JSON from response
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if not json_match:
                logger.warning("No JSON found in task extraction response")
                return []
            
            json_str = json_match.group(0)
            task_data = json.loads(json_str)
            
            extractions = []
            for task in task_data:
                try:
                    extraction = TaskExtraction(
                        dcwf_task_id=task.get('dcwf_task_id', 'UNKNOWN'),
                        task_name=task.get('task_name', ''),
                        task_description=task.get('task_description', ''),
                        work_role_id=task.get('work_role_id', ''),
                        work_role_name=task.get('work_role_name', ''),
                        ai_impact_category=task.get('ai_impact_category', 'human_only'),
                        confidence_score=float(task.get('confidence_score', 0.5)),
                        ai_tools_mentioned=task.get('ai_tools_mentioned', []),
                        example_prompts=task.get('example_prompts', []),
                        context_snippets=task.get('context_snippets', []),
                        rationale=task.get('rationale', ''),
                        extracted_at=datetime.now()
                    )
                    extractions.append(extraction)
                except Exception as e:
                    logger.warning(f"Failed to parse task extraction: {e}")
                    continue
            
            return extractions
            
        except Exception as e:
            logger.error(f"Error parsing task extraction response: {e}")
            return []
    
    def save_task_extractions_to_db(self, extractions: List[TaskExtraction], 
                                  artifact_id: str) -> bool:
        """Save task extractions to the database."""
        try:
            for extraction in extractions:
                # Step 1: Save or get DCWF task
                task_data = {
                    'dcwf_task_id': extraction.dcwf_task_id,
                    'task_name': extraction.task_name,
                    'task_description': extraction.task_description,
                    'dcwf_work_role_id': extraction.work_role_id,
                    'work_role_name': extraction.work_role_name,
                    'category': 'Cybersecurity',  # Default category
                    'complexity_level': 'Intermediate'  # Default complexity
                }
                
                task_id = self.db.save_dcwf_task(task_data)
                if not task_id:
                    logger.warning(f"Failed to save task: {extraction.task_name}")
                    continue
                
                # Step 2: Save article-task mapping
                mapping_data = {
                    'artifact_id': artifact_id,
                    'task_id': task_id,
                    'relevance_score': extraction.confidence_score,
                    'mentions_count': len(extraction.context_snippets),
                    'context_snippets': extraction.context_snippets,
                    'ai_impact_mentioned': extraction.ai_impact_category,
                    'confidence_level': extraction.confidence_score
                }
                
                self.db.save_article_task_mapping(mapping_data)
                
                # Step 3: Save AI tools mentioned
                for tool_name in extraction.ai_tools_mentioned:
                    # Check if tool exists, if not create basic entry
                    tool_data = {
                        'tool_name': tool_name,
                        'tool_category': 'Unknown',
                        'description': f'AI tool mentioned in relation to {extraction.task_name}',
                        'target_tasks': [extraction.task_name]
                    }
                    
                    tool_id = self.db.save_ai_tool(tool_data)
                    if tool_id:
                        # Save task-tool recommendation
                        rec_data = {
                            'task_id': task_id,
                            'tool_id': tool_id,
                            'effectiveness_rating': extraction.confidence_score,
                            'example_prompts': extraction.example_prompts,
                            'use_case_description': extraction.rationale,
                            'supporting_articles': [artifact_id],
                            'confidence_score': extraction.confidence_score
                        }
                        self.db.save_task_tool_recommendation(rec_data)
            
            logger.info(f"✅ Saved {len(extractions)} task extractions to database")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error saving task extractions: {e}")
            return False
    
    def _estimate_cost(self, tokens: int) -> float:
        """Estimate API cost based on tokens used."""
        if "claude" in self.model_name.lower():
            return tokens * 0.000008  # Approximate Claude cost per token
        else:
            return tokens * 0.000002  # Approximate GPT cost per token
