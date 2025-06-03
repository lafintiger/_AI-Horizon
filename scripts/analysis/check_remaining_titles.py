#!/usr/bin/env python3
"""
Check Remaining Generic Titles
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from aih.utils.database import DatabaseManager
import json

def check_generic_titles():
    """Check how many entries still have generic titles."""
    
    db = DatabaseManager()
    artifacts = db.get_artifacts()
    
    generic_titles = []
    for artifact in artifacts:
        title = artifact.get('title', '')
        if title.startswith('AI Cybersecurity Impact Analysis'):
            generic_titles.append({
                'id': artifact['id'],
                'title': title,
                'url': artifact.get('url', ''),
                'source_type': artifact.get('source_type', '')
            })
    
    print(f'Found {len(generic_titles)} entries with generic titles:')
    for i, entry in enumerate(generic_titles[:10]):
        print(f'{i+1:2d}. {entry["title"][:60]}...')
        print(f'    URL: {entry["url"][:70]}...')
        print()
    
    if len(generic_titles) > 10:
        print(f'... and {len(generic_titles) - 10} more')
    
    return generic_titles

if __name__ == "__main__":
    check_generic_titles() 