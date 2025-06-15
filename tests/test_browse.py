#!/usr/bin/env python3
"""
Test browse entries page with quality scoring
"""
import requests
import sys

def test_browse_entries():
    try:
        response = requests.get('http://localhost:5000/browse_entries', timeout=10)
        print(f"✅ Browse Entries Status: {response.status_code}")
        
        if response.status_code == 200:
            content = response.text
            print(f"✅ Response length: {len(content)} chars")
            
            # Check for quality indicators
            quality_indicators = [
                "🟢",  # Excellent badge
                "🟡",  # Good badge  
                "🟠",  # Fair badge
                "🔴",  # Poor badge
                "Quality Score",
                "Sort by Quality"
            ]
            
            found_indicators = []
            for indicator in quality_indicators:
                if indicator in content:
                    found_indicators.append(indicator)
            
            print(f"✅ Quality indicators found: {len(found_indicators)}/6")
            for indicator in found_indicators:
                print(f"   - {indicator}")
            
            # Check for document entries 
            if "artifact-entry" in content or "document" in content.lower():
                print("✅ Document entries detected")
            else:
                print("⚠️  No document entries detected")
            
            return len(found_indicators) >= 3  # At least some quality features
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Browse entries test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_browse_entries()
    print(f"\n{'✅ BROWSE ENTRIES TEST PASSED' if success else '❌ BROWSE ENTRIES TEST FAILED'}")
    sys.exit(0 if success else 1) 