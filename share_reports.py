"""
AI-Horizon Report Sharing Server

Creates temporary shareable links for the HTML reports, similar to Gradio's sharing functionality.
Serves the reports locally and optionally creates public tunnels for remote access.
"""

import http.server
import socketserver
import webbrowser
import threading
import time
import subprocess
import sys
from pathlib import Path
from aih.config import get_data_path

class ReportHTTPServer:
    def __init__(self, port=5000):
        self.port = port
        self.server = None
        self.server_thread = None
        self.reports_dir = get_data_path("reports")
        
    def start_local_server(self):
        """Start local HTTP server to serve the reports."""
        try:
            # Change to reports directory to serve files
            import os
            original_dir = os.getcwd()
            os.chdir(self.reports_dir)
            
            handler = http.server.SimpleHTTPRequestHandler
            self.server = socketserver.TCPServer(("", self.port), handler)
            
            print(f"🌐 Starting local server at http://localhost:{self.port}")
            print(f"📁 Serving files from: {self.reports_dir}")
            
            # Start server in a separate thread
            self.server_thread = threading.Thread(target=self.server.serve_forever)
            self.server_thread.daemon = True
            self.server_thread.start()
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to start server: {e}")
            return False
    
    def stop_server(self):
        """Stop the local server."""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            print("🛑 Local server stopped")
    
    def check_ngrok_installed(self):
        """Check if ngrok is installed."""
        try:
            result = subprocess.run(['ngrok', '--version'], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def check_ngrok_auth(self):
        """Check if ngrok is authenticated."""
        try:
            result = subprocess.run(['ngrok', 'config', 'check'], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except Exception:
            return False
    
    def create_ngrok_tunnel(self):
        """Create ngrok tunnel for public access."""
        if not self.check_ngrok_installed():
            print("❌ ngrok not found. Please install ngrok:")
            print("   1. Download from: https://ngrok.com/download")
            print("   2. Create free account and get auth token")
            print("   3. Run: ngrok authtoken YOUR_TOKEN")
            return None, None
        
        try:
            print("🔗 Creating ngrok tunnel with reserved domain...")
            
            # Use the specific ngrok command with reserved domain
            ngrok_url = "mighty-legally-bat.ngrok-free.app"
            public_url = f"https://{ngrok_url}"
            
            # Start ngrok tunnel with specific URL
            process = subprocess.Popen(
                ['ngrok', 'http', f'--url={ngrok_url}', str(self.port)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for ngrok to start
            print("⏳ Waiting for ngrok to establish tunnel...")
            time.sleep(5)
            
            # Check if the process is still running (no immediate errors)
            if process.poll() is None:
                print(f"✅ Public URL created: {public_url}")
                print(f"🔗 Dashboard: {public_url}/ai_horizon_analysis_report.html")
                print(f"📋 Methodology: {public_url}/process_methodology.html")
                return public_url, process
            else:
                # Process ended, check for errors
                stdout, stderr = process.communicate()
                print("❌ ngrok tunnel failed to start")
                if stderr:
                    print(f"Error: {stderr}")
                if stdout:
                    print(f"Output: {stdout}")
                return None, None
                
        except Exception as e:
            print(f"❌ Failed to create ngrok tunnel: {e}")
            return None, None
    
    def create_serveo_tunnel(self):
        """Alternative: Create serveo.net tunnel (no signup required)."""
        try:
            print("🔗 Creating serveo.net tunnel (no signup required)...")
            
            # Start serveo tunnel
            process = subprocess.Popen(
                ['ssh', '-R', f'80:localhost:{self.port}', 'serveo.net'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait and capture the URL
            time.sleep(3)
            
            # The URL is typically shown in the output
            print("✅ Serveo tunnel created!")
            print("📄 Check the terminal output above for the public URL")
            print("🔗 URL format will be: https://RANDOM.serveo.net")
            
            return "serveo.net", process
            
        except Exception as e:
            print(f"❌ Failed to create serveo tunnel: {e}")
            return None, None

def share_reports(method="local", auto_open=True):
    """
    Share AI-Horizon reports with different methods.
    
    Args:
        method: "local", "ngrok", or "serveo"
        auto_open: Whether to automatically open browser
    """
    
    print("🚀 AI-Horizon Report Sharing")
    print("=" * 50)
    
    # Check if reports exist
    reports_dir = get_data_path("reports")
    dashboard_file = reports_dir / "ai_horizon_analysis_report.html"
    methodology_file = reports_dir / "process_methodology.html"
    
    if not dashboard_file.exists():
        print("❌ Dashboard report not found. Please run generate_web_report.py first.")
        return
    
    print(f"📁 Reports directory: {reports_dir}")
    print(f"✅ Found dashboard: {dashboard_file.name}")
    print(f"✅ Found methodology: {methodology_file.name}")
    print()
    
    # Start local server
    server = ReportHTTPServer()
    
    if not server.start_local_server():
        return
    
    # Local access
    local_dashboard = f"http://localhost:{server.port}/ai_horizon_analysis_report.html"
    local_methodology = f"http://localhost:{server.port}/process_methodology.html"
    
    print(f"🔗 Local Dashboard: {local_dashboard}")
    print(f"📋 Local Methodology: {local_methodology}")
    print()
    
    if auto_open and method == "local":
        webbrowser.open(local_dashboard)
    
    # Public sharing
    if method == "ngrok":
        public_url, process = server.create_ngrok_tunnel()
        if public_url and auto_open:
            webbrowser.open(f"{public_url}/ai_horizon_analysis_report.html")
    
    elif method == "serveo":
        result, process = server.create_serveo_tunnel()
    
    else:
        print("📡 For public sharing, install ngrok or use serveo:")
        print("   python share_reports.py --method ngrok")
        print("   python share_reports.py --method serveo")
    
    print()
    print("🎯 Share these links with collaborators:")
    print("   📊 Dashboard for high-level insights")
    print("   📋 Methodology for process transparency")
    print()
    print("Press Ctrl+C to stop sharing...")
    
    try:
        # Keep running until interrupted
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping report sharing...")
        server.stop_server()
        print("✅ Sharing stopped")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Share AI-Horizon reports")
    parser.add_argument("--method", choices=["local", "ngrok", "serveo"], 
                       default="local", help="Sharing method")
    parser.add_argument("--no-open", action="store_true", 
                       help="Don't auto-open browser")
    parser.add_argument("--port", type=int, default=8080, 
                       help="Local server port")
    
    args = parser.parse_args()
    
    share_reports(
        method=args.method,
        auto_open=not args.no_open
    ) 