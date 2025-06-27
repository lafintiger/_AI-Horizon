"""
Direct SearXNG connector with local AI analysis.

Alternative to Perplexica that uses SearXNG directly and processes results with local AI.
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
from aih.utils.ollama_client import OllamaClient

logger = get_logger(__name__)

class SearXNGDirectConnector(BaseConnector):
    """
    Direct SearXNG connector with local AI analysis.
    
    Uses SearXNG for search and local Ollama models for AI analysis.
    More reliable alternative to Perplexica.
    """
    
    def __init__(self, searxng_url: str = None):
        """Initialize SearXNG direct connector."""
        super().__init__("searxng_direct")
        
        self.searxng_url = searxng_url or "http://localhost:4000"
        self.ollama_client = OllamaClient()
        self.session = requests.Session()
        
        # No rate limiting needed for local instance
        rate_limiter.set_limit('searxng_direct', 1000)
        
        logger.info(f"🔍 SearXNG Direct connector initialized: {self.searxng_url}")
    
    def validate_config(self) -> bool:
        """Validate SearXNG and Ollama configuration."""
        try:
            # Test SearXNG
            response = self.session.get(f"{self.searxng_url}/search?q=test&format=json", timeout=10)
            if response.status_code != 200:
                logger.error(f"❌ SearXNG not accessible: HTTP {response.status_code}")
                return False
            
            # Test Ollama
            if not self.ollama_client.validate_connection():
                logger.error("❌ Ollama not accessible")
                return False
            
            logger.info("✅ SearXNG Direct connection validated successfully")
            return True
                
        except Exception as e:
            logger.error(f"❌ SearXNG Direct validation failed: {e}")
            return False
    
    async def collect(self, query: str, max_results: int = 10, 
                     category: str = "general", timeframe: str = "2024") -> List[Artifact]:
        """
        Collect artifacts using SearXNG + local AI analysis.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            category: Category type
            timeframe: Time period to focus on
            
        Returns:
            List of collected artifacts
        """
        artifacts = []
        
        try:
            # Build focused query
            focused_query = self._build_focused_query(query, category, timeframe)
            
            logger.info(f"🔍 Collecting artifacts via SearXNG Direct: {focused_query}")
            
            rate_limiter.wait_if_needed('searxng_direct')
            
            start_time = time.time()
            
            # Search with SearXNG
            search_results = self._search_searxng(focused_query)
            
            if search_results:
                # Generate AI analysis of the search results
                ai_analysis = self._generate_ai_analysis(focused_query, search_results)
                
                # Create AI analysis artifact
                if ai_analysis:
                    analysis_artifact = Artifact(
                        id=self._generate_artifact_id("searxng://ai-analysis"),
                        title=f"AI Analysis: {query}",
                        content=ai_analysis,
                        url="searxng://ai-analysis",
                        source_type="searxng_direct",
                        collected_at=datetime.now(),
                        metadata={
                            "query": focused_query,
                            "source_count": len(search_results),
                            "ai_generated": True,
                            "category": category,
                            "relevance_score": 0.95
                        }
                    )
                    artifacts.append(analysis_artifact)
                
                # Process search results into artifacts
                for i, result in enumerate(search_results[:max_results-1]):  # Save one spot for AI analysis
                    try:
                        artifact = self._create_artifact_from_result(result, focused_query, category, i)
                        if artifact:
                            artifacts.append(artifact)
                    except Exception as e:
                        logger.warning(f"⚠️ Error processing result {i}: {e}")
                        continue
                
                elapsed_time = time.time() - start_time
                
                # Log usage
                log_api_call(
                    api_type="searxng_direct",
                    prompt=focused_query,
                    response=f"Found {len(search_results)} results, generated AI analysis",
                    tokens=len(focused_query.split()) * 2,
                    cost=0.0
                )
                
                cost_tracker.track_api_call("searxng_direct", "search_and_analyze", 
                                          len(focused_query.split()) * 2, custom_cost=0.0)
                
                logger.info(f"✅ Collected {len(artifacts)} artifacts via SearXNG Direct in {elapsed_time:.2f}s")
            
        except Exception as e:
            logger.error(f"❌ Error in SearXNG Direct collection: {e}")
            return []
        
        return artifacts
    
    def _search_searxng(self, query: str) -> List[Dict[str, Any]]:
        """Search SearXNG directly."""
        try:
            response = self.session.get(
                f"{self.searxng_url}/search",
                params={
                    "q": query,
                    "format": "json",
                    "categories": "general",
                    "time_range": "",
                    "language": "en"
                },
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("results", [])
            else:
                logger.error(f"❌ SearXNG search failed: HTTP {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"❌ SearXNG search error: {e}")
            return []
    
    def _generate_ai_analysis(self, query: str, search_results: List[Dict[str, Any]]) -> str:
        """Generate AI analysis of search results using local Ollama."""
        try:
            # Prepare context from search results
            context_items = []
            for i, result in enumerate(search_results[:5]):  # Use top 5 results
                title = result.get("title", "")
                content = result.get("content", "")
                url = result.get("url", "")
                
                if title and content:
                    context_items.append(f"Source {i+1}: {title}\n{content[:200]}...\nURL: {url}")
            
            context = "\n\n".join(context_items)
            
            # Create analysis prompt
            prompt = f"""Based on the following search results about "{query}", provide a comprehensive analysis focusing on cybersecurity workforce implications:

