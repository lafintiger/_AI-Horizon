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
        category = metadata.get('ai_impact_category')
        collection_method = metadata.get('collection_method')
        
        # Focus on student intelligence data
        if collection_method == 'student_intelligence' and category in categorized_data:
            categorized_data[category].append({
                'title': artifact.get('title', 'No title'),
                'url': artifact.get('url', 'No URL'),
                'content': artifact.get('content', 'No content'),
                'collected_at': artifact.get('collected_at', 'Unknown'),
                'metadata': metadata
            })
    
    return categorized_data

def extract_actionable_insights(articles: List[Dict], category: str) -> List[str]:
    """Extract specific, actionable insights from articles."""
    insights = []
    
    # Category-specific insight extraction
    if category == 'replace':
        keywords = ['eliminated', 'automated', 'replaced', 'redundant', 'outsourced', 'deprecated']
        for article in articles:
            content = article['content'].lower()
            title = article['title'].lower()
            
            # Look for specific job titles or tasks being eliminated
            if any(keyword in content or keyword in title for keyword in keywords):
                # Extract specific mentions
                if 'soc analyst' in content or 'soc tier 1' in content:
                    insights.append("❌ SOC Tier 1 Analyst positions being automated")
                if 'vulnerability scan' in content:
                    insights.append("❌ Manual vulnerability scanning roles declining")
                if 'compliance audit' in content:
                    insights.append("❌ Basic compliance auditing being automated")
                if 'threat intelligence' in content and 'junior' in content:
                    insights.append("❌ Junior threat intelligence analyst roles at risk")
    
    elif category == 'augment':
        tools = ['splunk', 'crowdstrike', 'sentinel', 'cortex', 'rapid7', 'ai copilot']
        for article in articles:
            content = article['content'].lower()
            
            # Look for specific tools and skills to learn
            if 'splunk' in content and ('ai' in content or 'machine learning' in content):
                insights.append("✅ Learn Splunk AI/ML capabilities")
            if 'crowdstrike' in content and 'ai' in content:
                insights.append("✅ Master CrowdStrike Falcon AI features")
            if 'microsoft sentinel' in content or 'azure sentinel' in content:
                insights.append("✅ Get Microsoft Sentinel AI certification")
            if 'ai copilot' in content and 'cybersecurity' in content:
                insights.append("✅ Practice with AI copilot tools for security")
            if 'prompt engineering' in content:
                insights.append("✅ Develop prompt engineering skills for security")
    
    elif category == 'new_tasks':
        new_roles = ['ai security', 'prompt security', 'ai governance', 'ai ethics', 'mlsecops']
        for article in articles:
            content = article['content'].lower()
            title = article['title'].lower()
            
            # Look for emerging role opportunities
            if 'ai security specialist' in content or 'ai security engineer' in content:
                insights.append("🆕 AI Security Specialist - high demand emerging role")
            if 'prompt security' in content or 'prompt injection' in content:
                insights.append("🆕 Prompt Security Engineer - new specialization")
            if 'ai governance' in content and 'compliance' in content:
                insights.append("🆕 AI Governance Officer - regulatory compliance focus")
            if 'mlsecops' in content or 'ml security' in content:
                insights.append("🆕 MLSecOps Engineer - machine learning security")
            if 'ai red team' in content:
                insights.append("🆕 AI Red Team Specialist - adversarial testing")
    
    elif category == 'human_only':
        human_skills = ['leadership', 'communication', 'creativity', 'judgment', 'relationship']
        for article in articles:
            content = article['content'].lower()
            
            # Look for human-centric skills to emphasize
            if 'leadership' in content and 'cybersecurity' in content:
                insights.append("💪 Develop cybersecurity leadership skills")
            if 'communication' in content and ('client' in content or 'stakeholder' in content):
                insights.append("💪 Master stakeholder communication")
            if 'crisis management' in content:
                insights.append("💪 Build crisis management expertise")
            if 'risk assessment' in content and 'human judgment' in content:
                insights.append("💪 Emphasize human risk assessment capabilities")
    
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