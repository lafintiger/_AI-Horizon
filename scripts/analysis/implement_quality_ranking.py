#!/usr/bin/env python3
"""
AI-Horizon Quality Ranking and Document Selection System

Implements intelligent document ranking and selection for optimal RAG performance.
"""

import sys
import json
import math
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Tuple
from collections import defaultdict

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from aih.utils.database import DatabaseManager
from aih.utils.logging import get_logger

logger = get_logger(__name__)

class DocumentQualityRanker:
    """Ranks documents by quality and relevance for RAG optimization."""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.weights = {
            'source_credibility': 0.25,
            'content_quality': 0.25,
            'temporal_relevance': 0.20,
            'category_balance': 0.15,
            'uniqueness': 0.15
        }
        
        # Define high-credibility sources
        self.trusted_sources = {
            'nist.gov': 1.0,
            'cybersecurity-insiders.com': 0.9,
            'darkreading.com': 0.9,
            'krebsonsecurity.com': 0.95,
            'schneier.com': 0.95,
            'csoonline.com': 0.85,
            'helpnetsecurity.com': 0.8,
            'securityweek.com': 0.85,
            'threatpost.com': 0.8,
            'infosecurity-magazine.com': 0.8,
            'bleepingcomputer.com': 0.75,
            'zdnet.com': 0.7,
            'techcrunch.com': 0.65,
            'wired.com': 0.8,
            'ieee.org': 0.95,
            'acm.org': 0.95
        }
    
    def calculate_document_score(self, artifact: Dict) -> Tuple[float, Dict]:
        """Calculate comprehensive quality score for a document."""
        scores = {}
        
        # 1. Source Credibility Score (0.25 weight)
        scores['source_credibility'] = self._calculate_source_credibility(artifact)
        
        # 2. Content Quality Score (0.25 weight)
        scores['content_quality'] = self._calculate_content_quality(artifact)
        
        # 3. Temporal Relevance Score (0.20 weight)
        scores['temporal_relevance'] = self._calculate_temporal_relevance(artifact)
        
        # 4. Category Balance Score (0.15 weight)
        scores['category_balance'] = self._calculate_category_balance(artifact)
        
        # 5. Uniqueness Score (0.15 weight)
        scores['uniqueness'] = self._calculate_uniqueness(artifact)
        
        # Calculate weighted total
        total_score = sum(
            scores[metric] * self.weights[metric]
            for metric in scores
        )
        
        return total_score, scores
    
    def _calculate_source_credibility(self, artifact: Dict) -> float:
        """Calculate source credibility score (0-1)."""
        url = artifact.get('url', '')
        source_type = artifact.get('source_type', '')
        
        # Manual entries get higher base credibility
        if source_type.startswith('manual_'):
            base_score = 0.8
        else:
            base_score = 0.6
        
        # Check against trusted sources
        for domain, credibility in self.trusted_sources.items():
            if domain in url.lower():
                return min(1.0, base_score + (credibility * 0.4))
        
        # Academic/government domains get bonus
        if any(tld in url.lower() for tld in ['.edu', '.gov', '.org']):
            base_score += 0.2
        
        return min(1.0, base_score)
    
    def _calculate_content_quality(self, artifact: Dict) -> float:
        """Calculate content quality score based on content analysis."""
        content = artifact.get('content', '')
        title = artifact.get('title', '')
        
        if not content:
            return 0.1
        
        score = 0.5  # Base score
        
        # Length appropriateness (not too short, not too long)
        content_length = len(content.split())
        if 300 <= content_length <= 3000:
            score += 0.3
        elif 100 <= content_length < 300 or 3000 < content_length <= 5000:
            score += 0.2
        elif content_length > 5000:
            score += 0.1
        
        # Technical depth indicators
        technical_terms = [
            'cybersecurity', 'artificial intelligence', 'machine learning',
            'vulnerability', 'threat', 'security', 'authentication',
            'encryption', 'malware', 'phishing', 'ransomware',
            'incident response', 'risk assessment', 'compliance',
            'penetration testing', 'soc', 'siem', 'automation'
        ]
        
        tech_term_count = sum(1 for term in technical_terms if term.lower() in content.lower())
        tech_score = min(0.2, tech_term_count * 0.02)
        score += tech_score
        
        # Title quality
        if len(title.split()) >= 5 and not title.lower().startswith('untitled'):
            score += 0.1
        
        return min(1.0, score)
    
    def _calculate_temporal_relevance(self, artifact: Dict) -> float:
        """Calculate temporal relevance score (newer = higher)."""
        collected_at = artifact.get('collected_at')
        if not collected_at:
            return 0.5
        
        try:
            if isinstance(collected_at, str):
                collected_date = datetime.fromisoformat(collected_at.replace('Z', '+00:00'))
            else:
                collected_date = collected_at
            
            now = datetime.now()
            age_days = (now - collected_date.replace(tzinfo=None)).days
            
            # Score based on age
            if age_days <= 30:
                return 1.0
            elif age_days <= 90:
                return 0.9
            elif age_days <= 180:
                return 0.8
            elif age_days <= 365:
                return 0.6
            else:
                return 0.4
                
        except Exception:
            return 0.5
    
    def _calculate_category_balance(self, artifact: Dict) -> float:
        """Calculate category balance score to maintain diversity."""
        metadata = json.loads(artifact.get('raw_metadata', '{}'))
        category = metadata.get('ai_impact_category', 'general')
        
        # Get current category distribution
        all_artifacts = self.db.get_artifacts()
        category_counts = defaultdict(int)
        
        for art in all_artifacts:
            art_metadata = json.loads(art.get('raw_metadata', '{}'))
            art_category = art_metadata.get('ai_impact_category', 'general')
            category_counts[art_category] += 1
        
        total_docs = len(all_artifacts)
        if total_docs == 0:
            return 1.0
        
        # Calculate how underrepresented this category is
        category_ratio = category_counts[category] / total_docs
        target_ratio = 0.25  # Aim for 25% per category
        
        if category_ratio < target_ratio:
            # Underrepresented categories get higher scores
            return min(1.0, 1.0 - (category_ratio / target_ratio))
        else:
            # Overrepresented categories get lower scores
            return max(0.3, target_ratio / category_ratio)
    
    def _calculate_uniqueness(self, artifact: Dict) -> float:
        """Calculate uniqueness score based on content similarity."""
        # Simplified uniqueness based on title/URL uniqueness
        # In a full implementation, this would use embedding similarity
        
        title = artifact.get('title', '').lower()
        url = artifact.get('url', '')
        
        all_artifacts = self.db.get_artifacts()
        
        # Check for similar titles or duplicate URLs
        similar_count = 0
        for other in all_artifacts:
            if other['id'] == artifact['id']:
                continue
                
            other_title = other.get('title', '').lower()
            other_url = other.get('url', '')
            
            # Check URL duplication
            if url and url == other_url:
                return 0.1  # Duplicate URL
            
            # Check title similarity (simple word overlap)
            title_words = set(title.split())
            other_words = set(other_title.split())
            
            if len(title_words) > 3 and len(other_words) > 3:
                overlap = len(title_words & other_words)
                similarity = overlap / min(len(title_words), len(other_words))
                
                if similarity > 0.7:
                    similar_count += 1
        
        # Score based on uniqueness
        if similar_count == 0:
            return 1.0
        elif similar_count <= 2:
            return 0.7
        else:
            return 0.4
    
    def rank_all_documents(self) -> List[Tuple[Dict, float, Dict]]:
        """Rank all documents by quality score."""
        artifacts = self.db.get_artifacts()
        ranked_docs = []
        
        logger.info(f"Ranking {len(artifacts)} documents for quality...")
        
        for artifact in artifacts:
            total_score, detailed_scores = self.calculate_document_score(artifact)
            ranked_docs.append((artifact, total_score, detailed_scores))
        
        # Sort by score (highest first)
        ranked_docs.sort(key=lambda x: x[1], reverse=True)
        
        return ranked_docs
    
    def select_optimal_documents(self, target_count: int = 200, 
                               ensure_category_balance: bool = True) -> List[Dict]:
        """Select optimal subset of documents for RAG."""
        ranked_docs = self.rank_all_documents()
        
        if len(ranked_docs) <= target_count:
            return [doc[0] for doc in ranked_docs]
        
        selected_docs = []
        category_counts = defaultdict(int)
        category_targets = defaultdict(int)
        
        if ensure_category_balance:
            # Calculate category targets
            categories = ['replace', 'augment', 'new_tasks', 'human_only', 'general']
            docs_per_category = target_count // len(categories)
            remainder = target_count % len(categories)
            
            for i, category in enumerate(categories):
                category_targets[category] = docs_per_category + (1 if i < remainder else 0)
        
        # Select documents with category balancing
        for doc, score, detailed_scores in ranked_docs:
            if len(selected_docs) >= target_count:
                break
            
            metadata = json.loads(doc.get('raw_metadata', '{}'))
            category = metadata.get('ai_impact_category', 'general')
            
            if ensure_category_balance:
                if category_counts[category] < category_targets[category]:
                    selected_docs.append(doc)
                    category_counts[category] += 1
                elif len(selected_docs) < target_count and all(
                    category_counts[cat] >= category_targets[cat] for cat in categories
                ):
                    # All categories met targets, add remaining by score
                    selected_docs.append(doc)
            else:
                selected_docs.append(doc)
        
        logger.info(f"Selected {len(selected_docs)} optimal documents")
        if ensure_category_balance:
            for category, count in category_counts.items():
                logger.info(f"  {category}: {count} documents")
        
        return selected_docs
    
    def create_quality_report(self) -> Dict:
        """Generate comprehensive quality analysis report."""
        ranked_docs = self.rank_all_documents()
        
        # Calculate statistics
        scores = [doc[1] for doc in ranked_docs]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        # Category analysis
        category_analysis = defaultdict(list)
        source_analysis = defaultdict(list)
        
        for doc, score, detailed in ranked_docs:
            metadata = json.loads(doc.get('raw_metadata', '{}'))
            category = metadata.get('ai_impact_category', 'general')
            category_analysis[category].append(score)
            
            url = doc.get('url', '')
            for domain in self.trusted_sources:
                if domain in url:
                    source_analysis[domain].append(score)
                    break
            else:
                source_analysis['other'].append(score)
        
        # Quality recommendations
        recommendations = []
        
        if avg_score < 0.6:
            recommendations.append("Overall document quality is below optimal. Consider stricter curation.")
        
        low_quality_count = sum(1 for score in scores if score < 0.4)
        if low_quality_count > len(scores) * 0.2:
            recommendations.append(f"Remove {low_quality_count} lowest quality documents")
        
        category_imbalance = max(len(scores) for scores in category_analysis.values()) - \
                           min(len(scores) for scores in category_analysis.values() if scores)
        
        if category_imbalance > len(ranked_docs) * 0.3:
            recommendations.append("Significant category imbalance detected. Focus collection on underrepresented categories.")
        
        return {
            'total_documents': len(ranked_docs),
            'average_quality_score': avg_score,
            'score_distribution': {
                'excellent (0.8+)': sum(1 for s in scores if s >= 0.8),
                'good (0.6-0.8)': sum(1 for s in scores if 0.6 <= s < 0.8),
                'fair (0.4-0.6)': sum(1 for s in scores if 0.4 <= s < 0.6),
                'poor (<0.4)': sum(1 for s in scores if s < 0.4),
            },
            'category_analysis': {
                cat: {
                    'count': len(scores),
                    'avg_score': sum(scores) / len(scores) if scores else 0
                }
                for cat, scores in category_analysis.items()
            },
            'top_10_documents': [
                {
                    'title': doc[0]['title'][:60],
                    'score': doc[1],
                    'category': json.loads(doc[0].get('raw_metadata', '{}')).get('ai_impact_category', 'general')
                }
                for doc in ranked_docs[:10]
            ],
            'recommendations': recommendations,
            'quality_weights': self.weights
        }