Search Results:
{context}

Please provide:
1. Key trends and insights related to AI and cybersecurity workforce
2. Implications for job roles and skills
3. Important developments or announcements
4. Future outlook and recommendations

Focus on actionable insights for cybersecurity professionals and workforce planning."""

            # Generate analysis using local AI
            response = self.ollama_client.generate(
                prompt=prompt,
                task_type="analysis",
                max_tokens=1000
            )
            
            return response.content if response.success else ""
            
        except Exception as e:
            logger.error(f"❌ AI analysis generation failed: {e}")
            return ""
    
    def _create_artifact_from_result(self, result: Dict[str, Any], query: str, 
                                   category: str, index: int) -> Optional[Artifact]:
        """Create an Artifact from a SearXNG search result."""
        try:
            title = result.get("title", f"Search Result {index+1}")
            content = result.get("content", "")
            url = result.get("url", "")
            published_date = result.get("publishedDate")
            
            if not content or not url:
                return None
            
            # Parse published date
            if published_date:
                try:
                    parsed_date = datetime.fromisoformat(published_date.replace("Z", "+00:00"))
                except:
                    parsed_date = datetime.now()
            else:
                parsed_date = datetime.now()
            
            artifact = Artifact(
                id=self._generate_artifact_id(url),
                title=title,
                content=content,
                url=url,
                source_type="searxng_direct",
                collected_at=parsed_date,
                metadata={
                    "query": query,
                    "search_index": index,
                    "category": category,
                    "relevance_score": max(0.5, 0.9 - (index * 0.05)),
                    "engines": result.get("engines", []),
                    "score": result.get("score", 0)
                }
            )
            
            return artifact
            
        except Exception as e:
            logger.error(f"❌ Error creating artifact from result: {e}")
            return None
    
    def _build_focused_query(self, base_query: str, category: str, timeframe: str) -> str:
        """Build a focused query based on category and timeframe."""
        query_parts = [base_query]
        
        # Add timeframe context
        if timeframe and timeframe != "all_time":
            query_parts.append(f"in {timeframe}")
        
        # Use template if category is recognized
        if category in SEARCH_TEMPLATES:
            template_query = SEARCH_TEMPLATES[category].format(timeframe=timeframe or "2024")
            query_parts.insert(0, template_query)
        
        # Add context for better results
        context_additions = [
            "cybersecurity workforce",
            "artificial intelligence automation",
            "job market trends"
        ]
        
        enhanced_query = f"{' '.join(query_parts)} {' '.join(context_additions)}"
        
        # Limit query length
        if len(enhanced_query) > 200:
            enhanced_query = enhanced_query[:200] + "..."
        
        return enhanced_query
    
    async def collect_multi_query(self, category: str = "general", max_results: int = 20, 
                                 timeframe: str = "2024", existing_urls: set = None) -> List[Artifact]:
        """Collect artifacts using multiple focused queries."""
        all_artifacts = []
        existing_urls = existing_urls or set()
        
        # Get task-focused queries for the category
        queries = TASK_FOCUSED_QUERIES.get(category, ["AI cybersecurity workforce"])
        
        for i, query in enumerate(queries[:3]):  # Limit to 3 queries
            try:
                artifacts = await self.collect(
                    query=query,
                    max_results=max_results // 3,
                    category=category,
                    timeframe=timeframe
                )
                
                # Filter out duplicates
                for artifact in artifacts:
                    if artifact.url not in existing_urls:
                        all_artifacts.append(artifact)
                        existing_urls.add(artifact.url)
                
            except Exception as e:
                logger.error(f"❌ Error in multi-query collection {i}: {e}")
                continue
        
        return all_artifacts[:max_results] 