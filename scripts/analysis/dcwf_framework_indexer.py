#!/usr/bin/env python3
"""
DCWF Framework Indexer

Loads and indexes the official DoD Cyber Workforce Framework (DCWF) for precise analysis
of AI impacts on specific DoD cybersecurity roles, tasks, and work functions.

This indexer enables sophisticated inference mapping from general AI statements 
(e.g., "no more coding in 5 years") to specific DCWF work roles and tasks.
"""

import sys
import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Set, Optional
from dataclasses import dataclass
from datetime import datetime

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from aih.utils.logging import get_logger

logger = get_logger(__name__)

@dataclass
class DCWFTask:
    """Represents a DCWF task/knowledge element."""
    task_id: str
    task_description: str
    work_role: str
    specialty_area: str
    category: str
    keywords: List[str]
    ai_vulnerability_score: float = 0.0  # How likely AI is to impact this task

@dataclass
class DCWFWorkRole:
    """Represents a DCWF work role."""
    role_id: str
    role_name: str
    role_description: str
    specialty_area: str
    tasks: List[DCWFTask]
    core_competencies: List[str]
    ai_impact_assessment: Dict[str, Any]

@dataclass
class DCWFSpecialtyArea:
    """Represents a DCWF specialty area."""
    area_id: str
    area_name: str
    area_description: str
    work_roles: List[DCWFWorkRole]

