#!/usr/bin/env python3
"""
System Health Monitor for AI-Horizon
Prevents regressions by checking critical system components
"""

import os
import sys
import json
import requests
import importlib.util
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

class HealthMonitor:
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.checks_passed = 0
        self.checks_total = 0
        
    def log_issue(self, category: str, message: str, severity: str = "ERROR"):
        """Log an issue with the system"""
        issue = {
            "category": category,
            "message": message,
            "severity": severity,
            "timestamp": datetime.now().isoformat()
        }
        
        if severity == "ERROR":
            self.issues.append(issue)
        else:
            self.warnings.append(issue)
            
        print(f"❌ {severity}: [{category}] {message}")
    
    def log_success(self, category: str, message: str):
        """Log a successful check"""
        self.checks_passed += 1
        print(f"✅ PASS: [{category}] {message}")
    
    def run_check(self, check_func, category: str, description: str):
        """Run a health check function"""
        self.checks_total += 1
        try:
            result = check_func()
            if result is True:
                self.log_success(category, description)
            elif isinstance(result, str):
                self.log_success(category, f"{description} - {result}")
            else:
                self.log_issue(category, f"{description} - Check returned False")
        except Exception as e:
            self.log_issue(category, f"{description} - {str(e)}")
    
    def check_library_versions(self) -> bool:
        """Check that critical libraries are at correct versions"""
        critical_libs = {
            'anthropic': '0.40.0',  # Minimum version to avoid 'proxies' issue
            'openai': '1.0.0',     # Minimum modern OpenAI version
            'flask': '2.0.0',      # Modern Flask
            'requests': '2.25.0'   # Stable requests
        }
        
        for lib_name, min_version in critical_libs.items():
            try:
                spec = importlib.util.find_spec(lib_name)
                if spec is None:
                    self.log_issue("LIBRARIES", f"{lib_name} not installed")
                    continue
                    
                module = importlib.import_module(lib_name)
                if hasattr(module, '__version__'):
                    version = module.__version__
                    # Simple version comparison (works for semantic versioning)
                    if version.split('.') < min_version.split('.'):
                        self.log_issue("LIBRARIES", 
                                     f"{lib_name} version {version} is below minimum {min_version}")
                    else:
                        self.log_success("LIBRARIES", f"{lib_name} {version} ✓")
                else:
                    self.log_issue("LIBRARIES", f"{lib_name} version unknown")
            except Exception as e:
                self.log_issue("LIBRARIES", f"Error checking {lib_name}: {e}")
        
        return len([i for i in self.issues if i['category'] == 'LIBRARIES']) == 0
    
    def check_api_keys(self) -> bool:
        """Check that required API keys are set"""
        required_keys = ['ANTHROPIC_API_KEY', 'OPENAI_API_KEY']
        optional_keys = ['PERPLEXITY_API_KEY']
        
        missing_required = []
        missing_optional = []
        
        for key in required_keys:
            value = os.getenv(key)
            if not value:
                missing_required.append(key)
            elif len(value) < 10:  # Basic sanity check
                self.log_issue("API_KEYS", f"{key} appears to be invalid (too short)")
            else:
                self.log_success("API_KEYS", f"{key} is set")
        
        for key in optional_keys:
            if not os.getenv(key):
                missing_optional.append(key)
            else:
                self.log_success("API_KEYS", f"{key} is set")
        
        if missing_required:
            self.log_issue("API_KEYS", f"Required API keys missing: {', '.join(missing_required)}")
        
        if missing_optional:
            self.log_issue("API_KEYS", f"Optional API keys missing: {', '.join(missing_optional)}", "WARNING")
        
        return len(missing_required) == 0
    
    def check_flask_routes(self) -> bool:
        """Check that critical Flask routes are defined"""
        try:
            # Import the main app to check routes
            sys.path.append('.')
            import status_server
            app = status_server.app
            
            required_routes = [
                '/chat',
                '/api/chat',
                '/api/database_stats',
                '/login',
                '/logout',
                '/'
            ]
            
            # Get all registered routes
            registered_routes = []
            for rule in app.url_map.iter_rules():
                registered_routes.append(rule.rule)
            
            missing_routes = []
            for route in required_routes:
                if route not in registered_routes:
                    missing_routes.append(route)
                else:
                    self.log_success("FLASK_ROUTES", f"Route {route} is registered")
            
            if missing_routes:
                self.log_issue("FLASK_ROUTES", f"Missing routes: {', '.join(missing_routes)}")
                return False
            
            return True
            
        except Exception as e:
            self.log_issue("FLASK_ROUTES", f"Error checking Flask routes: {e}")
            return False
    
    def check_template_files(self) -> bool:
        """Check that critical template files exist"""
        template_dir = Path('templates')
        required_templates = [
            'base.html',
            'chat.html',
            'login.html',
            'status.html'
        ]
        
        missing_templates = []
        for template in required_templates:
            template_path = template_dir / template
            if not template_path.exists():
                missing_templates.append(template)
            else:
                self.log_success("TEMPLATES", f"Template {template} exists")
        
        if missing_templates:
            self.log_issue("TEMPLATES", f"Missing templates: {', '.join(missing_templates)}")
            return False
        
        return True
    
    def check_database_connection(self) -> bool:
        """Check database connectivity"""
        try:
            from aih.utils.database import DatabaseManager
            db = DatabaseManager()
            stats = db.get_database_stats()
            self.log_success("DATABASE", f"Connected - {stats['total_articles']} articles")
            return True
        except Exception as e:
            self.log_issue("DATABASE", f"Database connection failed: {e}")
            return False
    
    def check_chat_system_init(self) -> bool:
        """Check that chat system can initialize"""
        try:
            from aih.chat.rag_chat import RAGChatSystem
            # Try to initialize with Claude (most common)
            if os.getenv('ANTHROPIC_API_KEY'):
                rag = RAGChatSystem(model="claude-3-5-sonnet-20241022")
                self.log_success("CHAT_SYSTEM", "RAG system initialized with Claude")
            elif os.getenv('OPENAI_API_KEY'):
                rag = RAGChatSystem(model="gpt-4o")
                self.log_success("CHAT_SYSTEM", "RAG system initialized with OpenAI")
            else:
                self.log_issue("CHAT_SYSTEM", "No API keys available for chat system")
                return False
            return True
        except Exception as e:
            self.log_issue("CHAT_SYSTEM", f"Chat system initialization failed: {e}")
            return False
    
    def check_server_startup(self, host="127.0.0.1", port=8000) -> bool:
        """Check if server can start and respond (optional - requires running server)"""
        try:
            response = requests.get(f"http://{host}:{port}/api/database_stats", timeout=5)
            if response.status_code == 200:
                self.log_success("SERVER", "Server is responding to requests")
                return True
            else:
                self.log_issue("SERVER", f"Server returned {response.status_code}", "WARNING")
                return False
        except requests.exceptions.RequestException:
            self.log_issue("SERVER", "Server not running or not accessible", "WARNING")
            return False
    
    def run_full_health_check(self, check_server=False) -> Dict[str, Any]:
        """Run all health checks"""
        print("🔍 Running AI-Horizon System Health Check...")
        print("=" * 60)
        
        # Core system checks
        self.run_check(self.check_library_versions, "LIBRARIES", "Library versions")
        self.run_check(self.check_api_keys, "API_KEYS", "API key configuration")
        self.run_check(self.check_template_files, "TEMPLATES", "Template files")
        self.run_check(self.check_database_connection, "DATABASE", "Database connection")
        self.run_check(self.check_flask_routes, "FLASK_ROUTES", "Flask routes")
        self.run_check(self.check_chat_system_init, "CHAT_SYSTEM", "Chat system initialization")
        
        # Optional server check
        if check_server:
            self.run_check(self.check_server_startup, "SERVER", "Server accessibility")
        
        # Generate report
        print("\n" + "=" * 60)
        print(f"📊 HEALTH CHECK RESULTS")
        print("=" * 60)
        print(f"✅ Checks Passed: {self.checks_passed}/{self.checks_total}")
        print(f"❌ Issues Found: {len(self.issues)}")
        print(f"⚠️  Warnings: {len(self.warnings)}")
        
        if self.issues:
            print(f"\n🚨 CRITICAL ISSUES:")
            for issue in self.issues:
                print(f"   • [{issue['category']}] {issue['message']}")
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"   • [{warning['category']}] {warning['message']}")
        
        # Overall status
        if len(self.issues) == 0:
            print(f"\n🎉 SYSTEM HEALTHY - All critical checks passed!")
            status = "HEALTHY"
        elif len(self.issues) <= 2:
            print(f"\n⚠️  SYSTEM DEGRADED - Some issues found but system may function")
            status = "DEGRADED"
        else:
            print(f"\n🚨 SYSTEM UNHEALTHY - Multiple critical issues found")
            status = "UNHEALTHY"
        
        # Save results
        results = {
            "timestamp": datetime.now().isoformat(),
            "status": status,
            "checks_passed": self.checks_passed,
            "checks_total": self.checks_total,
            "issues": self.issues,
            "warnings": self.warnings
        }
        
        # Save to file
        results_file = Path("system_health_results.json")
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\n📄 Results saved to: {results_file}")
        
        return results

def main():
    """Main entry point"""
    import argparse
    parser = argparse.ArgumentParser(description="AI-Horizon System Health Monitor")
    parser.add_argument("--check-server", action="store_true", 
                       help="Also check if server is running and accessible")
    parser.add_argument("--host", default="127.0.0.1", 
                       help="Server host to check (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, 
                       help="Server port to check (default: 8000)")
    
    args = parser.parse_args()
    
    monitor = HealthMonitor()
    results = monitor.run_full_health_check(check_server=args.check_server)
    
    # Exit with appropriate code
    if results["status"] == "HEALTHY":
        sys.exit(0)
    elif results["status"] == "DEGRADED":
        sys.exit(1)
    else:
        sys.exit(2)

if __name__ == "__main__":
    main() 