#!/usr/bin/env python3
"""
Final Report Generation and Viewing Test

Comprehensive test to verify that the intelligence report system is working correctly.
This test will validate both student and web report generation and viewing.
"""

import subprocess
import sys
import requests
import json
from pathlib import Path
import time

def test_direct_student_report():
    """Test student report generation directly."""
    print("🎓 Testing Student Report Generation (Direct)")
    print("-" * 50)
    
    result = subprocess.run(
        [sys.executable, "scripts/generate_student_report.py"],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).parent)
    )
    
    if result.returncode == 0:
        output_lines = result.stdout.strip().split('\n')
        filepath = None
        
        # Look for clean filepath output
        for line in output_lines:
            if line.startswith('[FILEPATH]'):
                filepath = line.replace('[FILEPATH]', '').strip()
                break
        
        if filepath and Path(filepath).exists():
            print(f"✅ Student report generated: {filepath}")
            print(f"📄 File size: {Path(filepath).stat().st_size} bytes")
            return filepath
        else:
            print(f"❌ Student report generation failed - filepath: {filepath}")
            return None
    else:
        print(f"❌ Student report script failed: {result.stderr}")
        return None

def test_direct_web_report():
    """Test web report generation directly."""
    print("\n🌐 Testing Web Report Generation (Direct)")
    print("-" * 50)
    
    result = subprocess.run(
        [sys.executable, "scripts/generate_web_report.py"],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).parent)
    )
    
    if result.returncode == 0:
        output_lines = result.stdout.strip().split('\n')
        filepath = None
        
        # Look for clean filepath output
        for line in output_lines:
            if line.startswith('[FILEPATH]'):
                filepath = line.replace('[FILEPATH]', '').strip()
                break
        
        if filepath and Path(filepath).exists():
            print(f"✅ Web report generated: {filepath}")
            print(f"📄 File size: {Path(filepath).stat().st_size} bytes")
            return filepath
        else:
            print(f"❌ Web report generation failed - filepath: {filepath}")
            return None
    else:
        print(f"❌ Web report script failed: {result.stderr}")
        return None

def test_report_viewing(filepath, report_type):
    """Test viewing a report through the web interface."""
    print(f"\n👁️ Testing {report_type} Report Viewing")
    print("-" * 50)
    
    if not filepath:
        print("❌ No filepath to test")
        return False
    
    import urllib.parse
    encoded_path = urllib.parse.quote(filepath)
    
    try:
        response = requests.get(
            f"http://localhost:5000/api/view_report?path={encoded_path}",
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"✅ Report viewing successful")
            print(f"📊 Response length: {len(response.text):,} characters")
            print(f"📄 Content type: {response.headers.get('content-type')}")
            return True
        else:
            print(f"❌ View failed (Status {response.status_code}): {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error viewing report: {e}")
        return False

def test_server_api():
    """Test report generation through the server API."""
    print("\n🖥️ Testing Server API Report Generation")
    print("-" * 50)
    
    # Test if server is running
    try:
        response = requests.get("http://localhost:5000/api/status", timeout=5)
        if response.status_code != 200:
            print("❌ Server not responding properly")
            return None, None
    except:
        print("❌ Server not running - please start the server first")
        return None, None
    
    print("✅ Server is running")
    
    # Test student report generation
    try:
        print("📊 Generating student report via API...")
        response = requests.post(
            "http://localhost:5000/api/generate_student_report",
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            student_filepath = data.get('filepath')
            print(f"✅ Student report API: {student_filepath}")
        else:
            print(f"❌ Student report API failed: {response.text}")
            student_filepath = None
            
    except Exception as e:
        print(f"❌ Student report API error: {e}")
        student_filepath = None
    
    # Test web report generation  
    try:
        print("📊 Generating web report via API...")
        response = requests.post(
            "http://localhost:5000/api/generate_web_report",
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            web_filepath = data.get('filepath')
            print(f"✅ Web report API: {web_filepath}")
        else:
            print(f"❌ Web report API failed: {response.text}")
            web_filepath = None
            
    except Exception as e:
        print(f"❌ Web report API error: {e}")
        web_filepath = None
    
    return student_filepath, web_filepath

def main():
    """Run comprehensive report system test."""
    print("🚀 AI-Horizon Intelligence Report System Test")
    print("=" * 60)
    
    results = {
        "direct_student": False,
        "direct_web": False,
        "view_student": False,
        "view_web": False,
        "api_student": False,
        "api_web": False,
        "api_view_student": False,
        "api_view_web": False
    }
    
    # Test 1: Direct script execution
    student_filepath = test_direct_student_report()
    results["direct_student"] = student_filepath is not None
    
    web_filepath = test_direct_web_report()
    results["direct_web"] = web_filepath is not None
    
    # Test 2: Report viewing for direct generation
    if student_filepath:
        results["view_student"] = test_report_viewing(student_filepath, "Student")
    
    if web_filepath:
        results["view_web"] = test_report_viewing(web_filepath, "Web")
    
    # Test 3: Server API generation and viewing
    api_student_filepath, api_web_filepath = test_server_api()
    results["api_student"] = api_student_filepath is not None
    results["api_web"] = api_web_filepath is not None
    
    # Test 4: API report viewing
    if api_student_filepath:
        results["api_view_student"] = test_report_viewing(api_student_filepath, "API Student")
    
    if api_web_filepath:
        results["api_view_web"] = test_report_viewing(api_web_filepath, "API Web")
    
    # Summary
    print("\n📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    print(f"📈 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print()
    
    test_categories = [
        ("Direct Script Generation", ["direct_student", "direct_web"]),
        ("Direct Report Viewing", ["view_student", "view_web"]),
        ("Server API Generation", ["api_student", "api_web"]),
        ("API Report Viewing", ["api_view_student", "api_view_web"])
    ]
    
    for category, tests in test_categories:
        category_passed = sum(1 for t in tests if results.get(t, False))
        category_total = len(tests)
        status = "✅" if category_passed == category_total else "⚠️" if category_passed > 0 else "❌"
        print(f"{status} {category}: {category_passed}/{category_total}")
    
    print()
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - Intelligence report system is working correctly!")
    elif passed >= total * 0.8:
        print("✅ MOSTLY WORKING - Minor issues need attention")
        if not results["api_student"] or not results["api_web"]:
            print("💡 Note: Server needs restart to apply latest fixes")
    else:
        print("❌ SIGNIFICANT ISSUES - System needs debugging")
    
    print()
    print("📋 Files generated in this test:")
    print(f"   Student: {student_filepath}")
    print(f"   Web: {web_filepath}")
    if api_student_filepath:
        print(f"   API Student: {api_student_filepath}")
    if api_web_filepath:
        print(f"   API Web: {api_web_filepath}")

if __name__ == "__main__":
    main() 