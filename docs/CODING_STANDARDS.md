# AI-Horizon Coding Standards & Style Guide

**Version**: 2.1  
**Last Updated**: June 14, 2025  
**Purpose**: Ensure consistent, maintainable code for future AI assistants

---

## 🎯 **FOR FUTURE AI ASSISTANTS**

This document establishes coding standards for the AI-Horizon project. Follow these patterns when making changes to ensure consistency and maintainability.

---

## 📁 **File Organization Standards**

### **Directory Structure (ESTABLISHED - DO NOT CHANGE)**
```
/aih/                    # Core processing pipeline
├── utils/               # Database, logging, utilities
├── gather/              # Data collection modules
├── classify/            # AI categorization logic
└── chat/                # RAG-based chat interface

/scripts/                # Organized utility scripts
├── analysis/            # Analysis tools and quality control
├── collection/          # Data collection scripts
├── fixes/               # Bug fixes and repair utilities
└── manual_entry/        # Manual entry processing

/tests/                  # All test files (recently organized)
/docs/                   # Documentation ecosystem
/templates/              # Flask web interface templates
/data/                   # Data storage, cache, logs, backups
```

### **File Naming Conventions**
- **Scripts**: Use descriptive names with underscores: `implement_quality_ranking.py`
- **Classes**: Use PascalCase: `DocumentQualityRanker`, `ComprehensiveReprocessor`
- **Functions**: Use snake_case: `calculate_document_score()`, `update_progress()`
- **Constants**: Use UPPER_CASE: `MAX_CONTENT_LENGTH`, `API_RATE_LIMIT`

---

## 🐍 **Python Coding Standards**

### **Import Organization (CRITICAL)**
```python
# Standard library imports (alphabetical)
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Third-party imports (alphabetical)
from flask import Flask, jsonify, request
from flask_cors import CORS

# Project root path (when needed)
sys.path.append(str(Path(__file__).parent.parent))

# AI-Horizon specific imports (by module)
from aih.utils.database import DatabaseManager
from aih.utils.logging import get_logger
from scripts.analysis.implement_quality_ranking import DocumentQualityRanker
```

### **Class Documentation Standards**
```python
class ExampleProcessor:
    """
    Brief description of the class purpose.
    
    Detailed description explaining the class functionality, its role in the system,
    and any critical status information (e.g., "All event loop issues resolved").
    
    Key Features:
    - Feature 1: Description
    - Feature 2: Description
    - Feature 3: Description
    
    Usage:
        processor = ExampleProcessor()
        result = processor.process_data(data)
    
    Performance:
    - Processing speed: ~100 items/second
    - Memory usage: Low (streaming processing)
    - Error handling: Comprehensive with logging
    """
    
    def __init__(self):
        """
        Initialize the processor with all required components.
        
        Sets up database connections, logging, and any required state
        for processing operations.
        """
        pass
```

### **Function Documentation Standards**
```python
def process_document(artifact: Dict, metadata: Dict, force: bool = False) -> bool:
    """
    Process a single document with specified algorithm.
    
    Args:
        artifact: Document data dictionary from database
        metadata: Document metadata dictionary (will be modified)
        force: If True, reprocess even if already processed
    
    Returns:
        bool: True if document was updated, False if skipped
    
    Raises:
        DatabaseError: If database operation fails
        ProcessingError: If document processing fails
    
    Performance:
        - Fast processing: ~100 docs/sec for algorithm-based operations
        - Slow processing: ~2-10 sec/doc for LLM-based operations
    """
    pass
```

---

## 🔧 **Error Handling Standards**

### **Standard Error Handling Pattern**
```python
def example_operation():
    """Example of standard error handling."""
    try:
        # Main operation logic
        result = perform_operation()
        
        # Log success
        logger.info(f"✅ Operation completed successfully: {result}")
        return result
        
    except SpecificError as e:
        # Handle specific errors
        logger.error(f"❌ Specific error in operation: {e}")
        raise
        
    except Exception as e:
        # Handle general errors
        logger.error(f"❌ Unexpected error in operation: {e}")
        raise
```

### **Logging Standards**
```python
# Use consistent emoji prefixes for log levels
logger.info("✅ Success message")
logger.warning("⚠️  Warning message")
logger.error("❌ Error message")
logger.debug("🔍 Debug information")

# Include operation context
logger.info(f"📄 Processing document [{i+1}/{total}]: {title[:50]}...")
logger.info(f"   📊 Quality score updated: {score:.3f}")
```

---

## 🌐 **Flask Route Standards**

### **Route Documentation Pattern**
```python
@app.route('/api/example_operation', methods=['POST'])
def api_example_operation():
    """
    API endpoint for example operation.
    
    Handles POST requests to perform example operations with proper error
    handling, progress tracking, and response formatting.
    
    Request Format:
        {
            "option1": true,
            "option2": false,
            "limit": 10
        }
    
    Response Format:
        {
            "success": true,
            "message": "Operation completed",
            "data": {...}
        }
    
    Status Codes:
        200: Success
        400: Bad request (invalid parameters)
        500: Server error
    """
    try:
        # Validate request
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        # Process request
        result = perform_operation(data)
        
        return jsonify({
            "success": True,
            "message": "Operation completed successfully",
            "data": result
        })
        
    except Exception as e:
        logger.error(f"❌ API error in example_operation: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
```

---

## 📊 **Database Operation Standards**

