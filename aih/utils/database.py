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
            
            # Count by category from metadata
            cursor.execute("SELECT raw_metadata FROM artifacts WHERE raw_metadata IS NOT NULL")
            category_counts = defaultdict(int)
            for (metadata_json,) in cursor.fetchall():
                try:
                    metadata = json.loads(metadata_json)
                    category = metadata.get('ai_impact_category', 'unknown')
                    category_counts[category] += 1
                except (json.JSONDecodeError, TypeError):
                    category_counts['unknown'] += 1
            
            return {
                'total_artifacts': total_artifacts,
                'total_classifications': total_classifications,
                'source_types': dict(source_types),
                'categories': dict(category_counts),
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