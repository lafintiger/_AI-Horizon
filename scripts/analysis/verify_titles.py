#!/usr/bin/env python3

from aih.utils.database import DatabaseManager

db = DatabaseManager()
artifacts = db.get_artifacts(limit=10)

print("=== TITLE VERIFICATION ===")
print("Checking first 10 artifacts for title quality:")

for i, artifact in enumerate(artifacts[:10]):
    title = artifact.get('title', 'No title')
    source_type = artifact.get('source_type', 'unknown')
    
    print(f"\n{i+1}. {title}")
    print(f"   Source: {source_type}")
    
    # Check if it's still a generic title
    if title.startswith('AI Cybersecurity Impact Analysis'):
        print("   ❌ Still has generic title")
    else:
        print("   ✅ Has proper title")

print("\n=== VERIFICATION COMPLETE ===") 