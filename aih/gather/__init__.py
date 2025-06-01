"""
Data gathering modules for AI-Horizon pipeline.

Collects artifacts from various sources including Perplexity API, news sources,
job postings, and other relevant content.
"""

from .perplexity import PerplexityConnector
from .base import BaseConnector

__all__ = ["PerplexityConnector", "BaseConnector"] 