def main():
    """Run quality ranking analysis."""
    print("📊 AI-Horizon Document Quality Ranking System")
    print("=" * 50)
    
    ranker = DocumentQualityRanker()
    
    print("Choose operation:")
    print("1. Generate quality report")
    print("2. Select optimal 200 documents")
    print("3. Rank all documents")
    print("4. Custom selection")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == '1':
        print("\n🔍 Generating quality analysis report...")
        report = ranker.create_quality_report()
        
        print(f"\n📈 Quality Report")
        print(f"Total Documents: {report['total_documents']}")
        print(f"Average Quality Score: {report['average_quality_score']:.3f}")
        
        print(f"\n📊 Score Distribution:")
        for level, count in report['score_distribution'].items():
            print(f"  {level}: {count}")
        
        print(f"\n🏷️ Category Analysis:")
        for category, data in report['category_analysis'].items():
            print(f"  {category}: {data['count']} docs, avg score: {data['avg_score']:.3f}")
        
        print(f"\n🏆 Top 10 Documents:")
        for i, doc in enumerate(report['top_10_documents'], 1):
            print(f"  {i}. {doc['title']} (Score: {doc['score']:.3f}, {doc['category']})")
        
        print(f"\n💡 Recommendations:")
        for rec in report['recommendations']:
            print(f"  • {rec}")
    
    elif choice == '2':
        print("\n🎯 Selecting optimal 200 documents...")
        optimal_docs = ranker.select_optimal_documents(200, ensure_category_balance=True)
        
        print(f"✅ Selected {len(optimal_docs)} optimal documents")
        
        # Show category distribution
        category_counts = defaultdict(int)
        for doc in optimal_docs:
            metadata = json.loads(doc.get('raw_metadata', '{}'))
            category = metadata.get('ai_impact_category', 'general')
            category_counts[category] += 1
        
        print(f"\n📋 Selection by Category:")
        for category, count in category_counts.items():
            print(f"  {category}: {count} documents")
    
    elif choice == '3':
        print("\n📈 Ranking all documents...")
        ranked_docs = ranker.rank_all_documents()
        
        print(f"\n🏆 Top 20 Ranked Documents:")
        for i, (doc, score, detailed) in enumerate(ranked_docs[:20], 1):
            category = json.loads(doc.get('raw_metadata', '{}')).get('ai_impact_category', 'general')
            print(f"{i:2d}. {doc['title'][:50]:<50} | Score: {score:.3f} | {category}")
    
    elif choice == '4':
        target_count = int(input("Enter target document count: "))
        balance_categories = input("Ensure category balance? (y/n): ").lower() == 'y'
        
        print(f"\n🎯 Selecting optimal {target_count} documents...")
        optimal_docs = ranker.select_optimal_documents(target_count, balance_categories)
        
        print(f"✅ Selected {len(optimal_docs)} documents")

if __name__ == "__main__":
    main() 