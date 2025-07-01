#!/usr/bin/env python3
"""
Student Career Intelligence Report Generator

Generates actionable reports for cybersecurity students graduating in 2025.
Focuses on practical recommendations for job market preparation.
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from aih.utils.database import DatabaseManager

def get_student_intelligence_data() -> Dict[str, List[Dict]]:
    """Retrieve student career intelligence from database."""
    db = DatabaseManager()
    artifacts = db.get_artifacts()
    
    categorized_data = {
        'replace': [],
        'augment': [],
        'new_tasks': [],
        'human_only': []
    }
    
    for artifact in artifacts:
        metadata = json.loads(artifact.get('raw_metadata', '{}'))
        
        # Get category from ai_impact_category or primary_category
        category = metadata.get('ai_impact_category')
        if not category:
            category = metadata.get('primary_category')
        
        # Include all articles with valid categories
        if category and category in categorized_data:
            categorized_data[category].append({
                'title': artifact.get('title', 'No title'),
                'url': artifact.get('url', 'No URL'),
                'content': artifact.get('content', 'No content'),
                'collected_at': artifact.get('collected_at', 'Unknown'),
                'collection_method': metadata.get('collection_method', 'Unknown'),
                'category': category,
                'metadata': metadata
            })
    
    return categorized_data

def extract_actionable_insights(articles: List[Dict], category: str) -> List[str]:
    """Extract specific, actionable insights from articles."""
    insights = []
    
    # Category-specific insight extraction
    if category == 'replace':
        # Look for specific jobs/tasks being eliminated
        replace_keywords = [
            ('soc tier 1', '❌ SOC Tier 1 Analyst positions being automated by AI'),
            ('manual vulnerability scan', '❌ Manual vulnerability scanning being replaced by automated tools'),
            ('basic compliance', '❌ Basic compliance checking being automated'),
            ('log analysis', '❌ Manual log analysis being replaced by AI correlation'),
            ('password reset', '❌ Basic helpdesk tasks being automated'),
            ('patch management', '❌ Routine patch management being automated'),
            ('signature-based detection', '❌ Traditional signature-based detection declining'),
            ('basic incident triage', '❌ Level 1 incident triage being automated'),
            ('report generation', '❌ Manual security report generation being automated'),
            ('basic risk assessment', '❌ Basic risk assessments being automated')
        ]
        
        for article in articles:
            content = article['content'].lower()
            title = article['title'].lower()
            text = f"{title} {content}"
            
            for keyword, insight in replace_keywords:
                if keyword in text and any(word in text for word in ['automat', 'ai ', 'replace', 'eliminat']):
                    insights.append(insight)
    
    elif category == 'augment':
        # Look for tools and skills to enhance with AI
        augment_keywords = [
            ('splunk ai', '✅ Master Splunk AI/ML capabilities for threat detection'),
            ('crowdstrike falcon', '✅ Learn CrowdStrike Falcon AI features'),
            ('microsoft sentinel', '✅ Get certified in Microsoft Sentinel AI'),
            ('cortex xsoar', '✅ Practice with Cortex XSOAR automation'),
            ('phantom', '✅ Learn Splunk Phantom SOAR capabilities'),
            ('rapid7', '✅ Master Rapid7 AI-enhanced security tools'),
            ('prompt engineering', '✅ Develop prompt engineering skills for security'),
            ('ai copilot', '✅ Practice with security AI copilot tools'),
            ('machine learning', '✅ Learn ML for cybersecurity applications'),
            ('threat hunting ai', '✅ Augment threat hunting with AI tools'),
            ('siem ai', '✅ Master AI-enhanced SIEM capabilities'),
            ('security orchestration', '✅ Learn security orchestration and automation'),
            ('behavioral analytics', '✅ Master AI-driven behavioral analytics'),
            ('anomaly detection', '✅ Enhance skills with AI anomaly detection')
        ]
        
        for article in articles:
            content = article['content'].lower()
            title = article['title'].lower()
            text = f"{title} {content}"
            
            for keyword, insight in augment_keywords:
                if keyword in text:
                    insights.append(insight)
    
    elif category == 'new_tasks':
        # Look for emerging roles and opportunities
        new_roles = [
            ('ai security engineer', '🆕 AI Security Engineer - high-demand emerging role'),
            ('prompt security', '🆕 Prompt Security Specialist - new AI security focus'),
            ('ai governance', '🆕 AI Governance Officer - regulatory compliance role'),
            ('mlsecops', '🆕 MLSecOps Engineer - ML pipeline security'),
            ('ai red team', '🆕 AI Red Team Specialist - adversarial AI testing'),
            ('ai risk', '🆕 AI Risk Analyst - emerging compliance role'),
            ('llm security', '🆕 LLM Security Specialist - large language model security'),
            ('ai auditor', '🆕 AI Auditor - emerging compliance role'),
            ('prompt injection', '🆕 Prompt Injection Tester - new attack vector specialist'),
            ('ai ethics', '🆕 AI Ethics Officer - responsible AI implementation'),
            ('model security', '🆕 Model Security Engineer - AI/ML model protection'),
            ('ai compliance', '🆕 AI Compliance Manager - regulatory oversight'),
            ('generative ai security', '🆕 Generative AI Security Specialist'),
            ('ai supply chain', '🆕 AI Supply Chain Security - model provenance tracking')
        ]
        
        for article in articles:
            content = article['content'].lower()
            title = article['title'].lower()
            text = f"{title} {content}"
            
            for keyword, insight in new_roles:
                if keyword in text and any(word in text for word in ['new', 'emerging', 'growing', 'demand', 'opportunit']):
                    insights.append(insight)
    
    elif category == 'human_only':
        # Look for human-centric skills to emphasize
        human_skills = [
            ('leadership', '💪 Develop cybersecurity leadership and team management'),
            ('communication', '💪 Master stakeholder and executive communication'),
            ('crisis management', '💪 Build crisis management and incident response leadership'),
            ('strategic thinking', '💪 Emphasize strategic security planning capabilities'),
            ('risk judgment', '💪 Highlight human risk assessment and judgment'),
            ('relationship building', '💪 Focus on relationship building and trust'),
            ('creativity', '💪 Emphasize creative problem-solving abilities'),
            ('business acumen', '💪 Develop business-focused security understanding'),
            ('regulatory knowledge', '💪 Master complex regulatory and compliance frameworks'),
            ('vendor management', '💪 Build vendor relationship and negotiation skills'),
            ('board communication', '💪 Learn executive and board-level security communication'),
            ('cultural awareness', '💪 Develop cultural and organizational awareness'),
            ('mentoring', '💪 Build mentoring and knowledge transfer skills'),
            ('innovation', '💪 Emphasize security innovation and strategy')
        ]
        
        for article in articles:
            content = article['content'].lower()
            title = article['title'].lower()
            text = f"{title} {content}"
            
            for keyword, insight in human_skills:
                if keyword in text and any(word in text for word in ['human', 'soft skill', 'irreplaceable', 'critical']):
                    insights.append(insight)
    
    return list(set(insights))  # Remove duplicates

def generate_student_report() -> str:
    """Generate comprehensive student career intelligence report."""
    data = get_student_intelligence_data()
    report_date = datetime.now().strftime("%Y-%m-%d")
    
    # Action mapping for clear student guidance
    action_categories = {
        'replace': {
            'title': '🚫 JOBS & TASKS TO AVOID',
            'description': 'These roles/tasks are being automated or eliminated. Focus elsewhere.',
            'action': 'Avoid specializing in these areas'
        },
        'augment': {
            'title': '🔧 SKILLS TO AUGMENT WITH AI',
            'description': 'These skills remain valuable but must be enhanced with AI tools.',
            'action': 'Learn these AI tools to stay competitive'
        },
        'new_tasks': {
            'title': '🌟 NEW OPPORTUNITIES TO PURSUE',
            'description': 'Emerging roles with high demand and growth potential.',
            'action': 'Consider pivoting or specializing in these areas'
        },
        'human_only': {
            'title': '💪 HUMAN SKILLS TO EMPHASIZE',
            'description': 'Skills that remain purely human and highly valued.',
            'action': 'Highlight these on your resume and in interviews'
        }
    }
    
    report = f"""
