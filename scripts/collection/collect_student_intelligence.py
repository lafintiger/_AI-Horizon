#!/usr/bin/env python3
"""
Student Career Intelligence Collection

Focuses on actionable intelligence for graduating cybersecurity students:
- What jobs/tasks to avoid (being replaced)
- What skills to augment with AI tools 
- What new roles to pivot into
- Specific tools/certifications to learn

Target audience: Jan 2025 and June 2025 graduates
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from aih.gather.searxng_direct import SearXNGDirectConnector
from aih.utils.database import DatabaseManager
from aih.utils.logging import get_logger

# Global status tracker for web integration
status_tracker = None

def set_status_tracker(tracker):
    """Set the status tracker for web dashboard integration."""
    global status_tracker
    status_tracker = tracker

def update_progress(current: int, total: int, status: str = ""):
    """Update progress in status tracker if available."""
    if status_tracker:
        status_tracker.update_progress(current, total, status)

def add_log(level: str, message: str, category: str = "STUDENT_INTEL"):
    """Add log entry to status tracker if available."""
    if status_tracker:
        status_tracker.add_log(level, message, category)

async def collect_student_intelligence():
    """Collect actionable career intelligence for graduating students."""
    logger = get_logger('student_intelligence')
    collector = SearXNGDirectConnector()
    db = DatabaseManager()
    
    # STUDENT-FOCUSED CAREER INTELLIGENCE SEARCHES
    # Focus on SPECIFIC, ACTIONABLE insights for 2025 graduates
    
    searches = {
        'replace': [
            # SPECIFIC cybersecurity jobs being eliminated/automated
            'site:reddit.com r/cybersecurity "lost job" OR "position eliminated" AI automation 2024',
            'site:linkedin.com cybersecurity layoffs AI automation replacing analysts 2024',
            'site:dice.com OR site:indeed.com cybersecurity jobs declining AI SOC analyst',
            'site:cyberseek.org OR cybersecurity workforce reports job market changes 2024',
            '"SOC analyst" jobs automated AI replaced 2024 cybersecurity careers',
            
            # Company announcements about reducing cybersecurity headcount
            'site:techcrunch.com cybersecurity company layoffs AI automation workforce reduction',
            'site:venturebeat.com cybersecurity startup AI replacing human analysts',
            '"earnings call" cybersecurity company reducing headcount AI efficiency',
            'site:glassdoor.com cybersecurity analyst "no longer hiring" AI automation',
            'reddit.com r/SecurityCareerAdvice jobs being eliminated AI 2024',
            
            # Specific cybersecurity tasks being automated
            'vulnerability scanning automated AI tools replacing manual work cybersecurity',
            'incident response automation AI reducing need human analysts',
            'compliance auditing AI automation cybersecurity jobs impact 2024',
            'threat hunting AI tools replacing junior analysts cybersecurity',
            'penetration testing automation AI impact cybersecurity careers 2024',
            
            # Industry transformation - what NOT to specialize in
            'cybersecurity roles avoid 2025 AI automation threat intelligence analyst',
            'entry level cybersecurity jobs disappearing AI automation 2024',
            'cybersecurity career advice avoid roles AI replacing 2024',
            'SOC tier 1 analyst jobs future AI automation impact',
            'cybersecurity certifications becoming obsolete AI 2024 graduates'
        ],
        
        'augment': [
            # SPECIFIC AI tools cybersecurity professionals must learn
            'site:github.com cybersecurity AI tools professionals must learn 2024',
            'site:stackoverflow.com cybersecurity developer AI copilot productivity',
            'cybersecurity analyst AI tools workflow enhancement CrowdStrike Splunk',
            'penetration testing AI tools ethical hacker productivity 2024',
            'incident response AI automation tools cybersecurity analyst skills',
            
            # AI-enhanced cybersecurity workflows students should learn
            'site:coursera.com OR site:udemy.com cybersecurity AI tools certification',
            'CISSP AI cybersecurity skills augmentation training 2024',
            'cybersecurity bootcamp AI tools curriculum graduate preparation',
            'site:sans.org cybersecurity training AI tools integration 2024',
            'CompTIA Security+ AI cybersecurity skills students need',
            
            # Company hiring requirements - AI skills needed
            'site:indeed.com cybersecurity analyst job requirements AI tools 2024',
            'site:linkedin.com cybersecurity jobs AI skills required hiring',
            'site:dice.com cybersecurity positions AI experience preferred 2024',
            'cybersecurity internship AI tools experience requirements 2024',
            'entry level cybersecurity AI skills job postings requirements',
            
            # Specific tools and platforms to learn
            'Splunk AI cybersecurity analyst training student preparation',
            'Microsoft Sentinel AI SIEM cybersecurity student skills',
            'CrowdStrike Falcon AI cybersecurity analyst training 2024',
            'Rapid7 InsightIDR AI cybersecurity tools student learning',
            'Palo Alto Cortex AI cybersecurity platform student training'
        ],
        
        'new_tasks': [
            # NEW cybersecurity roles emerging for 2025 graduates
            'site:indeed.com "AI cybersecurity specialist" jobs hiring 2024 entry level',
            'site:linkedin.com "prompt security engineer" cybersecurity jobs new',
            'AI red team specialist cybersecurity jobs emerging 2024 graduates',
            'site:dice.com "AI governance" cybersecurity compliance jobs new',
            '"AI safety engineer" cybersecurity positions emerging hiring',
            
            # Emerging specializations students can pivot into
            'cybersecurity AI ethics specialist new role opportunities 2024',
            'machine learning security engineer entry level jobs 2024',
            'AI model security testing cybersecurity new specialization',
            'prompt injection security specialist jobs cybersecurity 2024',
            'AI supply chain security analyst new cybersecurity roles',
            
            # Training/certification paths for new roles
            'site:coursera.com AI cybersecurity specialist certification 2024',
            'site:cybrary.it AI security training cybersecurity students',
            'AI red teaming certification cybersecurity career preparation',
            'machine learning security bootcamp cybersecurity professionals',
            'site:edx.org AI governance cybersecurity compliance training',
            
            # Company hiring plans for new AI security roles
            'cybersecurity AI specialist internship programs 2024 2025',
            'tech companies hiring AI security engineers entry level',
            'startup cybersecurity AI specialist job opportunities 2024',
            'government AI cybersecurity specialist positions hiring',
            'consulting firms AI cybersecurity roles graduate recruitment'
        ],
        
        'human_only': [
            # Cybersecurity skills that remain purely human
            'cybersecurity leadership skills AI cannot replace human judgment',
            'incident command cybersecurity crisis management human skills',
            'cybersecurity risk assessment human expertise AI limitations',
            'stakeholder communication cybersecurity analyst human skills essential',
            'cybersecurity policy development human creativity AI cannot replace',
            
            # Client-facing cybersecurity roles remaining human
            'cybersecurity consultant client relationships human trust building',
            'penetration testing client communication human skills required',
            'cybersecurity sales engineer human relationship building essential',
            'CISO leadership strategic planning human judgment cybersecurity',
            'cybersecurity training delivery human instructor irreplaceable',
            
            # Creative and strategic cybersecurity work
            'cybersecurity architecture design human creativity AI limitations',
            'threat modeling creative thinking cybersecurity human skills',
            'cybersecurity innovation human insight AI cannot replicate',
            'business risk assessment cybersecurity human judgment critical',
            'cybersecurity program development human strategic thinking',
            
            # Skills to emphasize on resume/interviews
            'cybersecurity soft skills employers value human capabilities',
            'cybersecurity career advice human skills differentiation AI',
            'cybersecurity interview tips emphasizing human value 2024',
            'cybersecurity leadership development human skills essential',
            'cybersecurity project management human coordination skills'
        ]
    }
    
    total_queries = sum(len(queries) for queries in searches.values())
    total_collected = 0
    category_stats = {}
    
    add_log("INFO", f"Starting student career intelligence collection: {total_queries} targeted queries", "STUDENT")
    update_progress(0, 80, "Collecting actionable career intelligence for graduates...")
    
    for category, queries in searches.items():
        logger.info(f'🎓 Collecting {category.upper()} intelligence for students')
        add_log("INFO", f"Gathering {category.upper()} career intelligence for 2025 graduates", "STUDENT")
        
        category_count = 0
        category_stats[category] = 0
        
        for i, query in enumerate(queries):
            # Update persistent progress tracking
            if status_tracker:
                status_tracker.update_collection_progress(category, i+1, len(queries), category_count)
            
            if category_count >= 20:  # Stop once we have 20 for this category
                break
                
            try:
                status_msg = f"Student Intel: {category.upper()} | Query {i+1}/{len(queries)}"
                update_progress(total_collected, 80, status_msg)
                
                logger.info(f'Student query {i+1}/{len(queries)} for {category}: {query[:80]}...')
                add_log("INFO", f"Student intel query {i+1}/{len(queries)}: {query[:60]}...", "STUDENT")
                
                # Use career-focused search approach
                results = await collector.collect(
                    query=query,
                    max_results=5,
                    category=category,
                    timeframe="2024-2025"
                )
                
                # Save results with student focus metadata
                for artifact in results:
                    if category_count >= 20:
                        break
                    
                    # Convert artifact to database format
                    artifact_data = {
                        'id': artifact.id,
                        'url': artifact.url,
                        'title': artifact.title,
                        'content': artifact.content,
                        'source_type': f'student_intel_{category}',
                        'collected_at': artifact.collected_at,
                        'metadata': artifact.metadata
                    }
                    
                    # Add student-focused metadata
                    artifact_data['metadata']['ai_impact_category'] = category
                    artifact_data['metadata']['collection_method'] = 'student_intelligence'
                    artifact_data['metadata']['target_audience'] = 'graduating_students'
                    artifact_data['metadata']['urgency'] = 'high_actionable'
                    
                    # Check if already exists
                    if not db.artifact_exists(artifact.url):
                        artifact_id = db.save_artifact(artifact_data)
                        logger.info(f'✅ Student intel saved: {artifact.title[:50]}...')
                        add_log("INFO", f"Student actionable intel: {artifact.title[:50]}...", "STUDENT")
                        category_count += 1
                        total_collected += 1
                        
                        # Update progress
                        update_progress(total_collected, 80, f"Collected {total_collected}/80 career insights")
                        
                        # Update persistent progress
                        if status_tracker:
                            status_tracker.update_collection_progress(category, i+1, len(queries), category_count)
                    else:
                        logger.info(f'⚠️  Duplicate skipped: {artifact.url}')
                        add_log("WARN", f"Duplicate skipped: {artifact.url[:50]}...", "STUDENT")
                
                # Brief pause between queries
                await asyncio.sleep(3)
                
            except Exception as e:
                logger.error(f'❌ Error in student query {i+1} for {category}: {e}')
                add_log("ERROR", f"Student query failed: {str(e)[:100]}...", "STUDENT")
                continue
        
        category_stats[category] = category_count
        logger.info(f'✅ Student {category.upper()} intelligence: {category_count} actionable insights')
        add_log("INFO", f"Student {category.upper()} complete: {category_count} actionable insights", "STUDENT")
        
        # Final category progress update
        if status_tracker:
            status_tracker.update_collection_progress(category, len(queries), len(queries), category_count)
        
        # Pause between categories
        await asyncio.sleep(5)
    
    # Final summary
    logger.info('=' * 60)
    logger.info('🎓 STUDENT CAREER INTELLIGENCE COMPLETE!')
    logger.info('=' * 60)
    for category, count in category_stats.items():
        logger.info(f'{category.upper():>12}: {count:>3} actionable insights')
        add_log("INFO", f"STUDENT {category.upper()}: {count} actionable insights", "SUMMARY")
    logger.info(f'{"TOTAL":>12}: {total_collected:>3} career insights')
    add_log("INFO", f"STUDENT CAREER INTELLIGENCE COMPLETE: {total_collected} insights", "SUMMARY")
    logger.info('=' * 60)
    
    update_progress(total_collected, 80, f"Student career intelligence completed: {total_collected} insights")
    
    return total_collected, category_stats

def main():
    """Main function to run student career intelligence collection."""
    print("🎓 Starting Student Career Intelligence Collection")
    print("=" * 60)
    print("Mission: Actionable career guidance for 2025 cybersecurity graduates")
    print("Target: Jan 2025 & June 2025 graduating students")
    print("Focus: Jobs to avoid, skills to learn, new opportunities")
    print("=" * 60)
    
    try:
        result, stats = asyncio.run(collect_student_intelligence())
        
        print("\n🎯 Student Career Intelligence Summary:")
        print("-" * 40)
        for category, count in stats.items():
            action_map = {
                'replace': 'Jobs/Tasks to AVOID',
                'augment': 'Skills to AUGMENT with AI',
                'new_tasks': 'NEW Opportunities to Pursue',
                'human_only': 'Human Skills to EMPHASIZE'
            }
            print(f"{action_map.get(category, category):>25}: {count:>3} insights")
        print(f"{'Total Actionable Intelligence':>25}: {result:>3} insights")
        print("-" * 40)
        print("✅ Ready to guide 2025 graduates!")
        
    except Exception as e:
        print(f"❌ Error during student intelligence collection: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 