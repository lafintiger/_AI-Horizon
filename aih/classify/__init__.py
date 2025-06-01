"""
Classification modules for AI-Horizon pipeline.

Handles AI-powered classification of artifacts and NID-based source scoring.
"""

from .classifier import ArtifactClassifier
from .scorer import SourceScorer

__all__ = ["ArtifactClassifier", "SourceScorer"] 