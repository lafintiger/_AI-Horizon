"""
RAG Chat System for AI-Horizon

Enables intelligent conversation with collected cybersecurity articles
using retrieval-augmented generation.
"""

import json
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
import tiktoken

from openai import OpenAI
import anthropic

from aih.config import settings
from aih.utils.database import DatabaseManager
from aih.utils.logging import get_logger

logger = get_logger(__name__)

class RAGChatSystem:
    """
    Retrieval-Augmented Generation chat system for cybersecurity articles.
    
    Allows users to ask questions about collected articles and get
    intelligent responses based on the content.
    """
    
    def __init__(self, model: str = "claude-3-5-sonnet-20241022"):
        """
        Initialize RAG chat system.
        
        Args:
            model: LLM model to use ("gpt-4", "gpt-3.5-turbo", "claude-3-5-sonnet-20241022")
        """
        self.model = model
        self.db = DatabaseManager()
        
        # Initialize LLM clients
        if settings.openai_api_key:
            self.openai_client = OpenAI(api_key=settings.openai_api_key)
        else:
            self.openai_client = None
            
        if settings.anthropic_api_key:
            self.anthropic_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        else:
            self.anthropic_client = None
        
        # Token counting for context management
        self.encoding = tiktoken.get_encoding("cl100k_base")
        
        logger.info(f"RAG Chat System initialized with model: {model}")
        
        # Initialize DCWF framework if available
        self.dcwf_indexer = None
        try:
            from scripts.analysis.dcwf_framework_indexer import DCWFFrameworkIndexer
            self.dcwf_indexer = DCWFFrameworkIndexer()
            logger.info("DCWF Framework integration enabled")
        except ImportError:
            logger.warning("DCWF Framework not available")
    
    def search_articles(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search articles using semantic similarity.
        
        Args:
            query: Search query
            limit: Maximum number of articles to return
            
        Returns:
            List of relevant articles with metadata
        """
        # Get all articles from database
        all_articles = self.db.get_artifacts()
        
        if not all_articles:
            return []
        
        # Simple keyword-based search for now
        # TODO: Implement proper semantic search with embeddings
        query_lower = query.lower()
        query_terms = set(query_lower.split())
        
        scored_articles = []
        
        for article in all_articles:
            content_lower = article['content'].lower()
            title_lower = article.get('title', '').lower()
            
            # Calculate relevance score
            score = 0
            
            # Title matches (higher weight)
            title_matches = sum(1 for term in query_terms if term in title_lower)
            score += title_matches * 3
            
            # Content matches
            content_matches = sum(1 for term in query_terms if term in content_lower)
            score += content_matches
            
            # Bonus for category relevance
            if any(cat in query_lower for cat in ['replace', 'augment', 'new', 'human']):
                source_type = article.get('source_type', '')
                if any(cat in source_type for cat in ['replace', 'augment', 'new', 'human']):
                    score += 2
            
            if score > 0:
                scored_articles.append({
                    'article': article,
                    'score': score,
                    'title': article.get('title', 'Untitled'),
                    'url': article.get('url', ''),
                    'content_preview': content_lower[:300] + "..." if len(content_lower) > 300 else content_lower,
                    'collected_at': article.get('collected_at', ''),
                    'source_type': article.get('source_type', '')
                })
        
        # Sort by relevance score
        scored_articles.sort(key=lambda x: x['score'], reverse=True)
        
        return scored_articles[:limit]
    
    def prepare_context(self, articles: List[Dict[str, Any]], max_tokens: int = 6000) -> str:
        """
        Prepare context from articles for LLM input.
        
        Args:
            articles: List of articles with metadata
            max_tokens: Maximum tokens for context
            
        Returns:
            Formatted context string
        """
        context_parts = []
        current_tokens = 0
        
        context_parts.append("# Cybersecurity Articles Context\n")
        
        for i, item in enumerate(articles, 1):
            article = item['article']
            
            article_text = f"""
## Article {i}: {item['title']}
**Source:** {item['url']}
**Date:** {item['collected_at']}
**Category:** {item['source_type']}

**Content:**
{article['content'][:1500]}{"..." if len(article['content']) > 1500 else ""}

---
"""
            
            # Count tokens
            article_tokens = len(self.encoding.encode(article_text))
            
            if current_tokens + article_tokens > max_tokens:
                break
                
            context_parts.append(article_text)
            current_tokens += article_tokens
        
        return "\n".join(context_parts)
    
    def generate_response(self, query: str, context: str) -> str:
        """
        Generate response using LLM with retrieved context.
        
        Args:
            query: User question
            context: Retrieved article context
            
        Returns:
            Generated response
        """
        system_prompt = """You are an expert cybersecurity workforce analyst with access to recent research articles about AI's impact on cybersecurity jobs and tasks.

Your role is to:
1. Answer questions based ONLY on the provided article context
2. Focus on TASKS rather than jobs (tasks are more granular and important)
3. Cite specific articles when making claims
4. Distinguish between AI replacing, augmenting, creating new, or leaving human-only tasks
5. Provide nuanced, evidence-based analysis

Guidelines:
- Always cite article sources when making claims
- If information isn't in the provided context, say so clearly
- Focus on specific cybersecurity tasks and activities
- Consider the DCWF (DoD Cybersecurity Workforce Framework) perspective
- Be precise about the AI impact category (Replace/Augment/New/Human-Only)"""

        user_prompt = f"""Based on the cybersecurity articles provided below, please answer this question:

**Question:** {query}

**Available Articles:**
{context}

Please provide a comprehensive answer based on the article content, citing specific sources where appropriate."""

        try:
            if self.model.startswith("claude"):
                if not self.anthropic_client:
                    return "❌ Claude API key not configured. Please check your configuration."
                
                response = self.anthropic_client.messages.create(
                    model=self.model,
                    max_tokens=1500,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}]
                )
                return response.content[0].text
                
            elif self.model.startswith("gpt"):
                if not self.openai_client:
                    return "❌ OpenAI API key not configured. Please check your configuration."
                
                response = self.openai_client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=1500,
                    temperature=0.3
                )
                return response.choices[0].message.content
            else:
                return f"❌ Unsupported model: {self.model}"
                
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"❌ Error generating response: {str(e)}"
    
    def chat(self, query: str, category_filter: Optional[str] = None) -> Dict[str, Any]:
        """
        Main chat interface - search articles and generate response.
        
        Args:
            query: User question
            category_filter: Optional category filter (replace, augment, new_tasks, human_only)
            
        Returns:
            Dictionary with response, sources, and metadata
        """
        logger.info(f"Processing chat query: {query[:100]}...")
        
        # Search for relevant articles
        articles = self.search_articles(query, limit=8)
        
        # Filter by category if specified
        if category_filter:
            articles = [a for a in articles if category_filter in a.get('source_type', '')]
        
        if not articles:
            return {
                "response": "❌ No relevant articles found in the database. Please ensure articles have been collected first.",
                "sources": [],
                "total_articles": 0,
                "query": query,
                "timestamp": datetime.now().isoformat()
            }
        
        # Prepare context
        context = self.prepare_context(articles)
        
        # Generate response
        response = self.generate_response(query, context)
        
        # Prepare sources for display
        sources = []
        for item in articles:
            sources.append({
                "title": item['title'],
                "url": item['url'],
                "relevance_score": item['score'],
                "source_type": item['source_type'],
                "content_preview": item['content_preview']
            })
        
        return {
            "response": response,
            "sources": sources,
            "total_articles": len(articles),
            "query": query,
            "model_used": self.model,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_article_summary(self, category: Optional[str] = None) -> Dict[str, Any]:
        """
        Get summary of available articles for chat context.
        
        Args:
            category: Optional category filter
            
        Returns:
            Summary statistics
        """
        all_articles = self.db.get_artifacts()
        
        if category:
            filtered_articles = [a for a in all_articles if category in a.get('source_type', '')]
        else:
            filtered_articles = all_articles
        
        # Count by source type
        source_counts = {}
        total_content = 0
        
        for article in filtered_articles:
            source_type = article.get('source_type', 'unknown')
            source_counts[source_type] = source_counts.get(source_type, 0) + 1
            total_content += len(article.get('content', ''))
        
        return {
            "total_articles": len(filtered_articles),
            "source_breakdown": source_counts,
            "total_content_chars": total_content,
            "avg_content_length": total_content // len(filtered_articles) if filtered_articles else 0,
            "available_for_chat": len(filtered_articles) > 0
        }
    
    def get_enhanced_context(self, query: str, filters: Dict[str, Any] = None) -> str:
        """Get enhanced context with advanced filtering and DCWF integration."""
        if filters is None:
            filters = {}
        
        # Get articles with enhanced search
        articles = self.search_articles_enhanced(query, filters)
        
        # Prepare enhanced context
        context_parts = []
        context_parts.append("# Enhanced Cybersecurity Workforce Intelligence Context\n")
        
        # Add DCWF context if available and relevant
        if self.dcwf_indexer and any(term in query.lower() for term in ['role', 'task', 'dcwf', 'framework', 'job']):
            dcwf_context = self.get_dcwf_context(query)
            if dcwf_context:
                context_parts.append(dcwf_context)
        
        # Add article context
        article_context = self.prepare_context(articles, max_tokens=5000)
        context_parts.append(article_context)
        
        # Add filter information
        if filters:
            filter_info = f"\n## Applied Filters:\n"
            for key, value in filters.items():
                filter_info += f"- **{key}**: {value}\n"
            context_parts.append(filter_info)
        
        return "\n".join(context_parts)
    
    def search_articles_enhanced(self, query: str, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Enhanced article search with advanced filtering."""
        if filters is None:
            filters = {}
        
        # Start with basic search
        articles = self.search_articles(query, limit=50)
        
        # Apply category filters
        if filters.get('categories'):
            categories = filters['categories']
            if isinstance(categories, str):
                categories = [categories]
            articles = [a for a in articles if any(cat in a.get('source_type', '') for cat in categories)]
        
        # Apply confidence threshold
        if filters.get('confidence_threshold'):
            threshold = float(filters['confidence_threshold'])
            articles = [a for a in articles if a.get('score', 0) >= threshold]
        
        return articles[:20]
    
    def get_dcwf_context(self, query: str) -> str:
        """Get relevant DCWF framework context for the query."""
        if not self.dcwf_indexer:
            return ""
        
        try:
            dcwf_results = self.dcwf_indexer.search_framework(query)
            if not dcwf_results:
                return ""
            
            context = "\n## DCWF Framework Context\n"
            context += "**DoD Cybersecurity Workforce Framework (DCWF) Relevant Information:**\n\n"
            
            for i, result in enumerate(dcwf_results[:5], 1):
                context += f"**{i}. {result.get('work_role_name', 'Unknown Role')}**\n"
                context += f"- **Role ID**: {result.get('work_role_id', 'N/A')}\n"
                context += f"- **Description**: {result.get('role_description', 'N/A')[:200]}...\n"
                
                tasks = result.get('tasks', [])
                if tasks:
                    context += f"- **Key Tasks**: {', '.join(tasks[:3])}...\n"
                context += "\n"
            
            return context
        except Exception as e:
            logger.error(f"Error getting DCWF context: {e}")
            return ""
    
    def get_source_citations(self, query: str, context: str) -> List[Dict[str, Any]]:
        """Extract source citations from the context."""
        articles = self.search_articles(query, limit=10)
        
        citations = []
        for item in articles:
            article = item['article']
            citations.append({
                'title': item['title'],
                'url': item['url'],
                'source_type': item['source_type'],
                'collected_at': item['collected_at'],
                'relevance_score': item['score'],
                'content_preview': item['content_preview'],
                'metadata': {
                    'id': article.get('id'),
                    'source': article.get('source', 'Unknown'),
                    'quality_score': article.get('quality_score', 0)
                }
            })
        
        return citations
    
    def get_suggested_questions(self) -> List[str]:
        """Generate suggested questions based on current database content."""
        stats = self.db.get_database_stats()
        
        suggestions = [
            "What cybersecurity tasks are being replaced by AI?",
            "How is AI augmenting human cybersecurity work?",
            "What new cybersecurity roles are being created by AI?",
            "Which cybersecurity tasks remain uniquely human?",
            "How should cybersecurity students prepare for an AI-driven future?",
            "What are the latest trends in AI-powered security tools?",
            "How is AI changing incident response procedures?",
            "What skills are most important for AI-augmented cybersecurity work?",
            "How are organizations adapting their security teams for AI integration?",
            "What are the ethical considerations of AI in cybersecurity?"
        ]
        
        # Add category-specific suggestions based on available data
        categories = stats.get('categories', {})
        if categories.get('replace', 0) > 0:
            suggestions.append("Show me specific examples of AI replacing cybersecurity tasks")
        if categories.get('augment', 0) > 0:
            suggestions.append("How is AI enhancing human cybersecurity capabilities?")
        if categories.get('new_tasks', 0) > 0:
            suggestions.append("What new cybersecurity jobs are emerging due to AI?")
        if categories.get('human_only', 0) > 0:
            suggestions.append("What cybersecurity work will always require human expertise?")
        
        return suggestions[:12]  # Return top 12 suggestions 