#!/usr/bin/env python3
"""
AI-Horizon Comprehensive Category Narratives
Generates detailed narrative summaries for all AI impact categories:
- AI REPLACE: Jobs/tasks that will be replaced by AI
- AI AUGMENT: Human-AI collaboration scenarios
- AI NEW TASKS: New jobs created by AI technology
- AI HUMAN-ONLY: Tasks requiring uniquely human expertise
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

class ComprehensiveCategoryNarrativeAnalyzer:
    def __init__(self):
        self.db = DatabaseManager()
        
        # Category definitions and patterns
        self.categories = {
            'replace': {
                'title': 'AI REPLACE - Tasks Completely Automated by AI',
                'description': 'Jobs and tasks that will be fully automated and replaced by artificial intelligence',
                'job_patterns': [
                    r'log analysis', r'alert triage', r'vulnerability assessment', r'patch management',
                    r'security monitoring', r'network monitoring', r'endpoint security', r'malware analysis',
                    r'compliance monitoring', r'security reporting', r'firewall management', r'intrusion detection'
                ],
                'mechanism_patterns': {
                    'automated_detection': [r'automated detection', r'auto-detect', r'automatic identification'],
                    'machine_learning': [r'machine learning', r'ml algorithms', r'predictive models'],
                    'robotic_process_automation': [r'robotic process automation', r'rpa', r'process automation'],
                    'behavioral_analytics': [r'behavioral analytics', r'behavior analysis', r'anomaly detection']
                }
            },
            'augment': {
                'title': 'AI AUGMENT - Human-AI Collaboration',
                'description': 'Roles where AI enhances human capabilities rather than replacing them',
                'job_patterns': [
                    r'threat hunting', r'incident response', r'security analyst', r'penetration testing',
                    r'forensic analysis', r'security architecture', r'risk assessment', r'security consulting',
                    r'threat intelligence', r'security research', r'vulnerability research', r'red team'
                ],
                'mechanism_patterns': {
                    'ai_assisted_analysis': [r'ai-assisted', r'ai-powered analysis', r'intelligent analysis'],
                    'decision_support': [r'decision support', r'recommendation engine', r'advisory system'],
                    'enhanced_detection': [r'enhanced detection', r'improved accuracy', r'augmented capabilities'],
                    'collaborative_intelligence': [r'human-ai collaboration', r'collaborative intelligence', r'hybrid approach']
                }
            },
            'new_tasks': {
                'title': 'AI NEW TASKS - Jobs Created by AI Technology',
                'description': 'New roles and responsibilities that emerge due to AI adoption in cybersecurity',
                'job_patterns': [
                    r'ai security engineer', r'ml security specialist', r'ai governance', r'ai ethics officer',
                    r'prompt engineer', r'ai trainer', r'ai auditor', r'ai risk manager',
                    r'ai compliance officer', r'ai security architect', r'ai operations', r'mlsecops'
                ],
                'mechanism_patterns': {
                    'ai_governance': [r'ai governance', r'ai oversight', r'ai compliance'],
                    'model_security': [r'model security', r'ai model protection', r'ml security'],
                    'ai_ethics': [r'ai ethics', r'responsible ai', r'ai fairness'],
                    'ai_operations': [r'ai operations', r'mlops', r'ai deployment']
                }
            },
            'human_only': {
                'title': 'AI HUMAN-ONLY - Uniquely Human Expertise',
                'description': 'Tasks that require human judgment, creativity, and interpersonal skills that AI cannot replicate',
                'job_patterns': [
                    r'security leadership', r'ciso', r'security management', r'crisis management',
                    r'stakeholder communication', r'security strategy', r'business alignment', r'team leadership',
                    r'vendor management', r'board reporting', r'regulatory liaison', r'executive briefing'
                ],
                'mechanism_patterns': {
                    'human_judgment': [r'human judgment', r'critical thinking', r'strategic decision'],
                    'interpersonal_skills': [r'communication', r'leadership', r'negotiation'],
                    'creative_problem_solving': [r'creative solutions', r'innovative approaches', r'strategic thinking'],
                    'ethical_oversight': [r'ethical oversight', r'moral judgment', r'value-based decisions']
                }
            }
        }
    
    def get_category_articles(self, category):
        """Retrieve articles for a specific category with confidence scores."""
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
                    
                    # Only include articles with the specified category
                    if category in multicategory:
                        category_data = multicategory[category]
                        confidence = category_data.get('confidence', 0)
                        
                        if confidence > 0:  # Any positive confidence
                            wisdom = metadata.get('extracted_wisdom', {})
                            
                            articles.append({
                                'id': row[0],
                                'title': row[1] or '',
                                'content': row[2] or '',
                                'url': row[3] or '',
                                'source_type': row[4] or 'unknown',
                                'created_at': row[5],
                                'confidence': confidence,
                                'evidence': category_data.get('evidence', []),
                                'quality_score': metadata.get('quality_score', 0),
                                'wisdom': wisdom,
                                'key_insights': wisdom.get('key_wisdom', []) if wisdom else [],
                                'career_implications': wisdom.get('career_implications', []) if wisdom else [],
                                'metadata': metadata
                            })
                
                # Sort by confidence
                articles.sort(key=lambda x: x['confidence'], reverse=True)
                
                logger.info(f"Retrieved {len(articles)} articles for {category} category")
                return articles
                
        except Exception as e:
            logger.error(f"Error retrieving {category} articles: {e}")
            return []
    
    def extract_jobs_and_tasks(self, articles, category):
        """Extract specific jobs and tasks for a category."""
        jobs_tasks = defaultdict(lambda: {
            'articles': [],
            'evidence_count': 0,
            'total_confidence': 0,
            'explanations': [],
            'citations': []
        })
        
        job_patterns = self.categories[category]['job_patterns']
        
        for article in articles:
            content_lower = (article['content'] + ' ' + article['title']).lower()
            
            # Check for job/task mentions
            for pattern in job_patterns:
                if re.search(pattern, content_lower):
                    job_key = pattern.replace(r'\\b', '').replace(r'\\s+', ' ')
                    
                    jobs_tasks[job_key]['articles'].append(article)
                    jobs_tasks[job_key]['evidence_count'] += 1
                    jobs_tasks[job_key]['total_confidence'] += article['confidence']
                    
                    # Extract explanations from wisdom
                    if article['key_insights']:
                        for insight in article['key_insights']:
                            if pattern.replace(r'\\b', '').replace(r'\\s+', ' ') in insight.lower():
                                jobs_tasks[job_key]['explanations'].append(insight)
                    
                    # Add citation
                    citation = {
                        'title': article['title'],
                        'url': article['url'],
                        'confidence': article['confidence'],
                        'quality': article['quality_score'],
                        'evidence': article['evidence']
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
    
    def extract_mechanisms(self, articles, category):
        """Extract automation/enhancement mechanisms for a category."""
        mechanisms = defaultdict(lambda: {
            'articles': [],
            'examples': [],
            'confidence_scores': []
        })
        
        mechanism_patterns = self.categories[category]['mechanism_patterns']
        
        for article in articles:
            content_lower = (article['content'] + ' ' + article['title']).lower()
            
            for mechanism, patterns in mechanism_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, content_lower):
                        mechanisms[mechanism]['articles'].append(article['title'])
                        mechanisms[mechanism]['confidence_scores'].append(article['confidence'])
                        
                        # Extract examples from evidence
                        for evidence in article['evidence']:
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
    
    def generate_category_narrative_text(self, category, articles, jobs_tasks, mechanisms):
        """Generate narrative text for a specific category."""
        total_articles = len(articles)
        avg_confidence = sum(a['confidence'] for a in articles) / len(articles) if articles else 0
        high_confidence_count = len([a for a in articles if a['confidence'] >= 0.7])
        
        category_info = self.categories[category]
        
        if category == 'replace':
            narrative = f"""
