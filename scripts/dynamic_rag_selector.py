#!/usr/bin/env python3
"""
Dynamic RAG Document Selector

Efficiently switches between different document selection modes:
- Report Mode: 200 documents per category (comprehensive analysis)
- Chat Mode: 200 best documents across all categories (optimal RAG performance)
"""

import sys
import json
import time
from pathlib import Path
from typing import List, Dict, Optional
from collections import defaultdict

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from aih.utils.database import DatabaseManager
from aih.utils.logging import get_logger
from analysis.implement_quality_ranking import DocumentQualityRanker

logger = get_logger(__name__)

class DynamicRAGSelector:
    """Manages dynamic document selection for different RAG use cases."""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.ranker = DocumentQualityRanker()
        self.cache = {
            'chat_mode': None,
            'report_mode': None,
            'last_updated': None
        }
        
        # Cache directory for pre-built indices
        self.cache_dir = Path("data/rag_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def get_chat_mode_documents(self, force_refresh: bool = False) -> List[Dict]:
        """
        Get optimal 200 documents for chat/RAG interface.
        Balanced across categories for best general performance.
        """
        if not force_refresh and self.cache['chat_mode']:
            logger.info("Using cached chat mode documents")
            return self.cache['chat_mode']
        
        logger.info("Selecting optimal 200 documents for chat mode...")
        start_time = time.time()
        
        # Get top 200 with category balancing (40 per category)
        optimal_docs = self.ranker.select_optimal_documents(
            target_count=200, 
            ensure_category_balance=True
        )
        
        self.cache['chat_mode'] = optimal_docs
        self.cache['last_updated'] = time.time()
        
        duration = time.time() - start_time
        logger.info(f"Chat mode selection completed in {duration:.1f} seconds")
        
        return optimal_docs
    
    def get_report_mode_documents(self, force_refresh: bool = False) -> Dict[str, List[Dict]]:
        """
        Get ~200 documents per category for comprehensive report generation.
        Returns dict with category as key, document list as value.
        """
        if not force_refresh and self.cache['report_mode']:
            logger.info("Using cached report mode documents")
            return self.cache['report_mode']
        
        logger.info("Selecting documents for report mode (200 per category)...")
        start_time = time.time()
        
        # Get all ranked documents
        ranked_docs = self.ranker.rank_all_documents()
        
        # Group by category
        category_docs = defaultdict(list)
        for doc, score, detailed_scores in ranked_docs:
            metadata = json.loads(doc.get('raw_metadata', '{}'))
            category = metadata.get('ai_impact_category', 'general')
            category_docs[category].append((doc, score))
        
        # Select top documents per category
        report_documents = {}
        target_per_category = 200
        
        for category, docs_with_scores in category_docs.items():
            # Sort by score and take top N
            sorted_docs = sorted(docs_with_scores, key=lambda x: x[1], reverse=True)
            selected_docs = [doc for doc, score in sorted_docs[:target_per_category]]
            report_documents[category] = selected_docs
            
            logger.info(f"Selected {len(selected_docs)} documents for {category} category")
        
        self.cache['report_mode'] = report_documents
        self.cache['last_updated'] = time.time()
        
        duration = time.time() - start_time
        logger.info(f"Report mode selection completed in {duration:.1f} seconds")
        
        return report_documents
    
    def get_category_documents(self, category: str, limit: int = 200) -> List[Dict]:
        """Get top documents for a specific category."""
        report_docs = self.get_report_mode_documents()
        return report_docs.get(category, [])[:limit]
    
    def estimate_rag_rebuild_time(self, document_count: int) -> Dict[str, float]:
        """Estimate time required to rebuild RAG index for given document count."""
        
        # Base estimates (in seconds)
        base_estimates = {
            'embedding_generation': document_count * 1.5,  # ~1.5 seconds per doc
            'vector_indexing': max(30, document_count * 0.3),  # Min 30s, +0.3s per doc
            'metadata_processing': max(10, document_count * 0.1),  # Min 10s, +0.1s per doc
            'cache_operations': 15  # Fixed overhead
        }
        
        total_time = sum(base_estimates.values())
        
        return {
            **base_estimates,
            'total_estimated_seconds': total_time,
            'total_estimated_minutes': total_time / 60,
            'document_count': document_count
        }
    
    def should_refresh_cache(self, max_age_hours: int = 24) -> bool:
        """Check if cache should be refreshed based on age."""
        if not self.cache['last_updated']:
            return True
        
        age_hours = (time.time() - self.cache['last_updated']) / 3600
        return age_hours > max_age_hours
    
    def clear_cache(self):
        """Clear all cached document selections."""
        self.cache = {
            'chat_mode': None,
            'report_mode': None,
            'last_updated': None
        }
        logger.info("Document selection cache cleared")
    
    def get_mode_statistics(self) -> Dict:
        """Get statistics about different document selection modes."""
        chat_docs = self.get_chat_mode_documents()
        report_docs = self.get_report_mode_documents()
        
        # Chat mode stats
        chat_categories = defaultdict(int)
        for doc in chat_docs:
            metadata = json.loads(doc.get('raw_metadata', '{}'))
            category = metadata.get('ai_impact_category', 'general')
            chat_categories[category] += 1
        
        # Report mode stats
        report_totals = {cat: len(docs) for cat, docs in report_docs.items()}
        
        # Overlap analysis
        chat_ids = {doc['id'] for doc in chat_docs}
        report_ids = set()
        for docs in report_docs.values():
            report_ids.update(doc['id'] for doc in docs)
        
        overlap_count = len(chat_ids & report_ids)
        
        return {
            'chat_mode': {
                'total_documents': len(chat_docs),
                'category_distribution': dict(chat_categories),
                'estimated_rag_time': self.estimate_rag_rebuild_time(len(chat_docs))
            },
            'report_mode': {
                'total_documents': sum(report_totals.values()),
                'documents_per_category': report_totals,
                'estimated_rag_time': self.estimate_rag_rebuild_time(sum(report_totals.values()))
            },
            'overlap': {
                'shared_documents': overlap_count,
                'chat_unique': len(chat_ids) - overlap_count,
                'report_unique': len(report_ids) - overlap_count
            }
        }
    
    def save_document_selection(self, mode: str, filename: Optional[str] = None):
        """Save document selection to file for external RAG systems."""
        if mode == 'chat':
            docs = self.get_chat_mode_documents()
            default_filename = f"chat_mode_documents_{int(time.time())}.json"
        elif mode == 'report':
            docs = self.get_report_mode_documents()
            default_filename = f"report_mode_documents_{int(time.time())}.json"
        else:
            raise ValueError("Mode must be 'chat' or 'report'")
        
        filename = filename or default_filename
        filepath = self.cache_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(docs, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Saved {mode} mode documents to {filepath}")
        return filepath

def main():
    """Interactive tool for testing document selection modes."""
    print("🎯 Dynamic RAG Document Selector")
    print("=" * 40)
    
    selector = DynamicRAGSelector()
    
    print("\nChoose operation:")
    print("1. Get chat mode documents (200 optimal)")
    print("2. Get report mode documents (200 per category)")  
    print("3. Show mode statistics and timing")
    print("4. Test specific category")
    print("5. Estimate RAG rebuild times")
    
    choice = input("\nEnter choice (1-5): ").strip()
    
    if choice == '1':
        print("\n📱 Chat Mode Document Selection")
        start_time = time.time()
        
        docs = selector.get_chat_mode_documents()
        
        duration = time.time() - start_time
        print(f"✅ Selected {len(docs)} documents in {duration:.1f} seconds")
        
        # Show category distribution
        categories = defaultdict(int)
        for doc in docs:
            metadata = json.loads(doc.get('raw_metadata', '{}'))
            category = metadata.get('ai_impact_category', 'general')
            categories[category] += 1
        
        print(f"\n📊 Category Distribution:")
        for cat, count in categories.items():
            print(f"  {cat}: {count} documents")
        
        # RAG timing estimate
        timing = selector.estimate_rag_rebuild_time(len(docs))
        print(f"\n⏱️ Estimated RAG Rebuild Time: {timing['total_estimated_minutes']:.1f} minutes")
    
    elif choice == '2':
        print("\n📋 Report Mode Document Selection")
        start_time = time.time()
        
        docs_by_category = selector.get_report_mode_documents()
        
        duration = time.time() - start_time
        total_docs = sum(len(docs) for docs in docs_by_category.values())
        print(f"✅ Selected {total_docs} documents in {duration:.1f} seconds")
        
        print(f"\n📊 Documents by Category:")
        for category, docs in docs_by_category.items():
            print(f"  {category}: {len(docs)} documents")
        
        # RAG timing estimate
        timing = selector.estimate_rag_rebuild_time(total_docs)
        print(f"\n⏱️ Estimated RAG Rebuild Time: {timing['total_estimated_minutes']:.1f} minutes")
    
    elif choice == '3':
        print("\n📊 Mode Statistics and Performance Analysis")
        stats = selector.get_mode_statistics()
        
        print(f"\n📱 Chat Mode:")
        print(f"  Total Documents: {stats['chat_mode']['total_documents']}")
        print(f"  RAG Rebuild Time: {stats['chat_mode']['estimated_rag_time']['total_estimated_minutes']:.1f} min")
        print(f"  Category Balance:")
        for cat, count in stats['chat_mode']['category_distribution'].items():
            print(f"    {cat}: {count}")
        
        print(f"\n📋 Report Mode:")
        print(f"  Total Documents: {stats['report_mode']['total_documents']}")
        print(f"  RAG Rebuild Time: {stats['report_mode']['estimated_rag_time']['total_estimated_minutes']:.1f} min")
        print(f"  Per Category:")
        for cat, count in stats['report_mode']['documents_per_category'].items():
            print(f"    {cat}: {count}")
        
        print(f"\n🔄 Overlap Analysis:")
        print(f"  Shared Documents: {stats['overlap']['shared_documents']}")
        print(f"  Chat Mode Unique: {stats['overlap']['chat_unique']}")
        print(f"  Report Mode Unique: {stats['overlap']['report_unique']}")
    
    elif choice == '4':
        categories = ['replace', 'augment', 'new_tasks', 'human_only', 'general']
        print(f"\nAvailable categories: {', '.join(categories)}")
        category = input("Enter category name: ").strip().lower()
        
        if category in categories:
            docs = selector.get_category_documents(category)
            print(f"\n✅ Found {len(docs)} documents in '{category}' category")
            
            # Show top 5
            print(f"\n🏆 Top 5 Documents:")
            for i, doc in enumerate(docs[:5], 1):
                print(f"  {i}. {doc['title'][:60]}...")
        else:
            print(f"❌ Category '{category}' not found")
    
    elif choice == '5':
        print("\n⏱️ RAG Rebuild Time Estimates")
        
        test_sizes = [50, 100, 200, 400, 800, 1000]
        
        print(f"{'Documents':<12} {'Embedding':<12} {'Indexing':<10} {'Total (min)':<12}")
        print("-" * 50)
        
        for size in test_sizes:
            timing = selector.estimate_rag_rebuild_time(size)
            embed_min = timing['embedding_generation'] / 60
            index_min = timing['vector_indexing'] / 60  
            total_min = timing['total_estimated_minutes']
            
            print(f"{size:<12} {embed_min:<12.1f} {index_min:<10.1f} {total_min:<12.1f}")

if __name__ == "__main__":
    main() 