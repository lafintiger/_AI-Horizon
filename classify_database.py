#!/usr/bin/env python3
"""
Classify all artifacts in your database using local models.
This shows the real production power of your system!
"""

import asyncio
import sqlite3
from datetime import datetime
from aih.classify.local_classifier import LocalArtifactClassifier

async def classify_all_artifacts(limit=10):
    """Classify artifacts from your database."""
    print("🚀 AI-Horizon Database Classification")
    print("=" * 50)
    
    # Connect to database
    db = sqlite3.connect('data/aih_database.db')
    cursor = db.cursor()
    
    # Get unclassified artifacts
    cursor.execute("""
        SELECT id, title, content, source_type 
        FROM artifacts 
        WHERE id NOT IN (SELECT artifact_id FROM classifications)
        LIMIT ?
    """, (limit,))
    
    artifacts = cursor.fetchall()
    
    if not artifacts:
        print("✅ All artifacts are already classified!")
        cursor.execute("SELECT COUNT(*) FROM classifications")
        classified_count = cursor.fetchone()[0] 
        print(f"📊 Total classified artifacts: {classified_count}")
        return
    
    print(f"📊 Found {len(artifacts)} unclassified artifacts to process")
    print(f"💰 Cost: $0.00 (100% local processing)")
    print()
    
    # Initialize classifier
    classifier = LocalArtifactClassifier()
    
    start_time = datetime.now()
    
    for i, (artifact_id, title, content, source_type) in enumerate(artifacts, 1):
        print(f"🔍 Processing {i}/{len(artifacts)}: {title[:50]}...")
        print(f"   Source: {source_type}")
        
        try:
            # Classify
            classification_start = datetime.now()
            results = await classifier.classify_artifact(title, content)
            classification_time = (datetime.now() - classification_start).total_seconds()
            
            # Save to database
            for result in results:
                cursor.execute("""
                    INSERT INTO classifications 
                    (artifact_id, category, confidence, rationale, model_used, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    artifact_id,
                    result.category,
                    result.confidence,
                    result.rationale,
                    "llama3:latest",
                    datetime.now().isoformat()
                ))
                
                print(f"   ✅ Category: {result.category} (confidence: {result.confidence:.2f})")
                print(f"   ⏱️  Time: {classification_time:.2f}s")
            
            db.commit()
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            continue
    
    total_time = (datetime.now() - start_time).total_seconds()
    avg_time = total_time / len(artifacts)
    
    print(f"\n📊 Classification Complete!")
    print(f"   Total time: {total_time:.2f}s")
    print(f"   Average per artifact: {avg_time:.2f}s")
    print(f"   Throughput: {3600/avg_time:.0f} artifacts/hour")
    print(f"   Cost: $0.00 (100% local)")
    
    # Show classification summary
    cursor.execute("""
        SELECT category, COUNT(*) as count 
        FROM classifications 
        GROUP BY category 
        ORDER BY count DESC
    """)
    
    results = cursor.fetchall()
    print(f"\n📈 Classification Summary:")
    for category, count in results:
        print(f"   {category}: {count} artifacts")
    
    db.close()

if __name__ == "__main__":
    asyncio.run(classify_all_artifacts()) 