# {category_info['title']}: Comprehensive Analysis

## Executive Summary

Based on analysis of {total_articles} articles with AI replacement indicators, our research reveals significant automation potential in cybersecurity operations. With an average confidence score of {avg_confidence:.3f}, and {high_confidence_count} articles showing high confidence (≥0.7) in replacement scenarios, the evidence suggests that AI will fundamentally automate many routine cybersecurity tasks.

## Overall Findings

AI replacement in cybersecurity targets primarily operational and repetitive tasks that can be systematized and automated. The replacement patterns show immediate impact on:

1. **Log Analysis and Monitoring**: AI can process vast amounts of data faster than humans
2. **Alert Triage and Response**: Automated prioritization and initial response capabilities
3. **Vulnerability Assessment**: Continuous automated scanning and risk evaluation
4. **Compliance Monitoring**: Rule-based compliance checking and reporting

The evidence indicates that AI replacement will be most pronounced in tasks requiring pattern recognition, data processing, and rule-based decision making.
"""
        elif category == 'augment':
            narrative = f"""
# {category_info['title']}: Comprehensive Analysis

## Executive Summary

Based on analysis of {total_articles} articles with AI augmentation indicators, our research reveals the emergence of powerful human-AI collaboration models. With an average confidence score of {avg_confidence:.3f}, and {high_confidence_count} articles showing high confidence (≥0.7) in augmentation scenarios, the evidence suggests that AI will significantly enhance human capabilities rather than replace them.

## Overall Findings

AI augmentation in cybersecurity focuses on enhancing human expertise with intelligent tools and insights. The augmentation patterns show enhancement in:

