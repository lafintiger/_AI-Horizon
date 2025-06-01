"""
Base connector class for data gathering.

Defines the interface for all data connectors.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class Artifact:
    """Data structure for collected artifacts."""
    id: str
    url: str
    title: str
    content: str
    source_type: str
    collected_at: datetime
    metadata: Dict[str, Any]

class BaseConnector(ABC):
    """Abstract base class for all data connectors."""
    
    def __init__(self, name: str):
        """
        Initialize connector.
        
        Args:
            name: Name of the connector (e.g., 'perplexity', 'bing_news')
        """
        self.name = name
        self.source_type = name
    
    @abstractmethod
    async def collect(self, query: str, max_results: int = 10, **kwargs) -> List[Artifact]:
        """
        Collect artifacts based on a query.
        
        Args:
            query: Search query or topic
            max_results: Maximum number of results to return
            **kwargs: Additional connector-specific parameters
            
        Returns:
            List of collected artifacts
        """
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """
        Validate connector configuration (API keys, etc.).
        
        Returns:
            True if configuration is valid
        """
        pass
    
    def _generate_artifact_id(self, url: str) -> str:
        """
        Generate a unique artifact ID from URL.
        
        Args:
            url: Source URL
            
        Returns:
            Unique artifact identifier
        """
        import hashlib
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        return f"{self.name}_{timestamp}_{url_hash}"
    
    def _create_artifact(self, url: str, title: str, content: str, 
                        metadata: Dict[str, Any] = None) -> Artifact:
        """
        Create an Artifact object.
        
        Args:
            url: Source URL
            title: Article/content title
            content: Full text content
            metadata: Additional metadata
            
        Returns:
            Artifact object
        """
        return Artifact(
            id=self._generate_artifact_id(url),
            url=url,
            title=title,
            content=content,
            source_type=self.source_type,
            collected_at=datetime.now(),
            metadata=metadata or {}
        ) 