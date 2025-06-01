"""
Web Report Generator

Creates an HTML report showing AI impact category analysis results
that can be opened in a web browser.
"""

import json
from datetime import datetime
from pathlib import Path
from aih.config import get_data_path
from aih.utils.database import DatabaseManager

def analyze_manual_entries():
    """Analyze manually entered articles using the same categorization logic."""
    db = DatabaseManager()
    
    # Get all manual entries
    manual_artifacts = [a for a in db.get_artifacts() if a.get('source_type', '').startswith('manual_')]
    
    if not manual_artifacts:
        return {}
    
    # Category configuration matching test_all_categories.py
    category_config = {
        "replace": {
            "name": "AI REPLACING Cybersecurity Tasks",
            "indicators": ["replacing", "automation", "autonomous", "job displacement", "workforce reduction", "eliminating", "lights-out"]
        },
        "augment": {
            "name": "AI AUGMENTING Cybersecurity Tasks", 
            "indicators": ["augmenting", "assisting", "collaboration", "copilot", "enhanced", "productivity", "human-ai"]
        },
        "new_tasks": {
            "name": "NEW TASKS Created by AI",
            "indicators": ["new roles", "emerging", "ai security engineer", "ml specialist", "governance", "skill requirements", "created by ai"]
        },
        "human_only": {
            "name": "HUMAN-ONLY Cybersecurity Tasks",
            "indicators": ["human judgment", "strategic", "ethics", "compliance", "creative", "intuition", "human-driven", "human-only"]
        }
    }
    
    # Analyze each manual entry across all categories
    manual_analysis = {}
    
    for category, config in category_config.items():
        category_analysis = {
            "name": config["name"],
            "total_articles": 0,
            "artifacts": [],
            "indicators_found": {ind: 0 for ind in config["indicators"]},
            "content_quality": {"avg_length": 0, "total_content": 0},
            "source_analysis": {"domains": [], "credible_sources": 0}
        }
        
        total_length = 0
        relevant_artifacts = []
        
        for artifact in manual_artifacts:
            content_lower = artifact['content'].lower()
            indicators_in_artifact = []
            
            # Check for indicators in this category
            for indicator in config["indicators"]:
                if indicator.lower() in content_lower:
                    category_analysis["indicators_found"][indicator] += 1
                    indicators_in_artifact.append(indicator)
            
            # If this artifact has indicators for this category, include it
            if indicators_in_artifact:
                artifact_info = {
                    "title": artifact.get('title', 'Untitled'),
                    "url": artifact.get('url', ''),
                    "collected_at": artifact.get('collected_at', '').strftime('%Y-%m-%d %H:%M:%S') if hasattr(artifact.get('collected_at', ''), 'strftime') else str(artifact.get('collected_at', '')),
                    "content_length": len(artifact['content']),
                    "content_preview": artifact['content'][:250] + "..." if len(artifact['content']) > 250 else artifact['content'],
                    "indicators_found": indicators_in_artifact,
                    "source_type": artifact.get('source_type', 'manual')
                }
                
                relevant_artifacts.append(artifact_info)
                total_length += len(artifact['content'])
                
                # Source analysis
                if artifact.get('url'):
                    domain = artifact['url'].split('/')[2] if len(artifact['url'].split('/')) > 2 else "manual"
                    category_analysis["source_analysis"]["domains"].append(domain)
        
        # Update category stats
        category_analysis["total_articles"] = len(relevant_artifacts)
        category_analysis["artifacts"] = relevant_artifacts
        
        if relevant_artifacts:
            category_analysis["content_quality"]["avg_length"] = total_length // len(relevant_artifacts)
            category_analysis["content_quality"]["total_content"] = total_length
        
        manual_analysis[category] = category_analysis
    
    return manual_analysis

