"""
Perplexica connector for local data gathering.

Replaces external Perplexity API with local Perplexica instance.
Provides the same interface as PerplexityConnector for seamless migration.
"""

import asyncio
import json
import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

import requests
from bs4 import BeautifulSoup

from aih.gather.base import BaseConnector, Artifact
from aih.config import settings, SEARCH_TEMPLATES, TASK_FOCUSED_QUERIES
from aih.utils.logging import get_logger, log_api_call
from aih.utils.rate_limiter import rate_limiter
from aih.utils.cost_tracker import cost_tracker

logger = get_logger(__name__)

class PerplexicaConnector(BaseConnector):
    """
    Connector for local Perplexica instance to gather AI/cybersecurity workforce information.
    
    Replaces external Perplexity API with local Perplexica instance running on port 3000.
    Provides identical interface to PerplexityConnector for seamless migration.
    """
    
    def __init__(self, base_url: str = None):
        """Initialize Perplexica connector."""
        super().__init__("perplexica")
        
        self.base_url = base_url or getattr(settings, 'perplexica_url', 'http://localhost:3000')
        self.session = requests.Session()
        
        # No rate limiting needed for local instance
        rate_limiter.set_limit('perplexica', 1000)  # Generous limit for local
        
        logger.info(f"🔍 Perplexica connector initialized: {self.base_url}")
    
    def validate_config(self) -> bool:
        """Validate Perplexica instance configuration."""
        try:
            # Test connection with a simple POST request
            response = self.session.post(
                f"{self.base_url}/api/chat",
                json={
                    "message": "test",
                    "focusMode": "webSearch",
                    "history": [],
                    "optimizationMode": "speed"
                },
                timeout=10
            )
            
            # Perplexica should return 200 for valid requests
            if response.status_code == 200:
                logger.info("✅ Perplexica connection validated successfully")
                return True
            else:
                logger.error(f"❌ Perplexica API check failed: HTTP {response.status_code}")
                logger.error(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Perplexica validation failed: {e}")
            logger.error("   Ensure Perplexica is running on port 3000")
            return False
    
    async def collect(self, query: str, max_results: int = 10, 
                     category: str = "general", timeframe: str = "2024") -> List[Artifact]:
        """
        Collect artifacts from Perplexica instance.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            category: Category type (replace, augment, new_tasks, human_only, general)
            timeframe: Time period to focus on (e.g., "2024", "last 6 months")
            
        Returns:
            List of collected artifacts
        """
        artifacts = []
        
        try:
            # Build focused query based on category
            focused_query = self._build_focused_query(query, category, timeframe)
            
            logger.info(f"🔍 Collecting artifacts from Perplexica: {focused_query}")
            
            # No rate limiting needed for local instance
            rate_limiter.wait_if_needed('perplexica')
            
            # Make API request to Perplexica
            start_time = time.time()
            
            # Based on Perplexica repository, use the chat API endpoint with streaming
            response = self.session.post(
                f"{self.base_url}/api/chat",
                json={
                    "message": focused_query,
                    "history": [],
                    "focusMode": "webSearch",  # Options: webSearch, academicSearch, writingAssistant, etc.
                    "optimizationMode": "speed"  # or "balanced"
                },
                headers={
                    "Content-Type": "application/json"
                },
                timeout=30,
                stream=True
            )
            
            elapsed_time = time.time() - start_time
            
            if response.status_code == 200:
                # Handle streaming response from Perplexica
                search_results = self._parse_streaming_response(response)
                
                # Log API call (no cost for local)
                log_api_call(
                    api_type="perplexica",
                    prompt=focused_query,
                    response=f"Perplexica search completed",
                    tokens=len(focused_query.split()) * 2,  # Rough estimate
                    cost=0.0  # Local is free!
                )
                
                # Track usage without cost
                cost_tracker.track_api_call("perplexica", "local_search", 
                                          len(focused_query.split()) * 2, custom_cost=0.0)
                
                # Parse search results from Perplexica format
                parsed_artifacts = self._parse_perplexica_results(
                    search_results, focused_query, category
                )
                
                artifacts.extend(parsed_artifacts[:max_results])
                
                logger.info(f"✅ Collected {len(artifacts)} artifacts from Perplexica in {elapsed_time:.2f}s")
                
            else:
                logger.error(f"❌ Perplexica search failed: HTTP {response.status_code}")
                logger.error(f"   Response: {response.text}")
                
        except requests.exceptions.Timeout:
            logger.error(f"⏰ Perplexica request timed out after 30 seconds")
            return []
        except requests.exceptions.ConnectionError:
            logger.error(f"🔌 Cannot connect to Perplexica on {self.base_url}")
            logger.error("   Please ensure Perplexica is running on port 3000")
            return []
        except Exception as e:
            logger.error(f"❌ Error collecting from Perplexica: {e}")
            return []
        
        return artifacts
    
    def _parse_streaming_response(self, response) -> Dict[str, Any]:
        """
        Parse streaming response from Perplexica API.
        
        Args:
            response: Streaming HTTP response
            
        Returns:
            Parsed response data
        """
        sources = []
        message = ""
        
        try:
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    try:
                        # Parse each JSON line
                        data = json.loads(line)
                        
                        if data.get("type") == "sources":
                            # Sources information
                            sources = data.get("data", [])
                        elif data.get("type") == "message":
                            # AI response message
                            message += data.get("data", "")
                        elif data.get("type") == "messageEnd":
                            # End of message
                            break
                            
                    except json.JSONDecodeError:
                        # Skip invalid JSON lines
                        continue
                        
        except Exception as e:
            logger.warning(f"⚠️ Error parsing streaming response: {e}")
        
        return {
            "message": message,
            "sources": sources
        }
    
    def _build_focused_query(self, base_query: str, category: str, timeframe: str) -> str:
        """
        Build a focused query based on category and timeframe.
        
        Args:
            base_query: Base search query
            category: AI impact category
            timeframe: Time period or filter
            
        Returns:
            Enhanced query string
        """
        # Start with base query
        query_parts = [base_query]
        
        # Add timeframe context
        if timeframe and timeframe != "all_time":
            if "after:" in timeframe or "before:" in timeframe:
                # Perplexica might support date filters
                query_parts.append(timeframe)
            else:
                # Add as context
                query_parts.append(f"in {timeframe}")
        
        # Use template if category is recognized
        if category in SEARCH_TEMPLATES:
            template_query = SEARCH_TEMPLATES[category].format(timeframe=timeframe or "2024")
            query_parts.insert(0, template_query)
        
        # Add context for better results
        context_additions = [
            "cybersecurity workforce",
            "artificial intelligence automation",
            "job market trends",
            "recent research studies"
        ]
        
        # Combine all parts
        enhanced_query = f"{' '.join(query_parts)} {' '.join(context_additions)}"
        
        # Limit query length
        if len(enhanced_query) > 300:
            enhanced_query = enhanced_query[:300] + "..."
        
        return enhanced_query
    
    def _parse_perplexica_results(self, search_results: Dict[str, Any], 
                                original_query: str, category: str) -> List[Artifact]:
        """
        Parse Perplexica search results into Artifact objects.
        
        Args:
            search_results: Raw search results from Perplexica
            original_query: Original search query
            category: Search category
            
        Returns:
            List of Artifact objects
        """
        artifacts = []
        
        try:
            # Perplexica returns different format than our mock
            # Expected format: {"message": "answer", "sources": [...]}
            
            answer = search_results.get("message", "")
            sources = search_results.get("sources", [])
            
            if answer:
                # Create main artifact from the AI-generated answer
                main_artifact = Artifact(
                    id=self._generate_artifact_id("perplexica://ai-analysis"),
                    title=f"AI Analysis: {original_query}",
                    content=answer,
                    url="perplexica://ai-analysis",
                    source_type="perplexica",
                    collected_at=datetime.now(),
                    metadata={
                        "query": original_query,
                        "source_count": len(sources),
                        "ai_generated": True,
                        "perplexica_focus": "webSearch",
                        "category": category,
                        "relevance_score": 0.95
                    }
                )
                artifacts.append(main_artifact)
            
            # Process sources
            for i, source in enumerate(sources[:10]):  # Limit to 10 sources
                try:
                    # Parse source information
                    title = source.get("title", f"Source {i+1}")
                    url = source.get("url", "")
                    content = source.get("content", "") or source.get("text", "")
                    
                    if content and url:
                        artifact = Artifact(
                            id=self._generate_artifact_id(url),
                            title=title,
                            content=content,
                            url=url,
                            source_type="perplexica",
                            collected_at=self._parse_date(source.get("date", "")),
                            metadata={
                                "query": original_query,
                                "source_index": i,
                                "via_perplexica": True,
                                "category": category,
                                "relevance_score": max(0.5, 0.9 - (i * 0.05))
                            }
                        )
                        artifacts.append(artifact)
                        
                except Exception as e:
                    logger.warning(f"⚠️ Error parsing source {i}: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"❌ Error parsing Perplexica results: {e}")
            
        return artifacts
    
    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string into datetime object."""
        if not date_str:
            return datetime.now()
        
        try:
            # Try common date formats
            for fmt in ['%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S']:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            
            # Fallback to current time
            return datetime.now()
            
        except Exception:
            return datetime.now()
    
    async def collect_multi_query(self, category: str = "general", max_results: int = 20, 
                                 timeframe: str = "2024", existing_urls: set = None) -> List[Artifact]:
        """
        Collect artifacts using multiple focused queries for better coverage.
        
        Args:
            category: AI impact category
            max_results: Maximum total results
            timeframe: Time period filter
            existing_urls: URLs to avoid duplicating
            
        Returns:
            List of collected artifacts
        """
        all_artifacts = []
        existing_urls = existing_urls or set()
        
        # Get task-focused queries for this category
        queries = TASK_FOCUSED_QUERIES.get(category, [])
        
        if not queries:
            # Fallback to general query
            queries = [f"AI impact on cybersecurity workforce {category}"]
        
        results_per_query = max(1, max_results // len(queries))
        
        for i, query in enumerate(queries):
            try:
                logger.info(f"🔍 Multi-query {i+1}/{len(queries)}: {query[:50]}...")
                
                artifacts = await self.collect(
                    query=query,
                    max_results=results_per_query,
                    category=category,
                    timeframe=timeframe
                )
                
                # Filter out duplicates
                new_artifacts = []
                for artifact in artifacts:
                    if artifact.url not in existing_urls:
                        new_artifacts.append(artifact)
                        existing_urls.add(artifact.url)
                
                all_artifacts.extend(new_artifacts)
                
                # Add small delay between queries
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"❌ Multi-query {i+1} failed: {e}")
                continue
        
        logger.info(f"✅ Multi-query collection complete: {len(all_artifacts)} unique artifacts")
        return all_artifacts[:max_results] 