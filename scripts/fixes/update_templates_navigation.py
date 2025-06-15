#!/usr/bin/env python3
"""
Template Navigation Consistency Update Script

This script updates all HTML templates to use the new base.html template
for consistent, professional navigation across all pages.

Usage:
    python scripts/fixes/update_templates_navigation.py
"""

import os
import re
from pathlib import Path

def update_template_to_extend_base(template_path, page_title):
    """Update a template to extend the base template."""
    
    print(f"Updating {template_path}...")
    
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Skip if already extends base
    if '{% extends "base.html" %}' in content:
        print(f"  ✅ {template_path} already extends base template")
        return
    
    # Extract the main content (everything after <body> and before </body>)
    body_match = re.search(r'<body[^>]*>(.*)</body>', content, re.DOTALL)
    if not body_match:
        print(f"  ❌ Could not find body content in {template_path}")
        return
    
    body_content = body_match.group(1).strip()
    
    # Remove any existing navigation (common patterns)
    # Remove nav headers
    body_content = re.sub(r'<nav[^>]*class="nav-header"[^>]*>.*?</nav>', '', body_content, flags=re.DOTALL)
    
    # Remove duplicate container divs
    body_content = re.sub(r'<div[^>]*class="container"[^>]*>', '', body_content)
    body_content = re.sub(r'</div>\s*$', '', body_content.strip())
    
    # Extract any page-specific styles
    style_match = re.search(r'<style>(.*?)</style>', content, re.DOTALL)
    page_styles = ""
    if style_match:
        page_styles = style_match.group(1).strip()
        # Remove base styles that are now in base template
        page_styles = re.sub(r'\s*\*\s*\{[^}]*\}', '', page_styles)
        page_styles = re.sub(r'\s*body\s*\{[^}]*\}', '', page_styles)
        page_styles = re.sub(r'\s*\.container\s*\{[^}]*\}', '', page_styles)
        page_styles = re.sub(r'\s*\.nav-[^{]*\{[^}]*\}', '', page_styles, flags=re.MULTILINE)
    
    # Extract any scripts
    script_match = re.search(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
    page_scripts = ""
    if script_match:
        page_scripts = script_match.group(1).strip()
    
    # Create new template content
    new_content = '{% extends "base.html" %}\n\n'
    new_content += f'{{% block title %}}{page_title}{{% endblock %}}\n'
    
    if page_styles:
        new_content += '\n{% block extra_styles %}\n<style>\n'
        new_content += page_styles
        new_content += '\n</style>\n{% endblock %}\n'
    
    new_content += '\n{% block content %}\n    <div class="main-content">\n'
    new_content += body_content
    new_content += '\n    </div>\n{% endblock %}\n'
    
    if page_scripts:
        new_content += '\n{% block scripts %}\n<script>\n'
        new_content += page_scripts
        new_content += '\n</script>\n{% endblock %}\n'
    
    # Write the updated template
    with open(template_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"  ✅ Updated {template_path}")

def main():
    """Update all templates to use consistent navigation."""
    
    templates_dir = Path("templates")
    
    # Template mappings (filename -> page title)
    template_mappings = {
        "browse_entries.html": "Browse Entries - AI-Horizon",
        "analysis.html": "Analysis Tools - AI-Horizon", 
        "reports.html": "Reports - AI-Horizon",
        "summaries.html": "Category Summaries - AI-Horizon",
        "methodology.html": "Methodology - AI-Horizon",
        "workflow.html": "Visual Workflow - AI-Horizon",
        "settings.html": "Settings - AI-Horizon",
        "cost_analysis.html": "Cost Analysis - AI-Horizon",
        "manual_entry.html": "Manual Entry - AI-Horizon",
        "add_url.html": "Add URL - AI-Horizon",
        "add_file.html": "Add File - AI-Horizon", 
        "add_youtube.html": "Add YouTube - AI-Horizon",
        "view_entry.html": "View Entry - AI-Horizon",
        "process_entries.html": "Process Entries - AI-Horizon"
    }
    
    print("🔧 Updating templates for consistent navigation...")
    print("=" * 60)
    
    updated_count = 0
    for template_file, page_title in template_mappings.items():
        template_path = templates_dir / template_file
        if template_path.exists():
            update_template_to_extend_base(template_path, page_title)
            updated_count += 1
        else:
            print(f"  ⚠️  Template not found: {template_path}")
    
    print("=" * 60)
    print(f"✅ Navigation consistency update complete!")
    print(f"📊 Updated {updated_count} templates")
    print(f"🎯 All pages now use consistent professional navigation")

if __name__ == "__main__":
    main() 