1. **Threat Hunting**: AI-powered analytics to identify sophisticated threats
2. **Incident Response**: Accelerated investigation with AI-assisted analysis
3. **Security Analysis**: Enhanced pattern recognition and anomaly detection
4. **Risk Assessment**: Data-driven insights supporting human judgment

The evidence indicates that AI augmentation will be most valuable in complex analytical tasks requiring both computational power and human expertise.
"""
        elif category == 'new_tasks':
            narrative = f"""
# {category_info['title']}: Comprehensive Analysis

## Executive Summary

Based on analysis of {total_articles} articles with AI-driven job creation indicators, our research reveals the emergence of entirely new cybersecurity roles. With an average confidence score of {avg_confidence:.3f}, and {high_confidence_count} articles showing high confidence (≥0.7) in new task creation, the evidence suggests that AI adoption will create specialized positions requiring hybrid skills.

## Overall Findings

AI technology adoption in cybersecurity is creating new specialized roles that didn't exist before. The new task patterns show emergence of:

1. **AI Security Engineering**: Securing AI systems and models
2. **AI Governance and Compliance**: Ensuring responsible AI deployment
3. **AI Operations (MLSecOps)**: Managing AI/ML security pipelines
4. **AI Ethics and Risk Management**: Overseeing ethical AI implementation

The evidence indicates that new tasks will require deep understanding of both traditional cybersecurity and AI/ML technologies.
"""
        else:  # human_only
            narrative = f"""
# {category_info['title']}: Comprehensive Analysis

## Executive Summary

Based on analysis of {total_articles} articles with human-only task indicators, our research reveals the enduring importance of uniquely human capabilities. With an average confidence score of {avg_confidence:.3f}, and {high_confidence_count} articles showing high confidence (≥0.7) in human-only scenarios, the evidence suggests that strategic and interpersonal aspects of cybersecurity will remain fundamentally human.

## Overall Findings

Human-only tasks in cybersecurity center on capabilities that require emotional intelligence, strategic thinking, and complex judgment. The human-only patterns show critical importance in:

1. **Strategic Leadership**: Setting organizational security direction and vision
2. **Crisis Management**: Managing complex incidents requiring human judgment
3. **Stakeholder Communication**: Building relationships and managing expectations
4. **Ethical Decision Making**: Navigating complex moral and legal considerations