class DCWFFrameworkIndexer:
    """
    Indexes the official DoD Cyber Workforce Framework for AI impact analysis.
    
    Provides comprehensive mapping between general AI statements and specific
    DCWF work roles, tasks, and competencies.
    """
    
    def __init__(self, excel_file_path: Optional[str] = None):
        """Initialize the DCWF Framework Indexer."""
        self.excel_file_path = excel_file_path or self._find_dcwf_file()
        self.specialty_areas: Dict[str, DCWFSpecialtyArea] = {}
        self.work_roles: Dict[str, DCWFWorkRole] = {}
        self.tasks: Dict[str, DCWFTask] = {}
        self.keyword_index: Dict[str, Set[str]] = {}  # keyword -> set of task_ids
        self.ai_impact_patterns: Dict[str, List[str]] = {}
        
        # Load and index the framework
        self._load_framework()
        self._build_keyword_index()
        self._analyze_ai_vulnerabilities()
        
    def _find_dcwf_file(self) -> str:
        """Find the DCWF Excel file in the project."""
        possible_paths = [
            "Documents/(U) 2025-01-24 DCWF Work Role Tool_v5.0.xlsx",
            "../Documents/(U) 2025-01-24 DCWF Work Role Tool_v5.0.xlsx",
            "../../Documents/(U) 2025-01-24 DCWF Work Role Tool_v5.0.xlsx"
        ]
        
        for path in possible_paths:
            full_path = Path(__file__).parent.parent.parent / path
            if full_path.exists():
                logger.info(f"Found DCWF file: {full_path}")
                return str(full_path)
        
        # Fallback search
        project_root = Path(__file__).parent.parent.parent
        for file in project_root.rglob("*DCWF*.xlsx"):
            logger.info(f"Found DCWF file via search: {file}")
            return str(file)
            
        raise FileNotFoundError("DCWF Excel file not found. Please ensure it's in the Documents folder.")
    
    def _load_framework(self):
        """Load the DCWF framework from Excel file."""
        try:
            logger.info(f"Loading DCWF framework from: {self.excel_file_path}")
            
            # Read Excel file - try to load role-specific sheets
            excel_file = pd.ExcelFile(self.excel_file_path)
            logger.info(f"Available sheets: {len(excel_file.sheet_names)} sheets")
            
            # First, load the DCWF Roles overview
            roles_mapping = self._load_dcwf_roles_mapping(excel_file)
            
            # Focus on key roles for testing
            key_roles = [
                "Software Developer", "Systems Developer", "Database Administrator", 
                "IT Project Manager", "Enterprise Architect", "Cyber Defense Incident Responder"
            ]
            
            # Then load tasks from individual role sheets
            total_tasks = 0
            for sheet_name in key_roles:
                if sheet_name in excel_file.sheet_names:
                    logger.info(f"Processing {sheet_name}...")
                    tasks_loaded = self._load_role_tasks(excel_file, sheet_name, roles_mapping)
                    total_tasks += tasks_loaded
                    logger.info(f"Loaded {tasks_loaded} tasks from {sheet_name}")
                else:
                    logger.warning(f"Sheet {sheet_name} not found")
            
            logger.info(f"Loaded {len(self.work_roles)} work roles and {len(self.tasks)} tasks from DCWF")
            
            # If we didn't get enough data, supplement with fallback
            if len(self.tasks) < 10:
                logger.info("Supplementing with fallback framework")
                self._create_fallback_framework()
                
        except Exception as e:
            logger.error(f"Failed to load DCWF framework: {e}")
            import traceback
            traceback.print_exc()
            # Create a fallback minimal framework for testing
            self._create_fallback_framework()
    
    def _load_dcwf_roles_mapping(self, excel_file) -> Dict[str, Dict[str, str]]:
        """Load the mapping of DCWF codes to role information."""
        try:
            # Load DCWF Roles sheet with proper header
            roles_df = pd.read_excel(self.excel_file_path, sheet_name='DCWF Roles', header=1)
            
            roles_mapping = {}
            
            for _, row in roles_df.iterrows():
                work_role = str(row.get('Work Role', '')).strip()
                dcwf_code = str(row.get('DCWF Code', '')).strip()
                ncwf_id = str(row.get('NCWF ID', '')).strip()
                definition = str(row.get('Work Role Definition', '')).strip()
                element = str(row.get('Element', '')).strip()
                
                if work_role and dcwf_code and work_role != 'nan':
                    roles_mapping[work_role] = {
                        'dcwf_code': dcwf_code,
                        'ncwf_id': ncwf_id,
                        'definition': definition,
                        'element': element,
                        'specialty_area': self._map_element_to_specialty(element)
                    }
            
            logger.info(f"Loaded {len(roles_mapping)} role mappings")
            return roles_mapping
            
        except Exception as e:
            logger.warning(f"Failed to load DCWF roles mapping: {e}")
            return {}
    
    def _map_element_to_specialty(self, element: str) -> str:
        """Map DCWF element to specialty area."""
        element_lower = element.lower()
        
        if 'cyber it' in element_lower or 'software' in element_lower:
            return "Securely Provision (SP)"
        elif 'cyber defense' in element_lower or 'protect' in element_lower:
            return "Protect and Defend (PR)"
        elif 'cyber intelligence' in element_lower or 'analysis' in element_lower:
            return "Analyze (AN)"
        elif 'cyber operations' in element_lower:
            return "Collect and Operate (CO)"
        elif 'cyber investigation' in element_lower:
            return "Investigate (IN)"
        elif 'cyber enabler' in element_lower or 'management' in element_lower:
            return "Oversee and Govern (OV)"
        else:
            return "Operate and Maintain (OM)"
    
    def _load_role_tasks(self, excel_file, sheet_name: str, roles_mapping: Dict[str, Dict[str, str]]) -> int:
        """Load tasks for a specific work role from its sheet."""
        try:
            logger.info(f"Loading tasks for {sheet_name}")
            
            # Read the role sheet
            role_df = pd.read_excel(self.excel_file_path, sheet_name=sheet_name)
            logger.info(f"Sheet {sheet_name} has shape: {role_df.shape}")
            
            # Get role information from mapping
            role_info = roles_mapping.get(sheet_name, {})
            if not role_info:
                logger.warning(f"No role mapping found for {sheet_name}")
                return 0
            else:
                logger.info(f"Role info for {sheet_name}: {role_info}")
            
            # Find the header row (should contain 'DCWF #', 'Task/KSA')
            header_row = None
            for i, row in role_df.iterrows():
                row_values = [str(val) for val in row.values]
                if any('DCWF #' in val for val in row_values):
                    header_row = i
                    logger.info(f"Found header row at index {i}: {row_values}")
                    break
            
            if header_row is None:
                logger.warning(f"No header row found in {sheet_name}")
                # Try to find any row with "Task/KSA"
                for i, row in role_df.iterrows():
                    row_values = [str(val) for val in row.values]
                    if any('Task/KSA' in val for val in row_values):
                        header_row = i
                        logger.info(f"Found alternative header row at index {i}: {row_values}")
                        break
                
                if header_row is None:
                    logger.warning(f"No Task/KSA header found in {sheet_name}")
                    return 0
            
            # Set proper column names from header row
            new_columns = []
            header_values = role_df.iloc[header_row].values
            logger.info(f"Header values: {header_values}")
            
            for col_val in header_values:
                if pd.notna(col_val) and str(col_val).strip():
                    new_columns.append(str(col_val).strip())
                else:
                    new_columns.append(f"Unnamed_{len(new_columns)}")
            
            logger.info(f"New columns: {new_columns}")
            
            # Create a new dataframe with proper headers starting after the header row
            task_df = role_df.iloc[header_row + 1:].copy()
            task_df.columns = new_columns
            
            logger.info(f"Task dataframe shape: {task_df.shape}")
            logger.info(f"Task dataframe columns: {list(task_df.columns)}")
            
            # Extract tasks from the rows
            tasks_loaded = 0
            
            # Look for the structure: DCWF #, NIST SP #, Task/KSA, Description
            dcwf_col = None
            nist_col = None
            type_col = None
            desc_col = None
            
            # Find the relevant columns by name
            for col in task_df.columns:
                col_lower = str(col).lower()
                if 'dcwf' in col_lower and '#' in col_lower:
                    dcwf_col = col
                elif 'nist' in col_lower and '#' in col_lower:
                    nist_col = col
                elif 'task/ksa' in col_lower or 'task' in col_lower:
                    type_col = col
                    # The description should be the next column after Task/KSA
                    col_index = list(task_df.columns).index(col)
                    if col_index + 1 < len(task_df.columns):
                        desc_col = task_df.columns[col_index + 1]
            
            logger.info(f"Column mapping: DCWF={dcwf_col}, NIST={nist_col}, Type={type_col}, Description={desc_col}")
            
            if not (dcwf_col and type_col and desc_col):
                logger.warning(f"Could not find required columns in {sheet_name}")
                return 0
            
            # Process each row
            for idx, row in task_df.iterrows():
                try:
                    dcwf_num = str(row.get(dcwf_col, '')).strip()
                    nist_num = str(row.get(nist_col, '')).strip() if nist_col else ''
                    task_type = str(row.get(type_col, '')).strip()
                    task_description = str(row.get(desc_col, '')).strip()
                    
                    # Only process rows that are specifically "Task" entries
                    if (task_type.lower() != 'task' or 
                        not task_description or 
                        task_description in ['nan', 'None', ''] or 
                        len(task_description) < 10):
                        continue
                    
                    # Create DCWF task
                    task = DCWFTask(
                        task_id=f"DCWF_{role_info.get('dcwf_code', sheet_name)}_{dcwf_num}",
                        task_description=task_description,
                        work_role=sheet_name,
                        specialty_area=role_info.get('specialty_area', 'General'),
                        category="official_dcwf",
                        keywords=self._extract_keywords(task_description)
                    )
                    
                    self.tasks[task.task_id] = task
                    tasks_loaded += 1
                    
                    # Log first few tasks
                    if tasks_loaded <= 3:
                        logger.info(f"Created task {tasks_loaded}: DCWF#{dcwf_num} NIST#{nist_num} - {task_description[:100]}...")
                        
                except Exception as e:
                    logger.error(f"Error processing row {idx}: {e}")
                    continue
                
            # Create/update work role with tasks
            if tasks_loaded > 0:
                role_tasks = [task for task in self.tasks.values() if task.work_role == sheet_name]
                
                work_role = DCWFWorkRole(
                    role_id=f"DCWF_{role_info.get('dcwf_code', sheet_name.replace(' ', '_'))}",
                    role_name=sheet_name,
                    role_description=role_info.get('definition', f"DoD DCWF work role: {sheet_name}"),
                    specialty_area=role_info.get('specialty_area', 'General'),
                    tasks=role_tasks,
                    core_competencies=[],
                    ai_impact_assessment={'dcwf_code': role_info.get('dcwf_code', ''), 'ncwf_id': role_info.get('ncwf_id', '')}
                )
                
                self.work_roles[work_role.role_id] = work_role
                logger.info(f"Created work role {sheet_name} with {len(role_tasks)} tasks")
            
            return tasks_loaded
            
        except Exception as e:
            logger.error(f"Failed to load tasks for {sheet_name}: {e}")
            import traceback
            traceback.print_exc()
            return 0
    
    def _create_fallback_framework(self):
        """Create a minimal DCWF framework for testing when Excel parsing fails."""
        logger.info("Creating fallback DCWF framework for testing")
        
        # DoD Cyber Workforce Framework work roles (enhanced sample)
        fallback_roles = [
            {
                "role_id": "SP-RSK-001",
                "role_name": "Risk/Vulnerability Assessment Analyst", 
                "specialty_area": "Securely Provision (SP)",
                "tasks": [
                    "Conduct automated vulnerability scanning and analysis of systems and networks",
                    "Analyze security risks using AI-enhanced tools and provide mitigation recommendations", 
                    "Review security configurations and compliance using automated assessment tools",
                    "Generate vulnerability reports through automated analysis systems",
                    "Monitor security metrics using AI-powered dashboards"
                ]
            },
            {
                "role_id": "PR-INF-001", 
                "role_name": "Information Systems Security Manager",
                "specialty_area": "Protect and Defend (PR)",
                "tasks": [
                    "Manage information security programs with AI-assisted oversight",
                    "Oversee security incident response activities using automated detection",
                    "Coordinate security awareness training and policy development",
                    "Lead strategic security planning and governance decisions",
                    "Communicate with stakeholders and provide executive briefings"
                ]
            },
            {
                "role_id": "AN-TWA-001",
                "role_name": "Threat/Warning Analyst",
                "specialty_area": "Analyze (AN)", 
                "tasks": [
                    "Analyze cyber threat intelligence using machine learning algorithms",
                    "Produce threat assessments and warnings through automated analysis",
                    "Monitor adversary tactics and techniques using AI detection systems",
                    "Correlate threat indicators across multiple data sources",
                    "Provide strategic threat briefings to leadership"
                ]
            },
            {
                "role_id": "OM-SPA-001",
                "role_name": "Systems Administrator",
                "specialty_area": "Operate and Maintain (OM)",
                "tasks": [
                    "Maintain computer systems and networks through automated provisioning",
                    "Monitor system performance and security using AI-powered tools",
                    "Apply security patches and updates via automated deployment systems",
                    "Configure systems using infrastructure-as-code and automation",
                    "Respond to system alerts and performance issues"
                ]
            },
            {
                "role_id": "SP-DEV-001",
                "role_name": "Software Developer", 
                "specialty_area": "Securely Provision (SP)",
                "tasks": [
                    "Develop secure software applications using coding and programming languages",
                    "Implement security controls in code through software development practices",
                    "Conduct code reviews for security vulnerabilities and quality assurance",
                    "Design software architecture and system integrations",
                    "Debug and troubleshoot software applications and systems",
                    "Write automated tests and implement CI/CD pipelines",
                    "Create technical documentation and specifications"
                ]
            },
            {
                "role_id": "SP-ARC-001",
                "role_name": "Enterprise Architect",
                "specialty_area": "Securely Provision (SP)", 
                "tasks": [
                    "Design enterprise security architecture and strategic technology roadmaps",
                    "Evaluate emerging technologies including AI and automation capabilities",
                    "Lead architectural governance and standards development",
                    "Coordinate complex system integrations and migrations",
                    "Provide technical leadership and mentoring to development teams"
                ]
            },
            {
                "role_id": "OV-MGT-001",
                "role_name": "IT Project Manager",
                "specialty_area": "Oversee and Govern (OV)",
                "tasks": [
                    "Manage cybersecurity project timelines and resource allocation",
                    "Coordinate cross-functional teams and stakeholder communication",
                    "Oversee budget planning and procurement processes", 
                    "Ensure compliance with regulatory requirements and standards",
                    "Lead strategic planning sessions and executive presentations"
                ]
            },
            {
                "role_id": "PR-CIR-001",
                "role_name": "Cyber Incident Responder",
                "specialty_area": "Protect and Defend (PR)",
                "tasks": [
                    "Respond to security incidents using automated triage and analysis tools",
                    "Investigate security breaches through digital forensics and log analysis",
                    "Coordinate incident response activities across multiple teams",
                    "Document incident findings and lessons learned",
                    "Develop incident response procedures and playbooks"
                ]
            }
        ]
        
        for role_data in fallback_roles:
            tasks = []
            for i, task_desc in enumerate(role_data["tasks"]):
                task = DCWFTask(
                    task_id=f"{role_data['role_id']}_T{i+1}",
                    task_description=task_desc,
                    work_role=role_data["role_name"],
                    specialty_area=role_data["specialty_area"],
                    category="operational",
                    keywords=self._extract_keywords(task_desc)
                )
                tasks.append(task)
                self.tasks[task.task_id] = task
                
            work_role = DCWFWorkRole(
                role_id=role_data["role_id"],
                role_name=role_data["role_name"],
                role_description=f"DoD cybersecurity work role: {role_data['role_name']}",
                specialty_area=role_data["specialty_area"],
                tasks=tasks,
                core_competencies=[],
                ai_impact_assessment={}
            )
            
            self.work_roles[work_role.role_id] = work_role
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from task descriptions for indexing."""
        import re
        
        # Convert to lowercase and extract words
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Filter out common words and keep relevant terms
        stop_words = {'and', 'or', 'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        keywords = [word for word in words if len(word) > 3 and word not in stop_words]
        
        return list(set(keywords))  # Remove duplicates
    
    def _build_keyword_index(self):
        """Build keyword index for fast task lookup."""
        for task_id, task in self.tasks.items():
            for keyword in task.keywords:
                if keyword not in self.keyword_index:
                    self.keyword_index[keyword] = set()
                self.keyword_index[keyword].add(task_id)
        
        logger.info(f"Built keyword index with {len(self.keyword_index)} keywords")
    
    def _analyze_ai_vulnerabilities(self):
        """Analyze which DCWF tasks are most vulnerable to AI disruption."""
        
        # Define AI impact patterns
        automation_keywords = [
            'routine', 'repetitive', 'manual', 'monitoring', 'scanning', 'analysis', 
            'documentation', 'reporting', 'configuration', 'patching', 'updating'
        ]
        
        augmentation_keywords = [
            'assessment', 'evaluation', 'investigation', 'response', 'coordination',
            'planning', 'design', 'architecture', 'strategy', 'oversight'
        ]
        
        human_critical_keywords = [
            'leadership', 'management', 'communication', 'training', 'policy',
            'compliance', 'governance', 'decision', 'briefing', 'stakeholder'
        ]
        
        # Score each task for AI vulnerability
        for task_id, task in self.tasks.items():
            score = 0.0
            task_text = task.task_description.lower()
            
            # Check for automation indicators (high AI impact)
            automation_score = sum(1 for keyword in automation_keywords if keyword in task_text)
            score += automation_score * 0.3
            
            # Check for augmentation indicators (medium AI impact)  
            augmentation_score = sum(1 for keyword in augmentation_keywords if keyword in task_text)
            score += augmentation_score * 0.2
            
            # Check for human-critical indicators (low AI impact)
            human_score = sum(1 for keyword in human_critical_keywords if keyword in task_text)
            score -= human_score * 0.1
            
            # Normalize score
            task.ai_vulnerability_score = max(0.0, min(1.0, score / 3.0))
    
    def find_relevant_tasks(self, content: str, threshold: float = 0.3) -> List[DCWFTask]:
        """Find DCWF tasks relevant to the given content."""
        content_keywords = self._extract_keywords(content)
        
        task_scores = {}
        
        # Score tasks based on keyword overlap
        for keyword in content_keywords:
            if keyword in self.keyword_index:
                for task_id in self.keyword_index[keyword]:
                    if task_id not in task_scores:
                        task_scores[task_id] = 0
                    task_scores[task_id] += 1
        
        # Normalize scores and filter by threshold
        relevant_tasks = []
        for task_id, score in task_scores.items():
            task = self.tasks[task_id]
            normalized_score = score / len(task.keywords) if task.keywords else 0
            if normalized_score >= threshold:
                relevant_tasks.append(task)
        
        # Sort by relevance score
        relevant_tasks.sort(key=lambda t: task_scores[t.task_id], reverse=True)
        return relevant_tasks[:10]  # Return top 10 most relevant
    
    def infer_dcwf_impacts(self, content: str) -> Dict[str, Any]:
        """
        Infer DCWF impacts from general AI statements.
        
        This is the key function that makes sophisticated inferences like:
        "no more coding in 5 years" -> Impact on Software Developer roles
        """
        
        # Phase 1: Find relevant tasks using keyword matching
        relevant_tasks = self.find_relevant_tasks(content)
        
        # Phase 2: Use OpenAI for sophisticated inference (NEW)
        llm_insights = self._analyze_with_openai(content, relevant_tasks)
        
        # Categorize impacts
        replace_tasks = [t for t in relevant_tasks if t.ai_vulnerability_score > 0.7]
        augment_tasks = [t for t in relevant_tasks if 0.3 <= t.ai_vulnerability_score <= 0.7]
        human_tasks = [t for t in relevant_tasks if t.ai_vulnerability_score < 0.3]
        
        # Enhance with LLM insights
        if llm_insights:
            replace_tasks.extend(llm_insights.get('replace_tasks', []))
            augment_tasks.extend(llm_insights.get('augment_tasks', []))
            human_tasks.extend(llm_insights.get('human_tasks', []))
        
        # Analyze work role impacts
        affected_roles = set()
        for task in relevant_tasks:
            affected_roles.add(task.work_role)
        
        # Add LLM-identified roles
        if llm_insights:
            affected_roles.update(llm_insights.get('affected_roles', []))
        
        # Generate specific DCWF insights
        dcwf_insights = {
            "relevant_work_roles": list(affected_roles)[:5],
            "tasks_at_risk": [
                {
                    "task_id": t.task_id if hasattr(t, 'task_id') else f"llm_task_{i}",
                    "description": t.task_description if hasattr(t, 'task_description') else t.get('task_description', ''),
                    "work_role": t.work_role if hasattr(t, 'work_role') else t.get('work_role', ''),
                    "vulnerability_score": t.ai_vulnerability_score if hasattr(t, 'ai_vulnerability_score') else 0.8
                } for i, t in enumerate(replace_tasks[:3])
            ],
            "tasks_to_augment": [
                {
                    "task_id": t.task_id if hasattr(t, 'task_id') else f"llm_task_{i}",
                    "description": t.task_description if hasattr(t, 'task_description') else t.get('task_description', ''),
                    "work_role": t.work_role if hasattr(t, 'work_role') else t.get('work_role', ''),
                    "vulnerability_score": t.ai_vulnerability_score if hasattr(t, 'ai_vulnerability_score') else 0.5
                } for i, t in enumerate(augment_tasks[:3])
            ],
            "human_critical_tasks": [
                {
                    "task_id": t.task_id if hasattr(t, 'task_id') else f"llm_task_{i}",
                    "description": t.task_description if hasattr(t, 'task_description') else t.get('task_description', ''),
                    "work_role": t.work_role if hasattr(t, 'work_role') else t.get('work_role', ''),
                    "vulnerability_score": t.ai_vulnerability_score if hasattr(t, 'ai_vulnerability_score') else 0.2
                } for i, t in enumerate(human_tasks[:3])
            ],
            "specialty_areas_affected": list(set(t.specialty_area for t in relevant_tasks if hasattr(t, 'specialty_area'))),
            "inference_confidence": len(relevant_tasks) / 10.0,  # Confidence based on relevance
            "total_tasks_analyzed": len(relevant_tasks),
            "llm_enhanced": llm_insights is not None,
            "sophisticated_inferences": llm_insights.get('inferences', []) if llm_insights else []
        }
        
        return dcwf_insights
    
    def _analyze_with_openai(self, content: str, relevant_tasks: List[DCWFTask]) -> Dict[str, Any]:
        """Use OpenAI to make sophisticated inferences about DCWF impacts."""
        try:
            import openai
            import os
            
            client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            
            # Create analysis prompt
            task_context = "\n".join([f"- {task.work_role}: {task.task_description[:100]}..." 
                                    for task in relevant_tasks[:5]])
            
            prompt = f"""