def merge_analysis_results(automated_results, manual_results):
    """Merge automated and manual analysis results."""
    merged = {}
    
    all_categories = set(automated_results.keys()) | set(manual_results.keys())
    
    for category in all_categories:
        auto_data = automated_results.get(category, {})
        manual_data = manual_results.get(category, {})
        
        # Merge the data
        merged_category = {
            "name": auto_data.get("name") or manual_data.get("name", category.title()),
            "total_articles": auto_data.get("total_articles", 0) + manual_data.get("total_articles", 0),
            "artifacts": auto_data.get("artifacts", []) + manual_data.get("artifacts", []),
            "indicators_found": {},
            "content_quality": {
                "avg_length": 0,
                "total_content": auto_data.get("content_quality", {}).get("total_content", 0) + manual_data.get("content_quality", {}).get("total_content", 0)
            },
            "source_analysis": {
                "domains": auto_data.get("source_analysis", {}).get("domains", []) + manual_data.get("source_analysis", {}).get("domains", []),
                "credible_sources": auto_data.get("source_analysis", {}).get("credible_sources", 0) + manual_data.get("source_analysis", {}).get("credible_sources", 0)
            }
        }
        
        # Merge indicator counts
        auto_indicators = auto_data.get("indicators_found", {})
        manual_indicators = manual_data.get("indicators_found", {})
        all_indicators = set(auto_indicators.keys()) | set(manual_indicators.keys())
        
        for indicator in all_indicators:
            merged_category["indicators_found"][indicator] = auto_indicators.get(indicator, 0) + manual_indicators.get(indicator, 0)
        
        # Recalculate average length
        if merged_category["total_articles"] > 0:
            merged_category["content_quality"]["avg_length"] = merged_category["content_quality"]["total_content"] // merged_category["total_articles"]
        
        merged[category] = merged_category
    
    return merged

