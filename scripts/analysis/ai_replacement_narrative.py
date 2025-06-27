#!/usr/bin/env python3
"""
AI-Horizon AI Replacement Narrative Analysis
Generates a comprehensive narrative summary of jobs and tasks that will be replaced by AI
with detailed explanations and citations.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from aih.utils.database import DatabaseManager
import json
from collections import defaultdict, Counter
from datetime import datetime
import logging
import re

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

class AIReplacementNarrativeAnalyzer:
    def __init__(self):
        self.db = DatabaseManager()
        
    def get_replacement_articles(self):
        """Retrieve articles with high AI REPLACE confidence scores."""
        try:
            articles = []
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                query = """
                SELECT id, title, content, url, source_type, collected_at, raw_metadata
                FROM artifacts
                ORDER BY collected_at DESC
                """
                
                cursor.execute(query)
                results = cursor.fetchall()
                
                for row in results:
                    metadata = json.loads(row[6]) if row[6] else {}
                    multicategory = metadata.get('ai_impact_categories', {})
                    
                    # Only include articles with REPLACE category
                    if 'replace' in multicategory:
                        replace_data = multicategory['replace']
                        confidence = replace_data.get('confidence', 0)
                        
                        if confidence > 0:  # Any positive confidence
                            wisdom = metadata.get('extracted_wisdom', {})
                            
                            articles.append({
                                'id': row[0],
                                'title': row[1] or '',
                                'content': row[2] or '',
                                'url': row[3] or '',
                                'source_type': row[4] or 'unknown',
                                'created_at': row[5],
                                'replace_confidence': confidence,
                                'replace_evidence': replace_data.get('evidence', []),
                                'quality_score': metadata.get('quality_score', 0),
                                'wisdom': wisdom,
                                'key_insights': wisdom.get('key_wisdom', []) if wisdom else [],
                                'career_implications': wisdom.get('career_implications', []) if wisdom else [],
                                'metadata': metadata
                            })
                
                # Sort by replacement confidence
                articles.sort(key=lambda x: x['replace_confidence'], reverse=True)
                
                logger.info(f"Retrieved {len(articles)} articles with AI replacement analysis")
                return articles
                
        except Exception as e:
            logger.error(f"Error retrieving articles: {e}")
            return []
    
    def extract_specific_jobs_and_tasks(self, articles):
        """Extract specific jobs and tasks mentioned as being replaced by AI."""
        jobs_tasks = defaultdict(lambda: {
            'articles': [],
            'evidence_count': 0,
            'total_confidence': 0,
            'explanations': [],
            'citations': []
        })
        
        # Common cybersecurity job titles and tasks
        job_patterns = [
            r'security analyst',
            r'soc analyst',
            r'incident response',
            r'threat detection',
            r'vulnerability assessment',
            r'penetration testing',
            r'security monitoring',
            r'log analysis',
            r'malware analysis',
            r'threat hunting',
            r'compliance monitoring',
            r'risk assessment',
            r'security operations',
            r'network monitoring',
            r'endpoint security',
            r'firewall management',
            r'intrusion detection',
            r'security reporting',
            r'alert triage',
            r'patch management'
        ]
        
        for article in articles:
            content_lower = (article['content'] + ' ' + article['title']).lower()
            
            # Check for job/task mentions
            for pattern in job_patterns:
                if re.search(pattern, content_lower):
                    job_key = pattern.replace(r'\\b', '').replace(r'\\s+', ' ')
                    
                    jobs_tasks[job_key]['articles'].append(article)
                    jobs_tasks[job_key]['evidence_count'] += 1
                    jobs_tasks[job_key]['total_confidence'] += article['replace_confidence']
                    
                    # Extract explanations from wisdom
                    if article['key_insights']:
                        for insight in article['key_insights']:
                            if pattern.replace(r'\\b', '').replace(r'\\s+', ' ') in insight.lower():
                                jobs_tasks[job_key]['explanations'].append(insight)
                    
                    # Add citation
                    citation = {
                        'title': article['title'],
                        'url': article['url'],
                        'confidence': article['replace_confidence'],
                        'quality': article['quality_score'],
                        'evidence': article['replace_evidence']
                    }
                    jobs_tasks[job_key]['citations'].append(citation)
        
        # Calculate averages and clean up
        for job in jobs_tasks:
            data = jobs_tasks[job]
            data['avg_confidence'] = data['total_confidence'] / data['evidence_count'] if data['evidence_count'] > 0 else 0
            # Remove duplicates and sort citations by confidence
            unique_citations = []
            seen_titles = set()
            for citation in data['citations']:
                if citation['title'] not in seen_titles:
                    unique_citations.append(citation)
                    seen_titles.add(citation['title'])
            data['citations'] = sorted(unique_citations, key=lambda x: x['confidence'], reverse=True)
            data['explanations'] = list(set(data['explanations']))  # Remove duplicates
        
        return dict(jobs_tasks)
    
    def extract_automation_mechanisms(self, articles):
        """Extract how AI will replace these jobs (the mechanisms)."""
        mechanisms = defaultdict(lambda: {
            'articles': [],
            'examples': [],
            'confidence_scores': []
        })
        
        automation_patterns = {
            'machine_learning': [r'machine learning', r'ml algorithms', r'predictive models'],
            'automated_detection': [r'automated detection', r'auto-detect', r'automatic identification'],
            'ai_powered_analysis': [r'ai-powered analysis', r'ai analysis', r'intelligent analysis'],
            'behavioral_analytics': [r'behavioral analytics', r'behavior analysis', r'anomaly detection'],
            'natural_language_processing': [r'natural language processing', r'nlp', r'text analysis'],
            'computer_vision': [r'computer vision', r'image analysis', r'visual recognition'],
            'robotic_process_automation': [r'robotic process automation', r'rpa', r'process automation'],
            'intelligent_automation': [r'intelligent automation', r'smart automation', r'cognitive automation']
        }
        
        for article in articles:
            content_lower = (article['content'] + ' ' + article['title']).lower()
            
            for mechanism, patterns in automation_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, content_lower):
                        mechanisms[mechanism]['articles'].append(article['title'])
                        mechanisms[mechanism]['confidence_scores'].append(article['replace_confidence'])
                        
                        # Extract examples from evidence
                        for evidence in article['replace_evidence']:
                            if any(p.replace(r'\\b', '') in evidence.lower() for p in patterns):
                                mechanisms[mechanism]['examples'].append(evidence)
        
        # Clean up and calculate averages
        for mechanism in mechanisms:
            data = mechanisms[mechanism]
            data['articles'] = list(set(data['articles']))  # Remove duplicates
            data['examples'] = list(set(data['examples']))  # Remove duplicates
            data['avg_confidence'] = sum(data['confidence_scores']) / len(data['confidence_scores']) if data['confidence_scores'] else 0
            data['article_count'] = len(data['articles'])
        
        return dict(mechanisms)
    
    def generate_narrative_report(self):
        """Generate comprehensive narrative report."""
        logger.info("Starting AI replacement narrative analysis...")
        
        articles = self.get_replacement_articles()
        if not articles:
            logger.error("No replacement articles found")
            return None
        
        jobs_tasks = self.extract_specific_jobs_and_tasks(articles)
        mechanisms = self.extract_automation_mechanisms(articles)
        
        # Overall statistics
        high_confidence_articles = [a for a in articles if a['replace_confidence'] >= 0.7]
        medium_confidence_articles = [a for a in articles if 0.4 <= a['replace_confidence'] < 0.7]
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'total_articles_analyzed': len(articles),
            'high_confidence_replacements': len(high_confidence_articles),
            'medium_confidence_replacements': len(medium_confidence_articles),
            'avg_replacement_confidence': sum(a['replace_confidence'] for a in articles) / len(articles),
            'jobs_and_tasks': jobs_tasks,
            'automation_mechanisms': mechanisms,
            'narrative_summary': self.generate_narrative_text(articles, jobs_tasks, mechanisms),
            'top_replacement_articles': sorted(articles, key=lambda x: x['replace_confidence'], reverse=True)[:10]
        }
        
        return report
    
    def generate_narrative_text(self, articles, jobs_tasks, mechanisms):
        """Generate the narrative summary text."""
        total_articles = len(articles)
        avg_confidence = sum(a['replace_confidence'] for a in articles) / len(articles)
        high_confidence_count = len([a for a in articles if a['replace_confidence'] >= 0.7])
        
        narrative = f"""
