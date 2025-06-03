# File Organization Guide

This document describes the organized file structure of the AI-Horizon project.

## Directory Structure

### Root Directory
- `status_server.py` - Main web interface server
- `requirements.txt` - Python dependencies
- `setup.py` - Package setup configuration
- `config.env` - Environment configuration
- `.env.example` - Environment template

### `/scripts/` - Utility Scripts
#### `/scripts/fixes/` - Bug Fixes and Repairs
- `fix_all_generic_titles.py` - Fixes generic article titles
- `fix_remaining_entries.py` - Fixes problematic entries
- `fix_wisdom_extraction.py` - Robust wisdom extraction system
- `cleanup_failed_entries.py` - Removes unfixable entries
- `extract_wisdom_batch.py` - Batch wisdom extraction
- `comprehensive_wisdom_processor.py` - Complete content enhancement system

#### `/scripts/analysis/` - Analysis and Quality Control
- `implement_quality_ranking.py` - Document quality scoring system
- `analyze_costs.py` - API cost analysis
- `analyze_successful_articles.py` - Success metrics analysis
- `audit_wisdom_status.py` - Wisdom extraction audit
- `check_remaining_titles.py` - Title verification
- `check_status.py` - System status check
- `verify_titles.py` - Title validation

#### `/scripts/collection/` - Data Collection
- `collect_comprehensive.py` - Comprehensive data collection
- `collect_student_intelligence.py` - Student-focused collection
- `collect_targeted_sources.py` - Targeted source collection

#### `/scripts/manual_entry/` - Manual Entry Processing
- `launch_manual_entry.py` - Manual entry interface launcher
- `manual_entry_processor.py` - Manual entry processing logic

#### `/scripts/` - General Utilities
- `dynamic_rag_selector.py` - RAG system selector
- `create_backup_system.py` - Backup system creation
- `generate_student_report.py` - Student-focused report generation
- `generate_web_report.py` - Web-based report generation
- `share_reports.py` - Report sharing utilities

### `/tests/` - Test Files
- `test_browse_quality.py` - Quality scoring tests
- `test_collection_validation.py` - Collection validation tests
- `test_all_categories.py` - Category testing
- `test_enhanced_system.py` - Enhanced system tests
- `test_strategic_simple.py` - Simple strategy tests
- `test_strategic_pipeline.py` - Pipeline strategy tests
- `test_phase1.py` - Phase 1 testing

### `/docs/` - Documentation
- `README.md` - Main project documentation
- `COST_TRACKING_GUIDE.md` - API cost tracking guide
- `NAVIGATION_GUIDE.md` - System navigation guide
- `RAG_LIMITATIONS_GUIDE.md` - RAG system limitations
- `QUALITY_SCORING_GUIDE.md` - Comprehensive quality scoring system guide
- `FILE_ORGANIZATION.md` - This file organization guide

### Other Directories
- `/aih/` - Main package source code
- `/templates/` - Web interface templates
- `/data/` - Data storage and cache
- `/manual_entry/` - Manual entry system
- `/logs/` - System logs

## Import Path Updates

After reorganization, import paths have been updated:

### Quality Ranking System
```python
# Old import
from implement_quality_ranking import DocumentQualityRanker

# New import
from scripts.analysis.implement_quality_ranking import DocumentQualityRanker
```

### Wisdom Extraction System
```python
# Old import
from fix_wisdom_extraction import RobustWisdomExtractor

# New import
from scripts.fixes.fix_wisdom_extraction import RobustWisdomExtractor
```

## Benefits of Organization

1. **Clear Separation of Concerns** - Each directory has a specific purpose
2. **Easy Navigation** - Related files are grouped together
3. **Better Maintainability** - Easier to find and update related functionality
4. **Professional Structure** - Follows software engineering best practices
5. **Scalability** - Easy to add new scripts in appropriate directories

## Usage Notes

- All existing functionality remains intact
- Import paths have been updated automatically
- The status server continues to work without changes
- All tests continue to function correctly 