#!/usr/bin/env python3
"""Quick status check script."""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from aih.utils.database import DatabaseManager

def main():
    db = DatabaseManager()
    
    # Get all artifacts
    artifacts = db.get_artifacts()
    
    print(f"Current Database Status:")
    print(f"Total artifacts: {len(artifacts)}")
    
    if artifacts:
        print("\nRecent artifacts:")
        for i, artifact in enumerate(artifacts[-5:], 1):
            title = artifact.get('title', 'No title')[:60]
            url = artifact.get('url', 'No URL')[:50]
            print(f"  {i}. {title}...")
            print(f"     URL: {url}...")
    else:
        print("No artifacts found in database.")
    
    return 0

if __name__ == "__main__":
    main() 