def generate_html_report():
    """Generate HTML report from category analysis results."""
    
    # Load automated results
    results_file = get_data_path("reports") / "category_analysis_results.json"
    
    automated_results = {}
    test_timestamp = datetime.now().isoformat()
    
    if results_file.exists():
        with open(results_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        automated_results = data.get('results', {})
        test_timestamp = data.get('test_timestamp', 'Unknown')
    
    # Analyze manual entries
    print("📊 Analyzing manually entered articles...")
    manual_results = analyze_manual_entries()
    
    # Merge both sets of results
    if manual_results:
        print(f"✅ Found manual entries in {len(manual_results)} categories")
        results = merge_analysis_results(automated_results, manual_results)
    else:
        print("ℹ️  No manual entries found")
        results = automated_results
    
    if not results:
        print("❌ No analysis results found. Please run test_all_categories.py or add manual entries first.")
        return
    
    # HTML template
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI-Horizon: Cybersecurity Workforce Impact Analysis</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 300;
        }}
        
        .header .subtitle {{
            font-size: 1.2em;
            opacity: 0.9;
            margin-bottom: 20px;
        }}
        
        .meta-info {{
            background: rgba(255,255,255,0.1);
            padding: 15px;
            border-radius: 8px;
            margin-top: 20px;
        }}
        
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 30px;
            padding: 40px;
        }}
        
        .category-card {{
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            overflow: hidden;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        
        .category-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.15);
        }}
        
        .card-header {{
            padding: 25px;
            color: white;
            font-weight: 600;
            font-size: 1.1em;
            cursor: pointer;
            transition: background-color 0.3s ease;
        }}
        
        .card-header:hover {{
            opacity: 0.9;
        }}
        
        .replace {{ background: linear-gradient(135deg, #e74c3c, #c0392b); }}
        .augment {{ background: linear-gradient(135deg, #3498db, #2980b9); }}
        .new_tasks {{ background: linear-gradient(135deg, #27ae60, #229954); }}
        .human_only {{ background: linear-gradient(135deg, #f39c12, #e67e22); }}
        
        .card-body {{
            padding: 25px;
        }}
        
        .stat {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            padding: 10px 0;
            border-bottom: 1px solid #eee;
        }}
        
        .stat:last-child {{
            border-bottom: none;
            margin-bottom: 0;
        }}
        
        .stat-label {{
            font-weight: 500;
            color: #555;
        }}
        
        .stat-value {{
            font-weight: 700;
            font-size: 1.2em;
            color: #2c3e50;
        }}
        
        .indicators {{
            margin-top: 20px;
        }}
        
        .indicators h4 {{
            color: #2c3e50;
            margin-bottom: 10px;
            font-size: 1em;
        }}
        
        .indicator-list {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }}
        
        .indicator-tag {{
            background: #ecf0f1;
            color: #2c3e50;
            padding: 4px 8px;
            border-radius: 15px;
            font-size: 0.85em;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s ease;
        }}
        
        .indicator-tag:hover {{
            background: #bdc3c7;
        }}
        
        .indicator-tag.found {{
            background: #2ecc71;
            color: white;
        }}
        
        .indicator-tag.found:hover {{
            background: #27ae60;
        }}
        
        .progress-bar {{
            width: 100%;
            height: 8px;
            background: #ecf0f1;
            border-radius: 4px;
            margin-top: 15px;
            overflow: hidden;
        }}
        
        .progress-fill {{
            height: 100%;
            border-radius: 4px;
            transition: width 0.3s ease;
        }}
        
        .details-section {{
            padding: 40px;
            background: #f8f9fa;
        }}
        
        .details-section h2 {{
            color: #2c3e50;
            margin-bottom: 30px;
            text-align: center;
            font-size: 2em;
        }}
        
        .article-grid {{
            display: grid;
            gap: 20px;
        }}
        
        .article-item {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.05);
            border-left: 4px solid #3498db;
        }}
        
        .article-title {{
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 10px;
            font-size: 1.1em;
            cursor: pointer;
        }}
        
        .article-title:hover {{
            color: #3498db;
        }}
        
        .article-meta {{
            color: #7f8c8d;
            font-size: 0.9em;
            margin-bottom: 15px;
        }}
        
        .article-preview {{
            color: #555;
            line-height: 1.6;
            margin-bottom: 15px;
        }}
        
        .article-indicators {{
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
        }}
        
        .search-prompt-section {{
            background: #f8f9fa;
            padding: 30px;
            margin: 20px 0;
            border-radius: 8px;
            border-left: 4px solid #3498db;
        }}
        
        .search-prompt {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin: 10px 0;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            white-space: pre-wrap;
            border: 1px solid #e0e0e0;
            max-height: 200px;
            overflow-y: auto;
        }}
        
        .definitions-section {{
            background: #2c3e50;
            color: white;
            padding: 40px;
            margin-top: 0;
        }}
        
        .definitions-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 30px;
            margin-top: 20px;
        }}
        
        .definition-card {{
            background: rgba(255,255,255,0.1);
            padding: 20px;
            border-radius: 8px;
        }}
        
        .definition-card h4 {{
            color: #ecf0f1;
            margin-bottom: 10px;
            font-size: 1.2em;
        }}
        
        .category-section {{
            scroll-margin-top: 100px;
        }}
        
        .footer {{
            background: #34495e;
            color: white;
            padding: 30px 40px;
            text-align: center;
        }}
        
        .footer h3 {{
            margin-bottom: 15px;
            color: #ecf0f1;
        }}
        
        @media (max-width: 768px) {{
            .summary-grid {{
                grid-template-columns: 1fr;
                padding: 20px;
            }}
            
            .header {{
                padding: 20px;
            }}
            
            .header h1 {{
                font-size: 2em;
            }}
        }}
    </style>
    <script>
        function scrollToCategory(categoryId) {{
            const element = document.getElementById(categoryId + '-details');
            if (element) {{
                element.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
            }}
        }}
        
        function highlightIndicatorInArticle(indicator, categoryId) {{
            // Find all articles in this category and highlight the indicator
            const categorySection = document.getElementById(categoryId + '-details');
            if (categorySection) {{
                // Remove previous highlights
                const highlighted = categorySection.querySelectorAll('.highlight');
                highlighted.forEach(el => {{
                    el.outerHTML = el.innerHTML;
                }});
                
                // Add new highlights
                const articles = categorySection.querySelectorAll('.article-preview');
                articles.forEach(article => {{
                    const text = article.innerHTML;
                    const regex = new RegExp(`(\\b${{indicator}}\\b)`, 'gi');
                    article.innerHTML = text.replace(regex, '<span class="highlight" style="background-color: yellow; padding: 2px 4px; border-radius: 3px;">$1</span>');
                }});
                
                // Scroll to category
                categorySection.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
            }}
        }}
        
        function showSearchPrompt(category) {{
            const prompts = {data.get('search_prompts', '{}')};
            if (prompts[category]) {{
                alert('Search Prompt for ' + category.toUpperCase() + ':\\n\\n' + prompts[category]);
            }} else {{
                alert('Search prompt not available for this category.');
            }}
        }}
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 AI-Horizon</h1>
            <div class="subtitle">Cybersecurity Workforce Impact Analysis</div>
            <div class="meta-info">
                <strong>Analysis Date:</strong> {datetime.fromisoformat(test_timestamp).strftime('%B %d, %Y at %I:%M %p')}<br>
                <strong>Data Source:</strong> Perplexity AI Research<br>
                <strong>Categories Analyzed:</strong> {len(results)} AI Impact Categories
            </div>
        </div>
        
        <div style="background: #3498db; padding: 15px; text-align: center;">
            <a href="process_methodology.html" style="display: inline-block; background: rgba(255,255,255,0.2); color: white; padding: 10px 20px; margin: 0 10px; border-radius: 5px; text-decoration: none; transition: background 0.3s ease;" onmouseover="this.style.background='rgba(255,255,255,0.3)'" onmouseout="this.style.background='rgba(255,255,255,0.2)'">📋 View Process Methodology</a>
            <a href="#definitions" style="display: inline-block; background: rgba(255,255,255,0.2); color: white; padding: 10px 20px; margin: 0 10px; border-radius: 5px; text-decoration: none; transition: background 0.3s ease;" onmouseover="this.style.background='rgba(255,255,255,0.3)'" onmouseout="this.style.background='rgba(255,255,255,0.2)'">📊 Scoring Definitions</a>
            <a href="/" style="display: inline-block; background: rgba(255,255,255,0.2); color: white; padding: 10px 20px; margin: 0 10px; border-radius: 5px; text-decoration: none; transition: background 0.3s ease;" onmouseover="this.style.background='rgba(255,255,255,0.3)'" onmouseout="this.style.background='rgba(255,255,255,0.2)'">➕ Manual Entry</a>
            <a href="/chat" style="display: inline-block; background: rgba(255,255,255,0.2); color: white; padding: 10px 20px; margin: 0 10px; border-radius: 5px; text-decoration: none; transition: background 0.3s ease;" onmouseover="this.style.background='rgba(255,255,255,0.3)'" onmouseout="this.style.background='rgba(255,255,255,0.2)'">💬 Chat with Articles</a>
        </div>
        
        <div class="summary-grid">
"""
    
    # Category mappings
    category_info = {
        "replace": {
            "icon": "🤖",
            "title": "AI Replacing Jobs",
            "description": "Tasks AI will completely replace"
        },
        "augment": {
            "icon": "🤝", 
            "title": "AI Augmenting Work",
            "description": "Tasks requiring AI assistance"
        },
        "new_tasks": {
            "icon": "⭐",
            "title": "New Jobs Created",
            "description": "Roles created by AI technology"
        },
        "human_only": {
            "icon": "👤",
            "title": "Human-Only Tasks", 
            "description": "Tasks remaining human-driven"
        }
    }
    
    # Generate category cards
    for category, data in results.items():
        if 'error' in data:
            continue
            
        info = category_info.get(category, {"icon": "📊", "title": category.title(), "description": ""})
        total_indicators = sum(data.get('indicators_found', {}).values())
        total_articles = data.get('total_articles', 0)
        avg_length = data.get('content_quality', {}).get('avg_length', 0)
        credible_sources = data.get('source_analysis', {}).get('credible_sources', 0)
        
        # Calculate effectiveness percentage
        max_possible_indicators = len(data.get('indicators_found', {})) * total_articles
        effectiveness = (total_indicators / max_possible_indicators * 100) if max_possible_indicators > 0 else 0
        
        html_content += f"""
            <div class="category-card">
                <div class="card-header {category}" onclick="scrollToCategory('{category}')">
                    {info['icon']} {info['title']}
                </div>
                <div class="card-body">
                    <div class="stat">
                        <span class="stat-label">Articles Collected</span>
                        <span class="stat-value">{total_articles}</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Key Indicators Found</span>
                        <span class="stat-value">{total_indicators}</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Avg Content Length</span>
                        <span class="stat-value">{avg_length:,} chars</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Credible Sources</span>
                        <span class="stat-value">{credible_sources}/{total_articles}</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Targeting Effectiveness</span>
                        <span class="stat-value">{effectiveness:.1f}%</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill {category}" style="width: {effectiveness}%"></div>
                    </div>
                    
                    <div class="indicators">
                        <h4>Key Indicators Tracked:</h4>
                        <div class="indicator-list">
"""
        
        # Add indicator tags with click functionality
        for indicator, count in data.get('indicators_found', {}).items():
            found_class = "found" if count > 0 else ""
            onclick = f"highlightIndicatorInArticle('{indicator}', '{category}')" if count > 0 else ""
            html_content += f'<span class="indicator-tag {found_class}" onclick="{onclick}">{indicator} ({count})</span>'
        
        html_content += """
                        </div>
                    </div>
                </div>
            </div>
        """
    
    # Add detailed articles section
    html_content += """
        </div>
        
        <div class="search-prompt-section">
            <h2 style="color: #2c3e50; text-align: center; margin-bottom: 30px;">🔍 Search Prompts Used</h2>
            <p style="text-align: center; margin-bottom: 20px; color: #7f8c8d;">
                These are the actual search queries sent to Perplexity AI for each category. Click to expand each prompt.
            </p>
        """
    
    # Add search prompts for each category
    search_prompts = {
        "replace": """CYBERSECURITY WORKFORCE AUTOMATION 2024-2025:

Find authoritative sources on AI COMPLETELY REPLACING cybersecurity professionals:

KEY INDICATORS:
• SIEM/log analysis fully automated (no human analysts)
• AI threat detection replacing SOC analysts entirely
• Autonomous incident response eliminating human responders
• Job displacement studies showing workforce reduction
• "Lights-out" security operations centers
• AI taking over vulnerability management completely

PRIORITY SOURCES: Gartner, Forrester, SANS, academic studies, government workforce reports""",
        
        "augment": """CYBERSECURITY AI-HUMAN COLLABORATION 2024-2025:

Find sources on AI ASSISTING and ENHANCING cybersecurity professionals:

KEY INDICATORS:
• AI copilots for security analysts
• ML-enhanced threat analysis requiring human oversight
• AI-assisted incident response with human decision-making
• Analyst productivity improvements through AI tools
• Human-AI collaboration in security operations
• AI augmentation improving analyst capabilities

PRIORITY SOURCES: SANS surveys, vendor case studies, practitioner reports, industry analysis""",
        
        "new_tasks": """EMERGING CYBERSECURITY ROLES 2024-2025:

Find sources on NEW cybersecurity jobs created by AI technology:

KEY INDICATORS:
• AI security engineers and ML security specialists
• AI model security and bias testing roles
• AI governance and ethics positions in cybersecurity
• Prompt engineering for security applications
• AI red team and adversarial testing specialists
• New skill requirements for AI-integrated security

PRIORITY SOURCES: Job market reports, LinkedIn workforce insights, recruitment studies, career surveys""",
        
        "human_only": """HUMAN-ESSENTIAL CYBERSECURITY 2024-2025:

Find sources on cybersecurity tasks that REMAIN human-driven:

KEY INDICATORS:
• Strategic security planning requiring human judgment
• Crisis communication and stakeholder management
• Legal/compliance decisions in security incidents
• Ethical considerations in security policies
• Creative threat modeling and red team planning
• Complex investigations requiring human intuition

PRIORITY SOURCES: CISO perspectives, security leadership studies, policy research, ethics papers"""
    }
    
    for category, prompt in search_prompts.items():
        if category in results:
            info = category_info.get(category, {"icon": "📊", "title": category.title()})
            
            html_content += f"""
            <div style="margin-bottom: 20px;">
                <details style="background: white; border-radius: 8px; padding: 20px; box-shadow: 0 5px 15px rgba(0,0,0,0.05);">
                    <summary style="font-weight: 600; color: #2c3e50; cursor: pointer; margin-bottom: 15px;">
                        {info['icon']} {info['title']} Search Prompt
                    </summary>
                    <div class="search-prompt">{prompt}</div>
                </details>
            </div>
            """
    
    html_content += """
        </div>
        
        <div class="details-section">
            <h2>📄 Collected Articles by Category</h2>
            <div class="article-grid">
    """
    
    # Add articles for each category
    for category, data in results.items():
        if 'error' in data or not data.get('artifacts'):
            continue
            
        info = category_info.get(category, {"icon": "📊", "title": category.title()})
        
        html_content += f"""
                <div class="category-section" id="{category}-details">
                    <h3 style="color: #2c3e50; margin-bottom: 20px; padding: 15px; background: #ecf0f1; border-radius: 8px;">
                        {info['icon']} {info['title']} - {len(data['artifacts'])} Articles
                    </h3>
        """
        
        for i, article in enumerate(data.get('artifacts', []), 1):
            # Make article title clickable to open URL
            title_onclick = f"window.open('{article['url']}', '_blank')" if article.get('url') else ""
            
            html_content += f"""
                    <div class="article-item">
                        <div class="article-title" onclick="{title_onclick}">#{i}: {article['title'][:100]}{'...' if len(article['title']) > 100 else ''}</div>
                        <div class="article-meta">
                            🗓️ {article['collected_at']} | 📝 {article['content_length']:,} characters
                        </div>
                        <div style="background: #e8f4f8; padding: 10px; border-radius: 5px; margin: 10px 0; border-left: 3px solid #3498db;">
                            <strong>📰 Source:</strong> <a href="{article['url']}" target="_blank" style="color: #2980b9; font-weight: 600; text-decoration: none;">{article['url']}</a>
                            {article.get('metadata', {}).get('date') and f"<br><strong>📅 Published:</strong> {article['metadata']['date']}" or ""}
                        </div>
                        <div class="article-preview">{article['content_preview']}</div>
                        <div class="article-indicators">
                            <strong>Indicators Found:</strong>
            """
            
            for indicator in article.get('indicators_found', []):
                html_content += f'<span class="indicator-tag found">{indicator}</span>'
            
            if not article.get('indicators_found'):
                html_content += '<span class="indicator-tag">None found</span>'
            
            html_content += """
                        </div>
                    </div>
            """
        
        html_content += "</div>"
    
    # Add definitions section
    html_content += """
        </div>
        
        <div class="definitions-section" id="definitions">
            <h2 style="text-align: center; margin-bottom: 30px;">📊 Scoring Methodology & Definitions</h2>
            <div class="definitions-grid">
                <div class="definition-card">
                    <h4>🎯 Targeting Effectiveness Score</h4>
                    <p><strong>Formula:</strong> (Total Indicators Found) ÷ (Max Possible Indicators × Total Articles) × 100</p>
                    <p><strong>Purpose:</strong> Measures how well our search queries captured relevant content for each AI impact category.</p>
                    <p><strong>Range:</strong> 0-100%, where higher scores indicate better search targeting.</p>
                </div>
                
                <div class="definition-card">
                    <h4>🏛️ Credible Source Criteria</h4>
                    <p><strong>Current Implementation:</strong> Based on domain matching against authoritative sources.</p>
                    <p><strong>Recognized Domains:</strong> Gartner, Forrester, SANS, NIST, IEEE, ACM, McKinsey, ArXiv</p>
                    <p><strong>Issue:</strong> Perplexity aggregates sources, so URLs don't match individual credible domains.</p>
                    <p><strong>Result:</strong> All sources marked as non-credible (0 credible sources found).</p>
                </div>
                
                <div class="definition-card">
                    <h4>🔍 Key Indicators</h4>
                    <p><strong>Purpose:</strong> Specific terms and phrases that indicate AI's impact on cybersecurity roles.</p>
                    <p><strong>Categories:</strong> Replacing, Augmenting, New Tasks, Human-Only</p>
                    <p><strong>Detection:</strong> Case-insensitive text matching within article content.</p>
                    <p><strong>Clickable:</strong> Click found indicators to highlight them in supporting articles.</p>
                </div>
                
                <div class="definition-card">
                    <h4>📊 Data Collection Status</h4>
                    <p><strong>Current Run:</strong> Limited test data (1 article per category)</p>
                    <p><strong>Total Articles:</strong> 4 articles collected from Perplexity AI</p>
                    <p><strong>Source:</strong> Real data from Perplexity API searches, not simulated</p>
                    <p><strong>Limitation:</strong> Small sample size for comprehensive analysis</p>
                </div>
            </div>
        </div>
    """
    
    # Calculate total stats
    total_articles = sum(r.get('total_articles', 0) for r in results.values())
    total_indicators = sum(sum(r.get('indicators_found', {}).values()) for r in results.values())
    total_content = sum(r.get('content_quality', {}).get('total_content', 0) for r in results.values())
    
    # Footer
    html_content += f"""
        
        <div class="footer">
            <h3>📊 Analysis Summary</h3>
            <p>
                <strong>Total Articles:</strong> {total_articles} | 
                <strong>Total Indicators Found:</strong> {total_indicators} | 
                <strong>Total Content:</strong> {total_content:,} characters
            </p>
            <p style="margin-top: 15px; opacity: 0.8;">
                Generated by AI-Horizon Strategic Intelligence Pipeline | NSF Grant Research Project
            </p>
        </div>
    </div>
</body>
</html>
    """
    
    # Save HTML report
    report_file = get_data_path("reports") / "ai_horizon_analysis_report.html"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ HTML report generated successfully!")
    print(f"📄 Report saved to: {report_file}")
    print(f"🌐 Open this file in your web browser to view the analysis")
    
    return report_file

if __name__ == "__main__":
    generate_html_report() 