"""
Perplexity API connector for data gathering.

Collects information using Perplexity's search and analysis capabilities.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import re

import requests
from openai import OpenAI
from bs4 import BeautifulSoup

from aih.gather.base import BaseConnector, Artifact
from aih.config import settings, SEARCH_TEMPLATES, TASK_FOCUSED_QUERIES
from aih.utils.logging import get_logger, log_api_call
from aih.utils.rate_limiter import rate_limiter
from aih.utils.cost_tracker import cost_tracker

logger = get_logger(__name__)

class PerplexityConnector(BaseConnector):
    """
    Connector for Perplexity API to gather AI/cybersecurity workforce information.
    
    Uses Perplexity's real-time search capabilities to find current articles,
    reports, and discussions about AI's impact on cybersecurity jobs.
    """
    
    def __init__(self):
        """Initialize Perplexity connector."""
        super().__init__("perplexity")
        
        if not settings.perplexity_api_key:
            raise ValueError("Perplexity API key not found in configuration")
        
        self.client = OpenAI(
            api_key=settings.perplexity_api_key,
            base_url="https://api.perplexity.ai"
        )
        
        # Set rate limits from config
        rate_limiter.set_limit('perplexity', settings.perplexity_requests_per_minute)
    
    def validate_config(self) -> bool:
        """Validate Perplexity API configuration."""
        try:
            # Make a test request
            rate_limiter.wait_if_needed('perplexity')
            
            response = self.client.chat.completions.create(
                model="sonar-small",
                messages=[{"role": "user", "content": "Test connection"}],
                max_tokens=10
            )
            
            logger.info("Perplexity API connection validated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Perplexity API validation failed: {e}")
            return False
    
    async def collect(self, query: str, max_results: int = 10, 
                     category: str = "general", timeframe: str = "2024") -> List[Artifact]:
        """
        Collect artifacts from Perplexity API.
        
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
            
            logger.info(f"Collecting artifacts from Perplexity: {focused_query}")
            
            # Rate limiting
            rate_limiter.wait_if_needed('perplexity')
            
            # Make API request
            response = self.client.chat.completions.create(
                model="sonar-pro",  # Use pro model for better results
                messages=[
                    {
                        "role": "system", 
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user", 
                        "content": focused_query
                    }
                ],
                max_tokens=2000,
                temperature=0.3  # Lower temperature for more factual responses
            )
            
            # Log API call
            usage = response.usage
            estimated_cost = self._estimate_cost(usage.total_tokens)
            log_api_call(
                api_type="perplexity",
                prompt=focused_query,
                response=response.choices[0].message.content[:200],
                tokens=usage.total_tokens,
                cost=estimated_cost
            )
            
            # Track API cost with actual token usage
            cost_tracker.track_api_call("perplexity", "sonar_large", usage.total_tokens)
            
            # Parse response using proper citation extraction
            content = response.choices[0].message.content
            parsed_artifacts = self._parse_response_with_citations(content, focused_query, response)
            
            artifacts.extend(parsed_artifacts[:max_results])
            
            logger.info(f"Collected {len(artifacts)} artifacts from Perplexity")
            
        except Exception as e:
            logger.error(f"Error collecting from Perplexity: {e}")
            raise
        
        return artifacts
    
    def _build_focused_query(self, base_query: str, category: str, timeframe: str) -> str:
        """
        Build a focused query based on category and timeframe.
        
        Args:
            base_query: Base search query
            category: AI impact category
            timeframe: Time period or filter (e.g., "2024", "after:2024-01-01", "after:2024-01-01 before:2024-12-31")
            
        Returns:
            Enhanced query string
        """
        # Start with base query
        query_parts = [base_query]
        
        # Add timeframe if provided
        if timeframe:
            if timeframe.startswith('after:') or timeframe.startswith('before:') or 'after:' in timeframe:
                # Use Perplexity's date filter syntax directly
                query_parts.append(timeframe)
            elif timeframe and timeframe != "all_time":
                # For simple timeframes like "2024", "2024-2025", append as context
                query_parts.append(timeframe)
        
        # Use template if category is recognized
        if category in SEARCH_TEMPLATES:
            template_query = SEARCH_TEMPLATES[category].format(timeframe=timeframe or "2024")
            query_parts.insert(0, template_query)
        
        # Add context for better results
        context_additions = [
            "cybersecurity workforce",
            "artificial intelligence impact",
            "job market analysis",
            "recent studies reports"
        ]
        
        # Combine all parts
        enhanced_query = f"{' '.join(query_parts)} {' '.join(context_additions)}"
        
        # Limit query length
        if len(enhanced_query) > 250:
            enhanced_query = enhanced_query[:250] + "..."
        
        return enhanced_query
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for Perplexity API."""
        return """You are a research assistant analyzing the impact of AI on cybersecurity workforce. 
        
        For each query, provide a comprehensive analysis that includes:
        1. Current trends and developments
        2. Specific examples with sources
        3. Expert opinions and studies
        4. Concrete data points where available
        5. Clear citations and references
        
        Focus on factual, evidence-based information from credible sources like:
        - Academic research papers
        - Industry reports from major consulting firms
        - Government cybersecurity agencies
        - Established technology news outlets
        - Professional cybersecurity organizations
        
        Always include source URLs when possible and indicate the credibility level of each source."""
    
    def _scrape_article_title(self, url: str) -> str:
        """
        Scrape the actual article title from a URL.
        
        Args:
            url: URL to scrape
            
        Returns:
            Article title or None if scraping fails
        """
        try:
            # Set timeout and headers to avoid blocking
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try multiple selectors for title
            title_selectors = [
                'title',
                'meta[property="og:title"]',
                'meta[name="twitter:title"]',
                'h1',
                '.title',
                '.article-title'
            ]
            
            for selector in title_selectors:
                element = soup.select_one(selector)
                if element:
                    title = element.get('content') if element.name == 'meta' else element.get_text()
                    title = title.strip()
                    if title and len(title) > 5:  # Reasonable title length
                        return title
            
            return None
            
        except Exception as e:
            logger.debug(f"Failed to scrape title from {url}: {e}")
            return None

    def _parse_response_with_citations(self, content: str, original_query: str, response) -> List[Artifact]:
        """
        Parse Perplexity response and extract artifacts using citations.
        
        Args:
            content: Response content from API
            original_query: Original search query
            response: Full API response
            
        Returns:
            List of parsed artifacts
        """
        artifacts = []
        
        # Extract citations from response
        citations = self._extract_citations(response)
        
        # If we found citations, create artifacts for each
        if citations:
            # Split content into sections based on citations
            sections = self._split_content_by_citations(content, citations)
            
            for i, citation in enumerate(citations):
                # Use actual article title if available
                title = citation.get('title') 
                
                # If no title from Perplexity, try scraping from URL
                if not title or title.strip() == "":
                    scraped_title = self._scrape_article_title(citation['url'])
                    if scraped_title:
                        title = scraped_title
                        logger.info(f"Scraped title: {title[:50]}...")
                    else:
                        # Fallback to content-based title
                        title = self._extract_title_from_content(content, i)
                        logger.warning(f"Using fallback title for {citation['url']}")
                
                # Get the content section for this citation
                section_content = sections.get(citation['url'], content)
                
                artifact = self._create_artifact(
                    url=citation['url'],
                    title=title,
                    content=section_content,
                    metadata={
                        "original_query": original_query,
                        "response_section": i + 1,
                        "total_sources": len(citations),
                        "extraction_method": "perplexity_citations",
                        "full_response": content,
                        "source": citation['source'],
                        "date": citation['date'],
                        "title_source": "scraped" if not citation.get('title') else "perplexity"
                    }
                )
                artifacts.append(artifact)
        else:
            # If no citations found, create a single artifact with the full response
            artifact = self._create_artifact(
                url=f"perplexity://search/{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                title=f"Perplexity Analysis: {original_query[:50]}...",
                content=content,
                metadata={
                    "original_query": original_query,
                    "extraction_method": "full_response",
                    "source_type": "perplexity_analysis"
                }
            )
            artifacts.append(artifact)
        
        return artifacts
    
    def _extract_citations(self, response):
        """
        Extract citations from Perplexity API response.
        
        Args:
            response: Full API response object
            
        Returns:
            List of citation URLs with metadata
        """
        citations = []
        
        try:
            # Convert response to dict to access citation fields
            response_dict = response.model_dump()
            
            # PRIORITIZE search_results field (has more metadata including titles)
            if 'search_results' in response_dict:
                for result in response_dict['search_results']:
                    citations.append({
                        'url': result.get('url', ''),
                        'title': result.get('title', ''),
                        'date': result.get('date', None),
                        'source': 'search_result'
                    })
            
            # Add from direct citations field if search_results didn't provide enough
            if 'citations' in response_dict and len(citations) < 5:
                for url in response_dict['citations']:
                    # Skip if already have this URL from search_results
                    existing_urls = [c['url'] for c in citations]
                    if url not in existing_urls:
                        citations.append({
                            'url': url,
                            'title': None,  # Will be scraped later
                            'date': None,
                            'source': 'citation'
                        })
            
            # Remove duplicates based on URL
            seen_urls = set()
            unique_citations = []
            for citation in citations:
                if citation['url'] and citation['url'] not in seen_urls:
                    seen_urls.add(citation['url'])
                    unique_citations.append(citation)
            
            return unique_citations
            
        except Exception as e:
            logger.error(f"Error extracting citations: {e}")
            return []
    
    def _split_content_by_citations(self, content: str, citations: List[Dict]) -> Dict[str, str]:
        """
        Split content into sections associated with specific citations.
        
        Args:
            content: Full response content
            citations: List of citation dictionaries
            
        Returns:
            Dictionary mapping citation URLs to their associated content
        """
        sections = {}
        
        if not citations:
            return sections
        
        # Split content into paragraphs
        paragraphs = [p.strip() for p in content.split('\n') if p.strip()]
        
        # For now, associate the full content with each citation
        # This ensures each artifact has the complete analysis
        # TODO: Could improve by parsing citation numbers [1][2] to match specific content
        for citation in citations:
            sections[citation['url']] = content
        
        return sections
    
    def _extract_title_from_content(self, content: str, index: int) -> str:
        """
        Extract or generate a title from content.
        
        Args:
            content: Section content
            index: Section index
            
        Returns:
            Generated title
        """
        # Try to find a title-like sentence (first sentence, capitalized)
        sentences = content.split('.')
        if sentences:
            first_sentence = sentences[0].strip()
            if len(first_sentence) < 100:  # Reasonable title length
                return first_sentence
        
        # Fallback: use first 50 characters + ...
        truncated = content[:50].strip()
        if len(content) > 50:
            truncated += "..."
        
        return f"AI Cybersecurity Impact Analysis {index + 1}: {truncated}"
    
    def _estimate_cost(self, tokens: int) -> float:
        """
        Estimate cost of API call based on tokens.
        
        Args:
            tokens: Number of tokens used
            
        Returns:
            Estimated cost in USD
        """
        # Perplexity pricing (approximate)
        # sonar-pro: $0.0006 per 1K tokens (blended input/output)
        cost_per_1k_tokens = 0.0006
        return (tokens / 1000) * cost_per_1k_tokens 
    
    async def collect_multi_query(self, category: str = "general", max_results: int = 20, 
                                 timeframe: str = "2024", existing_urls: set = None) -> List[Artifact]:
        """
        Collect artifacts using multiple task-focused queries to get more diverse results.
        
        Args:
            category: Category type (replace, augment, new_tasks, human_only, general)
            max_results: Maximum total number of unique results
            timeframe: Time period to focus on
            existing_urls: Set of URLs already collected to avoid duplicates
            
        Returns:
            List of unique collected artifacts
        """
        if existing_urls is None:
            existing_urls = set()
        
        all_artifacts = []
        collected_urls = set(existing_urls)
        
        # Get queries for the category
        if category in TASK_FOCUSED_QUERIES:
            queries = TASK_FOCUSED_QUERIES[category]
        else:
            # Fallback to all queries if category not found
            queries = []
            for cat_queries in TASK_FOCUSED_QUERIES.values():
                queries.extend(cat_queries)
        
        logger.info(f"Multi-query collection for category '{category}' using {len(queries)} queries")
        
        for i, query in enumerate(queries):
            if len(all_artifacts) >= max_results:
                break
                
            logger.info(f"Query {i+1}/{len(queries)}: {query}")
            
            try:
                # Collect artifacts for this query
                artifacts = await self.collect(
                    query=query,
                    max_results=8,  # Limit per query to encourage diversity
                    category=category,
                    timeframe=timeframe
                )
                
                # Filter out duplicates
                new_artifacts = []
                for artifact in artifacts:
                    if artifact.url not in collected_urls:
                        new_artifacts.append(artifact)
                        collected_urls.add(artifact.url)
                        all_artifacts.append(artifact)
                    else:
                        logger.debug(f"Skipping duplicate URL: {artifact.url}")
                
                logger.info(f"Added {len(new_artifacts)} new artifacts (total: {len(all_artifacts)})")
                
                # Rate limiting between queries
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in query '{query}': {e}")
                continue
        
        logger.info(f"Multi-query collection complete: {len(all_artifacts)} unique artifacts")
        return all_artifacts[:max_results] 