# 🎓 CYBERSECURITY CAREER INTELLIGENCE REPORT
**For Students Graduating January & June 2025**

Generated: {report_date}
Data Sources: {sum(len(articles) for articles in data.values())} industry intelligence articles

---

## 📋 EXECUTIVE SUMMARY FOR STUDENTS

The cybersecurity job market is rapidly evolving due to AI automation. This report provides **actionable intelligence** to help you:

1. **Avoid specializing** in roles being automated
2. **Learn AI tools** to augment traditional skills  
3. **Pivot into** emerging high-demand roles
4. **Emphasize human skills** that remain irreplaceable

**🎯 Key Recommendation**: Focus your remaining coursework on AI-augmented cybersecurity skills and emerging specializations.

---
"""
    
    # Generate insights for each category
    for category, category_data in action_categories.items():
        articles = data.get(category, [])
        insights = extract_actionable_insights(articles, category)
        
        report += f"""
## {category_data['title']}

**{category_data['description']}**

**Action for Students**: {category_data['action']}

### Specific Intelligence ({len(articles)} sources analyzed):
"""
        
        if insights:
            for insight in insights[:10]:  # Top 10 insights
                report += f"- {insight}\n"
        else:
            report += "- More intelligence needed - consider running targeted collection\n"
        
        report += f"\n**📊 Data Confidence**: {len(articles)} articles analyzed\n\n---\n"
    
    # Add specific recommendations for different graduation timelines
    report += """