### **Database Query Patterns**
```python
def example_database_operation():
    """Example of standard database operation."""
    try:
        # Initialize database manager
        db = DatabaseManager()
        
        # Get data with error handling
        artifacts = db.get_artifacts()
        logger.info(f"📋 Retrieved {len(artifacts)} artifacts from database")
        
        # Process with progress tracking
        for i, artifact in enumerate(artifacts):
            try:
                # Process individual item
                result = process_artifact(artifact)
                
                # Update database
                db.update_artifact_metadata(artifact['id'], result)
                
                # Log progress
                if (i + 1) % 10 == 0:  # Log every 10 items
                    logger.info(f"📊 Progress: {i+1}/{len(artifacts)} processed")
                    
            except Exception as e:
                logger.error(f"❌ Error processing artifact {artifact['id']}: {e}")
                continue  # Continue with next item
        
        logger.info("✅ Database operation completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Database operation failed: {e}")
        raise
```

---

## 🧪 **Testing Standards**

### **Test File Organization**
- All tests in `/tests/` directory
- Test files named: `test_feature_name.py`
- Test classes named: `TestFeatureName`
- Test methods named: `test_specific_functionality()`

### **Test Structure Pattern**
```python
#!/usr/bin/env python3
"""
Test suite for feature functionality.

Tests cover the core functionality of FeatureName with comprehensive
coverage of success cases, error cases, and edge cases.
"""

import unittest
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from feature.module import FeatureClass

class TestFeatureName(unittest.TestCase):
    """Test suite for FeatureName functionality."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.feature = FeatureClass()
    
    def test_basic_functionality(self):
        """Test basic feature functionality."""
        result = self.feature.basic_operation()
        self.assertTrue(result)
    
    def test_error_handling(self):
        """Test error handling in edge cases."""
        with self.assertRaises(ValueError):
            self.feature.operation_with_invalid_input(None)

if __name__ == '__main__':
    unittest.main()
```

---

## 📝 **Documentation Standards**

### **File Header Pattern**
```python
#!/usr/bin/env python3
"""
Brief description of file purpose.

CRITICAL STATUS: Include any critical status information (e.g., "All event loop issues resolved")

Detailed description of the file's functionality, its role in the system,
and any important implementation details.

Key Features:
- Feature 1: Description
- Feature 2: Description

Usage:
    python filename.py [options]
    
    # Or programmatic usage
    from module import ClassName
    instance = ClassName()

Author: AI-Horizon Research Team
Version: 2.1
Last Updated: June 2025
"""
```

### **README Structure**
Each major directory should have a README.md with:
1. Purpose and overview
2. File descriptions
3. Usage examples
4. Key classes/functions
5. Integration points

---

## 🔄 **Version Control Standards**

### **Commit Message Format**
```
Type: Brief description

Detailed explanation if needed

Examples:
- Fix: Resolve event loop issues in reprocessing system
- Feature: Add comprehensive category narratives
- Docs: Update coding standards documentation
- Cleanup: Reorganize test files to proper directory
```

### **Version Numbering**
- Major versions: 1.0, 2.0, 3.0 (breaking changes)
- Minor versions: 2.1, 2.2, 2.3 (new features)
- Patch versions: 2.1.1, 2.1.2 (bug fixes)

---

## 🚨 **Critical Patterns to Maintain**

### **Event Loop Management (RESOLVED)**
```python
# For any async operations in synchronous contexts
import asyncio

def synchronous_wrapper():
    """Wrapper for async operations in sync context."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(async_operation())
        return result
    finally:
        loop.close()
```

### **Quality Score Integration**
```python
# Always integrate quality scoring in new features
from scripts.analysis.implement_quality_ranking import DocumentQualityRanker

def process_documents():
    ranker = DocumentQualityRanker()
    for doc in documents:
        quality_score, details = ranker.calculate_document_score(doc)
        # Store quality information
```

### **Status Tracking Integration**
```python
# Always integrate with StatusTracker for long operations
def long_operation():
    global status_tracker
    status_tracker.set_operation("Processing documents")
    
    for i, item in enumerate(items):
        # Process item
        status_tracker.update_progress(i + 1, len(items), f"Processing {item}")
    
    status_tracker.complete_operation(success=True)
```

---

## 📋 **Code Review Checklist**

### **Before Committing Code:**
- [ ] All imports organized according to standards
- [ ] Classes have comprehensive docstrings
- [ ] Functions have proper documentation
- [ ] Error handling follows standard patterns
- [ ] Logging uses consistent format and emojis
- [ ] Quality scoring integrated where applicable
- [ ] Status tracking for long operations
- [ ] Tests added for new functionality
- [ ] Documentation updated

### **File Organization Check:**
- [ ] Files in correct directories
- [ ] No duplicate functionality
- [ ] Imports use correct paths
- [ ] No circular dependencies

---

## 🎯 **For Future AI Assistants**

**CRITICAL**: This codebase has evolved to Version 2.1 with comprehensive features and zero critical issues. When making changes:

1. **Follow Established Patterns**: Use existing code as examples
2. **Maintain Quality Integration**: Keep quality scoring functional
3. **Preserve File Organization**: Don't reorganize directory structure
4. **Document Thoroughly**: Future AI assistants depend on clear documentation
5. **Test Changes**: Ensure web interface remains functional

**Status**: All standards established and working. No major refactoring needed.

---

*Document maintained by AI-Horizon Research Team*  
*Version 2.1 - Production Ready Standards* 