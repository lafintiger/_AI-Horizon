#!/usr/bin/env python3
"""
AI-Horizon Backup and Archival System

Creates local copies of all processed content including:
- Web pages saved as PDF and HTML
- Original file copies
- Text extractions
- Metadata backups
"""

import sys
import os
import json
import shutil
import requests
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from aih.utils.database import DatabaseManager
from aih.utils.logging import get_logger

logger = get_logger(__name__)

class BackupManager:
    """Manages local backup and archival of processed content."""
    
    def __init__(self, backup_root: str = "data/backups"):
        self.backup_root = Path(backup_root)
        self.backup_root.mkdir(parents=True, exist_ok=True)
        
        # Create backup directory structure
        self.dirs = {
            'content': self.backup_root / "content",
            'web_pages': self.backup_root / "web_pages", 
            'files': self.backup_root / "files",
            'metadata': self.backup_root / "metadata",
            'exports': self.backup_root / "exports"
        }
        
        for dir_path in self.dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def backup_all_content(self):
        """Backup all content from the database."""
        logger.info("Starting comprehensive backup of all content...")
        
        db = DatabaseManager()
        artifacts = db.get_artifacts()
        
        backup_summary = {
            'timestamp': datetime.now().isoformat(),
            'total_artifacts': len(artifacts),
            'backed_up': 0,
            'failed': 0,
            'errors': []
        }
        
        for artifact in artifacts:
            try:
                self.backup_single_artifact(artifact)
                backup_summary['backed_up'] += 1
                logger.info(f"Backed up: {artifact['title'][:50]}...")
            except Exception as e:
                backup_summary['failed'] += 1
                backup_summary['errors'].append({
                    'artifact_id': artifact.get('id', 'unknown'),
                    'title': artifact.get('title', 'unknown')[:50],
                    'error': str(e)
                })
                logger.error(f"Failed to backup {artifact.get('id', 'unknown')}: {e}")
        
        # Save backup summary
        summary_file = self.dirs['metadata'] / f"backup_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(backup_summary, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Backup completed: {backup_summary['backed_up']} backed up, {backup_summary['failed']} failed")
        return backup_summary
    
    def backup_single_artifact(self, artifact):
        """Backup a single artifact with all its content."""
        artifact_id = artifact['id']
        source_type = artifact.get('source_type', 'unknown')
        
        # Create artifact-specific directory
        artifact_dir = self.dirs['content'] / artifact_id
        artifact_dir.mkdir(exist_ok=True)
        
        # Save metadata
        metadata_file = artifact_dir / "metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(artifact, f, indent=2, ensure_ascii=False, default=str)
        
        # Save content as text
        content_file = artifact_dir / "content.txt"
        with open(content_file, 'w', encoding='utf-8') as f:
            f.write(artifact.get('content', ''))
        
        # Handle different source types
        if source_type.startswith('manual_url') or source_type.startswith('perplexity'):
            self.backup_web_content(artifact, artifact_dir)
        elif source_type.startswith('manual_file'):
            self.backup_file_content(artifact, artifact_dir)
        elif source_type.startswith('manual_youtube'):
            self.backup_youtube_content(artifact, artifact_dir)
        
        # Create human-readable summary
        self.create_artifact_summary(artifact, artifact_dir)
    
    def backup_web_content(self, artifact, artifact_dir):
        """Backup web page content as HTML and attempt PDF conversion."""
        url = artifact.get('url', '')
        if not url or url.startswith('file://'):
            return
        
        try:
            # Save original HTML
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                html_file = artifact_dir / "original.html"
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                
                # Create a simple offline-readable HTML version
                self.create_readable_html(artifact, artifact_dir, response.text)
            
        except Exception as e:
            logger.warning(f"Could not backup web content for {url}: {e}")
    
    def backup_file_content(self, artifact, artifact_dir):
        """Backup original uploaded files."""
        metadata = json.loads(artifact.get('raw_metadata', '{}'))
        original_path = metadata.get('file_path')
        
        if original_path and Path(original_path).exists():
            try:
                original_filename = metadata.get('original_filename', 'uploaded_file')
                backup_file = artifact_dir / f"original_{original_filename}"
                shutil.copy2(original_path, backup_file)
                logger.info(f"Copied original file: {original_filename}")
            except Exception as e:
                logger.warning(f"Could not backup original file: {e}")
    
    def backup_youtube_content(self, artifact, artifact_dir):
        """Backup YouTube video metadata and create info file."""
        metadata = json.loads(artifact.get('raw_metadata', '{}'))
        video_id = metadata.get('video_id')
        
        if video_id:
            # Save YouTube metadata
            youtube_info = {
                'video_id': video_id,
                'url': artifact.get('url', ''),
                'title': artifact.get('title', ''),
                'backup_note': 'YouTube transcript extraction not implemented - manual notes preserved'
            }
            
            info_file = artifact_dir / "youtube_info.json"
            with open(info_file, 'w', encoding='utf-8') as f:
                json.dump(youtube_info, f, indent=2, ensure_ascii=False)
    
    def create_readable_html(self, artifact, artifact_dir, original_html):
        """Create a clean, offline-readable HTML version."""
        readable_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{artifact.get('title', 'Archived Article')}</title>
    <style>
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 800px; 
            margin: 0 auto; 
            padding: 20px; 
            line-height: 1.6; 
            color: #333;
        }}
        .header {{ 
            border-bottom: 2px solid #667eea; 
            padding-bottom: 20px; 
            margin-bottom: 30px; 
        }}
        .metadata {{ 
            background: #f8f9fa; 
            padding: 15px; 
            border-radius: 5px; 
            margin-bottom: 30px; 
        }}
        .content {{ 
            font-size: 16px; 
            line-height: 1.8; 
        }}
        .category-badge {{ 
            display: inline-block; 
            padding: 4px 8px; 
            border-radius: 3px; 
            font-size: 12px; 
            font-weight: 600; 
            color: white; 
        }}
        .category-replace {{ background: #dc3545; }}
        .category-augment {{ background: #17a2b8; }}
        .category-new_tasks {{ background: #28a745; }}
        .category-human_only {{ background: #ffc107; color: #333; }}
        .category-general {{ background: #6c757d; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{artifact.get('title', 'Archived Article')}</h1>
        <p><strong>Source:</strong> <a href="{artifact.get('url', '')}" target="_blank">{artifact.get('url', '')}</a></p>
        <p><strong>Archived:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="metadata">
        <h3>AI-Horizon Analysis</h3>
        <p><strong>Collection Method:</strong> {artifact.get('source_type', 'Unknown')}</p>
        <p><strong>Collected:</strong> {artifact.get('collected_at', 'Unknown')}</p>
        {self._get_category_html(artifact)}
    </div>
    
    <div class="content">
        <h3>Content</h3>
        <div>{self._clean_content_for_html(artifact.get('content', ''))}</div>
    </div>
</body>
</html>
        """
        
        html_file = artifact_dir / "readable.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(readable_html)
    
    def _get_category_html(self, artifact):
        """Get HTML for category display."""
        metadata = json.loads(artifact.get('raw_metadata', '{}'))
        category = metadata.get('ai_impact_category')
        
        if category:
            category_names = {
                'replace': 'Jobs/Tasks Being Replaced',
                'augment': 'Human Work Enhanced by AI',
                'new_tasks': 'New Opportunities Created',
                'human_only': 'Human-Only Tasks'
            }
            return f'<p><strong>AI Impact Category:</strong> <span class="category-badge category-{category}">{category_names.get(category, category)}</span></p>'
        return '<p><strong>AI Impact Category:</strong> Not processed</p>'
    
    def _clean_content_for_html(self, content):
        """Clean and format content for HTML display."""
        if not content:
            return '<p>No content available</p>'
        
        # Basic HTML escaping and paragraph formatting
        import html
        escaped = html.escape(content)
        paragraphs = escaped.split('\n\n')
        return '\n'.join([f'<p>{p.strip()}</p>' for p in paragraphs if p.strip()])
    
    def create_artifact_summary(self, artifact, artifact_dir):
        """Create a human-readable summary of the artifact."""
        metadata = json.loads(artifact.get('raw_metadata', '{}'))
        
        summary = f"""
AI-HORIZON ARTIFACT BACKUP
============================

Title: {artifact.get('title', 'Unknown')}
ID: {artifact.get('id', 'Unknown')}
URL: {artifact.get('url', 'Unknown')}
Source Type: {artifact.get('source_type', 'Unknown')}
Collected: {artifact.get('collected_at', 'Unknown')}

AI Impact Analysis:
- Category: {metadata.get('ai_impact_category', 'Not processed')}
- Processed At: {metadata.get('processed_at', 'Not processed')}
- Processing Method: {metadata.get('processing_method', 'N/A')}

Content Preview:
{artifact.get('content', 'No content')[:500]}{'...' if len(artifact.get('content', '')) > 500 else ''}

Files in this backup:
- metadata.json: Complete artifact metadata
- content.txt: Full text content
- readable.html: Human-readable web version
- original.*: Original source file (if applicable)

Backup Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        summary_file = artifact_dir / "README.txt"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary.strip())
    
    def export_database_backup(self):
        """Export complete database as JSON for disaster recovery."""
        logger.info("Creating complete database export...")
        
        db = DatabaseManager()
        artifacts = db.get_artifacts()
        
        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'total_artifacts': len(artifacts),
            'artifacts': artifacts,
            'export_note': 'Complete database backup for AI-Horizon system'
        }
        
        export_file = self.dirs['exports'] / f"database_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(export_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Database export saved: {export_file}")
        return export_file
    
    def get_backup_stats(self):
        """Get statistics about current backups."""
        stats = {
            'total_artifacts_backed_up': 0,
            'backup_size_mb': 0,
            'latest_backup': None,
            'backup_directories': {}
        }
        
        if self.dirs['content'].exists():
            artifact_dirs = [d for d in self.dirs['content'].iterdir() if d.is_dir()]
            stats['total_artifacts_backed_up'] = len(artifact_dirs)
            
            # Calculate total size
            total_size = 0
            for dir_path in self.dirs.values():
                if dir_path.exists():
                    for file_path in dir_path.rglob('*'):
                        if file_path.is_file():
                            total_size += file_path.stat().st_size
            
            stats['backup_size_mb'] = round(total_size / (1024 * 1024), 2)
            
            # Find latest backup
            if artifact_dirs:
                latest_dir = max(artifact_dirs, key=lambda d: d.stat().st_mtime)
                stats['latest_backup'] = latest_dir.name
        
        return stats

def main():
    """Run backup operations."""
    print("🗄️ AI-Horizon Backup System")
    print("=" * 40)
    
    backup_manager = BackupManager()
    
    # Show current stats
    stats = backup_manager.get_backup_stats()
    print(f"Current backups: {stats['total_artifacts_backed_up']} artifacts")
    print(f"Backup size: {stats['backup_size_mb']} MB")
    print(f"Latest backup: {stats['latest_backup'] or 'None'}")
    print()
    
    # Options
    print("Choose backup operation:")
    print("1. Backup all content (comprehensive)")
    print("2. Export database only")
    print("3. Show backup statistics")
    print("4. Exit")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == '1':
        print("\n🚀 Starting comprehensive backup...")
        summary = backup_manager.backup_all_content()
        backup_manager.export_database_backup()
        
        print(f"\n✅ Backup completed!")
        print(f"- Artifacts backed up: {summary['backed_up']}")
        print(f"- Failed: {summary['failed']}")
        print(f"- Location: {backup_manager.backup_root}")
        
    elif choice == '2':
        print("\n📤 Exporting database...")
        export_file = backup_manager.export_database_backup()
        print(f"✅ Database exported to: {export_file}")
        
    elif choice == '3':
        stats = backup_manager.get_backup_stats()
        print(f"\n📊 Backup Statistics:")
        print(f"- Total artifacts backed up: {stats['total_artifacts_backed_up']}")
        print(f"- Total backup size: {stats['backup_size_mb']} MB")
        print(f"- Latest backup: {stats['latest_backup'] or 'None'}")
        print(f"- Backup location: {backup_manager.backup_root}")
        
    elif choice == '4':
        print("👋 Goodbye!")
        
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    main() 