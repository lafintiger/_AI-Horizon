#!/usr/bin/env python3
"""
DCWF Framework Indexer - Comprehensive Version

Provides search capabilities for the DoD Cybersecurity Workforce Framework (DCWF).
Loads all 73 work roles and categorizes tasks by AI impact potential.
"""

import json
import pandas as pd
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class DCWFFrameworkIndexer:
    """
    Comprehensive indexer for DoD Cybersecurity Workforce Framework (DCWF) data.
    
    Provides search capabilities for work roles, tasks, and competencies
    within the DCWF framework, with AI impact categorization.
    """
    
    def __init__(self):
        """Initialize the DCWF framework indexer."""
        self.excel_path = "Documents/(U) 2025-01-24 DCWF Work Role Tool_v5.0.xlsx"
        self.cache_path = "data/dcwf_comprehensive_framework.json"
        self.ai_impact_analyzer = DCWFAIImpactAnalyzer()
        self.framework_data = self._load_framework_data()
    
    def _load_framework_data(self) -> Dict[str, Any]:
        """
        Load comprehensive DCWF framework data from Excel file.
        
        Returns:
            Dictionary containing all framework data
        """
        # Check cache first
        if Path(self.cache_path).exists():
            try:
                with open(self.cache_path, 'r') as f:
                    cached_data = json.load(f)
                    # Check if cache is recent (less than 7 days old)
                    cache_date = datetime.fromisoformat(cached_data.get('generated_at', '2020-01-01'))
                    if (datetime.now() - cache_date).days < 7:
                        logger.info("Loading DCWF data from cache")
                        return cached_data
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}")
        
        logger.info("Loading comprehensive DCWF data from Excel file...")
        return self._parse_excel_file()
    
    def _parse_excel_file(self) -> Dict[str, Any]:
        """Parse the complete DCWF Excel file."""
        try:
            # Load the main roles sheet
            roles_df = pd.read_excel(self.excel_path, sheet_name='DCWF Roles', header=1)
            
            framework_data = {
                "generated_at": datetime.now().isoformat(),
                "total_work_roles": len(roles_df),
                "work_roles": [],
                "ai_impact_categories": {
                    "replace": [],
                    "augment": [],
                    "new_tasks": [],
                    "human_only": []
                }
            }
            
            # Process each work role
            for _, role_row in roles_df.iterrows():
                work_role_data = self._process_work_role(role_row)
                if work_role_data:
                    framework_data["work_roles"].append(work_role_data)
            
            # Categorize tasks by AI impact
            self._categorize_tasks_by_ai_impact(framework_data)
            
            # Cache the results
            self._save_cache(framework_data)
            
            logger.info(f"Loaded {len(framework_data['work_roles'])} work roles with comprehensive task analysis")
            return framework_data
            
        except Exception as e:
            logger.error(f"Error parsing DCWF Excel file: {e}")
            return self._get_fallback_data()
    
    def _process_work_role(self, role_row: pd.Series) -> Optional[Dict[str, Any]]:
        """Process a single work role and extract its tasks."""
        try:
            work_role_name = str(role_row.get('Work Role', '')).strip()
            dcwf_code = str(role_row.get('DCWF Code', '')).strip()
            definition = str(role_row.get('Work Role Definition', '')).strip()
            element = str(role_row.get('Element', '')).strip()
            
            if not work_role_name or work_role_name == 'nan':
                return None
            
            # Try to load the specific role sheet
            role_tasks = self._extract_role_tasks(work_role_name)
            
            work_role_data = {
                "work_role_id": f"DCWF_{dcwf_code}",
                "work_role_name": work_role_name,
                "dcwf_code": dcwf_code,
                "element": element,
                "role_description": definition,
                "tasks": role_tasks.get("tasks", []),
                "knowledge_skills": role_tasks.get("knowledge_skills", []),
                "total_tasks": len(role_tasks.get("tasks", [])),
                "ai_impact_analysis": {}
            }
            
            return work_role_data
            
        except Exception as e:
            logger.warning(f"Error processing work role: {e}")
            return None
    
    def _extract_role_tasks(self, work_role_name: str) -> Dict[str, List[str]]:
        """Extract tasks and KSAs from a specific role sheet."""
        try:
            # Map work role name to actual sheet name
            sheet_name = self._map_role_to_sheet_name(work_role_name)
            if not sheet_name:
                return {"tasks": [], "knowledge_skills": []}
            
            # Try to read the role-specific sheet
            role_df = pd.read_excel(self.excel_path, sheet_name=sheet_name)
            
            tasks = []
            knowledge_skills = []
            
            # Look for the Task/KSA column (usually column 3, index 3)
            if len(role_df.columns) >= 4:
                task_column = role_df.columns[3]  # Usually 'Unnamed: 3' contains Task/KSA descriptions
                
                for _, row in role_df.iterrows():
                    task_value = str(row.get(task_column, '')).strip()
                    
                    # Skip header rows and empty values
                    if (task_value and task_value != 'nan' and len(task_value) > 5 and
                        not task_value.startswith('Task/KSA') and 
                        not task_value.startswith('DCWF #') and
                        task_value not in ['Element', 'Work Role (DCWF Code)', 'OPR']):
                        
                        # Classify as task or knowledge/skill based on content
                        if any(indicator in task_value.lower() for indicator in [
                            'knowledge of', 'skill in', 'ability to', 'understanding of'
                        ]):
                            knowledge_skills.append(task_value)
                        else:
                            tasks.append(task_value)
            
            return {
                "tasks": tasks[:50],  # Limit to 50 tasks per role
                "knowledge_skills": knowledge_skills[:30]  # Limit to 30 KSAs per role
            }
            
        except Exception as e:
            logger.debug(f"Could not extract tasks for {work_role_name}: {e}")
            return {"tasks": [], "knowledge_skills": []}
    
    def _map_role_to_sheet_name(self, work_role_name: str) -> Optional[str]:
        """Map work role name to actual sheet name in Excel file."""
        try:
            excel_file = pd.ExcelFile(self.excel_path)
            sheet_names = excel_file.sheet_names
            
            # First try exact match
            if work_role_name in sheet_names:
                return work_role_name
            
            # Create mapping for common abbreviations
            role_mappings = {
                "Technical Support Specialist": "Tech Support Specialist",
                "Network Operations Specialist": "Net Ops Specialist", 
                "System Administrator": "System Admin",
                "Systems Requirements Planner": "Systems Req Planner",
                "Research & Development Specialist": "R&D Specialist",
                "System Testing and Evaluation Specialist": "System T&E Specialist",
                "Information Systems Security Manager": "ISSM",
                "Cyber Threat Analyst": "Threat Analyst",
                "Vulnerability Assessment Analyst": "Vuln Assessment Analyst",
                "Incident Response Specialist": "IR Specialist",
                "IT Program Auditor": "IT Auditor",
                "Authorizing Official/Designating Representative": "AO/DR",
                "Information Systems Security Developer": "ISSD",
                "Secure Software Assessor": "SW Assessor",
                "Software Developer": "Software Developer",
                "Systems Developer": "Systems Developer",
                "Database Administrator": "Database Administrator",
                "Knowledge Manager": "Knowledge Manager",
                "Enterprise Architect": "Enterprise Architect"
            }
            
            # Try mapped name
            if work_role_name in role_mappings:
                mapped_name = role_mappings[work_role_name]
                if mapped_name in sheet_names:
                    return mapped_name
            
            # Try partial matching (find sheet that contains key words)
            role_words = work_role_name.lower().split()
            for sheet_name in sheet_names:
                sheet_words = sheet_name.lower().split()
                # If at least 2 key words match, consider it a match
                matches = sum(1 for word in role_words if any(word in sheet_word for sheet_word in sheet_words))
                if matches >= 2:
                    return sheet_name
            
            return None
            
        except Exception as e:
            logger.debug(f"Error mapping role to sheet: {e}")
            return None
    
    def _categorize_tasks_by_ai_impact(self, framework_data: Dict[str, Any]):
        """Categorize all tasks by their potential AI impact."""
        logger.info("Analyzing AI impact for all DCWF tasks...")
        
        for work_role in framework_data["work_roles"]:
            role_analysis = self.ai_impact_analyzer.analyze_work_role(work_role)
            work_role["ai_impact_analysis"] = role_analysis
            
            # Add tasks to category collections
            for category, task_list in role_analysis.items():
                if category in framework_data["ai_impact_categories"]:
                    framework_data["ai_impact_categories"][category].extend([
                        {
                            "work_role": work_role["work_role_name"],
                            "dcwf_code": work_role["dcwf_code"],
                            "task": task["task"],
                            "confidence": task["confidence"],
                            "rationale": task["rationale"]
                        }
                        for task in task_list
                    ])
    
    def _save_cache(self, framework_data: Dict[str, Any]):
        """Save framework data to cache."""
        try:
            Path(self.cache_path).parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_path, 'w') as f:
                json.dump(framework_data, f, indent=2)
            logger.info(f"Cached DCWF framework data to {self.cache_path}")
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")
    
    def _get_fallback_data(self) -> Dict[str, Any]:
        """Return fallback data if Excel parsing fails."""
        return {
            "generated_at": datetime.now().isoformat(),
            "total_work_roles": 5,
            "work_roles": [
                {
                    "work_role_id": "DCWF_621",
                    "work_role_name": "Software Developer",
                    "dcwf_code": "621",
                    "element": "Software Engineering",
                    "role_description": "Executes software planning, requirements, risk management, design, development, architecture, modeling, estimation, configuration management, quality, security, and tests using software development methodologies, architectural structures, viewpoints, styles, design decisions, and frameworks across all lifecycle phases.",
                    "tasks": [
                        "Analyze information to determine, recommend, and plan the development of a new application or modification of an existing application.",
                        "Apply secure code documentation.",
                        "Conduct software debugging."
                    ],
                    "knowledge_skills": [
                        "Knowledge of software development lifecycle",
                        "Skill in secure coding practices"
                    ],
                    "total_tasks": 3,
                    "ai_impact_analysis": {}
                }
            ],
            "ai_impact_categories": {
                "replace": [],
                "augment": [],
                "new_tasks": [],
                "human_only": []
            }
        }
    
    def get_tasks_by_ai_category(self, category: str) -> List[Dict[str, Any]]:
        """Get all tasks categorized under a specific AI impact category."""
        return self.framework_data.get("ai_impact_categories", {}).get(category, [])
    
    def get_work_role_by_code(self, dcwf_code: str) -> Optional[Dict[str, Any]]:
        """Get a work role by its DCWF code."""
        for role in self.framework_data.get("work_roles", []):
            if role.get("dcwf_code") == dcwf_code:
                return role
        return None

    def search_framework(self, query: str) -> List[Dict[str, Any]]:
        """Search the comprehensive DCWF framework."""
        if not query:
            return []
        
        query_lower = query.lower()
        query_terms = set(query_lower.split())
        
        results = []
        
        for role in self.framework_data.get("work_roles", []):
            score = 0
            
            # Check work role name
            role_name = role.get("work_role_name", "").lower()
            if any(term in role_name for term in query_terms):
                score += 10
            
            # Check role description
            description = role.get("role_description", "").lower()
            description_matches = sum(1 for term in query_terms if term in description)
            score += description_matches * 2
            
            # Check tasks
            tasks = role.get("tasks", [])
            for task in tasks:
                task_lower = task.lower()
                task_matches = sum(1 for term in query_terms if term in task_lower)
                score += task_matches
            
            # Check knowledge/skills
            knowledge_skills = role.get("knowledge_skills", [])
            for ks in knowledge_skills:
                ks_lower = ks.lower()
                ks_matches = sum(1 for term in query_terms if term in ks_lower)
                score += ks_matches
            
            if score > 0:
                result = role.copy()
                result["relevance_score"] = score
                results.append(result)
        
        # Sort by relevance score
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return results[:20]  # Return top 20 results
    
    def get_framework_summary(self) -> Dict[str, Any]:
        """Get summary statistics for the framework."""
        work_roles = self.framework_data.get("work_roles", [])
        total_tasks = sum(role.get("total_tasks", 0) for role in work_roles)
        
        ai_categories = self.framework_data.get("ai_impact_categories", {})
        
        return {
            "total_work_roles": len(work_roles),
            "total_tasks": total_tasks,
            "ai_impact_distribution": {
                category: len(tasks) for category, tasks in ai_categories.items()
            },
            "generated_at": self.framework_data.get("generated_at"),
            "top_roles_by_tasks": sorted(
                [(role["work_role_name"], role["total_tasks"]) for role in work_roles],
                key=lambda x: x[1], reverse=True
            )[:10]
        }
    
    def infer_dcwf_impacts(self, content: str) -> Dict[str, Any]:
        """
        Analyze content and infer DCWF framework impacts.
        
        Args:
            content: Text content to analyze
            
        Returns:
            Dictionary with DCWF impact analysis
        """
        if not content or len(content.strip()) < 50:
            return {
                "relevant_work_roles": [],
                "tasks_at_risk": [],
                "tasks_to_augment": [],
                "human_critical_tasks": [],
                "specialty_areas_affected": [],
                "inference_confidence": 0.0
            }
        
        content_lower = content.lower()
        
        # Find relevant work roles based on content
        relevant_roles = []
        tasks_at_risk = []
        tasks_to_augment = []
        human_critical_tasks = []
        specialty_areas = set()
        
        # Analyze each work role for relevance
        for role in self.framework_data.get("work_roles", []):
            role_relevance = self._calculate_role_relevance(role, content_lower)
            
            if role_relevance > 0.3:  # Threshold for relevance
                relevant_roles.append({
                    "work_role": role["work_role_name"],
                    "dcwf_code": role["dcwf_code"],
                    "relevance_score": role_relevance
                })
                
                # Add specialty area
                if role.get("element"):
                    specialty_areas.add(role["element"])
                
                # Analyze tasks within this role
                ai_analysis = role.get("ai_impact_analysis", {})
                
                # Categorize tasks based on AI impact
                for category, task_list in ai_analysis.items():
                    for task_info in task_list:
                        task_text = task_info.get("task", "")
                        confidence = task_info.get("confidence", 0)
                        
                        if confidence > 0.5:  # Only high-confidence tasks
                            task_data = {
                                "task": task_text,
                                "work_role": role["work_role_name"],
                                "confidence": confidence,
                                "category": category
                            }
                            
                            if category == "replace":
                                tasks_at_risk.append(task_data)
                            elif category == "augment":
                                tasks_to_augment.append(task_data)
                            elif category == "human_only":
                                human_critical_tasks.append(task_data)
        
        # Sort by relevance/confidence
        relevant_roles.sort(key=lambda x: x["relevance_score"], reverse=True)
        tasks_at_risk.sort(key=lambda x: x["confidence"], reverse=True)
        tasks_to_augment.sort(key=lambda x: x["confidence"], reverse=True)
        human_critical_tasks.sort(key=lambda x: x["confidence"], reverse=True)
        
        # Calculate overall confidence
        if relevant_roles:
            inference_confidence = sum(role["relevance_score"] for role in relevant_roles) / len(relevant_roles)
            inference_confidence = min(0.9, inference_confidence)  # Cap at 0.9
        else:
            inference_confidence = 0.0
        
        return {
            "relevant_work_roles": [role["work_role"] for role in relevant_roles[:5]],  # Top 5
            "tasks_at_risk": tasks_at_risk[:10],  # Top 10
            "tasks_to_augment": tasks_to_augment[:10],  # Top 10
            "human_critical_tasks": human_critical_tasks[:10],  # Top 10
            "specialty_areas_affected": list(specialty_areas),
            "inference_confidence": round(inference_confidence, 2)
        }
    
    def _calculate_role_relevance(self, role: Dict[str, Any], content_lower: str) -> float:
        """Calculate how relevant a work role is to the given content."""
        score = 0.0
        
        # Check role name
        role_name_words = role.get("work_role_name", "").lower().split()
        for word in role_name_words:
            if len(word) > 3 and word in content_lower:
                score += 0.2
        
        # Check role description
        description = role.get("role_description", "").lower()
        description_words = [w for w in description.split() if len(w) > 4]
        for word in description_words[:20]:  # Check first 20 meaningful words
            if word in content_lower:
                score += 0.05
        
        # Check tasks
        tasks = role.get("tasks", [])
        for task in tasks[:10]:  # Check first 10 tasks
            task_words = [w for w in task.lower().split() if len(w) > 4]
            for word in task_words[:5]:  # Check first 5 meaningful words
                if word in content_lower:
                    score += 0.02
        
        # Check knowledge/skills
        knowledge_skills = role.get("knowledge_skills", [])
        for ks in knowledge_skills[:5]:  # Check first 5 KSAs
            ks_words = [w for w in ks.lower().split() if len(w) > 4]
            for word in ks_words[:3]:  # Check first 3 meaningful words
                if word in content_lower:
                    score += 0.03
        
        return min(1.0, score)  # Cap at 1.0
    
    def find_relevant_tasks(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """
        Find DCWF tasks matching specific keywords.
        
        Args:
            keywords: List of keywords to search for
            
        Returns:
            List of matching tasks with relevance scores
        """
        if not keywords:
            return []
        
        keywords_lower = [kw.lower() for kw in keywords]
        matching_tasks = []
        
        for role in self.framework_data.get("work_roles", []):
            role_name = role.get("work_role_name", "")
            
            for task in role.get("tasks", []):
                task_lower = task.lower()
                relevance_score = 0.0
                
                # Calculate relevance based on keyword matches
                for keyword in keywords_lower:
                    if keyword in task_lower:
                        # Boost score for exact matches
                        relevance_score += 0.5
                        # Additional boost for word boundaries
                        if f" {keyword} " in f" {task_lower} ":
                            relevance_score += 0.3
                
                if relevance_score > 0:
                    matching_tasks.append({
                        "task_id": f"DCWF_{role.get('dcwf_code', 'unknown')}",
                        "description": task,
                        "relevance_score": min(1.0, relevance_score),
                        "work_role": role_name
                    })
        
        # Sort by relevance score
        matching_tasks.sort(key=lambda x: x["relevance_score"], reverse=True)
        return matching_tasks[:20]  # Return top 20 matches
    
    def get_work_role_details(self, role_name: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific work role.
        
        Args:
            role_name: Name of the work role
            
        Returns:
            Detailed work role information
        """
        for role in self.framework_data.get("work_roles", []):
            if role.get("work_role_name", "").lower() == role_name.lower():
                return {
                    "role_id": role.get("work_role_id", ""),
                    "role_name": role.get("work_role_name", ""),
                    "role_description": role.get("role_description", ""),
                    "specialty_area": role.get("element", ""),
                    "task_count": len(role.get("tasks", [])),
                    "tasks": role.get("tasks", []),
                    "knowledge_skills": role.get("knowledge_skills", []),
                    "ai_impact_analysis": role.get("ai_impact_analysis", {})
                }
        
        return {
            "role_id": "",
            "role_name": role_name,
            "role_description": "Work role not found",
            "specialty_area": "",
            "task_count": 0,
            "tasks": [],
            "knowledge_skills": [],
            "ai_impact_analysis": {}
        }


class DCWFAIImpactAnalyzer:
    """Analyzes DCWF tasks for AI impact potential."""
    
    def __init__(self):
        self.impact_indicators = {
            "replace": [
                "routine", "repetitive", "automated", "standard", "template",
                "documentation", "reporting", "monitoring", "scanning", "checking",
                "data entry", "file management", "backup", "maintenance", "update"
            ],
            "augment": [
                "analyze", "assess", "evaluate", "review", "investigate",
                "research", "plan", "design", "develop", "implement",
                "coordinate", "collaborate", "support", "assist", "enhance"
            ],
            "new_tasks": [
                "AI", "machine learning", "artificial intelligence", "automation",
                "ML", "algorithm", "model", "neural", "deep learning",
                "AI governance", "AI ethics", "AI security", "MLOps"
            ],
            "human_only": [
                "leadership", "strategic", "crisis", "judgment", "decision",
                "communication", "stakeholder", "negotiation", "creative",
                "ethical", "interpersonal", "mentoring", "training", "briefing",
                "policy", "compliance", "legal", "oversight", "management"
            ]
        }
    
    def analyze_work_role(self, work_role: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """Analyze a work role's tasks for AI impact."""
        analysis = {
            "replace": [],
            "augment": [],
            "new_tasks": [],
            "human_only": []
        }
        
        tasks = work_role.get("tasks", [])
        role_name = work_role.get("work_role_name", "")
        
        for task in tasks:
            task_analysis = self._analyze_single_task(task, role_name)
            category = task_analysis["category"]
            
            if category in analysis:
                analysis[category].append({
                    "task": task,
                    "confidence": task_analysis["confidence"],
                    "rationale": task_analysis["rationale"]
                })
        
        return analysis
    
    def _analyze_single_task(self, task: str, role_name: str) -> Dict[str, Any]:
        """Analyze a single task for AI impact category."""
        task_lower = task.lower()
        scores = {category: 0 for category in self.impact_indicators.keys()}
        
        # Score based on keyword presence
        for category, indicators in self.impact_indicators.items():
            for indicator in indicators:
                if indicator in task_lower:
                    scores[category] += 1
        
        # Determine primary category
        max_score = max(scores.values())
        if max_score == 0:
            # Default categorization based on task characteristics
            if any(word in task_lower for word in ["manage", "lead", "coordinate", "communicate"]):
                primary_category = "human_only"
                confidence = 0.6
            else:
                primary_category = "augment"
                confidence = 0.5
        else:
            primary_category = max(scores, key=scores.get)
            confidence = min(0.9, 0.5 + (max_score * 0.1))
        
        # Generate rationale
        rationale = self._generate_rationale(task, primary_category, role_name)
        
        return {
            "category": primary_category,
            "confidence": confidence,
            "rationale": rationale
        }
    
    def _generate_rationale(self, task: str, category: str, role_name: str) -> str:
        """Generate rationale for task categorization."""
        rationales = {
            "replace": f"Task involves routine/automated processes that AI can fully handle in {role_name}",
            "augment": f"Task requires human judgment enhanced by AI capabilities in {role_name}",
            "new_tasks": f"Task involves AI/ML technologies creating new responsibilities in {role_name}",
            "human_only": f"Task requires uniquely human skills (leadership, creativity, judgment) in {role_name}"
        }
        
        return rationales.get(category, f"Task classified as {category} for {role_name}") 