The evidence indicates that human-only tasks will become more valuable as AI handles routine operations, elevating the importance of strategic and interpersonal skills.
"""
        
        return narrative
    
    def generate_category_report(self, category):
        """Generate comprehensive report for a specific category."""
        logger.info(f"Starting {category} category narrative analysis...")
        
        articles = self.get_category_articles(category)
        if not articles:
            logger.error(f"No {category} articles found")
            return None
        
        jobs_tasks = self.extract_jobs_and_tasks(articles, category)
        mechanisms = self.extract_mechanisms(articles, category)
        
        # Overall statistics
        high_confidence_articles = [a for a in articles if a['confidence'] >= 0.7]
        medium_confidence_articles = [a for a in articles if 0.4 <= a['confidence'] < 0.7]
        
        report = {
            'category': category,
            'generated_at': datetime.now().isoformat(),
            'total_articles_analyzed': len(articles),
            'high_confidence_articles': len(high_confidence_articles),
            'medium_confidence_articles': len(medium_confidence_articles),
            'avg_confidence': sum(a['confidence'] for a in articles) / len(articles),
            'jobs_and_tasks': jobs_tasks,
            'mechanisms': mechanisms,
            'narrative_summary': self.generate_category_narrative_text(category, articles, jobs_tasks, mechanisms),
            'top_articles': sorted(articles, key=lambda x: x['confidence'], reverse=True)[:10]
        }
        
        return report
    
    def print_category_report(self, report):
        """Print comprehensive category report."""
        category = report['category']
        category_info = self.categories[category]
        
        print("\n" + "="*120)
        print(f"🎯 {category_info['title'].upper()}")
        print("="*120)
        print(f"📊 Generated: {report['generated_at']}")
        print(f"📄 Total Articles Analyzed: {report['total_articles_analyzed']}")
        print(f"🔴 High Confidence Articles: {report['high_confidence_articles']}")
        print(f"🟡 Medium Confidence Articles: {report['medium_confidence_articles']}")
        print(f"📈 Average Confidence: {report['avg_confidence']:.3f}")
        
        print(report['narrative_summary'])
        
        print("\n" + "="*120)
        print(f"🎯 SPECIFIC JOBS AND TASKS - {category.upper()}")
        print("="*120)
        
        # Sort jobs by confidence and evidence count
        sorted_jobs = sorted(report['jobs_and_tasks'].items(), 
                           key=lambda x: (x[1]['avg_confidence'], x[1]['evidence_count']), 
                           reverse=True)
        
        for job, data in sorted_jobs[:10]:  # Top 10 jobs/tasks
            if data['evidence_count'] >= 2:  # Only show jobs with multiple mentions
                print(f"\n🔧 **{job.upper().replace('_', ' ')}**")
                print("-" * 80)
                print(f"📊 **Confidence**: {data['avg_confidence']:.3f}")
                print(f"📄 **Evidence Count**: {data['evidence_count']} articles")
                
                # Category-specific explanations
                if category == 'replace':
                    print(f"\n**Why AI Will Replace This Job/Task:**")
                elif category == 'augment':
                    print(f"\n**How AI Will Augment This Job/Task:**")
                elif category == 'new_tasks':
                    print(f"\n**Why This New Job/Task is Emerging:**")
                else:  # human_only
                    print(f"\n**Why This Remains Human-Only:**")
                
                if data['explanations']:
                    for explanation in data['explanations'][:2]:  # Top 2 explanations
                        print(f"• {explanation}")
                else:
                    # Generate category-appropriate explanation
                    evidence_text = ', '.join(data['citations'][0]['evidence'][:3]) if data['citations'] else 'relevant capabilities'
                    if category == 'replace':
                        print(f"• AI can automate this role through {evidence_text}, reducing the need for human intervention.")
                    elif category == 'augment':
                        print(f"• AI enhances this role through {evidence_text}, improving human capabilities and efficiency.")
                    elif category == 'new_tasks':
                        print(f"• This new role emerges from {evidence_text}, requiring specialized AI-related expertise.")
                    else:  # human_only
                        print(f"• This role requires {evidence_text} that are uniquely human and cannot be automated.")
                
                print(f"\n**Supporting Citations:**")
                for i, citation in enumerate(data['citations'][:3], 1):  # Top 3 citations
                    print(f"{i}. **{citation['title']}**")
                    print(f"   - Confidence: {citation['confidence']:.3f} | Quality: {citation['quality']:.3f}")
                    print(f"   - Evidence: {', '.join(citation['evidence'][:3])}")
                    print(f"   - URL: {citation['url']}")
                    print()
        
        # Mechanisms section with category-appropriate title
        mechanism_title = {
            'replace': 'AUTOMATION MECHANISMS',
            'augment': 'AUGMENTATION MECHANISMS', 
            'new_tasks': 'EMERGENCE MECHANISMS',
            'human_only': 'HUMAN-CENTRIC MECHANISMS'
        }
        
        print("\n" + "="*120)
        print(f"⚙️ {mechanism_title[category]}")
        print("="*120)
        
        sorted_mechanisms = sorted(report['mechanisms'].items(),
                                 key=lambda x: x[1]['avg_confidence'], reverse=True)
        
        for mechanism, data in sorted_mechanisms:
            if data['article_count'] >= 2:  # Only show mechanisms with multiple mentions
                print(f"\n🔬 **{mechanism.upper().replace('_', ' ')}**")
                print("-" * 60)
                print(f"📊 Average Confidence: {data['avg_confidence']:.3f}")
                print(f"📄 Mentioned in {data['article_count']} articles")
                print(f"🔍 Examples: {', '.join(data['examples'][:3])}")
                print()
        
        print("\n" + "="*120)
        print(f"📚 TOP ARTICLES - {category.upper()}")
        print("="*120)
        
        for i, article in enumerate(report['top_articles'][:5], 1):
            print(f"\n{i}. **{article['title']}**")
            print(f"   - Confidence: {article['confidence']:.3f}")
            print(f"   - Quality Score: {article['quality_score']:.3f}")
            print(f"   - Evidence: {', '.join(article['evidence'][:3])}")
            if article['key_insights']:
                print(f"   - Key Insight: {article['key_insights'][0][:150]}...")
            print(f"   - URL: {article['url']}")
            print()
        
        print("\n" + "="*120)
    
    def generate_all_category_reports(self):
        """Generate reports for all categories."""
        all_reports = {}
        
        for category in self.categories.keys():
            logger.info(f"Generating report for {category} category...")
            report = self.generate_category_report(category)
            if report:
                all_reports[category] = report
                self.print_category_report(report)
        
        return all_reports

def main():
    """Main execution function."""
    try:
        analyzer = ComprehensiveCategoryNarrativeAnalyzer()
        
        # Generate all category reports
        all_reports = analyzer.generate_all_category_reports()
        
        if all_reports:
            # Save comprehensive report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data/comprehensive_category_narratives_{timestamp}.json"
            
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(all_reports, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 Comprehensive category narratives saved to: {filename}")
            print("🎉 All category narrative analysis completed successfully!")
            
        else:
            print("❌ Failed to generate category reports")
            
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        print(f"❌ Error generating narratives: {e}")

if __name__ == "__main__":
    main() 