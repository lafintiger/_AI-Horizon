# Task-Centric Database Enhancements

## Overview

This document describes the major enhancement to the AI-Horizon system that implements a **task-centric database architecture**. This enhancement shifts the focus from high-level work roles to specific, actionable tasks, providing much more granular and actionable insights for cybersecurity workforce development.

## Key Features

### 🎯 **Task-Level Analysis**
- Extract specific DCWF tasks mentioned in articles
- Map tasks to AI impact categories (replace/augment/new_tasks/human_only)
- Track confidence levels for each task-impact mapping

### 🔧 **AI Tool Database**
- Comprehensive database of AI tools and their capabilities
- Tool-to-task mappings with effectiveness ratings
- Example prompts and use cases for each tool-task combination

### 📊 **Enhanced Analytics**
- Task-level statistics and insights
- AI impact distribution by specific tasks
- Tool recommendation system based on task requirements

### 🔄 **Hybrid Architecture**
- Preserves existing work role structure
- Adds new task-centric tables alongside existing ones
- Maintains backward compatibility

## Database Schema

### New Tables

#### `dcwf_tasks`
Stores individual DCWF tasks with detailed information:
```sql
CREATE TABLE dcwf_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dcwf_task_id TEXT UNIQUE NOT NULL,       -- e.g., "DCWF_543"
    task_name TEXT NOT NULL,                 -- e.g., "Develop secure code and error handling"
    task_description TEXT,
    dcwf_work_role_id TEXT,                  -- Links to work role
    work_role_name TEXT,
    category TEXT,                           -- Core category
    complexity_level TEXT,                   -- Basic, Intermediate, Advanced
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### `ai_tools`
Comprehensive AI tools database:
```sql
CREATE TABLE ai_tools (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_name TEXT UNIQUE NOT NULL,          -- e.g., "Cursor", "ChatGPT"
    tool_category TEXT,                      -- Code Assistant, Analysis Tool, etc.
    vendor TEXT,
    description TEXT,
    capabilities TEXT,                       -- JSON array of capabilities
    pricing_model TEXT,                      -- Free, Subscription, Usage-based
    target_tasks TEXT,                       -- JSON array of task types
    website_url TEXT,
    api_available BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### `task_tool_recommendations`
Maps tasks to recommended AI tools with example prompts:
```sql
CREATE TABLE task_tool_recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    tool_id INTEGER NOT NULL,
    effectiveness_rating REAL,              -- 0.0-1.0
    example_prompts TEXT,                    -- JSON array of example prompts
    use_case_description TEXT,
    configuration_notes TEXT,
    supporting_articles TEXT,               -- JSON array of article IDs
    confidence_score REAL DEFAULT 0.5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES dcwf_tasks (id),
    FOREIGN KEY (tool_id) REFERENCES ai_tools (id)
);
```

#### `article_task_mappings`
Links articles to specific tasks they discuss:
```sql
CREATE TABLE article_task_mappings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    artifact_id TEXT NOT NULL,
    task_id INTEGER NOT NULL,
    relevance_score REAL NOT NULL,          -- 0.0-1.0
    mentions_count INTEGER DEFAULT 1,
    context_snippets TEXT,                  -- JSON array of relevant quotes
    ai_impact_mentioned TEXT,               -- AI impact type for this task
    confidence_level REAL DEFAULT 0.5,
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (artifact_id) REFERENCES artifacts (id),
    FOREIGN KEY (task_id) REFERENCES dcwf_tasks (id)
);
```

#### `task_analysis_summary`
Aggregated insights per task:
```sql
CREATE TABLE task_analysis_summary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER UNIQUE NOT NULL,
    total_articles_analyzed INTEGER DEFAULT 0,
    replace_confidence REAL DEFAULT 0.0,
    augment_confidence REAL DEFAULT 0.0,
    new_tasks_confidence REAL DEFAULT 0.0,
    human_only_confidence REAL DEFAULT 0.0,
    primary_ai_impact TEXT,                 -- Category with highest confidence
    recommended_tools TEXT,                 -- JSON array of top tools
    key_insights TEXT,                      -- JSON array of insights
    example_prompts TEXT,                   -- JSON array of effective prompts
    last_analyzed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES dcwf_tasks (id)
);
```

## Usage Guide

### 1. Testing the New System

First, run the test script to ensure everything is working:

```bash
python test_task_database.py
```

This will test:
- Database schema creation
- Sample data insertion
- Query functionality
- Task extractor initialization

### 2. Processing Articles for Task Extraction

Use the integration script to process existing articles:

```bash
# Process unanalyzed articles (recommended first run)
python scripts/analysis/task_analysis_integration.py

# Check processing status
python scripts/analysis/task_analysis_integration.py --status

# Process with limit (for testing)
python scripts/analysis/task_analysis_integration.py --limit 10

# Reprocess all articles (when system is updated)
python scripts/analysis/task_analysis_integration.py --reprocess-all

# Generate task analysis summaries
python scripts/analysis/task_analysis_integration.py --generate-summaries
```

### 3. Using the Enhanced Task Extractor

```python
from aih.classify.task_extractor import EnhancedTaskExtractor

# Initialize extractor
extractor = EnhancedTaskExtractor()

# Extract tasks from an article
article_data = {
    'id': 'article_123',
    'title': 'AI Tools for Cybersecurity',
    'content': 'Article content here...',
    'url': 'https://example.com/article',
    'source_type': 'article'
}

# Extract tasks
task_extractions = extractor.extract_tasks_from_article(article_data)

# Save to database
success = extractor.save_task_extractions_to_db(task_extractions, article_data['id'])
```

### 4. Querying Task-Centric Data

```python
from aih.utils.database import DatabaseManager

db = DatabaseManager()

# Get all tasks for a work role
tasks = db.get_tasks_by_work_role('SOFTWARE_DEVELOPER')

# Get AI tools recommended for a specific task
tools = db.get_tools_for_task(task_id)

# Search tasks by keyword
coding_tasks = db.search_tasks_by_keyword('code')

# Get task analysis summary
summary = db.get_task_analysis_summary(task_id)

# Get overall statistics
stats = db.get_task_statistics()
```

## Example Use Cases

### Use Case 1: Student Career Guidance

**Scenario**: A cybersecurity student wants to know which coding tasks they should focus on learning.

**Query**:
```python
# Find all coding-related tasks
coding_tasks = db.search_tasks_by_keyword('code')

# For each task, get AI impact and tools
for task in coding_tasks:
    summary = db.get_task_analysis_summary(task['id'])
    tools = db.get_tools_for_task(task['id'])
    
    print(f"Task: {task['task_name']}")
    print(f"AI Impact: {summary['primary_ai_impact']}")
    print(f"Recommended Tools: {[tool['tool_name'] for tool in tools]}")
    print(f"Focus Level: {'HIGH' if summary['human_only_confidence'] > 0.7 else 'MEDIUM'}")
```

### Use Case 2: AI Tool Recommendation

**Scenario**: A software developer wants to know which AI tools can help with secure code development.

**Query**:
```python
# Find secure coding tasks
secure_tasks = db.search_tasks_by_keyword('secure code')

# Get tools for these tasks
all_tools = {}
for task in secure_tasks:
    tools = db.get_tools_for_task(task['id'])
    for tool in tools:
        if tool['tool_name'] not in all_tools:
            all_tools[tool['tool_name']] = {
                'tool': tool,
                'tasks': [],
                'avg_effectiveness': 0
            }
        all_tools[tool['tool_name']]['tasks'].append(task['task_name'])

# Rank by effectiveness
ranked_tools = sorted(all_tools.items(), 
                     key=lambda x: x[1]['tool']['effectiveness_rating'], 
                     reverse=True)
```

### Use Case 3: Curriculum Development

**Scenario**: An educator wants to identify which cybersecurity tasks are most impacted by AI for curriculum updates.

**Query**:
```python
# Get tasks with high AI impact
with db.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT dt.task_name, dt.work_role_name, tas.primary_ai_impact, 
               tas.replace_confidence, tas.augment_confidence,
               tas.total_articles_analyzed
        FROM dcwf_tasks dt
        JOIN task_analysis_summary tas ON dt.id = tas.task_id
        WHERE (tas.replace_confidence > 0.6 OR tas.augment_confidence > 0.6)
        AND tas.total_articles_analyzed >= 3
        ORDER BY tas.replace_confidence DESC, tas.augment_confidence DESC
    """)
    
    high_impact_tasks = [dict(row) for row in cursor.fetchall()]
```

## API Integration Points

The enhanced system integrates with existing AI-Horizon functionality:

### Web Interface Integration
- Task-level analysis views
- AI tool recommendation interfaces
- Student guidance dashboards

### Data Export Integration
- PDF reports now include task-level insights
- NSF reporting enhanced with task granularity
- Research data exports with task mappings

### Future API Endpoints
```python
# Planned REST API endpoints
GET /api/v1/tasks                          # List all tasks
GET /api/v1/tasks/{task_id}               # Get specific task
GET /api/v1/tasks/{task_id}/tools         # Get tools for task
GET /api/v1/tasks/{task_id}/articles      # Get articles discussing task
GET /api/v1/tools                         # List all AI tools
GET /api/v1/tools/{tool_id}/tasks         # Get tasks for tool
GET /api/v1/work-roles/{role_id}/tasks    # Get tasks for work role
```

## Benefits

### 1. **Granular Insights**
- Move from "Software Developer will be impacted by AI" to "Code review tasks will be augmented by AI tools like SonarQube AI"

### 2. **Actionable Guidance**
- Students get specific task-level guidance instead of vague work role predictions
- Educators can update curricula with precision

### 3. **Tool Discovery**
- Comprehensive AI tool database with real-world usage examples
- Task-specific tool recommendations with example prompts

### 4. **Research Enhancement**
- More granular data for NSF research reporting
- Better insights for academic publications
- Enhanced validation through task-level analysis

## Future Enhancements

### Phase 2 Features
- **Multi-LLM Validation**: Use multiple AI models for task extraction validation
- **Temporal Analysis**: Track how task-AI relationships evolve over time
- **Skill Gap Analysis**: Identify tasks where human skills remain critical
- **Industry Variation**: Track how task impacts vary across industries

### Phase 3 Features
- **Real-time Processing**: Process new articles automatically for task extraction
- **Interactive Task Explorer**: Web interface for exploring task-tool relationships
- **Curriculum Generator**: Automatic curriculum suggestions based on task analysis
- **Workforce Planning**: Tools for workforce development planning

## Migration Notes

### Backward Compatibility
- All existing functionality remains unchanged
- New features are additive, not replacements
- Existing database queries continue to work

### Performance Considerations
- Task extraction is computationally intensive (LLM API calls)
- Consider processing articles in batches
- Use rate limiting to avoid API throttling
- Monitor costs for large-scale processing

### Data Quality
- Task extraction confidence scores help identify reliable data
- Manual review recommended for high-stakes decisions
- Regular reprocessing recommended as AI models improve

## Support

For questions or issues with the task-centric enhancements:

1. **Run the test script**: `python test_task_database.py`
2. **Check logs**: Review application logs for detailed error information
3. **Validate data**: Use the integration status command to check data quality
4. **Documentation**: Refer to existing AI-Horizon documentation for base functionality

---

*This enhancement represents a significant step forward in making AI-Horizon's insights more actionable and precise for cybersecurity workforce development.* 