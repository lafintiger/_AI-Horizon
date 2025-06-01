"""
Configuration management for AI-Horizon pipeline.

Handles environment variables, API keys, and application settings.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pydantic import Field

# Load environment variables from .env file
load_dotenv("config.env")

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Keys
    perplexity_api_key: Optional[str] = Field(None, env="PERPLEXITY_API_KEY")
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY") 
    anthropic_api_key: Optional[str] = Field(None, env="ANTHROPIC_API_KEY")
    
    # Database
    database_url: str = Field("sqlite:///data/aih_database.db", env="DATABASE_URL")
    
    # Application Settings
    log_level: str = Field("INFO", env="LOG_LEVEL")
    debug: bool = Field(False, env="DEBUG")
    
    # Data Collection
    default_max_artifacts_per_run: int = Field(50, env="DEFAULT_MAX_ARTIFACTS_PER_RUN")
    default_search_lookback_days: int = Field(7, env="DEFAULT_SEARCH_LOOKBACK_DAYS")
    
    # Classification
    default_confidence_threshold: float = Field(0.6, env="DEFAULT_CONFIDENCE_THRESHOLD")
    default_llm_model: str = Field("claude-3-7-sonnet-20250219", env="DEFAULT_LLM_MODEL")
    
    # Rate Limiting
    max_api_calls_per_minute: int = Field(10, env="MAX_API_CALLS_PER_MINUTE")
    perplexity_requests_per_minute: int = Field(60, env="PERPLEXITY_REQUESTS_PER_MINUTE")
    
    # File Paths
    data_dir: str = Field("./data", env="DATA_DIR")
    logs_dir: str = Field("./logs", env="LOGS_DIR") 
    reports_dir: str = Field("./data/reports", env="REPORTS_DIR")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()

def get_data_path(subdir: str = "") -> Path:
    """Get path to data directory or subdirectory."""
    path = Path(settings.data_dir) / subdir
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_logs_path() -> Path:
    """Get path to logs directory."""
    path = Path(settings.logs_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_reports_path() -> Path:
    """Get path to reports directory.""" 
    path = Path(settings.reports_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path

# AI Impact Categories
AI_IMPACT_CATEGORIES = {
    "replace": {
        "name": "Replace", 
        "description": "Tasks or jobs that AI will replace entirely"
    },
    "augment": {
        "name": "Augment",
        "description": "Tasks that will require AI assistance to perform effectively"
    },
    "new_tasks": {
        "name": "New Tasks", 
        "description": "Jobs/tasks created because of AI developments"
    },
    "human_only": {
        "name": "Human-Only",
        "description": "Tasks that remain predominantly human-driven"
    }
}

# NID Source Reliability Scale
SOURCE_RELIABILITY_SCALE = {
    "A": {"name": "Reliable", "description": "No doubt about authenticity, trustworthiness, competency"},
    "B": {"name": "Usually reliable", "description": "Minor doubts, mostly valid information history"},
    "C": {"name": "Fairly reliable", "description": "Some doubts, provided valid information in past"},
    "D": {"name": "Not usually reliable", "description": "Significant doubts about reliability"},
    "E": {"name": "Unreliable", "description": "Lacks authenticity, history of invalid information"},
    "F": {"name": "Cannot be judged", "description": "Insufficient information to evaluate reliability"}
}

# NID Information Credibility Scale
INFO_CREDIBILITY_SCALE = {
    "1": {"name": "Confirmed", "description": "Logical, consistent, confirmed by independent sources"},
    "2": {"name": "Probably true", "description": "Logical, consistent, not confirmed"},
    "3": {"name": "Possibly true", "description": "Reasonably logical, agrees with some information"},
    "4": {"name": "Doubtfully true", "description": "Not logical but possible, not confirmed"},
    "5": {"name": "Improbable", "description": "Not logical, contradicted by other information"},
    "6": {"name": "Cannot be judged", "description": "Validity cannot be determined"}
}

# Search Query Templates
SEARCH_TEMPLATES = {
    "general": "AI automation cybersecurity tasks workforce impact {timeframe}",
    "replace": "vulnerability assessment incident response threat detection tasks automated by AI {timeframe}",
    "augment": "cybersecurity analysts using AI tools machine learning assistance {timeframe}",
    "new_tasks": "AI security engineer MLSecOps AI governance cybersecurity jobs created {timeframe}",
    "human_only": "strategic planning compliance human judgment cybersecurity tasks AI cannot replace {timeframe}"
}

# Task-focused search queries for multi-query collection
TASK_FOCUSED_QUERIES = {
    "replace": [
        "vulnerability scanning automated by AI tools",
        "incident response procedures AI automation",
        "threat detection machine learning cybersecurity",
        "network monitoring tasks automated AI",
        "log analysis SIEM automation artificial intelligence",
        "malware analysis automated AI security tools",
        "patch management automation cybersecurity AI"
    ],
    "augment": [
        "cybersecurity analysts AI-assisted threat hunting",
        "SOC analysts using machine learning tools",
        "penetration testing AI-enhanced tools",
        "forensic analysis AI-assisted investigation",
        "risk assessment AI-augmented cybersecurity",
        "compliance monitoring AI-supported tools"
    ],
    "new_tasks": [
        "AI security engineer jobs cybersecurity",
        "MLSecOps machine learning security operations",
        "AI governance cybersecurity roles",
        "prompt injection security specialist",
        "AI red team cybersecurity jobs",
        "algorithm auditing security positions"
    ],
    "human_only": [
        "strategic cybersecurity planning human expertise",
        "regulatory compliance human judgment cybersecurity",
        "crisis communication cybersecurity incidents",
        "stakeholder management cybersecurity leadership",
        "ethical decision making cybersecurity",
        "business strategy cybersecurity alignment"
    ]
} 