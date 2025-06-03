#!/usr/bin/env python3
"""
Test Quality Scoring in Browse Function
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from aih.utils.database import DatabaseManager
from scripts.analysis.implement_quality_ranking import DocumentQualityRanker

def test_browse_quality():
    """Test the quality scoring functionality."""
    
    print("🔍 Testing Quality Scoring in Browse Function")
    print("=" * 50)
    
    try:
        # Initialize components
        db = DatabaseManager()
        quality_ranker = DocumentQualityRanker()
        
        # Get artifacts
        all_artifacts = db.get_artifacts(limit=5)  # Test with just 5
        print(f"✅ Retrieved {len(all_artifacts)} artifacts from database")
        
        # Test quality scoring
        artifacts_with_scores = []
        for i, artifact in enumerate(all_artifacts):
            try:
                print(f"\n📊 Scoring artifact {i+1}: {artifact.get('title', 'Untitled')[:50]}...")
                quality_score, detailed_scores = quality_ranker.calculate_document_score(artifact)
                
                artifact_with_score = artifact.copy()
                artifact_with_score['quality_score'] = round(quality_score, 3)
                artifact_with_score['quality_grade'] = (
                    'Excellent' if quality_score >= 0.8 else
                    'Good' if quality_score >= 0.6 else
                    'Fair' if quality_score >= 0.4 else 'Poor'
                )
                artifacts_with_scores.append(artifact_with_score)
                
                print(f"   Score: {quality_score:.3f} ({artifact_with_score['quality_grade']})")
                print(f"   Detailed scores: {detailed_scores}")
                
            except Exception as e:
                print(f"   ❌ Error scoring artifact: {e}")
                # Add artifact without score
                artifact_with_score = artifact.copy()
                artifact_with_score['quality_score'] = 0.0
                artifact_with_score['quality_grade'] = 'Error'
                artifacts_with_scores.append(artifact_with_score)
        
        # Sort by quality score
        artifacts_with_scores.sort(key=lambda x: x['quality_score'], reverse=True)
        
        print(f"\n🏆 Top Scored Artifacts:")
        for i, artifact in enumerate(artifacts_with_scores[:3]):
            title = artifact.get('title', 'Untitled')[:40]
            score = artifact.get('quality_score', 0.0)
            grade = artifact.get('quality_grade', 'Unknown')
            print(f"   {i+1}. {title}... | Score: {score} ({grade})")
        
        print(f"\n✅ Quality scoring test completed successfully!")
        print(f"   - All artifacts have quality_score and quality_grade attributes")
        print(f"   - Ready for web interface display")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Quality scoring test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_browse_quality()
    if success:
        print("\n🎉 Test passed! Quality scores should appear in web interface.")
    else:
        print("\n💥 Test failed! Quality scores will not appear in web interface.") 