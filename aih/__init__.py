"""
AI-Horizon: Cybersecurity Workforce Intelligence Platform

A comprehensive research platform that analyzes how artificial intelligence is transforming 
cybersecurity careers. Built for NSF research, it combines automated data collection with 
expert curation to provide evidence-based guidance for cybersecurity students graduating in 2025.

Core Mission:
    Categorize AI's impact on cybersecurity workforce into four key areas:
    - 🤖 REPLACE: Tasks completely automated by AI
    - 🤝 AUGMENT: Human-AI collaboration enhancing capabilities  
    - ⭐ NEW TASKS: Jobs created due to AI technology
    - 👤 HUMAN-ONLY: Tasks requiring uniquely human expertise

Key Features:
    - Quality Scoring System: Real-time document quality assessment
    - Reprocessing System: Algorithm reapplication to existing data
    - Interactive Visualizations: Chart.js-powered analysis tools
    - Category Narratives: Comprehensive AI impact summaries
    - Professional Web Interface: Flask-based dashboard

Author: AI-Horizon Research Team
Institution: California State University, San Bernardino
Grant: NSF Grant - AI-Horizon
Version: 2.1 - Professional Workforce Intelligence Platform
Status: Production Ready - All critical issues resolved

Package Structure:
    aih.utils/    - Core utilities (database, logging, cost tracking)
    aih.gather/   - Data collection modules
    aih.classify/ - AI categorization and classification
    aih.chat/     - RAG-based chat interface
"""

__version__ = "2.1.0"
__author__ = "AI-Horizon Research Team"
__email__ = "research@csusb.edu"
__status__ = "Production"

# Package metadata for future AI assistants
__package_info__ = {
    "name": "AI-Horizon",
    "version": __version__,
    "description": "Cybersecurity Workforce Intelligence Platform",
    "status": "Production Ready",
    "database_size": "230+ articles and growing",
    "features": [
        "Quality Scoring System",
        "Reprocessing System", 
        "Interactive Visualizations",
        "Category Narratives",
        "Professional Web Interface"
    ],
    "critical_issues": "All resolved",
    "last_major_update": "June 2025 - Version 2.1 enhancements"
}

# Core modules available for import
# Import pattern: from aih.utils.database import DatabaseManager
# All imports should be explicit to avoid circular dependencies 