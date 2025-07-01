#!/usr/bin/env python3
"""
AI-Horizon System Check Script
Comprehensive health check for all system components
"""

import os
import sys
import json
import time
import sqlite3
import requests
from datetime import datetime
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class SystemChecker:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "UNKNOWN",
            "checks": {},
            "summary": {
                "total_checks": 0,
                "passed": 0,
                "failed": 0,
                "warnings": 0
            }
        }
        
        # Test credentials for login
        self.test_credentials = {
            "username": "admin",
            "password": "admin123"
        }
        
        self.session = requests.Session()
        self.session.timeout = 10
        
    def check_result(self, category, test_name, status, message="", details=None):
        """Record a check result"""
        if category not in self.results["checks"]:
            self.results["checks"][category] = {}
            
        self.results["checks"][category][test_name] = {
            "status": status,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        }
        
        self.results["summary"]["total_checks"] += 1
        if status == "PASS":
            self.results["summary"]["passed"] += 1
        elif status == "FAIL":
            self.results["summary"]["failed"] += 1
        elif status == "WARN":
            self.results["summary"]["warnings"] += 1
            
    def check_server_connectivity(self):
        """Test if the server is running and accessible"""
        print("🔍 Checking server connectivity...")
        
        # Check if server process is running
        try:
            import subprocess
            result = subprocess.run(['pgrep', '-f', 'status_server.py'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                pids = result.stdout.strip().split('\n')
                self.check_result("connectivity", "process_running", "PASS", 
                                f"Server process found (PID: {', '.join(pids)})")
            else:
                self.check_result("connectivity", "process_running", "WARN", 
                                "No status_server.py process found")
        except Exception as e:
            self.check_result("connectivity", "process_running", "WARN", 
                            f"Could not check process: {str(e)}")
        
        # Test HTTP connectivity
        try:
            response = self.session.get(f"{self.base_url}/", allow_redirects=False)
            if response.status_code in [200, 302]:
                self.check_result("connectivity", "server_responding", "PASS", 
                                f"Server responding (HTTP {response.status_code})")
                return True
            else:
                self.check_result("connectivity", "server_responding", "FAIL", 
                                f"Server returned HTTP {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            self.check_result("connectivity", "server_responding", "FAIL", 
                            f"Cannot connect to server at {self.base_url}")
            return False
        except Exception as e:
            self.check_result("connectivity", "server_responding", "FAIL", 
                            f"Connection error: {str(e)}")
            return False
    
    def check_database_connectivity(self):
        """Test database connectivity and basic queries"""
        print("🔍 Checking database connectivity...")
        
        db_path = "data/content.db"
        
        # Check if database file exists
        if not os.path.exists(db_path):
            self.check_result("database", "file_exists", "FAIL", 
                            f"Database file not found: {db_path}")
            return False
        
        # Check if database file is empty
        db_size = os.path.getsize(db_path)
        if db_size == 0:
            self.check_result("database", "file_exists", "WARN", 
                            f"Database file exists but is empty (0 bytes): {db_path}")
            self.check_result("database", "initialization", "FAIL", 
                            "Database not initialized - run server to initialize")
            return False
        
        self.check_result("database", "file_exists", "PASS", 
                        f"Database file exists ({db_size} bytes): {db_path}")
        
        try:
            # Test database connection with timeout
            conn = sqlite3.connect(db_path, timeout=10)
            cursor = conn.cursor()
            
            # Test basic query
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]
            
            if table_count == 0:
                self.check_result("database", "connectivity", "WARN", 
                                f"Database accessible but no tables found")
                conn.close()
                return False
            
            self.check_result("database", "connectivity", "PASS", 
                            f"Database accessible with {table_count} tables")
            
            # List actual tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            # Check for common tables (articles might be named differently)
            article_tables = [t for t in tables if 'article' in t.lower() or 'content' in t.lower() or 'artifact' in t.lower()]
            
            if article_tables:
                # Try the first article-like table
                table_name = article_tables[0]
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                record_count = cursor.fetchone()[0]
                
                self.check_result("database", "data_table", "PASS", 
                                f"Data table '{table_name}' accessible with {record_count} records")
            else:
                self.check_result("database", "data_table", "WARN", 
                                f"No article/content tables found. Available tables: {', '.join(tables)}")
            
            conn.close()
            return True
            
        except Exception as e:
            self.check_result("database", "connectivity", "FAIL", 
                            f"Database error: {str(e)}")
            return False
    
    def check_api_keys(self):
        """Test API key validity"""
        print("🔍 Checking API keys...")
        
        # Check environment variables
        anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        openai_key = os.getenv('OPENAI_API_KEY')
        perplexity_key = os.getenv('PERPLEXITY_API_KEY')
        
        if not anthropic_key:
            self.check_result("api_keys", "anthropic_env", "FAIL", 
                            "ANTHROPIC_API_KEY not set in environment")
        else:
            self.check_result("api_keys", "anthropic_env", "PASS", 
                            "ANTHROPIC_API_KEY found in environment")
            
        if not openai_key:
            self.check_result("api_keys", "openai_env", "FAIL", 
                            "OPENAI_API_KEY not set in environment")
        else:
            self.check_result("api_keys", "openai_env", "PASS", 
                            "OPENAI_API_KEY found in environment")
            
        if not perplexity_key:
            self.check_result("api_keys", "perplexity_env", "WARN", 
                            "PERPLEXITY_API_KEY not set (optional for some features)")
        else:
            self.check_result("api_keys", "perplexity_env", "PASS", 
                            "PERPLEXITY_API_KEY found in environment")
    
    def login_to_system(self):
        """Attempt to login to the system"""
        print("🔍 Testing authentication...")
        
        try:
            # Get login page
            response = self.session.get(f"{self.base_url}/login")
            if response.status_code != 200:
                self.check_result("authentication", "login_page", "FAIL", 
                                f"Login page not accessible (HTTP {response.status_code})")
                return False
            
            self.check_result("authentication", "login_page", "PASS", 
                            "Login page accessible")
            
            # Try multiple credential combinations
            credential_sets = [
                {"username": "admin", "password": "admin123"},
                {"username": "admin", "password": "admin"},
                {"username": "test", "password": "test"},
                {"username": "user", "password": "password"}
            ]
            
            for creds in credential_sets:
                response = self.session.post(f"{self.base_url}/login", data=creds)
                
                if response.status_code == 302:
                    # Check if redirect is to home page (successful login)
                    if response.headers.get('Location', '').endswith('/'):
                        self.check_result("authentication", "login_success", "PASS", 
                                        f"Successfully logged in with {creds['username']}")
                        return True
                elif response.status_code == 200 and len(response.text) > 1000:
                    # Likely logged in and showing dashboard content
                    self.check_result("authentication", "login_success", "PASS", 
                                    f"Successfully logged in with {creds['username']}")
                    return True
            
            # If none worked, it's a warning not a failure
            self.check_result("authentication", "login_success", "WARN", 
                            "Login system working but test credentials failed. Manual login may be required.")
            return False
                
        except Exception as e:
            self.check_result("authentication", "login_process", "FAIL", 
                            f"Login process error: {str(e)}")
            return False
    
    def check_main_pages(self):
        """Test accessibility of main pages (core pages only)"""
        print("🔍 Checking main pages...")
        
        # Test only core pages to speed up the check
        core_pages = {
            "home": "/",
            "chat": "/chat",
            "browse_entries": "/browse_entries",
            "analysis": "/analysis",
            "methodology": "/methodology"
        }
        
        for page_name, path in core_pages.items():
            try:
                response = self.session.get(f"{self.base_url}{path}", timeout=10)
                if response.status_code == 200:
                    self.check_result("pages", page_name, "PASS", 
                                    f"Page accessible (HTTP {response.status_code})")
                elif response.status_code == 302:
                    self.check_result("pages", page_name, "PASS", 
                                    f"Page redirects properly (HTTP {response.status_code})")
                else:
                    self.check_result("pages", page_name, "FAIL", 
                                    f"Page not accessible (HTTP {response.status_code})")
                
                # Small delay between page requests
                time.sleep(0.3)
                    
            except Exception as e:
                self.check_result("pages", page_name, "FAIL", 
                                f"Page error: {str(e)}")
    
    def check_api_endpoints(self):
        """Test API endpoints (optimized for speed)"""
        print("🔍 Checking API endpoints...")
        
        # Test only essential endpoints to avoid slowdown
        essential_endpoints = {
            "database_stats": "/api/database_stats",
            "stream": "/api/stream"
        }
        
        for endpoint_name, path in essential_endpoints.items():
            try:
                # Add timeout to prevent hanging
                response = self.session.get(f"{self.base_url}{path}", timeout=10)
                if response.status_code == 200:
                    self.check_result("api_endpoints", endpoint_name, "PASS", 
                                    f"API endpoint accessible (HTTP {response.status_code})")
                elif response.status_code == 302:
                    self.check_result("api_endpoints", endpoint_name, "WARN", 
                                    f"API endpoint redirects (HTTP {response.status_code})")
                else:
                    self.check_result("api_endpoints", endpoint_name, "FAIL", 
                                    f"API endpoint not accessible (HTTP {response.status_code})")
                    
                # Add small delay between requests to prevent overload
                time.sleep(0.5)
                    
            except Exception as e:
                self.check_result("api_endpoints", endpoint_name, "FAIL", 
                                f"API endpoint error: {str(e)}")
        
        # Test one additional endpoint only if essentials pass
        if all(self.results["checks"].get("api_endpoints", {}).get(name, {}).get("status") == "PASS" 
               for name in essential_endpoints.keys()):
            try:
                response = self.session.get(f"{self.base_url}/api/visualization_data/quality", timeout=10)
                if response.status_code == 200:
                    self.check_result("api_endpoints", "visualization_data", "PASS", 
                                    "Visualization API working")
                else:
                    self.check_result("api_endpoints", "visualization_data", "WARN", 
                                    f"Visualization API returned HTTP {response.status_code}")
            except Exception as e:
                self.check_result("api_endpoints", "visualization_data", "WARN", 
                                f"Visualization API error: {str(e)}")
    
    def check_file_system(self):
        """Check important files and directories"""
        print("🔍 Checking file system...")
        
        important_paths = {
            "data_directory": "data/",
            "templates_directory": "templates/",
            "logs_directory": "logs/",
            "config_file": "config.env",
            "requirements_file": "requirements.txt",
            "main_server": "status_server.py"
        }
        
        for path_name, path in important_paths.items():
            if os.path.exists(path):
                self.check_result("filesystem", path_name, "PASS", 
                                f"Path exists: {path}")
            else:
                self.check_result("filesystem", path_name, "FAIL", 
                                f"Path missing: {path}")
    
    def check_llm_functionality(self):
        """Test LLM functionality through chat endpoint (optional)"""
        print("🔍 Testing LLM functionality...")
        
        # Check if API keys are present first
        if not (os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY")):
            self.check_result("llm", "chat_functionality", "SKIP", 
                            "No API keys found - skipping LLM test")
            return
        
        test_message = "Test"  # Shorter message for faster response
        
        try:
            chat_data = {
                "message": test_message,
                "model": "claude-3-5-sonnet-20241022"
            }
            
            # Use longer timeout for LLM requests but still limit it
            response = self.session.post(f"{self.base_url}/api/chat", 
                                       json=chat_data, 
                                       headers={"Content-Type": "application/json"},
                                       timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if "response" in result and result["response"]:
                    self.check_result("llm", "chat_functionality", "PASS", 
                                    "LLM chat functionality working")
                else:
                    self.check_result("llm", "chat_functionality", "WARN", 
                                    "LLM returned empty response")
            elif response.status_code == 401:
                self.check_result("llm", "chat_functionality", "WARN", 
                                "LLM API authentication failed - check API keys")
            else:
                self.check_result("llm", "chat_functionality", "FAIL", 
                                f"Chat API returned HTTP {response.status_code}")
                
        except Exception as e:
            if "timeout" in str(e).lower():
                self.check_result("llm", "chat_functionality", "WARN", 
                                "LLM test timed out - API may be slow")
            else:
                self.check_result("llm", "chat_functionality", "FAIL", 
                                f"LLM test error: {str(e)}")
    
    def check_predictive_analytics(self):
        """Test predictive analytics functionality (optional)"""
        print("🔍 Testing predictive analytics...")
        
        try:
            analytics_data = {
                "analysis_type": "industry",
                "timeframe": "6months"
            }
            
            response = self.session.post(f"{self.base_url}/api/predictive_analytics", 
                                       json=analytics_data,
                                       headers={"Content-Type": "application/json"},
                                       timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                if "analysis" in result:
                    self.check_result("analytics", "predictive_functionality", "PASS", 
                                    "Predictive analytics functionality working")
                else:
                    self.check_result("analytics", "predictive_functionality", "WARN", 
                                    "Predictive analytics returned incomplete response")
            elif response.status_code == 404:
                self.check_result("analytics", "predictive_functionality", "SKIP", 
                                "Predictive analytics endpoint not found")
            else:
                self.check_result("analytics", "predictive_functionality", "WARN", 
                                f"Predictive analytics API returned HTTP {response.status_code}")
                
        except Exception as e:
            if "timeout" in str(e).lower():
                self.check_result("analytics", "predictive_functionality", "WARN", 
                                "Predictive analytics test timed out")
            else:
                self.check_result("analytics", "predictive_functionality", "WARN", 
                                f"Predictive analytics test error: {str(e)}")
    
    def run_all_checks(self, fast_mode=False):
        """Run all system checks"""
        mode_text = "FAST MODE" if fast_mode else "FULL SYSTEM CHECK"
        print(f"🚀 Starting AI-Horizon {mode_text}...")
        print("=" * 60)
        
        # Core connectivity
        server_running = self.check_server_connectivity()
        if not server_running:
            print("❌ Server not running - skipping dependent checks")
            self.finalize_results()
            return self.results
        
        # Essential checks for fast mode
        self.check_database_connectivity()
        self.check_api_keys()
        
        if fast_mode:
            print("⚡ Fast mode - testing core functionality only...")
            # Skip authentication in fast mode
            self.check_api_endpoints()
            print("✅ Fast check complete!")
        else:
            # Full check mode
            logged_in = self.login_to_system()
            self.check_file_system()
            
            # Pages (only if logged in)
            if logged_in:
                self.check_main_pages()
                self.check_api_endpoints()
                self.check_llm_functionality()
                self.check_predictive_analytics()
            else:
                print("⚠️  Not logged in - skipping authenticated checks")
        
        self.finalize_results()
        return self.results
    
    def finalize_results(self):
        """Finalize and categorize overall results"""
        if self.results["summary"]["failed"] > 0:
            self.results["overall_status"] = "CRITICAL"
        elif self.results["summary"]["warnings"] > 0:
            self.results["overall_status"] = "WARNING"
        else:
            self.results["overall_status"] = "HEALTHY"
    
    def print_results(self):
        """Print formatted results"""
        print("\n" + "=" * 60)
        print("🏁 SYSTEM CHECK RESULTS")
        print("=" * 60)
        
        # Overall status
        status_emoji = {
            "HEALTHY": "✅",
            "WARNING": "⚠️",
            "CRITICAL": "❌",
            "UNKNOWN": "❓"
        }
        
        print(f"Overall Status: {status_emoji.get(self.results['overall_status'], '❓')} {self.results['overall_status']}")
        print(f"Total Checks: {self.results['summary']['total_checks']}")
        print(f"Passed: {self.results['summary']['passed']}")
        print(f"Failed: {self.results['summary']['failed']}")
        print(f"Warnings: {self.results['summary']['warnings']}")
        print(f"Timestamp: {self.results['timestamp']}")
        
        # Detailed results by category
        for category, checks in self.results["checks"].items():
            print(f"\n📋 {category.upper()}")
            print("-" * 40)
            
            for check_name, result in checks.items():
                status_icon = "✅" if result["status"] == "PASS" else "❌" if result["status"] == "FAIL" else "⚠️"
                print(f"  {status_icon} {check_name}: {result['message']}")
        
        # Add recommendations section
        self.print_recommendations()
    
    def print_recommendations(self):
        """Print actionable recommendations based on failed checks"""
        failed_checks = []
        warning_checks = []
        
        for category, checks in self.results["checks"].items():
            for check_name, result in checks.items():
                if result["status"] == "FAIL":
                    failed_checks.append((category, check_name, result["message"]))
                elif result["status"] == "WARN":
                    warning_checks.append((category, check_name, result["message"]))
        
        if failed_checks or warning_checks:
            print("\n🔧 RECOMMENDATIONS")
            print("=" * 60)
            
            if failed_checks:
                print("❌ CRITICAL ISSUES TO FIX:")
                for category, check, message in failed_checks:
                    if "database" in category.lower():
                        if "empty" in message or "not initialized" in message:
                            print("  • Start the server to initialize the database:")
                            print("    python status_server.py --host 0.0.0.0 --port 8000")
                        elif "no such table" in message:
                            print("  • Database schema issue - run database migration/setup")
                    elif "connectivity" in category.lower():
                        if "Cannot connect" in message:
                            print("  • Start the AI-Horizon server:")
                            print("    python status_server.py --host 0.0.0.0 --port 8000")
                    elif "api_keys" in category.lower():
                        print("  • Set missing API keys in environment:")
                        if "ANTHROPIC" in message:
                            print("    export ANTHROPIC_API_KEY='your-key-here'")
                        if "OPENAI" in message:
                            print("    export OPENAI_API_KEY='your-key-here'")
            
            if warning_checks:
                print("\n⚠️  WARNINGS TO ADDRESS:")
                for category, check, message in warning_checks:
                    if "authentication" in category.lower() and "credentials failed" in message:
                        print("  • Update test credentials or create test user account")
                    elif "perplexity" in message.lower():
                        print("  • PERPLEXITY_API_KEY is optional but recommended for data collection")
                    elif "process" in check.lower():
                        print("  • Server may be running but process not detectable")
            
            print("\n💡 GENERAL TIPS:")
            print("  • Make sure you're in the project root directory")
            print("  • Verify all environment variables are set")
            print("  • Check logs in logs/ directory for detailed error messages")
            print("  • Try running: python status_server.py --host 0.0.0.0 --port 8000")
    
    def save_results(self, filename=None):
        """Save results to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"system_check_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n💾 Results saved to: {filename}")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI-Horizon System Check")
    parser.add_argument("--url", default="http://localhost:8000", 
                       help="Base URL for the system (default: http://localhost:8000)")
    parser.add_argument("--save", action="store_true", 
                       help="Save results to JSON file")
    parser.add_argument("--output", help="Output filename for results")
    parser.add_argument("--fast", action="store_true", 
                       help="Run fast check (core functionality only)")
    
    args = parser.parse_args()
    
    # Create checker and run checks
    checker = SystemChecker(base_url=args.url)
    results = checker.run_all_checks(fast_mode=args.fast)
    
    # Print results
    checker.print_results()
    
    # Save results if requested
    if args.save:
        checker.save_results(args.output)
    
    # Exit with error code if critical issues found
    if results["overall_status"] == "CRITICAL":
        sys.exit(1)
    elif results["overall_status"] == "WARNING":
        sys.exit(2)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main() 