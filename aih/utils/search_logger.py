#!/usr/bin/env python3
"""
Search Logging System for AI-Horizon

Provides comprehensive logging of all search operations, prompts used, and results obtained.
Essential for NSF project documentation and reproducibility.
"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

from aih.config import get_data_path
from aih.utils.logging import get_logger

logger = get_logger(__name__)


class SearchType(Enum):
    """Types of searches performed."""
    AUTOMATED_SINGLE = "automated_single"
    AUTOMATED_MULTI = "automated_multi_query"
    MANUAL_ENTRY = "manual_entry"
    WEEKLY_COLLECTION = "weekly_collection"


@dataclass
class SearchSession:
    """Represents a complete search session with metadata."""
    session_id: str
    search_type: SearchType
    started_at: datetime
    completed_at: Optional[datetime] = None
    total_queries: int = 0
    total_results: int = 0
    unique_results: int = 0
    duplicates_filtered: int = 0
    errors: List[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.metadata is None:
            self.metadata = {}


@dataclass  
class SearchQuery:
    """Represents a single search query within a session."""
    query_id: str
    session_id: str
    prompt: str
    search_term: str
    max_results: int
    executed_at: datetime
    results_count: int = 0
    processing_time_seconds: float = 0.0
    success: bool = True
    error_message: Optional[str] = None
    category: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class SearchResult:
    """Represents a single search result with full metadata."""
    result_id: str
    query_id: str
    session_id: str
    artifact_id: str
    url: str
    title: str
    content_length: int
    collected_at: datetime
    duplicate_of: Optional[str] = None
    quality_score: float = 0.0
    credibility_score: float = 0.0
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class SearchLogger:
    """
    Comprehensive search logging system for academic reproducibility.
    
    Tracks all search operations with full provenance and metadata.
    """
    
    def __init__(self):
        self.log_dir = get_data_path("logs") / "searches"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Current session tracking
        self.current_session: Optional[SearchSession] = None
        self.current_queries: List[SearchQuery] = []
        self.current_results: List[SearchResult] = []
    
    def start_search_session(
        self,
        search_type: SearchType,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Start a new search session.
        
        Args:
            search_type: Type of search being performed
            metadata: Additional session metadata
            
        Returns:
            Session ID for tracking
        """
        session_id = f"search_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        self.current_session = SearchSession(
            session_id=session_id,
            search_type=search_type,
            started_at=datetime.now(timezone.utc),
            metadata=metadata or {}
        )
        
        self.current_queries = []
        self.current_results = []
        
        logger.info(f"Started search session: {session_id} ({search_type.value})")
        return session_id
    
    def log_search_query(
        self,
        prompt: str,
        search_term: str,
        max_results: int,
        category: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Log a search query within the current session.
        
        Args:
            prompt: The full prompt template used
            search_term: The actual search term sent to API
            max_results: Maximum results requested
            category: Category if applicable (replace, augment, etc.)
            metadata: Additional query metadata
            
        Returns:
            Query ID for tracking
        """
        if not self.current_session:
            raise ValueError("No active search session. Call start_search_session() first.")
        
        query_id = f"query_{datetime.now().strftime('%H%M%S')}_{uuid.uuid4().hex[:6]}"
        
        query = SearchQuery(
            query_id=query_id,
            session_id=self.current_session.session_id,
            prompt=prompt,
            search_term=search_term,
            max_results=max_results,
            executed_at=datetime.now(timezone.utc),
            category=category,
            metadata=metadata or {}
        )
        
        self.current_queries.append(query)
        self.current_session.total_queries += 1
        
        logger.info(f"Logged search query: {query_id} for '{search_term[:50]}...'")
        return query_id
    
    def update_query_results(
        self,
        query_id: str,
        results_count: int,
        processing_time: float,
        success: bool = True,
        error_message: Optional[str] = None
    ):
        """
        Update query with results information.
        
        Args:
            query_id: The query to update
            results_count: Number of results returned
            processing_time: Processing time in seconds
            success: Whether query succeeded
            error_message: Error message if failed
        """
        query = next((q for q in self.current_queries if q.query_id == query_id), None)
        if not query:
            logger.warning(f"Query {query_id} not found for update")
            return
        
        query.results_count = results_count
        query.processing_time_seconds = processing_time
        query.success = success
        query.error_message = error_message
        
        if not success and error_message:
            self.current_session.errors.append(f"{query_id}: {error_message}")
    
    def log_search_result(
        self,
        query_id: str,
        artifact_id: str,
        url: str,
        title: str,
        content_length: int,
        duplicate_of: Optional[str] = None,
        quality_score: float = 0.0,
        credibility_score: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Log a search result.
        
        Args:
            query_id: The query that produced this result
            artifact_id: The artifact ID in database
            url: Source URL
            title: Article title
            content_length: Length of content
            duplicate_of: If duplicate, the original artifact ID
            quality_score: Calculated quality score
            credibility_score: Calculated credibility score
            metadata: Additional result metadata
            
        Returns:
            Result ID for tracking
        """
        if not self.current_session:
            raise ValueError("No active search session")
        
        result_id = f"result_{len(self.current_results)+1:03d}_{uuid.uuid4().hex[:6]}"
        
        result = SearchResult(
            result_id=result_id,
            query_id=query_id,
            session_id=self.current_session.session_id,
            artifact_id=artifact_id,
            url=url,
            title=title,
            content_length=content_length,
            collected_at=datetime.now(timezone.utc),
            duplicate_of=duplicate_of,
            quality_score=quality_score,
            credibility_score=credibility_score,
            metadata=metadata or {}
        )
        
        self.current_results.append(result)
        
        # Update session statistics
        self.current_session.total_results += 1
        if duplicate_of:
            self.current_session.duplicates_filtered += 1
        else:
            self.current_session.unique_results += 1
        
        return result_id
    
    def end_search_session(self):
        """End the current search session and save all logs."""
        if not self.current_session:
            logger.warning("No active search session to end")
            return
        
        self.current_session.completed_at = datetime.now(timezone.utc)
        
        # Save session log
        session_file = self.log_dir / f"{self.current_session.session_id}_session.json"
        session_data = {
            "session": asdict(self.current_session),
            "queries": [asdict(q) for q in self.current_queries],
            "results": [asdict(r) for r in self.current_results]
        }
        
        # Convert datetime objects to ISO strings for JSON serialization
        session_data = self._serialize_datetimes(session_data)
        
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Search session completed: {self.current_session.session_id}")
        logger.info(f"  Queries: {self.current_session.total_queries}")
        logger.info(f"  Total results: {self.current_session.total_results}")
        logger.info(f"  Unique results: {self.current_session.unique_results}")
        logger.info(f"  Duplicates filtered: {self.current_session.duplicates_filtered}")
        
        # Clear current session
        self.current_session = None
        self.current_queries = []
        self.current_results = []
    
    def get_search_history(
        self,
        search_type: Optional[SearchType] = None,
        days_back: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get search history for analysis.
        
        Args:
            search_type: Filter by search type
            days_back: How many days back to look
            
        Returns:
            List of session summaries
        """
        history = []
        cutoff_date = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        cutoff_date = cutoff_date.replace(day=cutoff_date.day - days_back)
        
        for session_file in self.log_dir.glob("*_session.json"):
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                
                session = session_data["session"]
                session_date = datetime.fromisoformat(session["started_at"].replace('Z', '+00:00'))
                
                if session_date < cutoff_date:
                    continue
                
                if search_type and session["search_type"] != search_type.value:
                    continue
                
                history.append({
                    "session_id": session["session_id"],
                    "search_type": session["search_type"],
                    "started_at": session["started_at"],
                    "completed_at": session.get("completed_at"),
                    "total_queries": session["total_queries"],
                    "total_results": session["total_results"],
                    "unique_results": session["unique_results"],
                    "duplicates_filtered": session["duplicates_filtered"],
                    "queries": len(session_data["queries"]),
                    "results": len(session_data["results"])
                })
                
            except Exception as e:
                logger.error(f"Error reading session file {session_file}: {e}")
        
        return sorted(history, key=lambda x: x["started_at"], reverse=True)
    
    def _serialize_datetimes(self, obj):
        """Recursively convert datetime objects to ISO strings."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {k: self._serialize_datetimes(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize_datetimes(item) for item in obj]
        else:
            return obj


# Global logger instance
search_logger = SearchLogger()


def log_search_session(search_type: SearchType, metadata: Optional[Dict[str, Any]] = None):
    """
    Context manager for search sessions.
    
    Usage:
        with log_search_session(SearchType.AUTOMATED_SINGLE) as session_id:
            query_id = search_logger.log_search_query(prompt, term, max_results)
            # ... perform search ...
            search_logger.update_query_results(query_id, count, time)
    """
    class SearchSessionContext:
        def __init__(self, search_type: SearchType, metadata: Optional[Dict[str, Any]]):
            self.search_type = search_type
            self.metadata = metadata
            self.session_id = None
        
        def __enter__(self):
            self.session_id = search_logger.start_search_session(self.search_type, self.metadata)
            return self.session_id
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            if exc_type:
                # Log any exception that occurred
                if search_logger.current_session:
                    search_logger.current_session.errors.append(f"Session error: {str(exc_val)}")
            search_logger.end_search_session()
    
    return SearchSessionContext(search_type, metadata) 