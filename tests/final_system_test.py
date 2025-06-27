#!/usr/bin/env python3
"""
Final comprehensive system test
"""
import requests
import sys
import time

def test_all_endpoints():
    """Test all key endpoints quickly"""
    print("🧪 Final System Test - Testing All Key Endpoints...")
    
    endpoints = [
        ('/', 'Dashboard'),
        ('/browse_entries', 'Browse Entries'),
        ('/manual-entry', 'Manual Entry'),
        ('/reports', 'Reports'),
        ('/methodology', 'Methodology'),
        ('/cost-analysis', 'Cost Analysis')
    ]
    
    results = {}
    
    for endpoint, name in endpoints:
        try:
            start_time = time.time()
            response = requests.get(f'http://localhost:5000{endpoint}', timeout=5)
            response_time = time.time() - start_time
            
            status = "✅ PASS" if response.status_code == 200 else "❌ FAIL"
            print(f"   {status} {name}: {response.status_code} ({response_time:.2f}s)")
            
            results[endpoint] = {
                'status': response.status_code,
                'time': response_time,
                'success': response.status_code == 200
            }
            
        except Exception as e:
            print(f"   ❌ FAIL {name}: {e}")
            results[endpoint] = {'success': False, 'error': str(e)}
    
    return results

def test_api_endpoints():
    """Test key API endpoints"""
    print("\n🔌 Testing API Endpoints...")
    
    api_endpoints = [
        ('/api/status', 'Status API'),
        ('/api/database_stats', 'Database Stats API')
    ]
    
    api_results = {}
    
    for endpoint, name in api_endpoints:
        try:
            response = requests.get(f'http://localhost:5000{endpoint}', timeout=5)
            status = "✅ PASS" if response.status_code == 200 else "❌ FAIL"
            print(f"   {status} {name}: {response.status_code}")
            
            api_results[endpoint] = response.status_code == 200
            
        except Exception as e:
            print(f"   ❌ FAIL {name}: {e}")
            api_results[endpoint] = False
    
    return api_results

def main():
    print("🚀 AI-Horizon System Test")
    print("=" * 50)
    
    # Test web endpoints
    web_results = test_all_endpoints()
    
    # Test API endpoints  
    api_results = test_api_endpoints()
    
    # Summary
    print("\n📊 Test Summary:")
    print("-" * 30)
    
    web_passed = sum(1 for r in web_results.values() if r.get('success', False))
    web_total = len(web_results)
    
    api_passed = sum(1 for r in api_results.values() if r)
    api_total = len(api_results)
    
    print(f"Web Pages: {web_passed}/{web_total} passed")
    print(f"API Endpoints: {api_passed}/{api_total} passed")
    
    overall_success = web_passed == web_total and api_passed == api_total
    
    if overall_success:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ System is ready for user testing")
        print("\n🌐 Access the application at: http://localhost:5000")
        print("📝 Main interface: http://localhost:5000/browse_entries")
    else:
        print("\n⚠️  Some tests failed - system may have issues")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 