"""
Database management for AI-Horizon pipeline.

Handles SQLite database operations for storing artifacts, classifications, and metadata.
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from contextlib import contextmanager
from collections import defaultdict

from aih.config import settings, get_data_path
from aih.utils.logging import get_logger

logger = get_logger(__name__)

class DatabaseManager:
    """Manages SQLite database operations for the AI-Horizon pipeline."""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize database manager.
        
        Args:
            db_path: Optional custom database path
        """
        if db_path:
            if db_path == ":memory:":
                self.db_path = ":memory:"
                self.is_memory_db = True
                # For in-memory databases, we need to keep the connection alive
                self._memory_conn = sqlite3.connect(":memory:")
                self._memory_conn.row_factory = sqlite3.Row
            else:
                self.db_path = Path(db_path)
                self.is_memory_db = False
        else:
            self.db_path = get_data_path() / "aih_database.db"
            self.is_memory_db = False
        
        if not self.is_memory_db:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_database()
    
    def _initialize_database(self) -> None:
        """Create database tables if they don't exist."""
        if self.is_memory_db:
            conn = self._memory_conn
            cursor = conn.cursor()
        else:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
        
        try:
            # Artifacts table - stores raw collected data
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS artifacts (
                    id TEXT PRIMARY KEY,
                    url TEXT UNIQUE NOT NULL,
                    title TEXT,
                    content TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    collected_at TIMESTAMP NOT NULL,
                    raw_metadata TEXT,
                    UNIQUE(url)
                )
            """)
            
            # Classifications table - stores AI analysis results
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS classifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    artifact_id TEXT NOT NULL,
                    category TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    rationale TEXT,
                    model_used TEXT,
                    classified_at TIMESTAMP NOT NULL,
                    human_verified BOOLEAN DEFAULT FALSE,
                    human_notes TEXT,
                    FOREIGN KEY (artifact_id) REFERENCES artifacts (id)
                )
            """)
            
            # Source scores table - stores NID reliability assessments
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS source_scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    artifact_id TEXT NOT NULL,
                    source_reliability TEXT NOT NULL,
                    info_credibility TEXT NOT NULL,
                    specificity_score REAL,
                    recency_score REAL,
                    evidence_score REAL,
                    expert_score REAL,
                    overall_score REAL NOT NULL,
                    scoring_rationale TEXT,
                    scored_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (artifact_id) REFERENCES artifacts (id)
                )
            """)
            
            # Collection runs table - tracks data gathering sessions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS collection_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_type TEXT NOT NULL,
                    query_used TEXT,
                    artifacts_collected INTEGER NOT NULL,
                    started_at TIMESTAMP NOT NULL,
                    completed_at TIMESTAMP,
                    status TEXT NOT NULL,
                    error_message TEXT
                )
            """)
            
            # PHASE 1: TASK-CENTRIC ENHANCEMENT TABLES
            
            # DCWF Tasks table - Individual tasks from the framework
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS dcwf_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dcwf_task_id TEXT UNIQUE NOT NULL,  -- e.g., "DCWF_543"
                    task_name TEXT NOT NULL,  -- e.g., "Develop secure code and error handling"
                    task_description TEXT,
                    dcwf_work_role_id TEXT,  -- Links to work role (e.g., "DCWF_621")
                    work_role_name TEXT,  -- e.g., "Software Developer"
                    category TEXT,  -- Core category: Cybersecurity, Cyber IT, etc.
                    complexity_level TEXT,  -- Basic, Intermediate, Advanced
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Task-WorkRole Relationships (Many-to-Many)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS task_work_role_relationships (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id INTEGER NOT NULL,
                    work_role_id TEXT NOT NULL,  -- DCWF work role ID
                    relationship_type TEXT DEFAULT 'primary',  -- primary, secondary, supportive
                    importance_weight REAL DEFAULT 1.0,  -- 0.0-1.0 importance for this role
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (task_id) REFERENCES dcwf_tasks (id),
                    UNIQUE(task_id, work_role_id)
                )
            """)
            
            # AI Impact Analysis per Task
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS task_ai_impact_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id INTEGER NOT NULL,
                    ai_impact_category TEXT NOT NULL,  -- replace, augment, new_tasks, human_only
                    confidence_score REAL NOT NULL,  -- 0.0-1.0
                    evidence TEXT,  -- JSON array of evidence from articles
                    analysis_rationale TEXT,
                    tools_mentioned TEXT,  -- JSON array of AI tools
                    example_prompts TEXT,  -- JSON array of example prompts
                    supporting_articles TEXT,  -- JSON array of article IDs
                    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (task_id) REFERENCES dcwf_tasks (id)
                )
            """)
            
            # AI Tools Database
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ai_tools (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tool_name TEXT UNIQUE NOT NULL,  -- e.g., "Cursor", "ChatGPT", "Windsurf"
                    tool_category TEXT,  -- Code Assistant, Analysis Tool, etc.
                    vendor TEXT,
                    description TEXT,
                    capabilities TEXT,  -- JSON array of capabilities
                    pricing_model TEXT,  -- Free, Subscription, Usage-based
                    target_tasks TEXT,  -- JSON array of task types this tool helps with
                    website_url TEXT,
                    api_available BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Task-Tool Relationships with Example Prompts
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS task_tool_recommendations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id INTEGER NOT NULL,
                    tool_id INTEGER NOT NULL,
                    effectiveness_rating REAL,  -- 0.0-1.0 how effective this tool is for this task
                    example_prompts TEXT,  -- JSON array of example prompts
                    use_case_description TEXT,
                    configuration_notes TEXT,
                    supporting_articles TEXT,  -- JSON array of article IDs that support this recommendation
                    confidence_score REAL DEFAULT 0.5,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (task_id) REFERENCES dcwf_tasks (id),
                    FOREIGN KEY (tool_id) REFERENCES ai_tools (id),
                    UNIQUE(task_id, tool_id)
                )
            """)
            
            # Article-Task Mappings (connects articles to specific tasks they discuss)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS article_task_mappings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    artifact_id TEXT NOT NULL,
                    task_id INTEGER NOT NULL,
                    relevance_score REAL NOT NULL,  -- 0.0-1.0 how relevant this article is to the task
                    mentions_count INTEGER DEFAULT 1,  -- How many times the task is mentioned
                    context_snippets TEXT,  -- JSON array of relevant text snippets
                    ai_impact_mentioned TEXT,  -- What type of AI impact is mentioned for this task
                    confidence_level REAL DEFAULT 0.5,
                    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (artifact_id) REFERENCES artifacts (id),
                    FOREIGN KEY (task_id) REFERENCES dcwf_tasks (id),
                    UNIQUE(artifact_id, task_id)
                )
            """)
            
            # Task Analysis Summary (aggregated insights per task)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS task_analysis_summary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id INTEGER UNIQUE NOT NULL,
                    total_articles_analyzed INTEGER DEFAULT 0,
                    replace_confidence REAL DEFAULT 0.0,
                    augment_confidence REAL DEFAULT 0.0,
                    new_tasks_confidence REAL DEFAULT 0.0,
                    human_only_confidence REAL DEFAULT 0.0,
                    primary_ai_impact TEXT,  -- The category with highest confidence
                    recommended_tools TEXT,  -- JSON array of top recommended tools
                    key_insights TEXT,  -- JSON array of key insights
                    example_prompts TEXT,  -- JSON array of most effective prompts
                    last_analyzed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (task_id) REFERENCES dcwf_tasks (id)
                )
            """)
            
            conn.commit()
            logger.info("Database initialized successfully")
        except Exception as e:
            conn.rollback()
            logger.error(f"Database initialization failed: {e}")
            raise
        finally:
            if not self.is_memory_db:
                conn.close()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        if self.is_memory_db:
            # Use the persistent memory connection
            yield self._memory_conn
        else:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            try:
                yield conn
            except Exception as e:
                conn.rollback()
                logger.error(f"Database error: {e}")
                raise
            finally:
                conn.close()
    
    def save_artifact(self, artifact_data: Dict[str, Any]) -> str:
        """
        Save an artifact to the database.
        
        Args:
            artifact_data: Dictionary containing artifact information
            
        Returns:
            The artifact ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            artifact_id = artifact_data.get('id', f"artifact_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}")
            
            cursor.execute("""
                INSERT OR REPLACE INTO artifacts 
                (id, url, title, content, source_type, collected_at, raw_metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                artifact_id,
                artifact_data['url'],
                artifact_data.get('title', ''),
                artifact_data['content'],
                artifact_data['source_type'],
                artifact_data.get('collected_at', datetime.now()),
                json.dumps(artifact_data.get('metadata', {}))
            ))
            
            conn.commit()
            logger.info(f"Saved artifact {artifact_id}")
            return artifact_id
    
    def save_classification(self, classification_data: Dict[str, Any]) -> int:
        """
        Save a classification result.
        
        Args:
            classification_data: Dictionary containing classification information
            
        Returns:
            The classification ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO classifications 
                (artifact_id, category, confidence, rationale, model_used, classified_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                classification_data['artifact_id'],
                classification_data['category'],
                classification_data['confidence'],
                classification_data.get('rationale', ''),
                classification_data.get('model_used', ''),
                classification_data.get('classified_at', datetime.now())
            ))
            
            classification_id = cursor.lastrowid
            conn.commit()
            logger.info(f"Saved classification {classification_id}")
            return classification_id
    
    def save_source_score(self, score_data: Dict[str, Any]) -> int:
        """
        Save source scoring results.
        
        Args:
            score_data: Dictionary containing scoring information
            
        Returns:
            The score ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO source_scores 
                (artifact_id, source_reliability, info_credibility, specificity_score,
                 recency_score, evidence_score, expert_score, overall_score, 
                 scoring_rationale, scored_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                score_data['artifact_id'],
                score_data['source_reliability'],
                score_data['info_credibility'],
                score_data.get('specificity_score'),
                score_data.get('recency_score'),
                score_data.get('evidence_score'),
                score_data.get('expert_score'),
                score_data['overall_score'],
                score_data.get('scoring_rationale', ''),
                score_data.get('scored_at', datetime.now())
            ))
            
            score_id = cursor.lastrowid
            conn.commit()
            logger.info(f"Saved source score {score_id}")
            return score_id
    
    def get_artifacts(self, limit: Optional[int] = None, unclassified_only: bool = False) -> List[Dict]:
        """
        Retrieve artifacts from the database.
        
        Args:
            limit: Maximum number of artifacts to return
            unclassified_only: Only return artifacts without classifications
            
        Returns:
            List of artifact dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if unclassified_only:
                query = """
                    SELECT a.* FROM artifacts a
                    LEFT JOIN classifications c ON a.id = c.artifact_id
                    WHERE c.artifact_id IS NULL
                    ORDER BY a.collected_at DESC
                """
            else:
                query = "SELECT * FROM artifacts ORDER BY collected_at DESC"
            
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_artifact_by_id(self, artifact_id: str) -> Optional[Dict]:
        """Get a specific artifact by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM artifacts WHERE id = ?", (artifact_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_classifications_by_category(self, category: str) -> List[Dict]:
        """Get all classifications for a specific category."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.*, a.title, a.url, a.source_type 
                FROM classifications c
                JOIN artifacts a ON c.artifact_id = a.id
                WHERE c.category = ?
                ORDER BY c.confidence DESC
            """, (category,))
            return [dict(row) for row in cursor.fetchall()]
    
    def start_collection_run(self, run_type: str, query: str = None) -> int:
        """Start a new collection run and return the run ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO collection_runs (run_type, query_used, artifacts_collected, started_at, status)
                VALUES (?, ?, 0, ?, 'running')
            """, (run_type, query, datetime.now()))
            
            run_id = cursor.lastrowid
            conn.commit()
            logger.info(f"Started collection run {run_id}")
            return run_id
    
    def complete_collection_run(self, run_id: int, artifacts_collected: int, error_message: str = None) -> None:
        """Mark a collection run as completed."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            status = "completed" if not error_message else "failed"
            cursor.execute("""
                UPDATE collection_runs 
                SET artifacts_collected = ?, completed_at = ?, status = ?, error_message = ?
                WHERE id = ?
            """, (artifacts_collected, datetime.now(), status, error_message, run_id))
            
            conn.commit()
            logger.info(f"Completed collection run {run_id}: {artifacts_collected} artifacts")
    
    def artifact_exists(self, url: str) -> bool:
        """
        Check if an artifact with the given URL already exists.
        
        Args:
            url: The URL to check
            
        Returns:
            True if artifact exists, False otherwise
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM artifacts WHERE url = ?", (url,))
            return cursor.fetchone() is not None
    
    def get_existing_urls(self) -> set:
        """
        Get all existing artifact URLs to avoid duplicates.
        
        Returns:
            Set of existing URLs
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT url FROM artifacts")
            return {row[0] for row in cursor.fetchall()}
    
    def get_artifact_by_url(self, url: str) -> Optional[Dict]:
        """
        Get an artifact by its URL.
        
        Args:
            url: The URL to search for
            
        Returns:
            Artifact dictionary if found, None otherwise
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM artifacts WHERE url = ?", (url,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def delete_artifact(self, artifact_id: str) -> bool:
        """
        Delete an artifact and all associated data.
        
        Args:
            artifact_id: The ID of the artifact to delete
            
        Returns:
            True if artifact was deleted, False if not found
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if artifact exists
            cursor.execute("SELECT 1 FROM artifacts WHERE id = ?", (artifact_id,))
            if not cursor.fetchone():
                logger.warning(f"Artifact {artifact_id} not found for deletion")
                return False
            
            # Delete associated classifications
            cursor.execute("DELETE FROM classifications WHERE artifact_id = ?", (artifact_id,))
            classifications_deleted = cursor.rowcount
            
            # Delete associated source scores
            cursor.execute("DELETE FROM source_scores WHERE artifact_id = ?", (artifact_id,))
            scores_deleted = cursor.rowcount
            
            # Delete the artifact itself
            cursor.execute("DELETE FROM artifacts WHERE id = ?", (artifact_id,))
            
            conn.commit()
            logger.info(f"Deleted artifact {artifact_id} with {classifications_deleted} classifications and {scores_deleted} source scores")
            return True
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive database statistics.
        
        Returns:
            Dictionary containing database statistics
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Count total artifacts
            cursor.execute("SELECT COUNT(*) FROM artifacts")
            total_artifacts = cursor.fetchone()[0]
            
            # Count by source type
            cursor.execute("SELECT source_type, COUNT(*) FROM artifacts GROUP BY source_type")
            source_types = dict(cursor.fetchall())
            
            # Count classifications
            cursor.execute("SELECT COUNT(*) FROM classifications")
            total_classifications = cursor.fetchone()[0]
            
            # Count by category from metadata (using multi-category analysis)
            cursor.execute("SELECT raw_metadata FROM artifacts WHERE raw_metadata IS NOT NULL")
            category_counts = defaultdict(int)
            multi_category_stats = defaultdict(int)
            quality_scores = []
            source_reliability_counts = defaultdict(int)
            recent_artifacts = 0
            
            for (metadata_json,) in cursor.fetchall():
                try:
                    metadata = json.loads(metadata_json)
                    
                    # Collect quality scores
                    quality_score = metadata.get('quality_score')
                    if quality_score is not None:
                        quality_scores.append(float(quality_score))
                    
                    # Collect source reliability data
                    source_reliability = metadata.get('source_reliability')
                    if source_reliability:
                        source_reliability_counts[source_reliability] += 1
                    
                    # Check if artifact is recent (last 30 days)
                    collected_at = metadata.get('collected_at')
                    if collected_at:
                        try:
                            if isinstance(collected_at, str):
                                collected_date = datetime.fromisoformat(collected_at.replace('Z', '+00:00'))
                            else:
                                collected_date = collected_at
                            if (datetime.now() - collected_date.replace(tzinfo=None)).days <= 30:
                                recent_artifacts += 1
                        except:
                            pass
                    
                    # Check for multi-category analysis first (new system)
                    multi_categories = metadata.get('ai_impact_categories', {})
                    if multi_categories:
                        # Count articles that have each category with confidence > 0.3
                        for category, category_data in multi_categories.items():
                            # Handle both old format (direct confidence) and new format (nested dict)
                            if isinstance(category_data, dict):
                                confidence = category_data.get('confidence', 0)
                            else:
                                confidence = category_data
                            
                            if confidence > 0.3:  # Only count significant classifications
                                multi_category_stats[category] += 1
                    else:
                        # Fallback to single category (old system)
                        category = metadata.get('ai_impact_category', 'unknown')
                        category_counts[category] += 1
                        
                except (json.JSONDecodeError, TypeError):
                    category_counts['unknown'] += 1
            
            # Use multi-category stats if available, otherwise fall back to single category
            final_categories = dict(multi_category_stats) if multi_category_stats else dict(category_counts)
            
            # Calculate quality statistics
            quality_stats = {}
            if quality_scores:
                quality_stats = {
                    'avg_quality_score': round(sum(quality_scores) / len(quality_scores), 3),
                    'min_quality_score': round(min(quality_scores), 3),
                    'max_quality_score': round(max(quality_scores), 3),
                    'high_quality_count': len([s for s in quality_scores if s >= 0.8]),
                    'medium_quality_count': len([s for s in quality_scores if 0.6 <= s < 0.8]),
                    'low_quality_count': len([s for s in quality_scores if s < 0.6])
                }
            
            # Get recent collection activity
            cursor.execute("""
                SELECT COUNT(*) FROM collection_runs 
                WHERE started_at > datetime('now', '-7 days')
            """)
            recent_runs = cursor.fetchone()[0]
            
            # Get wisdom extraction count
            cursor.execute("""
                SELECT COUNT(*) FROM artifacts 
                WHERE raw_metadata LIKE '%wisdom%' AND raw_metadata IS NOT NULL
            """)
            wisdom_extracted_count = cursor.fetchone()[0]
            
            return {
                'total_artifacts': total_artifacts,
                'total_articles': total_artifacts,  # Add this for template compatibility
                'total_classifications': total_classifications,
                'source_types': dict(source_types),
                'categories': final_categories,
                'quality_stats': quality_stats,
                'source_reliability': dict(source_reliability_counts),
                'recent_artifacts_30d': recent_artifacts,
                'recent_collection_runs_7d': recent_runs,
                'wisdom_extracted_count': wisdom_extracted_count,
                'last_updated': datetime.now().isoformat()
            }
    
    def update_artifact_metadata(self, artifact_id: str, metadata: Dict[str, Any]) -> bool:
        """
        Update the metadata for an existing artifact.
        
        Args:
            artifact_id: The ID of the artifact to update
            metadata: New metadata dictionary
            
        Returns:
            True if artifact was updated, False if not found
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if artifact exists
            cursor.execute("SELECT 1 FROM artifacts WHERE id = ?", (artifact_id,))
            if not cursor.fetchone():
                logger.warning(f"Artifact {artifact_id} not found for metadata update")
                return False
            
            # Update metadata
            cursor.execute(
                "UPDATE artifacts SET raw_metadata = ? WHERE id = ?",
                (json.dumps(metadata), artifact_id)
            )
            
            conn.commit()
            logger.info(f"Updated metadata for artifact {artifact_id}")
            return True

    # =====================================================
    # TASK-CENTRIC DATABASE METHODS
    # =====================================================
    
    def save_dcwf_task(self, task_data: Dict[str, Any]) -> Optional[int]:
        """
        Save a DCWF task to the database.
        
        Args:
            task_data: Dictionary containing task information
            
        Returns:
            The task ID or None if failed
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO dcwf_tasks 
                    (dcwf_task_id, task_name, task_description, dcwf_work_role_id, 
                     work_role_name, category, complexity_level)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    task_data['dcwf_task_id'],
                    task_data['task_name'],
                    task_data.get('task_description', ''),
                    task_data.get('dcwf_work_role_id', ''),
                    task_data.get('work_role_name', ''),
                    task_data.get('category', ''),
                    task_data.get('complexity_level', 'Intermediate')
                ))
                
                task_id = cursor.lastrowid
                conn.commit()
                logger.info(f"Saved DCWF task {task_data['dcwf_task_id']}")
                return task_id
                
        except Exception as e:
            logger.error(f"Error saving DCWF task: {e}")
            return None
    
    def save_ai_tool(self, tool_data: Dict[str, Any]) -> Optional[int]:
        """
        Save an AI tool to the database.
        
        Args:
            tool_data: Dictionary containing tool information
            
        Returns:
            The tool ID or None if failed
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO ai_tools 
                    (tool_name, tool_category, vendor, description, capabilities, 
                     pricing_model, target_tasks, website_url, api_available)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    tool_data['tool_name'],
                    tool_data.get('tool_category', ''),
                    tool_data.get('vendor', ''),
                    tool_data.get('description', ''),
                    json.dumps(tool_data.get('capabilities', [])),
                    tool_data.get('pricing_model', ''),
                    json.dumps(tool_data.get('target_tasks', [])),
                    tool_data.get('website_url', ''),
                    tool_data.get('api_available', False)
                ))
                
                tool_id = cursor.lastrowid
                conn.commit()
                logger.info(f"Saved AI tool {tool_data['tool_name']}")
                return tool_id
                
        except Exception as e:
            logger.error(f"Error saving AI tool: {e}")
            return None
    
    def save_task_tool_recommendation(self, recommendation_data: Dict[str, Any]) -> Optional[int]:
        """
        Save a task-tool recommendation with example prompts.
        
        Args:
            recommendation_data: Dictionary containing recommendation information
            
        Returns:
            The recommendation ID or None if failed
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO task_tool_recommendations 
                    (task_id, tool_id, effectiveness_rating, example_prompts, 
                     use_case_description, configuration_notes, supporting_articles, confidence_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    recommendation_data['task_id'],
                    recommendation_data['tool_id'],
                    recommendation_data.get('effectiveness_rating', 0.5),
                    json.dumps(recommendation_data.get('example_prompts', [])),
                    recommendation_data.get('use_case_description', ''),
                    recommendation_data.get('configuration_notes', ''),
                    json.dumps(recommendation_data.get('supporting_articles', [])),
                    recommendation_data.get('confidence_score', 0.5)
                ))
                
                rec_id = cursor.lastrowid
                conn.commit()
                logger.info(f"Saved task-tool recommendation {rec_id}")
                return rec_id
                
        except Exception as e:
            logger.error(f"Error saving task-tool recommendation: {e}")
            return None
    
    def save_article_task_mapping(self, mapping_data: Dict[str, Any]) -> Optional[int]:
        """
        Save an article-task mapping.
        
        Args:
            mapping_data: Dictionary containing mapping information
            
        Returns:
            The mapping ID or None if failed
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO article_task_mappings 
                    (artifact_id, task_id, relevance_score, mentions_count, 
                     context_snippets, ai_impact_mentioned, confidence_level)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    mapping_data['artifact_id'],
                    mapping_data['task_id'],
                    mapping_data['relevance_score'],
                    mapping_data.get('mentions_count', 1),
                    json.dumps(mapping_data.get('context_snippets', [])),
                    mapping_data.get('ai_impact_mentioned', ''),
                    mapping_data.get('confidence_level', 0.5)
                ))
                
                mapping_id = cursor.lastrowid
                conn.commit()
                logger.info(f"Saved article-task mapping {mapping_id}")
                return mapping_id
                
        except Exception as e:
            logger.error(f"Error saving article-task mapping: {e}")
            return None
    
    def get_tasks_by_work_role(self, work_role_id: str) -> List[Dict[str, Any]]:
        """Get all tasks for a specific DCWF work role."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT dt.*, tas.primary_ai_impact, tas.replace_confidence, 
                           tas.augment_confidence, tas.new_tasks_confidence, tas.human_only_confidence
                    FROM dcwf_tasks dt
                    LEFT JOIN task_analysis_summary tas ON dt.id = tas.task_id
                    WHERE dt.dcwf_work_role_id = ?
                    ORDER BY dt.task_name
                """, (work_role_id,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting tasks for work role {work_role_id}: {e}")
            return []
    
    def get_tools_for_task(self, task_id: int) -> List[Dict[str, Any]]:
        """Get all AI tools recommended for a specific task."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT at.*, ttr.effectiveness_rating, ttr.example_prompts, 
                           ttr.use_case_description, ttr.confidence_score
                    FROM ai_tools at
                    JOIN task_tool_recommendations ttr ON at.id = ttr.tool_id
                    WHERE ttr.task_id = ?
                    ORDER BY ttr.effectiveness_rating DESC, ttr.confidence_score DESC
                """, (task_id,))
                
                results = []
                for row in cursor.fetchall():
                    row_dict = dict(row)
                    # Parse JSON fields
                    if row_dict.get('example_prompts'):
                        row_dict['example_prompts'] = json.loads(row_dict['example_prompts'])
                    if row_dict.get('capabilities'):
                        row_dict['capabilities'] = json.loads(row_dict['capabilities'])
                    if row_dict.get('target_tasks'):
                        row_dict['target_tasks'] = json.loads(row_dict['target_tasks'])
                    results.append(row_dict)
                
                return results
        except Exception as e:
            logger.error(f"Error getting tools for task {task_id}: {e}")
            return []
    
    def get_articles_for_task(self, task_id: int) -> List[Dict[str, Any]]:
        """Get all articles that discuss a specific task."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT a.*, atm.relevance_score, atm.mentions_count, 
                           atm.context_snippets, atm.ai_impact_mentioned
                    FROM artifacts a
                    JOIN article_task_mappings atm ON a.id = atm.artifact_id
                    WHERE atm.task_id = ?
                    ORDER BY atm.relevance_score DESC, atm.mentions_count DESC
                """, (task_id,))
                
                results = []
                for row in cursor.fetchall():
                    row_dict = dict(row)
                    # Parse JSON fields
                    if row_dict.get('context_snippets'):
                        row_dict['context_snippets'] = json.loads(row_dict['context_snippets'])
                    if row_dict.get('raw_metadata'):
                        row_dict['raw_metadata'] = json.loads(row_dict['raw_metadata'])
                    results.append(row_dict)
                
                return results
        except Exception as e:
            logger.error(f"Error getting articles for task {task_id}: {e}")
            return []
    
    def update_task_analysis_summary(self, task_id: int, analysis_data: Dict[str, Any]) -> bool:
        """Update the analysis summary for a task."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO task_analysis_summary 
                    (task_id, total_articles_analyzed, replace_confidence, augment_confidence,
                     new_tasks_confidence, human_only_confidence, primary_ai_impact, 
                     recommended_tools, key_insights, example_prompts)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    task_id,
                    analysis_data.get('total_articles_analyzed', 0),
                    analysis_data.get('replace_confidence', 0.0),
                    analysis_data.get('augment_confidence', 0.0),
                    analysis_data.get('new_tasks_confidence', 0.0),
                    analysis_data.get('human_only_confidence', 0.0),
                    analysis_data.get('primary_ai_impact', ''),
                    json.dumps(analysis_data.get('recommended_tools', [])),
                    json.dumps(analysis_data.get('key_insights', [])),
                    json.dumps(analysis_data.get('example_prompts', []))
                ))
                
                conn.commit()
                logger.info(f"Updated analysis summary for task {task_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error updating task analysis summary: {e}")
            return False
    
    def get_task_analysis_summary(self, task_id: int) -> Optional[Dict[str, Any]]:
        """Get the analysis summary for a specific task."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT dt.*, tas.*
                    FROM dcwf_tasks dt
                    LEFT JOIN task_analysis_summary tas ON dt.id = tas.task_id
                    WHERE dt.id = ?
                """, (task_id,))
                
                row = cursor.fetchone()
                if row:
                    result = dict(row)
                    # Parse JSON fields
                    for field in ['recommended_tools', 'key_insights', 'example_prompts']:
                        if result.get(field):
                            result[field] = json.loads(result[field])
                    return result
                return None
                
        except Exception as e:
            logger.error(f"Error getting task analysis summary: {e}")
            return None
    
    def search_tasks_by_keyword(self, keyword: str) -> List[Dict[str, Any]]:
        """Search for tasks by keyword in name or description."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT dt.*, tas.primary_ai_impact, tas.replace_confidence, 
                           tas.augment_confidence, tas.new_tasks_confidence, tas.human_only_confidence
                    FROM dcwf_tasks dt
                    LEFT JOIN task_analysis_summary tas ON dt.id = tas.task_id
                    WHERE dt.task_name LIKE ? OR dt.task_description LIKE ?
                    ORDER BY dt.task_name
                """, (f'%{keyword}%', f'%{keyword}%'))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error searching tasks by keyword {keyword}: {e}")
            return []
    
    def get_task_statistics(self) -> Dict[str, Any]:
        """Get statistics about the task-centric database."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get basic counts
                cursor.execute("SELECT COUNT(*) FROM dcwf_tasks")
                total_tasks = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM ai_tools")
                total_tools = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM task_tool_recommendations")
                total_recommendations = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM article_task_mappings")
                total_mappings = cursor.fetchone()[0]
                
                # Get AI impact distribution
                cursor.execute("""
                    SELECT primary_ai_impact, COUNT(*) 
                    FROM task_analysis_summary 
                    WHERE primary_ai_impact IS NOT NULL 
                    GROUP BY primary_ai_impact
                """)
                ai_impact_distribution = dict(cursor.fetchall())
                
                # Get most analyzed work roles
                cursor.execute("""
                    SELECT work_role_name, COUNT(*) as task_count
                    FROM dcwf_tasks 
                    WHERE work_role_name IS NOT NULL 
                    GROUP BY work_role_name 
                    ORDER BY task_count DESC 
                    LIMIT 10
                """)
                top_work_roles = dict(cursor.fetchall())
                
                return {
                    'total_tasks': total_tasks,
                    'total_tools': total_tools,
                    'total_recommendations': total_recommendations,
                    'total_mappings': total_mappings,
                    'ai_impact_distribution': ai_impact_distribution,
                    'top_work_roles': top_work_roles
                }
                
        except Exception as e:
            logger.error(f"Error getting task statistics: {e}")
            return {} 