## 🗓️ TIMELINE-SPECIFIC RECOMMENDATIONS

### For January 2025 Graduates (5 months out):
**Immediate Action Required**
- ✅ **Learn basic AI prompt engineering** - essential for any cybersecurity role
- ✅ **Get hands-on with Splunk AI/ML** - widely used in industry
- ✅ **Practice with Microsoft Sentinel** - growing market share
- ❌ **Avoid SOC Tier 1 applications** - high automation risk
- 💪 **Emphasize communication skills** in interviews

### For June 2025 Graduates (12 months out):
**Strategic Planning Opportunity**
- 🌟 **Consider AI Security specialization** - emerging high-demand field
- 🔧 **Build portfolio with AI-augmented projects** 
- 📚 **Request curriculum on AI governance/ethics**
- 💼 **Seek internships in AI security roles**
- 🎯 **Focus capstone project on AI security**

---

## 📈 PROGRAM COMMITTEE RECOMMENDATIONS

Based on this intelligence, recommend developing:

1. **AI Security Fundamentals Course** - prompt engineering, AI tool usage
2. **Hands-on AI Tool Labs** - Splunk AI, Sentinel, CrowdStrike
3. **AI Governance & Ethics Module** - emerging compliance requirements
4. **Industry Partnership Program** - internships in AI security roles
5. **Rapid Response Curriculum Updates** - quarterly market intelligence reviews

---

## 🎯 NEXT STEPS FOR STUDENTS

1. **Review this report with academic advisor**
2. **Identify 2-3 AI tools to learn this semester**
3. **Network with professionals in emerging AI security roles**
4. **Consider independent study/research in AI security**
5. **Update resume to emphasize human skills + AI augmentation**

---

*This report is based on real-time industry intelligence and should be updated quarterly as the market evolves rapidly.*
"""
    
    return report

def main():
    """Generate and save student career intelligence report."""
    print("[STUDENT] Generating Student Career Intelligence Report...")
    
    try:
        report_content = generate_student_report()
        
        # Save to reports directory
        reports_dir = Path('data/reports')
        reports_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"student_career_intelligence_{timestamp}.md"
        filepath = reports_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"[SUCCESS] Student career report generated: {filepath}")
        print(f"[FILEPATH] {filepath}")  # Add clean filepath output for server parsing
        print(f"[INFO] Report contains actionable intelligence for 2025 graduates")
        print(f"[ACTION] Share with academic advisors and program committees")
        
        return str(filepath)
        
    except Exception as e:
        print(f"[ERROR] Error generating student report: {e}")
        return None

if __name__ == "__main__":
    main() 