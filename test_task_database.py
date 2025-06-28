#!/usr/bin/env python3
"""
Test script for the new task-centric database functionality.

This script tests:
1. Database schema creation
2. Sample data insertion
3. Database query functions
4. Task extraction functionality
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from aih.utils.database import DatabaseManager
from aih.utils.logging import get_logger

logger = get_logger(__name__)

def test_database_schema():
    """Test that the new database schema is created correctly."""
    logger.info("🧪 Testing database schema creation...")
    
    try:
        db = DatabaseManager()
        
        # Test database connection and tables
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if new tables exist
            new_tables = [
                'dcwf_tasks',
                'task_work_role_relationships',
                'task_ai_impact_analysis',
                'ai_tools',
                'task_tool_recommendations',
                'article_task_mappings',
                'task_analysis_summary'
            ]
            
            for table in new_tables:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
                result = cursor.fetchone()
                if result:
                    logger.info(f"✅ Table '{table}' exists")
                else:
                    logger.error(f"❌ Table '{table}' missing")
                    return False
            
            logger.info("✅ All new tables created successfully")
            return True
            
    except Exception as e:
        logger.error(f"❌ Database schema test failed: {e}")
        return False

def test_sample_data_insertion():
    """Test inserting sample data into the new tables."""
    logger.info("🧪 Testing sample data insertion...")
    
    try:
        db = DatabaseManager()
        
        # Test 1: Insert sample DCWF task
        task_data = {
            'dcwf_task_id': 'TEST_001',
            'task_name': 'Test Secure Code Development',
            'task_description': 'Develop secure code with proper error handling and validation',
            'dcwf_work_role_id': 'SOFTWARE_DEV_001',
            'work_role_name': 'Software Developer',
            'category': 'Cybersecurity',
            'complexity_level': 'Intermediate'
        }
        
        task_id = db.save_dcwf_task(task_data)
        if task_id:
            logger.info(f"✅ DCWF task saved with ID: {task_id}")
        else:
            logger.error("❌ Failed to save DCWF task")
            return False
        
        # Test 2: Insert sample AI tool
        tool_data = {
            'tool_name': 'Test AI Coder',
            'tool_category': 'Code Assistant',
            'vendor': 'Test Company',
            'description': 'AI-powered coding assistant for secure development',
            'capabilities': ['Code generation', 'Security scanning', 'Error detection'],
            'pricing_model': 'Subscription',
            'target_tasks': ['Code development', 'Security testing'],
            'website_url': 'https://example.com',
            'api_available': True
        }
        
        tool_id = db.save_ai_tool(tool_data)
        if tool_id:
            logger.info(f"✅ AI tool saved with ID: {tool_id}")
        else:
            logger.error("❌ Failed to save AI tool")
            return False
        
        # Test 3: Insert task-tool recommendation
        rec_data = {
            'task_id': task_id,
            'tool_id': tool_id,
            'effectiveness_rating': 0.85,
            'example_prompts': [
                'Generate secure Python function for user authentication',
                'Review this code for security vulnerabilities'
            ],
            'use_case_description': 'Using AI to assist with secure code development',
            'supporting_articles': ['test_article_1'],
            'confidence_score': 0.8
        }
        
        rec_id = db.save_task_tool_recommendation(rec_data)
        if rec_id:
            logger.info(f"✅ Task-tool recommendation saved with ID: {rec_id}")
        else:
            logger.error("❌ Failed to save task-tool recommendation")
            return False
        
        logger.info("✅ Sample data insertion successful")
        return True
        
    except Exception as e:
        logger.error(f"❌ Sample data insertion test failed: {e}")
        return False

def test_database_queries():
    """Test the new database query functions."""
    logger.info("🧪 Testing database query functions...")
    
    try:
        db = DatabaseManager()
        
        # Test 1: Get task statistics
        stats = db.get_task_statistics()
        logger.info(f"✅ Task statistics: {stats}")
        
        # Test 2: Search tasks by keyword
        tasks = db.search_tasks_by_keyword('secure')
        logger.info(f"✅ Found {len(tasks)} tasks matching 'secure'")
        
        # Test 3: Get tools for task (if we have any tasks)
        if stats.get('total_tasks', 0) > 0:
            # Get first task ID
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM dcwf_tasks LIMIT 1")
                result = cursor.fetchone()
                if result:
                    task_id = result[0]
                    tools = db.get_tools_for_task(task_id)
                    logger.info(f"✅ Found {len(tools)} tools for task {task_id}")
        
        logger.info("✅ Database query tests successful")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database query test failed: {e}")
        return False

def test_task_extractor():
    """Test the task extractor functionality."""
    logger.info("🧪 Testing task extractor functionality...")
    
    try:
        from aih.classify.task_extractor import EnhancedTaskExtractor
        
        # Initialize extractor
        extractor = EnhancedTaskExtractor()
        logger.info("✅ Task extractor initialized")
        
        # Test with sample article data
        sample_article = {
            'id': 'test_article_1',
            'title': 'AI Tools for Secure Software Development',
            'content': """
            Artificial intelligence is revolutionizing secure software development. 
            AI-powered tools like Cursor and GitHub Copilot are helping developers 
            write more secure code by automatically detecting vulnerabilities and 
            suggesting fixes. These tools can assist with tasks such as:
            
            1. Developing secure authentication systems
            2. Implementing proper error handling
            3. Conducting automated security testing
            4. Code review and vulnerability assessment
            
            For example, you can use the prompt: "Generate a secure login function 
            in Python with proper input validation and password hashing" to get 
            AI assistance with authentication code.
            """,
            'url': 'https://example.com/test-article',
            'source_type': 'article'
        }
        
        # Test task extraction (this would normally make API calls)
        logger.info("ℹ️  Note: Task extraction test requires API keys to run fully")
        logger.info("✅ Task extractor can be initialized and configured")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Task extractor test failed: {e}")
        return False

def run_all_tests():
    """Run all tests and report results."""
    logger.info("🧪 Starting comprehensive task-centric database tests...\n")
    
    tests = [
        ("Database Schema Creation", test_database_schema),
        ("Sample Data Insertion", test_sample_data_insertion),
        ("Database Queries", test_database_queries),
        ("Task Extractor", test_task_extractor)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"Running: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
            logger.info(f"{'✅ PASSED' if result else '❌ FAILED'}: {test_name}\n")
        except Exception as e:
            logger.error(f"❌ ERROR in {test_name}: {e}\n")
            results.append((test_name, False))
    
    # Summary
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    logger.info("=" * 50)
    logger.info("TEST SUMMARY")
    logger.info("=" * 50)
    logger.info(f"Total Tests: {total}")
    logger.info(f"Passed: {passed}")
    logger.info(f"Failed: {total - passed}")
    logger.info(f"Success Rate: {passed/total*100:.1f}%")
    
    if passed == total:
        logger.info("🎉 All tests passed! Task-centric database is ready.")
    else:
        logger.info("⚠️  Some tests failed. Please review the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1) 