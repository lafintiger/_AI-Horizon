"""
AI-Horizon Scripts Package

Comprehensive utility scripts for AI-Horizon system operations, organized by function
for professional maintainability and clarity.

Directory Structure:
    scripts/analysis/          - Analysis tools and quality control (6 major tools)
    scripts/collection/        - Data collection and automated gathering
    scripts/fixes/             - Bug fixes and system repair utilities
    scripts/manual_entry/      - Manual entry processing and categorization
    
Root Scripts:
    reprocess_all_entries.py   - Comprehensive reprocessing system (Version 2.0+)
    generate_web_report.py     - Web intelligence report generation
    generate_student_report.py - Student career intelligence reports
    create_backup_system.py    - Database backup and recovery
    share_reports.py           - Report sharing and distribution

Key Analysis Tools (scripts/analysis/):
    - implement_quality_ranking.py     - DocumentQualityRanker system
    - comprehensive_category_narratives.py - Category narrative generation (Version 2.1)
    - ai_adoption_predictions.py       - AI adoption forecasting with skills analysis
    - job_market_sentiment.py          - Career impact sentiment analysis
    - trend_analysis.py                - Temporal pattern analysis
    - collection_monitoring.py         - Real-time operational intelligence

Usage Patterns:
    # Import analysis tools
    from scripts.analysis.implement_quality_ranking import DocumentQualityRanker
    
    # Import reprocessing system
    from scripts.reprocess_all_entries import ComprehensiveReprocessor
    
    # Import manual entry processors  
    from scripts.manual_entry.manual_entry_processor import ManualEntryProcessor

Version: 2.1 - Professional organization with enhanced functionality
Status: All scripts operational, file organization complete
Last Major Reorganization: May 2025 - Professional directory structure implemented
""" 

# Package metadata for future AI assistants
__scripts_info__ = {
    "total_scripts": "20+ specialized utilities",
    "analysis_tools": 6,
    "status": "All operational",
    "organization": "Professional directory structure",
    "reprocessing_system": "Fully operational (event loop issues resolved)",
    "quality_system": "Real-time quality scoring integrated",
    "visualization_support": "Chart.js integration complete"
} 