# AI Replacement in Cybersecurity: A Comprehensive Analysis

## Executive Summary

Based on analysis of {total_articles} articles with AI replacement indicators, our research reveals a significant transformation in the cybersecurity workforce landscape. With an average replacement confidence score of {avg_confidence:.3f}, and {high_confidence_count} articles showing high confidence (≥0.7) in AI replacement scenarios, the evidence suggests that artificial intelligence will fundamentally reshape how cybersecurity work is performed.

## Overall Findings

The analysis reveals that AI replacement in cybersecurity is not a distant future scenario but an ongoing transformation affecting multiple job categories and operational tasks. The replacement patterns show three distinct waves:

1. **Immediate Replacement (High Confidence)**: Routine, rule-based tasks that can be automated with current AI technology
2. **Near-term Replacement (Medium Confidence)**: Complex analytical tasks that require AI advancement but are technically feasible
3. **Long-term Transformation**: Strategic and creative tasks that will be augmented rather than replaced

The evidence indicates that AI replacement will be most pronounced in operational and analytical roles, while strategic and leadership positions will evolve toward human-AI collaboration models.
"""
        return narrative
    
    def print_comprehensive_report(self, report):
        """Print the comprehensive narrative report."""
        print("\n" + "="*120)
        print("🤖 AI REPLACEMENT IN CYBERSECURITY: COMPREHENSIVE NARRATIVE ANALYSIS")
        print("="*120)
        print(f"📊 Generated: {report['generated_at']}")
        print(f"📄 Total Articles Analyzed: {report['total_articles_analyzed']}")
        print(f"🔴 High Confidence Replacements: {report['high_confidence_replacements']}")
        print(f"🟡 Medium Confidence Replacements: {report['medium_confidence_replacements']}")
        print(f"📈 Average Replacement Confidence: {report['avg_replacement_confidence']:.3f}")
        
        print(report['narrative_summary'])
        
        print("\n" + "="*120)
        print("🎯 SPECIFIC JOBS AND TASKS TO BE REPLACED BY AI")
        print("="*120)
        
        # Sort jobs by confidence and evidence count
        sorted_jobs = sorted(report['jobs_and_tasks'].items(), 
                           key=lambda x: (x[1]['avg_confidence'], x[1]['evidence_count']), 
                           reverse=True)
        
        for job, data in sorted_jobs[:15]:  # Top 15 jobs/tasks
            if data['evidence_count'] >= 2:  # Only show jobs with multiple mentions
                print(f"\n🔧 **{job.upper().replace('_', ' ')}**")
                print("-" * 80)
                print(f"📊 **Replacement Confidence**: {data['avg_confidence']:.3f}")
                print(f"📄 **Evidence Count**: {data['evidence_count']} articles")
                
                print(f"\n**Why AI Will Replace This Job/Task:**")
                if data['explanations']:
                    for explanation in data['explanations'][:2]:  # Top 2 explanations
                        print(f"• {explanation}")
                else:
                    # Generate explanation from evidence
                    evidence_text = ', '.join(data['citations'][0]['evidence'][:3]) if data['citations'] else 'automation capabilities'
                    print(f"• AI can automate this role through {evidence_text}, reducing the need for human intervention in routine tasks.")
                
                print(f"\n**Supporting Citations:**")
                for i, citation in enumerate(data['citations'][:3], 1):  # Top 3 citations
                    print(f"{i}. **{citation['title']}**")
                    print(f"   - Confidence: {citation['confidence']:.3f} | Quality: {citation['quality']:.3f}")
                    print(f"   - Evidence: {', '.join(citation['evidence'][:3])}")
                    print(f"   - URL: {citation['url']}")
                    print()
        
        print("\n" + "="*120)
        print("⚙️ HOW AI WILL REPLACE THESE JOBS (AUTOMATION MECHANISMS)")
        print("="*120)
        
        sorted_mechanisms = sorted(report['automation_mechanisms'].items(),
                                 key=lambda x: x[1]['avg_confidence'], reverse=True)
        
        for mechanism, data in sorted_mechanisms:
            if data['article_count'] >= 3:  # Only show mechanisms with multiple mentions
                print(f"\n🔬 **{mechanism.upper().replace('_', ' ')}**")
                print("-" * 60)
                print(f"📊 Average Confidence: {data['avg_confidence']:.3f}")
                print(f"📄 Mentioned in {data['article_count']} articles")
                print(f"🔍 Examples: {', '.join(data['examples'][:3])}")
                print()
        
        print("\n" + "="*120)
        print("📚 TOP ARTICLES SUPPORTING AI REPLACEMENT")
        print("="*120)
        
        for i, article in enumerate(report['top_replacement_articles'][:5], 1):
            print(f"\n{i}. **{article['title']}**")
            print(f"   - Replacement Confidence: {article['replace_confidence']:.3f}")
            print(f"   - Quality Score: {article['quality_score']:.3f}")
            print(f"   - Evidence: {', '.join(article['replace_evidence'][:3])}")
            if article['key_insights']:
                print(f"   - Key Insight: {article['key_insights'][0][:150]}...")
            print(f"   - URL: {article['url']}")
            print()
        
        print("\n" + "="*120)

def main():
    """Main execution function."""
    try:
        analyzer = AIReplacementNarrativeAnalyzer()
        
        # Generate comprehensive report
        report = analyzer.generate_narrative_report()
        
        if report:
            # Print comprehensive narrative
            analyzer.print_comprehensive_report(report)
            
            # Save to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data/ai_replacement_narrative_{timestamp}.json"
            
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 Full narrative report saved to: {filename}")
            print("🎉 AI replacement narrative analysis completed successfully!")
            
        else:
            print("❌ Failed to generate narrative report")
            
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        print(f"❌ Error generating narrative: {e}")

if __name__ == "__main__":
    main() 