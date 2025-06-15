#!/usr/bin/env python3
"""
DCWF Framework Indexer

Provides search capabilities for the DoD Cybersecurity Workforce Framework (DCWF).
This is a stub implementation that can be enhanced with actual DCWF data.
"""

import json
from typing import List, Dict, Any
from pathlib import Path

class DCWFFrameworkIndexer:
    """
    Indexer for DoD Cybersecurity Workforce Framework (DCWF) data.
    
    Provides search capabilities for work roles, tasks, and competencies
    within the DCWF framework.
    """
    
    def __init__(self):
        """Initialize the DCWF framework indexer."""
        self.framework_data = self._load_framework_data()
    
    def _load_framework_data(self) -> Dict[str, Any]:
        """
        Load DCWF framework data.
        
        Returns:
            Dictionary containing framework data
        """
        # This is a stub implementation with sample data
        # In a full implementation, this would load actual DCWF data
        return {
            "work_roles": [
                {
                    "work_role_id": "AN-ASA-001",
                    "work_role_name": "All-Source Analyst",
                    "role_description": "Analyzes data/information from one or multiple sources to conduct preparation of the environment, respond to requests for information, and submit intelligence collection and production requirements in support of planning and operations.",
                    "specialty_areas": ["Cyber Threat Analysis", "All-Source Analysis"],
                    "tasks": [
                        "Analyze collected information to identify vulnerabilities and potential for exploitation",
                        "Analyze data sources to provide actionable recommendations",
                        "Assess the effectiveness of cybersecurity measures"
                    ],
                    "knowledge_skills": [
                        "Knowledge of cyber threats and vulnerabilities",
                        "Skill in analyzing malware",
                        "Ability to think critically"
                    ]
                },
                {
                    "work_role_id": "CO-OPL-001", 
                    "work_role_name": "Cyber Operations Planner",
                    "role_description": "Develops detailed plans for the conduct or support of the applicable range of cyber operations through collaboration with other planners, operators and/or analysts.",
                    "specialty_areas": ["Cyber Operations Planning", "Mission Planning"],
                    "tasks": [
                        "Develop cyber operations plans and orders",
                        "Coordinate with stakeholders to validate operational requirements", 
                        "Assess operational environment and capabilities"
                    ],
                    "knowledge_skills": [
                        "Knowledge of operational planning processes",
                        "Understanding of cyber operations capabilities",
                        "Skill in strategic planning"
                    ]
                },
                {
                    "work_role_id": "PR-INF-001",
                    "work_role_name": "Information Systems Security Manager", 
                    "role_description": "Responsible for the cybersecurity of a program, organization, system, or enclave.",
                    "specialty_areas": ["Information Systems Security", "Security Management"],
                    "tasks": [
                        "Develop and maintain information security policies",
                        "Oversee implementation of security controls",
                        "Conduct security risk assessments"
                    ],
                    "knowledge_skills": [
                        "Knowledge of cybersecurity principles",
                        "Understanding of risk management frameworks", 
                        "Skill in security policy development"
                    ]
                },
                {
                    "work_role_id": "SP-DEV-001",
                    "work_role_name": "Software Developer",
                    "role_description": "Develops, creates, maintains, and writes/codes new (or modifies existing) computer applications, software, or specialized utility programs.",
                    "specialty_areas": ["Software Development", "Secure Coding"],
                    "tasks": [
                        "Design and develop secure software applications",
                        "Conduct code reviews for security vulnerabilities",
                        "Implement security controls in software"
                    ],
                    "knowledge_skills": [
                        "Knowledge of secure coding practices",
                        "Skill in multiple programming languages",
                        "Understanding of software security principles"
                    ]
                },
                {
                    "work_role_id": "SP-SYS-001",
                    "work_role_name": "Information Systems Security Developer",
                    "role_description": "Designs, develops, tests, and evaluates information system security throughout the systems development lifecycle.",
                    "specialty_areas": ["Systems Security", "Security Architecture"],
                    "tasks": [
                        "Design security architecture for information systems",
                        "Develop security requirements and specifications",
                        "Test and validate security implementations"
                    ],
                    "knowledge_skills": [
                        "Knowledge of systems security engineering",
                        "Understanding of security architectures",
                        "Skill in security testing methodologies"
                    ]
                }
            ]
        }
    
    def search_framework(self, query: str) -> List[Dict[str, Any]]:
        """
        Search the DCWF framework for relevant work roles and tasks.
        
        Args:
            query: Search query string
            
        Returns:
            List of matching work roles with relevance scores
        """
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
            
            # Check specialty areas
            specialty_areas = role.get("specialty_areas", [])
            for area in specialty_areas:
                area_lower = area.lower()
                if any(term in area_lower for term in query_terms):
                    score += 3
            
            if score > 0:
                result = role.copy()
                result["relevance_score"] = score
                results.append(result)
        
        # Sort by relevance score
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        return results[:10]  # Return top 10 results
    
    def get_work_role_by_id(self, role_id: str) -> Dict[str, Any]:
        """
        Get a specific work role by its ID.
        
        Args:
            role_id: DCWF work role ID
            
        Returns:
            Work role data or empty dict if not found
        """
        for role in self.framework_data.get("work_roles", []):
            if role.get("work_role_id") == role_id:
                return role
        return {}
    
    def get_all_work_roles(self) -> List[Dict[str, Any]]:
        """
        Get all work roles in the framework.
        
        Returns:
            List of all work roles
        """
        return self.framework_data.get("work_roles", [])
    
    def get_framework_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the framework data.
        
        Returns:
            Dictionary with framework statistics
        """
        work_roles = self.framework_data.get("work_roles", [])
        
        total_tasks = sum(len(role.get("tasks", [])) for role in work_roles)
        total_knowledge_skills = sum(len(role.get("knowledge_skills", [])) for role in work_roles)
        
        specialty_areas = set()
        for role in work_roles:
            specialty_areas.update(role.get("specialty_areas", []))
        
        return {
            "total_work_roles": len(work_roles),
            "total_tasks": total_tasks,
            "total_knowledge_skills": total_knowledge_skills,
            "unique_specialty_areas": len(specialty_areas),
            "specialty_areas": list(specialty_areas)
        } 