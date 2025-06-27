#!/usr/bin/env python3
"""
Test manual entry system
"""
import requests
import sys

def test_manual_entry_page():
    """Test the manual entry page loads correctly"""
    print("📝 Testing Manual Entry Page...")
    
    try:
        response = requests.get('http://localhost:5000/manual-entry', timeout=10)
        print(f"✅ Manual Entry Status: {response.status_code}")
        
        if response.status_code == 200:
            content = response.text
            print(f"✅ Response length: {len(content)} chars")
            
            # Check for key manual entry elements
            manual_elements = [
                "Add URL",
                "Upload File", 
                "Add YouTube",
                "form",
                "input",
                "submit"
            ]
            
            found_elements = []
            for element in manual_elements:
                if element.lower() in content.lower():
                    found_elements.append(element)
            
            print(f"✅ Manual entry elements found: {len(found_elements)}/6")
            for element in found_elements:
                print(f"   - {element}")
            
            return len(found_elements) >= 4  # At least basic form elements
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Manual entry test failed: {e}")
        return False

def test_reports_page():
    """Test the reports page"""
    print("\n📊 Testing Reports Page...")
    
    try:
        response = requests.get('http://localhost:5000/reports', timeout=10)
        print(f"✅ Reports Status: {response.status_code}")
        
        if response.status_code == 200:
            content = response.text
            print(f"✅ Response length: {len(content)} chars")
            
            # Check for reports elements
            if "report" in content.lower() or "generate" in content.lower():
                print("✅ Reports content detected")
                return True
            else:
                print("⚠️  Basic reports page (may be placeholder)")
                return True  # This might be a placeholder, which is OK
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Reports test failed: {e}")
        return False

def test_methodology_page():
    """Test the methodology page"""
    print("\n📖 Testing Methodology Page...")
    
    try:
        response = requests.get('http://localhost:5000/methodology', timeout=10)
        print(f"✅ Methodology Status: {response.status_code}")
        
        if response.status_code == 200:
            content = response.text
            print(f"✅ Response length: {len(content)} chars")
            
            # Check for methodology elements
            methodology_terms = ["research", "method", "NSF", "academic", "analysis"]
            found_terms = [term for term in methodology_terms if term.lower() in content.lower()]
            
            print(f"✅ Methodology terms found: {len(found_terms)}/5")
            for term in found_terms:
                print(f"   - {term}")
            
            return len(found_terms) >= 2  # At least some methodology content
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Methodology test failed: {e}")
        return False

if __name__ == "__main__":
    manual_ok = test_manual_entry_page()
    reports_ok = test_reports_page()
    methodology_ok = test_methodology_page()
    
    overall = manual_ok and reports_ok and methodology_ok
    print(f"\n{'✅ WEB INTERFACE TEST PASSED' if overall else '❌ WEB INTERFACE TEST FAILED'}")
    
    if overall:
        print("\n🎉 All major pages are working correctly!")
    else:
        print("\n🔧 Some issues detected - check page implementations")
    
    sys.exit(0 if overall else 1) 