Analyze this cybersecurity/AI article for IMPLICIT impacts on DoD Cyber Workforce Framework (DCWF) roles.

Article Content: {content[:1500]}...

Context - Relevant DCWF Tasks Found:
{task_context}

Your task: Make sophisticated inferences about how general AI statements impact specific DoD work roles.

Examples of sophisticated inference:
- "AI will automate coding in 5 years" → Software Developer (DCWF-621) tasks at risk
- "AI enhances threat detection" → Cyber Defense Analyst roles augmented
- "Strategic planning requires human judgment" → Enterprise Architect roles remain human-critical

For each inference, categorize as:
REPLACE: AI fully automates the task
AUGMENT: Human-AI collaboration enhances capability  
HUMAN-ONLY: Requires uniquely human expertise

Focus on DoD cybersecurity work roles:
- Software Developer (DCWF-621)
- Systems Developer (DCWF-632) 
- Database Administrator (DCWF-421)
- IT Project Manager (DCWF-802)
- Enterprise Architect (DCWF-651)

Output JSON format:
{{
    "replace_tasks": [
        {{"task_description": "specific task", "work_role": "Software Developer", "inference_reasoning": "why AI will replace this"}}
    ],
    "augment_tasks": [
        {{"task_description": "specific task", "work_role": "Systems Developer", "inference_reasoning": "how AI will augment human work"}}
    ],
    "human_tasks": [
        {{"task_description": "specific task", "work_role": "Enterprise Architect", "inference_reasoning": "why humans remain critical"}}
    ],
    "affected_roles": ["Software Developer", "IT Project Manager"],
    "inferences": [
        {{"general_statement": "AI automates routine tasks", "dcwf_impact": "Software Developer routine coding tasks (DCWF-621) at risk", "confidence": "high"}}
    ]
}}
"""
            
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.3
            )
            
            result = response.choices[0].message.content
            
            # Parse JSON response
            import json
            return json.loads(result)
            
        except Exception as e:
            logger.warning(f"OpenAI analysis failed: {e}")
            return None
    
    def get_framework_summary(self) -> Dict[str, Any]:
        """Get a summary of the loaded DCWF framework."""
        return {
            "total_work_roles": len(self.work_roles),
            "total_tasks": len(self.tasks),
            "specialty_areas": list(set(role.specialty_area for role in self.work_roles.values())),
            "keyword_index_size": len(self.keyword_index),
            "framework_source": self.excel_file_path,
            "loaded_at": datetime.now().isoformat()
        }
    
    def get_work_role_details(self, role_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific work role."""
        # Find the work role by name
        target_role = None
        for role in self.work_roles.values():
            if role.role_name.lower() == role_name.lower():
                target_role = role
                break
        
        if not target_role:
            return None
        
        return {
            "role_id": target_role.role_id,
            "role_name": target_role.role_name,
            "role_description": target_role.role_description,
            "specialty_area": target_role.specialty_area,
            "task_count": len(target_role.tasks),
            "tasks": target_role.tasks,
            "core_competencies": target_role.core_competencies,
            "ai_impact_assessment": target_role.ai_impact_assessment
        }
    
    def find_relevant_tasks(self, keywords: List[str], threshold: float = 0.3) -> List[Dict[str, Any]]:
        """Find DCWF tasks matching specific keywords."""
        relevant_tasks = []
        
        for task in self.tasks.values():
            # Calculate relevance score based on keyword matches
            matches = 0
            total_keywords = len(keywords)
            
            for keyword in keywords:
                keyword_lower = keyword.lower()
                # Check task description
                if keyword_lower in task.task_description.lower():
                    matches += 1
                # Check task keywords
                elif any(keyword_lower in tk.lower() for tk in task.keywords):
                    matches += 1
            
            if total_keywords > 0:
                relevance_score = matches / total_keywords
                
                if relevance_score >= threshold:
                    relevant_tasks.append({
                        "task_id": task.task_id,
                        "description": task.task_description,
                        "work_role": task.work_role,
                        "specialty_area": task.specialty_area,
                        "relevance_score": relevance_score,
                        "keywords": task.keywords
                    })
        
        # Sort by relevance score (highest first)
        relevant_tasks.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        return relevant_tasks
    
    def export_framework_data(self, output_file: str):
        """Export the indexed framework data to JSON for caching."""
        data = {
            "metadata": self.get_framework_summary(),
            "work_roles": {
                role_id: {
                    "role_name": role.role_name,
                    "role_description": role.role_description,
                    "specialty_area": role.specialty_area,
                    "task_count": len(role.tasks)
                } for role_id, role in self.work_roles.items()
            },
            "tasks": {
                task_id: {
                    "description": task.task_description,
                    "work_role": task.work_role,
                    "specialty_area": task.specialty_area,
                    "keywords": task.keywords,
                    "ai_vulnerability_score": task.ai_vulnerability_score
                } for task_id, task in self.tasks.items()
            }
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Exported DCWF framework data to: {output_file}")

def main():
    """Test the DCWF Framework Indexer."""
    try:
        logger.info("Testing DCWF Framework Indexer...")
        
        # Initialize indexer
        indexer = DCWFFrameworkIndexer()
        
        # Show framework summary
        summary = indexer.get_framework_summary()
        print("=== DCWF Framework Summary ===")
        for key, value in summary.items():
            print(f"{key}: {value}")
        
        # Test inference with sample content
        test_content = "AI will automate coding and software development in the next 5 years. No human programmers will be needed."
        
        print(f"\n=== Testing Inference ===")
        print(f"Content: {test_content}")
        
        insights = indexer.infer_dcwf_impacts(test_content)
        
        print(f"\n=== DCWF Impact Analysis ===")
        print(f"Affected Work Roles: {insights['relevant_work_roles']}")
        print(f"Tasks at Risk: {len(insights['tasks_at_risk'])}")
        print(f"Tasks to Augment: {len(insights['tasks_to_augment'])}")
        print(f"Specialty Areas: {insights['specialty_areas_affected']}")
        print(f"Inference Confidence: {insights['inference_confidence']:.2f}")
        
        # Export framework data
        output_file = "data/dcwf_framework_index.json"
        Path(output_file).parent.mkdir(exist_ok=True)
        indexer.export_framework_data(output_file)
        
        logger.info("DCWF Framework Indexer test completed successfully")
        
    except Exception as e:
        logger.error(f"DCWF Framework Indexer test failed: {e}")
        raise

if __name__ == "__main__":
    main() 