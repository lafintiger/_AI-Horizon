#!/usr/bin/env python3
"""
Test quality scoring display in detail
"""
import requests
import sys
from aih.utils.database import DatabaseManager
from scripts.analysis.implement_quality_ranking import DocumentQualityRanker

def test_quality_backend():
    """Test quality scoring backend"""
    print("🧪 Testing Quality Scoring Backend...")
    
    try:
        db = DatabaseManager()
        artifacts = db.get_artifacts(limit=3)
        print(f"✅ Found {len(artifacts)} artifacts")
        
        ranker = DocumentQualityRanker()
        print("✅ Quality ranker initialized")
        
        for i, artifact in enumerate(artifacts):
            try:
                quality_score, detailed_scores = ranker.calculate_document_score(artifact)
                grade = (
                    'Excellent' if quality_score >= 0.8 else
                    'Good' if quality_score >= 0.6 else
                    'Fair' if quality_score >= 0.4 else 'Poor'
                )
                print(f"   Artifact {i+1}: Score={quality_score:.3f}, Grade={grade}")
            except Exception as e:
                print(f"   Artifact {i+1}: Error calculating score: {e}")
        
        return True
    except Exception as e:
        print(f"❌ Backend test failed: {e}")
        return False

def test_browse_page_content():
    """Test the actual browse page content"""
    print("\n🌐 Testing Browse Page Content...")
    
    try:
        response = requests.get('http://localhost:5000/browse_entries', timeout=10)
        if response.status_code != 200:
            print(f"❌ Status code: {response.status_code}")
            return False
            
        content = response.text
        print(f"✅ Page loaded ({len(content)} chars)")
        
        # Check for specific quality elements
        quality_checks = {
            "quality-badge": content.count('class="quality-badge'),
            "quality-score": content.count('quality_score'),
            "quality-grade": content.count('quality_grade'),
            "Excellent": content.count('Excellent'),
            "Good": content.count('Good'),
            "Fair": content.count('Fair'),
            "Poor": content.count('Poor'),
            "Quality Score": content.count('Quality Score'),
        }
        
        print("🔍 Quality Element Analysis:")
        for element, count in quality_checks.items():
            status = "✅" if count > 0 else "❌"
            print(f"   {status} {element}: {count} occurrences")
        
        # Look for the specific HTML structure we expect
        if 'quality-badge' in content and any(grade in content for grade in ['Excellent', 'Good', 'Fair', 'Poor']):
            print("✅ Quality display structure detected")
            return True
        else:
            print("❌ Quality display structure missing")
            
            # Let's check what quality-related content is actually there
            import re
            quality_lines = []
            for line in content.split('\n'):
                if 'quality' in line.lower():
                    quality_lines.append(line.strip())
            
            if quality_lines:
                print("\n📝 Quality-related lines found:")
                for i, line in enumerate(quality_lines[:5]):  # Show first 5
                    print(f"   {i+1}. {line[:100]}...")
            
            return False
            
    except Exception as e:
        print(f"❌ Browse page test failed: {e}")
        return False

if __name__ == "__main__":
    backend_ok = test_quality_backend()
    frontend_ok = test_browse_page_content()
    
    overall = backend_ok and frontend_ok
    print(f"\n{'✅ QUALITY DISPLAY TEST PASSED' if overall else '❌ QUALITY DISPLAY TEST FAILED'}")
    
    if not overall:
        print("\n🔧 Suggested fixes:")
        if not backend_ok:
            print("   - Check quality ranking system imports and database")
        if not frontend_ok:
            print("   - Check template rendering and quality score passing")
    
    sys.exit(0 if overall else 1) 