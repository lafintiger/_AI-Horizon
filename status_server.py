#!/usr/bin/env python3
"""
AI-Horizon Status Server

Real-time web dashboard for the AI-Horizon cybersecurity workforce intelligence system.

Features:
- Real-time dashboard with live system statistics
- Quality-ranked document browsing with visual indicators
- Manual entry system for documents, URLs, and YouTube videos
- Report generation and analysis tools
- API cost tracking and monitoring
- Processing pipeline management
- RAG-based chat interface for querying collected documents

Main Routes:
- / : Dashboard with real-time system status
- /browse_entries : Quality-sorted document browser (primary interface)
- /manual-entry : Manual document/URL/video entry system
- /reports : Report generation and viewing
- /cost-analysis : API usage and cost tracking
- /methodology : Academic methodology documentation
- /chat : RAG chat interface for document queries

The server integrates with:
- DocumentQualityRanker for real-time quality assessment
- DatabaseManager for SQLite data operations
- Various collection and processing scripts
- Cost tracking for API usage monitoring

Usage:
    python status_server.py --host 0.0.0.0 --port 5000 [--debug]
"""

import sys
import json
import time
import threading
import atexit
import argparse
from datetime import datetime
from pathlib import Path
from collections import deque
from typing import Dict, Any, Optional
from werkzeug.utils import secure_filename
from urllib.parse import urlparse, parse_qs

from flask import Flask, render_template, jsonify, Response, request, send_file, stream_template, send_from_directory, redirect, url_for, flash
from flask_cors import CORS

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from aih.utils.database import DatabaseManager
from aih.utils.logging import get_logger
from aih.utils.cost_tracker import cost_tracker
from scripts.analysis.implement_quality_ranking import DocumentQualityRanker

app = Flask(__name__)
app.secret_key = 'ai-horizon-status-server-secret-key'  # Change in production
CORS(app)

# Register custom Jinja2 filters
def from_json_filter(value):
    """Convert JSON string to Python object."""
    if not value:
        return {}
    try:
        return json.loads(value)
    except (ValueError, TypeError):
        return {}

app.jinja_env.filters['from_json'] = from_json_filter

# Global status tracking
class StatusTracker:
    """
    Tracks the status of operations, progress, and system state for the AI-Horizon system.
    
    Manages real-time status updates, progress tracking, cost monitoring, and client notifications
    through Server-Sent Events (SSE) for the web interface.
    """
    
    def __init__(self):
        self.current_operation: Optional[str] = None
        self.operation_start: Optional[datetime] = None
        self.progress: Dict[str, Any] = {}
        self.recent_logs: deque = deque(maxlen=100)  # Keep last 100 log entries
        self.stats: Dict[str, Any] = {}
        self.is_running: bool = False
        self.clients: set = set()  # SSE clients
        
        # API Cost Tracking
        self.api_costs = {
            "total_cost": 0.0,
            "session_cost": 0.0,  # Cost for current session
            "perplexity_calls": 0,
            "perplexity_cost": 0.0,
            "last_reset": datetime.now().isoformat()
        }
        
        # Collection progress tracking (only active during collection)
        self.collection_progress = {
            "is_active": False,  # NEW: Track if collection is actively running
            "total_target": 80,
            "total_collected": 0,
            "categories": {
                "replace": {"target": 20, "collected": 0, "current_query": 0, "total_queries": 20},
                "augment": {"target": 20, "collected": 0, "current_query": 0, "total_queries": 20},
                "new_tasks": {"target": 20, "collected": 0, "current_query": 0, "total_queries": 20},
                "human_only": {"target": 20, "collected": 0, "current_query": 0, "total_queries": 20}
            },
            "current_category": None,
            "last_updated": None
        }
        
        # Initialize with actual database state on startup
        self.sync_with_database()
        
    def sync_with_database(self, log_result=False):
        """Sync collection progress with actual database."""
        try:
            db = DatabaseManager()
            artifacts = db.get_artifacts()
            
            # Count actual artifacts by category
            category_counts = {
                "replace": 0,
                "augment": 0, 
                "new_tasks": 0,
                "human_only": 0,
                "unknown": 0
            }
            
            for artifact in artifacts:
                metadata = json.loads(artifact.get('raw_metadata', '{}'))
                category = metadata.get('ai_impact_category', 'unknown')
                if category in category_counts:
                    category_counts[category] += 1
                else:
                    category_counts["unknown"] += 1
            
            # Update collection progress with actual counts
            total_collected = 0
            for category in self.collection_progress["categories"]:
                actual_count = category_counts.get(category, 0)
                self.collection_progress["categories"][category]["collected"] = actual_count
                # Reset query progress when not running
                if not self.is_running:
                    self.collection_progress["categories"][category]["current_query"] = 0
                total_collected += actual_count
                
            self.collection_progress["total_collected"] = total_collected
            self.collection_progress["current_category"] = None if not self.is_running else self.collection_progress["current_category"]
            self.collection_progress["last_updated"] = datetime.now().isoformat()
            
            if log_result:
                self.add_log("INFO", f"Collection progress synced: {total_collected} total articles", "SYSTEM")
            self.broadcast_update()
            
        except Exception as e:
            if log_result:
                self.add_log("ERROR", f"Failed to sync collection progress: {e}", "SYSTEM")

    def set_operation(self, operation: str):
        """
        Start a new operation and initialize progress tracking.
        
        Args:
            operation: Name of the operation being started
        """
        self.current_operation = operation
        self.operation_start = datetime.now()
        self.is_running = True
        self.progress = {"current": 0, "total": 0, "status": "Starting..."}
        
        # Activate collection progress if this is a collection operation
        if "collection" in operation.lower():
            self.collection_progress["is_active"] = True
            # Reset progress counters for new collection
            for category in self.collection_progress["categories"]:
                self.collection_progress["categories"][category]["current_query"] = 0
            self.collection_progress["current_category"] = None
        
        self.broadcast_update()
        
    def update_progress(self, current: int, total: int, status: str = ""):
        """
        Update the progress of the current operation.
        
        Args:
            current: Current progress count
            total: Total expected count
            status: Optional status message
        """
        self.progress = {"current": current, "total": total, "status": status}
        self.broadcast_update()
        
    def update_collection_progress(self, category: str, query_num: int, total_queries: int, collected_count: int):
        """Update persistent collection progress."""
        # Only update if collection is active
        if not self.collection_progress["is_active"]:
            return
            
        if category in self.collection_progress["categories"]:
            self.collection_progress["categories"][category]["current_query"] = query_num
            self.collection_progress["categories"][category]["total_queries"] = total_queries
            self.collection_progress["categories"][category]["collected"] = collected_count
            
        self.collection_progress["current_category"] = category
        self.collection_progress["total_collected"] = sum(
            cat["collected"] for cat in self.collection_progress["categories"].values()
        )
        self.collection_progress["last_updated"] = datetime.now().isoformat()
        self.broadcast_update()
        
    def add_log(self, level: str, message: str, category: str = "SYSTEM"):
        """
        Add a log entry to the recent logs.
        
        Args:
            level: Log level (INFO, WARNING, ERROR, etc.)
            message: Log message
            category: Log category for filtering
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "category": category,
            "message": message
        }
        self.recent_logs.append(log_entry)
        self.broadcast_update()
        
    def update_stats(self, stats: Dict[str, Any]):
        """
        Update system statistics.
        
        Args:
            stats: Dictionary containing system statistics
        """
        self.stats = stats
        # Also update collection progress from database stats
        if "categories" in stats:
            for category, count in stats["categories"].items():
                if category in self.collection_progress["categories"]:
                    self.collection_progress["categories"][category]["collected"] = count
            self.collection_progress["total_collected"] = stats.get("total_artifacts", 0)
        self.broadcast_update()
        
    def complete_operation(self, success: bool = True, message: str = ""):
        """Complete the current operation and reset status."""
        if success:
            self.add_log("INFO", f"Operation completed: {message}", "OPERATION")
        else:
            self.add_log("ERROR", f"Operation failed: {message}", "OPERATION")
        
        self.is_running = False
        self.current_operation = None
        
        # Deactivate collection progress and reset query counters
        self.collection_progress["is_active"] = False
        self.collection_progress["current_category"] = None
        for category in self.collection_progress["categories"]:
            self.collection_progress["categories"][category]["current_query"] = 0
        
        # Sync with actual database state
        self.sync_with_database(log_result=False)  # Don't log during operation completion
        self.broadcast_update()

    def broadcast_update(self):
        """Send update to all connected SSE clients."""
        if self.clients:
            data = self.get_status()
            for client in list(self.clients):
                try:
                    client.put(f"data: {json.dumps(data)}\n\n")
                except:
                    self.clients.discard(client)

    def get_status(self) -> Dict[str, Any]:
        return {
            "current_operation": self.current_operation,
            "operation_start": self.operation_start.isoformat() if self.operation_start else None,
            "is_running": self.is_running,
            "progress": self.progress,
            "collection_progress": self.collection_progress,  # Add persistent progress
            "api_costs": self.api_costs,  # Add cost tracking
            "cost_analysis": {
                "cost_per_article": self.calculate_cost_per_article(),
                "estimated_full_run": self.estimate_full_run_cost(),
                "runs_per_100_dollars": int(100 / self.estimate_full_run_cost()) if self.estimate_full_run_cost() > 0 else 0
            },
            "recent_logs": list(self.recent_logs)[-20:],  # Last 20 logs
            "stats": self.stats,
            "timestamp": datetime.now().isoformat()
        }

    def add_api_cost(self, api_name: str, cost: float, call_count: int = 1):
        """Track API costs."""
        self.api_costs["session_cost"] += cost
        self.api_costs["total_cost"] += cost
        
        if api_name.lower() == "perplexity":
            self.api_costs["perplexity_calls"] += call_count
            self.api_costs["perplexity_cost"] += cost
            
        self.add_log("INFO", f"API Cost: {api_name} ${cost:.4f} (Total: ${self.api_costs['total_cost']:.2f})", "COST")
        self.broadcast_update()
    
    def reset_session_cost(self):
        """Reset session cost tracking."""
        self.api_costs["session_cost"] = 0.0
        self.api_costs["last_reset"] = datetime.now().isoformat()
        self.add_log("INFO", "Session cost tracking reset", "COST")
        self.broadcast_update()
    
    def calculate_cost_per_article(self) -> float:
        """Calculate average cost per article collected."""
        total_articles = sum(
            cat["collected"] for cat in self.collection_progress["categories"].values()
        )
        if total_articles > 0 and self.api_costs["session_cost"] > 0:
            return self.api_costs["session_cost"] / total_articles
        return 0.0
    
    def estimate_full_run_cost(self) -> float:
        """Estimate cost for a full 80-article collection run."""
        cost_per_article = self.calculate_cost_per_article()
        if cost_per_article > 0:
            return cost_per_article * 80
        else:
            # Default estimate based on Perplexity pricing
            # Assuming ~3 queries per article, ~1000 tokens per query
            return 80 * 3 * 0.001  # $0.24 estimate for full run

# Global status tracker
status = StatusTracker()

# Initialize quality ranker globally
quality_ranker = DocumentQualityRanker()

# File upload configuration for manual entry
UPLOAD_FOLDER = Path("data/uploads")
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf', 'txt', 'docx', 'doc'}

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_youtube_url(url):
    """Check if URL is a YouTube link."""
    youtube_domains = ['youtube.com', 'youtu.be', 'm.youtube.com']
    try:
        parsed = urlparse(url)
        return any(domain in parsed.netloc.lower() for domain in youtube_domains)
    except:
        return False

def extract_youtube_id(url):
    """Extract YouTube video ID from URL."""
    try:
        parsed = urlparse(url)
        if 'youtu.be' in parsed.netloc:
            return parsed.path[1:]
        elif 'youtube.com' in parsed.netloc:
            if 'watch' in parsed.path:
                return parse_qs(parsed.query).get('v', [None])[0]
            elif 'embed' in parsed.path:
                return parsed.path.split('/')[2]
    except:
        pass
    return None

@app.route('/')
def index():
    """Main status dashboard."""
    return render_template('status.html')

@app.route('/api/status')
def api_status():
    """Get current status as JSON."""
    return jsonify(status.get_status())

@app.route('/api/database_stats')
def database_stats():
    """Get database statistics."""
    try:
        db = DatabaseManager()
        artifacts = db.get_artifacts()
        
        # Count by category if metadata exists
        category_counts = {}
        for artifact in artifacts:
            metadata = json.loads(artifact.get('raw_metadata', '{}'))
            category = metadata.get('ai_impact_category', 'unknown')
            category_counts[category] = category_counts.get(category, 0) + 1
        
        stats = {
            "total_artifacts": len(artifacts),
            "categories": category_counts,
            "last_updated": datetime.now().isoformat()
        }
        
        status.update_stats(stats)
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stream')
def stream():
    """Server-Sent Events endpoint for real-time updates."""
    import queue
    
    def event_stream():
        client_queue = queue.Queue()
        status.clients.add(client_queue)
        
        try:
            # Send initial status
            yield f"data: {json.dumps(status.get_status())}\n\n"
            
            while True:
                try:
                    # Wait for updates
                    data = client_queue.get(timeout=30)  # 30 second timeout
                    yield data
                except queue.Empty:
                    # Send heartbeat
                    yield f"data: {json.dumps({'heartbeat': True})}\n\n"
                    
        except GeneratorExit:
            status.clients.discard(client_queue)
    
    return Response(event_stream(), mimetype='text/event-stream')

@app.route('/api/start_collection')
def start_collection():
    """Start comprehensive collection in background."""
    if status.is_running:
        return jsonify({"error": "Operation already running"}), 400
    
    def run_collection():
        import asyncio
        from scripts.collection import collect_comprehensive
        
        try:
            status.set_operation("Comprehensive Article Collection")
            status.add_log("INFO", "Starting comprehensive collection for all categories", "COLLECTION")
            
            # Set the status tracker in the collection module
            collect_comprehensive.set_status_tracker(status)
            
            # Run the collection
            result, category_stats = asyncio.run(collect_comprehensive.collect_comprehensive())
            
            # Update final stats
            status.add_log("INFO", f"Collection completed: {result} total articles", "COLLECTION")
            for category, count in category_stats.items():
                status.add_log("INFO", f"{category.upper()}: {count} articles", "COLLECTION")
            
            status.complete_operation(True, f"Collected {result} articles")
            
        except Exception as e:
            status.add_log("ERROR", f"Collection failed: {e}", "COLLECTION")
            status.complete_operation(False, str(e))
    
    # Start collection in background thread
    thread = threading.Thread(target=run_collection)
    thread.daemon = True
    thread.start()
    
    return jsonify({"message": "Collection started"})

@app.route('/api/start_targeted_collection')
def start_targeted_collection():
    """Start targeted high-value source collection in background."""
    if status.is_running:
        return jsonify({"error": "Operation already running"}), 400
    
    def run_targeted_collection():
        import asyncio
        from scripts.collection import collect_targeted_sources
        
        try:
            status.set_operation("Targeted High-Value Source Collection")
            status.add_log("INFO", "Starting targeted collection from independent sources", "TARGETED")
            
            # Set the status tracker in the collection module
            collect_targeted_sources.set_status_tracker(status)
            
            # Run the targeted collection
            result, category_stats = asyncio.run(collect_targeted_sources.collect_targeted_sources())
            
            # Update final stats
            status.add_log("INFO", f"Targeted collection completed: {result} total articles", "TARGETED")
            for category, count in category_stats.items():
                status.add_log("INFO", f"TARGETED {category.upper()}: {count} articles", "TARGETED")
            
            status.complete_operation(True, f"Targeted collection: {result} articles from high-value sources")
            
        except Exception as e:
            status.add_log("ERROR", f"Targeted collection failed: {e}", "TARGETED")
            status.complete_operation(False, str(e))
    
    # Start targeted collection in background thread
    thread = threading.Thread(target=run_targeted_collection)
    thread.daemon = True
    thread.start()
    
    return jsonify({"message": "Targeted collection started"})

@app.route('/api/start_student_intelligence')
def start_student_intelligence():
    """Start student career intelligence collection in background."""
    if status.is_running:
        return jsonify({"error": "Operation already running"}), 400
    
    def run_student_intelligence():
        import asyncio
        from scripts.collection import collect_student_intelligence
        
        try:
            status.set_operation("Student Career Intelligence Collection")
            status.add_log("INFO", "Starting career intelligence for 2025 graduates", "STUDENT")
            
            # Set the status tracker in the collection module
            collect_student_intelligence.set_status_tracker(status)
            
            # Run the student intelligence collection
            result, category_stats = asyncio.run(collect_student_intelligence.collect_student_intelligence())
            
            # Update final stats
            status.add_log("INFO", f"Student intelligence completed: {result} actionable insights", "STUDENT")
            for category, count in category_stats.items():
                action_map = {
                    'replace': 'Jobs/Tasks to AVOID',
                    'augment': 'Skills to AUGMENT with AI', 
                    'new_tasks': 'NEW Opportunities to Pursue',
                    'human_only': 'Human Skills to EMPHASIZE'
                }
                status.add_log("INFO", f"{action_map.get(category, category)}: {count} insights", "STUDENT")
            
            status.complete_operation(True, f"Student career intelligence: {result} actionable insights for graduates")
            
        except Exception as e:
            status.add_log("ERROR", f"Student intelligence collection failed: {e}", "STUDENT")
            status.complete_operation(False, str(e))
    
    # Start student intelligence collection in background thread
    thread = threading.Thread(target=run_student_intelligence)
    thread.daemon = True
    thread.start()
    
    return jsonify({"message": "Student career intelligence collection started"})

@app.route('/api/start_comprehensive_collection')
def start_comprehensive_collection():
    """Alias for start_collection - comprehensive collection of all categories."""
    return start_collection()

@app.route('/manual-entry')
def manual_entry():
    """Manual entry page for uploading content."""
    return render_template('manual_entry.html')

@app.route('/browse_entries')
def browse_entries():
    """Browse all manual entries and artifacts."""
    try:
        db = DatabaseManager()
        all_artifacts = db.get_artifacts(limit=100)
        
        # Calculate quality scores for all artifacts
        artifacts_with_scores = []
        for artifact in all_artifacts:
            try:
                quality_score, detailed_scores = quality_ranker.calculate_document_score(artifact)
                artifact_with_score = artifact.copy()
                artifact_with_score['quality_score'] = round(quality_score, 3)
                artifact_with_score['quality_grade'] = (
                    'Excellent' if quality_score >= 0.8 else
                    'Good' if quality_score >= 0.6 else
                    'Fair' if quality_score >= 0.4 else 'Poor'
                )
                artifacts_with_scores.append(artifact_with_score)
            except Exception as e:
                # If scoring fails, add artifact without score
                artifact_with_score = artifact.copy()
                artifact_with_score['quality_score'] = 0.0
                artifact_with_score['quality_grade'] = 'Unknown'
                artifacts_with_scores.append(artifact_with_score)
        
        # Sort by quality score (highest first)
        artifacts_with_scores.sort(key=lambda x: x['quality_score'], reverse=True)
        
        # Separate manual entries from automated collections
        manual_entries = [a for a in artifacts_with_scores if a.get('source_type', '').startswith('manual_')]
        automated_entries = [a for a in artifacts_with_scores if not a.get('source_type', '').startswith('manual_')]
        
        # Count by category
        category_counts = {}
        for artifact in artifacts_with_scores:
            metadata = json.loads(artifact.get('raw_metadata', '{}'))
            category = metadata.get('category', 'general')
            category_counts[category] = category_counts.get(category, 0) + 1
        
        return render_template('browse_entries.html',
                             manual_entries=manual_entries,
                             automated_entries=automated_entries,
                             category_counts=category_counts,
                             total_manual=len(manual_entries),
                             total_automated=len(automated_entries))
                             
    except Exception as e:
        flash(f'Error browsing entries: {str(e)}', 'error')
        return redirect(url_for('manual_entry'))

@app.route('/view_entry/<artifact_id>')
def view_entry(artifact_id):
    """View detailed information about a specific entry."""
    try:
        db = DatabaseManager()
        artifact = db.get_artifact_by_id(artifact_id)
        
        if not artifact:
            flash('Entry not found!', 'error')
            return redirect(url_for('browse_entries'))
        
        # Parse metadata if it exists
        metadata = {}
        if artifact.get('raw_metadata'):
            try:
                metadata = json.loads(artifact['raw_metadata'])
            except:
                pass
        
        return render_template('view_entry.html', 
                             artifact=artifact, 
                             metadata=metadata)
                             
    except Exception as e:
        flash(f'Error viewing entry: {str(e)}', 'error')
        return redirect(url_for('browse_entries'))

@app.route('/process_entries')
def process_entries():
    """Process manual entries through AI categorization."""
    try:
        db = DatabaseManager()
        artifacts = db.get_artifacts(limit=500)
        
        # Get manual entries that need processing (no ai_impact_category)
        manual_entries = []
        for artifact in artifacts:
            if artifact.get('source_type', '').startswith('manual_'):
                # Parse metadata to check processing status
                metadata = json.loads(artifact.get('raw_metadata', '{}'))
                
                # Only include if not already processed
                if not metadata.get('ai_impact_category'):
                    manual_entries.append(artifact)
        
        if not manual_entries:
            flash('No manual entries need processing. All entries have been processed!', 'success')
            return redirect(url_for('browse_entries'))
        
        return render_template('process_entries.html', 
                             entries=manual_entries,
                             total_count=len(manual_entries))
                             
    except Exception as e:
        flash(f'Error accessing processing: {str(e)}', 'error')
        return redirect(url_for('manual_entry'))

@app.route('/methodology')
def methodology():
    """Research methodology page."""
    return render_template('methodology.html')

@app.route('/reports')
def reports():
    """Reports page."""
    return render_template('reports.html')

@app.route('/analysis')
def analysis():
    """Analysis page (placeholder)."""
    return render_template('analysis.html')

@app.route('/settings')
def settings():
    """Settings page (placeholder)."""
    return render_template('settings.html')

@app.route('/api/reports')
def api_reports():
    """Get list of available reports."""
    try:
        reports_dir = Path('data/reports')
        reports = []
        
        if reports_dir.exists():
            # Get both markdown and HTML files
            for report_file in reports_dir.glob('*.md'):
                stat = report_file.stat()
                # Clean path to remove any potential line ending characters
                clean_path = str(report_file).replace('\\', '/').strip()
                reports.append({
                    'name': report_file.name,
                    'path': clean_path,
                    'size': f"{stat.st_size / 1024:.1f} KB",
                    'created': stat.st_mtime,
                    'type': 'student'  # Mark as student report
                })
                
            for report_file in reports_dir.glob('*.html'):
                stat = report_file.stat()
                # Clean path to remove any potential line ending characters
                clean_path = str(report_file).replace('\\', '/').strip()
                reports.append({
                    'name': report_file.name,
                    'path': clean_path,
                    'size': f"{stat.st_size / 1024:.1f} KB", 
                    'created': stat.st_mtime,
                    'type': 'web'  # Mark as web report
                })
        
        # Sort by creation time (newest first)
        reports.sort(key=lambda x: x['created'], reverse=True)
        
        return jsonify({"reports": reports})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/generate_student_report', methods=['POST'])
def api_generate_student_report():
    """Generate student career intelligence report."""
    try:
        import subprocess
        import sys
        
        # Use subprocess to run the script directly
        script_path = "scripts/generate_student_report.py"
        
        # Run the script and capture output
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent)
        )
        
        if result.returncode == 0:
            # Parse the output to get the filepath
            output_lines = result.stdout.strip().split('\n')
            filepath = None
            
            # First, look for clean filepath output
            for line in output_lines:
                if line.startswith('[FILEPATH]'):
                    filepath = line.replace('[FILEPATH]', '').strip()
                    break
            
            # Fallback to parsing common report output patterns
            if not filepath:
                for line in output_lines:
                    if 'saved to:' in line.lower() or 'report saved' in line.lower():
                        # Extract filepath from output line
                        parts = line.split()
                        for part in parts:
                            if 'data' in part and ('.html' in part or '.md' in part):
                                filepath = part
                                break
                        if filepath:
                            break
            
            # Final fallback to scanning for data/reports paths
            if not filepath:
                # Look for the last line that might contain the filepath
                for line in reversed(output_lines):
                    if 'data' in line and 'reports' in line and ('.html' in line or '.md' in line):
                        # Try to extract just the file path part
                        parts = line.split()
                        for part in parts:
                            if 'data' in part and ('.html' in part or '.md' in part):
                                filepath = part
                                break
                        if filepath:
                            break
            
            return jsonify({
                "message": "Student report generated successfully",
                "filepath": filepath or "Report generated but filepath not found",
                "output": result.stdout
            })
        else:
            return jsonify({
                "error": f"Script execution failed: {result.stderr}",
                "stdout": result.stdout,
                "returncode": result.returncode
            }), 500
            
    except Exception as e:
        import traceback
        return jsonify({
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

@app.route('/api/generate_web_report', methods=['POST'])
def api_generate_web_report():
    """Generate web intelligence report."""
    try:
        import subprocess
        import sys
        
        # Use subprocess to run the script directly
        script_path = "scripts/generate_web_report.py"
        
        # Run the script and capture output
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent)
        )
        
        if result.returncode == 0:
            # Parse the output to get the filepath
            output_lines = result.stdout.strip().split('\n')
            filepath = None
            
            # First, look for clean filepath output
            for line in output_lines:
                if line.startswith('[FILEPATH]'):
                    filepath = line.replace('[FILEPATH]', '').strip()
                    break
            
            # Fallback to parsing common report output patterns
            if not filepath:
                for line in output_lines:
                    if 'saved to:' in line.lower() or 'report saved' in line.lower():
                        # Extract filepath from output line
                        parts = line.split()
                        for part in parts:
                            if 'data' in part and ('.html' in part or '.md' in part):
                                filepath = part
                                break
                        if filepath:
                            break
            
            # Final fallback to scanning for data/reports paths
            if not filepath:
                # Look for the last line that might contain the filepath
                for line in reversed(output_lines):
                    if 'data' in line and 'reports' in line and ('.html' in line or '.md' in line):
                        # Try to extract just the file path part
                        parts = line.split()
                        for part in parts:
                            if 'data' in part and ('.html' in part or '.md' in part):
                                filepath = part
                                break
                        if filepath:
                            break
            
            return jsonify({
                "message": "Web report generated successfully", 
                "filepath": filepath or "Report generated but filepath not found",
                "output": result.stdout
            })
        else:
            return jsonify({
                "error": f"Script execution failed: {result.stderr}",
                "stdout": result.stdout,
                "returncode": result.returncode
            }), 500
            
    except Exception as e:
        import traceback
        return jsonify({
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

@app.route('/api/view_report')
def api_view_report():
    """View a report in the browser."""
    try:
        report_path = request.args.get('path')
        if not report_path:
            return "Report path required", 400
        
        path = Path(report_path)
        if not path.exists():
            return "Report not found", 404
            
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Convert markdown to HTML for viewing
        # For now, return as plain text with basic formatting
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{path.name}</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                       max-width: 800px; margin: 0 auto; padding: 20px; line-height: 1.6; }}
                pre {{ background: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto; }}
                h1, h2, h3 {{ color: #333; }}
                .nav {{ margin-bottom: 20px; }}
                .nav a {{ color: #4299e1; text-decoration: none; margin-right: 10px; }}
            </style>
        </head>
        <body>
            <div class="nav">
                <a href="javascript:history.back()">← Back to Reports</a>
                <a href="/">📊 Dashboard</a>
            </div>
            <pre>{content}</pre>
        </body>
        </html>
        """
        
        return html_content
        
    except Exception as e:
        return f"Error viewing report: {e}", 500

@app.route('/api/download_report')
def api_download_report():
    """Download a report file."""
    try:
        report_path = request.args.get('path')
        if not report_path:
            return "Report path required", 400
        
        path = Path(report_path)
        if not path.exists():
            return "Report not found", 404
            
        return send_file(path, as_attachment=True, download_name=path.name)
        
    except Exception as e:
        return f"Error downloading report: {e}", 500

@app.route('/api/reset_session_cost', methods=['POST'])
def reset_session_cost():
    """Reset session cost tracking."""
    try:
        status.reset_session_cost()
        return jsonify({"message": "Session cost tracking reset successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/add_cost', methods=['POST'])
def add_cost():
    """Manually add API cost (for testing/adjustment)."""
    try:
        data = request.get_json()
        api_name = data.get('api_name', 'manual')
        cost = float(data.get('cost', 0))
        call_count = int(data.get('call_count', 1))
        
        status.add_api_cost(api_name, cost, call_count)
        return jsonify({"message": f"Added ${cost:.4f} cost for {api_name}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/cost-analysis')
def cost_analysis():
    """Cost analysis page."""
    return render_template('cost_analysis.html')

@app.route('/api/cost_analysis')
def api_cost_analysis():
    """Get comprehensive cost analysis data."""
    try:
        budget = float(request.args.get('budget', 100.0))
        
        # Get current costs
        today = datetime.now()
        today_cost = cost_tracker.get_daily_cost()
        monthly_cost = cost_tracker.get_monthly_cost(today.year, today.month)
        total_cost = cost_tracker.costs.get("total_cost", 0.0)
        
        # Get session cost from status tracker
        session_cost = status.api_costs.get("session_cost", 0.0)
        
        # Budget analysis
        budget_analysis = cost_tracker.get_budget_analysis(budget)
        
        # Collection cost estimates
        perplexity_estimate = cost_tracker.estimate_collection_cost().get("perplexity", {})
        cost_per_full_run = perplexity_estimate.get("cost", 0.24)
        collections_per_month = int(budget / cost_per_full_run) if cost_per_full_run > 0 else 0
        
        # Calculate frequency
        if collections_per_month > 365:
            frequency = "Multiple Daily"
        elif collections_per_month > 30:
            frequency = "Daily"
        elif collections_per_month > 4:
            frequency = f"Every {30/collections_per_month:.1f} days"
        elif collections_per_month > 0:
            frequency = f"Every {30/collections_per_month:.0f} days"
        else:
            frequency = "Not feasible"
        
        # Budget scenarios
        budget_scenarios = []
        scenario_budgets = [25, 50, 100, 200, 500]
        for scenario_budget in scenario_budgets:
            scenario_collections = int(scenario_budget / cost_per_full_run) if cost_per_full_run > 0 else 0
            if scenario_collections > 365:
                scenario_freq = "Multiple Daily"
            elif scenario_collections > 30:
                scenario_freq = "Daily" 
            elif scenario_collections > 4:
                scenario_freq = f"Every {30/scenario_collections:.1f} days"
            elif scenario_collections > 0:
                scenario_freq = f"Every {30/scenario_collections:.0f} days"
            else:
                scenario_freq = "Not feasible"
                
            budget_scenarios.append({
                "budget": scenario_budget,
                "collections": scenario_collections,
                "frequency": scenario_freq
            })
        
        # Recommendations
        recommendations = [
            "Use targeted collections for specific research needs",
            "Monitor cost per article to optimize query efficiency", 
            "Reset session costs between major collection runs",
            "Consider running larger collections less frequently",
            "Review duplicate detection to avoid redundant API calls"
        ]
        
        # Add budget-specific recommendations
        if budget_analysis["budget_utilization"] > 80:
            recommendations.insert(0, "⚠️ High budget usage - consider reducing collection frequency")
        elif budget_analysis["budget_utilization"] < 20:
            recommendations.insert(0, "✅ Low budget usage - opportunity to increase collection frequency")
        
        response_data = {
            "current_costs": {
                "today_cost": today_cost,
                "monthly_cost": monthly_cost,
                "total_cost": total_cost,
                "session_cost": session_cost
            },
            "budget_analysis": budget_analysis,
            "collection_estimates": {
                "cost_per_article": cost_per_full_run / 80 if cost_per_full_run > 0 else 0.003,
                "full_run_cost": cost_per_full_run,
                "collections_per_month": collections_per_month,
                "frequency": frequency
            },
            "api_usage": cost_tracker.costs.get("api_usage", {}),
            "budget_scenarios": budget_scenarios,
            "recommendations": recommendations
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/reset_collection_progress', methods=['POST'])
def reset_collection_progress():
    """Manually reset collection progress to sync with database."""
    try:
        status.sync_with_database(log_result=True)  # Log when manually triggered
        return jsonify({"message": "Collection progress reset and synced with database"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def _extract_content_from_url(url: str, notes: str = "") -> tuple[str, str]:
    """
    Extract content from a URL.
    
    Args:
        url: The URL to extract content from
        notes: Additional notes to append
        
    Returns:
        Tuple of (content, flash_message)
    """
    content = f"Manual URL entry. Notes: {notes}" if notes else "Manual URL entry."
    flash_message = ""
    
    try:
        import requests
        from bs4 import BeautifulSoup
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract main content
            content_selectors = [
                'article', '.article-content', '.post-content', 
                '.content', 'main', '.story-body', '.entry-content'
            ]
            
            extracted_content = ""
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    extracted_content = content_elem.get_text(separator=' ', strip=True)
                    break
            
            # If no specific content area found, try to get paragraphs
            if not extracted_content:
                paragraphs = soup.find_all('p')
                if paragraphs:
                    extracted_content = ' '.join([p.get_text(strip=True) for p in paragraphs[:10]])
            
            if extracted_content and len(extracted_content) > 100:
                content = extracted_content
                if notes:
                    content += f"\n\nNotes: {notes}"
                flash_message = 'Successfully fetched article content from URL!'
            else:
                flash_message = 'Could not extract substantial content from URL, saved with notes only.'
                
    except Exception as e:
        flash_message = 'Could not fetch content from URL, saved with notes only.'
    
    return content, flash_message

def _extract_title_from_url(url: str) -> str:
    """
    Extract title from a URL if not provided.
    
    Args:
        url: The URL to extract title from
        
    Returns:
        Extracted title or empty string
    """
    try:
        import requests
        from bs4 import BeautifulSoup
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            title_tag = soup.find('title')
            if title_tag:
                return title_tag.get_text().strip()
    except Exception:
        pass
    
    return ""

def _create_manual_artifact_data(url: str, title: str, content: str, category: str, notes: str) -> Dict[str, Any]:
    """
    Create artifact data dictionary for manual URL entry.
    
    Args:
        url: The URL
        title: The title
        content: The extracted content
        category: The category
        notes: Additional notes
        
    Returns:
        Artifact data dictionary
    """
    return {
        'id': f"manual_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        'url': url,
        'title': title or f"Manual Entry: {url}",
        'content': content,
        'source_type': 'manual_url',
        'collected_at': datetime.now(),
        'metadata': {
            'entry_method': 'manual_url',
            'category': category,
            'notes': notes,
            'added_by': 'manual_interface'
        }
    }

@app.route('/add_url', methods=['GET', 'POST'])
def add_url():
    """Add an article or webpage URL manually."""
    if request.method == 'POST':
        url = request.form.get('url', '').strip()
        title = request.form.get('title', '').strip()
        category = request.form.get('category', 'general')
        notes = request.form.get('notes', '').strip()
        
        if not url:
            flash('URL is required!', 'error')
            return render_template('add_url.html')
        
        try:
            db = DatabaseManager()
            
            # Check if URL already exists
            if db.artifact_exists(url):
                flash(f'URL already exists in database: {url}', 'warning')
                return redirect(url_for('manual_entry'))
            
            # Check if it's a YouTube URL
            if is_youtube_url(url):
                return redirect(url_for('add_youtube', prefill_url=url, 
                                      prefill_title=title, prefill_category=category))
            
            # Extract title if not provided
            if not title:
                title = _extract_title_from_url(url)
            
            # Extract content from URL
            content, flash_message = _extract_content_from_url(url, notes)
            if flash_message:
                flash(flash_message, 'success' if 'Successfully' in flash_message else 'warning')
            
            # Create artifact entry
            artifact_data = _create_manual_artifact_data(url, title, content, category, notes)
            
            # Save to database
            artifact_id = db.save_artifact(artifact_data)
            
            flash(f'Successfully added URL: {title or url}', 'success')
            status.add_log("INFO", f"Manual URL added: {artifact_id} - {url}", "MANUAL")
            
            return redirect(url_for('manual_entry'))
            
        except Exception as e:
            flash(f'Error adding URL: {str(e)}', 'error')
    
    return render_template('add_url.html')

@app.route('/add_file', methods=['GET', 'POST'])
def add_file():
    """Add a document file (PDF, TXT, DOCX)."""
    if request.method == 'POST':
        # Check if file was uploaded
        if 'file' not in request.files:
            flash('No file selected!', 'error')
            return render_template('add_file.html')
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected!', 'error')
            return render_template('add_file.html')
        
        if not allowed_file(file.filename):
            flash(f'File type not allowed. Supported: {", ".join(ALLOWED_EXTENSIONS)}', 'error')
            return render_template('add_file.html')
        
        try:
            # Get form data
            title = request.form.get('title', '').strip()
            category = request.form.get('category', 'general')
            notes = request.form.get('notes', '').strip()
            
            # Save uploaded file
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_filename = f"{timestamp}_{filename}"
            file_path = app.config['UPLOAD_FOLDER'] / unique_filename
            
            file.save(str(file_path))
            
            # Process the file to extract content
            content = f"Document file uploaded: {filename}"
            if notes:
                content += f"\n\nNotes: {notes}"
            
            # Try to extract text content (simplified)
            try:
                if filename.lower().endswith('.txt'):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if notes:
                            content += f"\n\nNotes: {notes}"
                elif filename.lower().endswith('.pdf'):
                    # PDF extraction would require PyPDF2 or similar
                    content = f"PDF file uploaded: {filename}. Text extraction not implemented yet."
                    if notes:
                        content += f"\n\nNotes: {notes}"
            except Exception as e:
                pass  # Keep default content if extraction fails
            
            # Create artifact entry
            db = DatabaseManager()
            artifact_data = {
                'id': f"manual_file_{timestamp}",
                'url': f"file://manual_uploads/{unique_filename}",
                'title': title or filename,
                'content': content,
                'source_type': 'manual_file',
                'collected_at': datetime.now(),
                'metadata': {
                    'entry_method': 'manual_file',
                    'category': category,
                    'notes': notes,
                    'original_filename': filename,
                    'file_path': str(file_path),
                    'file_type': filename.rsplit('.', 1)[1].lower(),
                    'added_by': 'manual_interface'
                }
            }
            
            # Save to database
            artifact_id = db.save_artifact(artifact_data)
            
            flash(f'Successfully uploaded and processed: {title or filename}', 'success')
            status.add_log("INFO", f"Manual file added: {artifact_id} - {filename}", "MANUAL")
            
            return redirect(url_for('manual_entry'))
            
        except Exception as e:
            flash(f'Error processing file: {str(e)}', 'error')
    
    return render_template('add_file.html')

@app.route('/add_youtube', methods=['GET', 'POST'])
def add_youtube():
    """Add a YouTube video with transcript extraction."""
    prefill_url = request.args.get('prefill_url', '')
    prefill_title = request.args.get('prefill_title', '')
    prefill_category = request.args.get('prefill_category', 'general')
    
    if request.method == 'POST':
        url = request.form.get('url', '').strip()
        title = request.form.get('title', '').strip()
        category = request.form.get('category', 'general')
        notes = request.form.get('notes', '').strip()
        
        if not url:
            flash('YouTube URL is required!', 'error')
            return render_template('add_youtube.html')
        
        if not is_youtube_url(url):
            flash('Please provide a valid YouTube URL!', 'error')
            return render_template('add_youtube.html')
        
        try:
            db = DatabaseManager()
            
            # Check if URL already exists
            if db.artifact_exists(url):
                flash(f'YouTube video already exists in database: {url}', 'warning')
                return redirect(url_for('manual_entry'))
            
            # Create basic artifact entry (transcript extraction would require youtube-transcript-api)
            content = f"YouTube video: {url}"
            if notes:
                content += f"\n\nNotes: {notes}"
            
            artifact_data = {
                'id': f"manual_youtube_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'url': url,
                'title': title or f"YouTube Video: {url}",
                'content': content,
                'source_type': 'manual_youtube',
                'collected_at': datetime.now(),
                'metadata': {
                    'entry_method': 'manual_youtube',
                    'category': category,
                    'notes': notes,
                    'video_id': extract_youtube_id(url),
                    'added_by': 'manual_interface'
                }
            }
            
            # Save to database
            artifact_id = db.save_artifact(artifact_data)
            
            flash(f'Successfully added YouTube video: {title or url}', 'success')
            status.add_log("INFO", f"Manual YouTube added: {artifact_id} - {url}", "MANUAL")
            
            return redirect(url_for('manual_entry'))
            
        except Exception as e:
            flash(f'Error adding YouTube video: {str(e)}', 'error')
    
    return render_template('add_youtube.html', 
                         prefill_url=prefill_url, 
                         prefill_title=prefill_title, 
                         prefill_category=prefill_category)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded files."""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.errorhandler(413)
def too_large(e):
    """Handle file too large error."""
    flash("File is too large! Maximum size is 50MB.", 'error')
    return redirect(request.url), 413

@app.route('/chat')
def chat_interface():
    """Chat interface placeholder."""
    flash('Chat interface will be implemented soon!', 'info')
    return redirect(url_for('manual_entry'))

# ===== END MANUAL ENTRY ROUTES =====

# ===== MANUAL ENTRY PROCESSING API ROUTES =====

@app.route('/api/process_all_entries', methods=['POST'])
def api_process_all_entries():
    """Process all unprocessed manual entries through AI categorization."""
    if status.is_running:
        return jsonify({"error": "Another operation is already running"}), 400
    
    def run_processing():
        import asyncio
        import manual_entry_processor
        
        try:
            status.set_operation("Processing Manual Entries")
            status.add_log("INFO", "Starting AI processing of all unprocessed manual entries", "PROCESSING")
            
            # Run the processing
            result = asyncio.run(manual_entry_processor.process_all_unprocessed_entries(status))
            
            # Update final stats
            if result.get('successful', 0) > 0:
                status.add_log("INFO", f"Processing completed: {result['successful']} successful, {result['failed']} failed", "PROCESSING")
                status.complete_operation(True, f"Processed {result['successful']} entries successfully")
            else:
                status.add_log("INFO", result.get('message', 'No entries to process'), "PROCESSING")
                status.complete_operation(True, result.get('message', 'No entries to process'))
            
        except Exception as e:
            status.add_log("ERROR", f"Manual entry processing failed: {e}", "PROCESSING")
            status.complete_operation(False, str(e))
    
    # Start processing in background thread
    thread = threading.Thread(target=run_processing)
    thread.daemon = True
    thread.start()
    
    return jsonify({"message": "Manual entry processing started"})

@app.route('/api/process_selected_entries', methods=['POST'])
def api_process_selected_entries():
    """Process selected manual entries through AI categorization."""
    if status.is_running:
        return jsonify({"error": "Another operation is already running"}), 400
    
    data = request.get_json()
    entry_ids = data.get('entry_ids', [])
    
    if not entry_ids:
        return jsonify({"error": "No entry IDs provided"}), 400
    
    def run_processing():
        import asyncio
        import manual_entry_processor
        
        try:
            status.set_operation("Processing Selected Entries")
            status.add_log("INFO", f"Starting AI processing of {len(entry_ids)} selected entries", "PROCESSING")
            
            # Run the processing
            result = asyncio.run(manual_entry_processor.process_multiple_entries(entry_ids, status))
            
            # Update final stats
            status.add_log("INFO", f"Selected processing completed: {result['successful']} successful, {result['failed']} failed", "PROCESSING")
            status.complete_operation(True, f"Processed {result['successful']} of {len(entry_ids)} selected entries")
            
        except Exception as e:
            status.add_log("ERROR", f"Selected entry processing failed: {e}", "PROCESSING")
            status.complete_operation(False, str(e))
    
    # Start processing in background thread
    thread = threading.Thread(target=run_processing)
    thread.daemon = True
    thread.start()
    
    return jsonify({"message": f"Processing {len(entry_ids)} selected entries"})

@app.route('/api/process_single_entry', methods=['POST'])
def api_process_single_entry():
    """Process a single manual entry through AI categorization."""
    data = request.get_json()
    entry_id = data.get('entry_id')
    
    if not entry_id:
        return jsonify({"error": "No entry ID provided"}), 400
    
    def run_processing():
        import asyncio
        import manual_entry_processor
        
        try:
            status.add_log("INFO", f"Starting AI processing of entry: {entry_id}", "PROCESSING")
            
            # Run the processing
            result = asyncio.run(manual_entry_processor.process_single_entry(entry_id, status))
            
            if result['status'] == 'processed':
                status.add_log("INFO", f"Single entry processed: {entry_id} -> {result['category']} (confidence: {result['confidence']:.2f})", "PROCESSING")
            elif result['status'] == 'already_processed':
                status.add_log("INFO", f"Entry already processed: {entry_id} -> {result['category']}", "PROCESSING")
            
        except Exception as e:
            status.add_log("ERROR", f"Single entry processing failed for {entry_id}: {e}", "PROCESSING")
    
    # Start processing in background thread
    thread = threading.Thread(target=run_processing)
    thread.daemon = True
    thread.start()
    
    return jsonify({"message": f"Processing entry: {entry_id}"})

# ===== END MANUAL ENTRY PROCESSING API ROUTES =====

@app.route('/api/extract_wisdom', methods=['POST'])
def api_extract_wisdom():
    """Extract wisdom and insights from an article using AI."""
    try:
        data = request.get_json()
        artifact_id = data.get('artifact_id')
        
        if not artifact_id:
            return jsonify({"error": "No artifact ID provided"}), 400
        
        # Get artifact from database
        db = DatabaseManager()
        artifact = db.get_artifact_by_id(artifact_id)
        
        if not artifact:
            return jsonify({"error": "Artifact not found"}), 404
        
        # Check if wisdom already extracted
        metadata = json.loads(artifact.get('raw_metadata', '{}'))
        if metadata.get('extracted_wisdom'):
            return jsonify({
                "wisdom": metadata['extracted_wisdom'],
                "cached": True,
                "extracted_at": metadata.get('wisdom_extracted_at')
            })
        
        # Prepare content for analysis
        title = artifact.get('title', 'Untitled')
        content = artifact.get('content', '')
        source_type = artifact.get('source_type', '')
        
        # Content validation - check if we have enough content
        if len(content) < 100:
            # Return a fallback wisdom response for insufficient content
            fallback_wisdom = {
                "key_wisdom": ["Insufficient content available for detailed analysis"],
                "career_implications": ["Limited actionable insights due to minimal content"],
                "actionable_takeaways": ["Consider finding sources with more detailed information"],
                "future_outlook": "Unable to assess due to limited content",
                "skill_recommendations": ["Focus on comprehensive cybersecurity learning resources"],
                "summary": "This entry contains minimal content and cannot provide detailed career insights.",
                "relevance_score": 0.1,
                "complexity_level": "beginner",
                "extraction_error": "Insufficient content for analysis",
                "content_length": len(content),
                "extracted_at": datetime.now().isoformat(),
                "extraction_method": "fallback_insufficient_content"
            }
            
            # Save fallback wisdom
            metadata['extracted_wisdom'] = fallback_wisdom
            metadata['wisdom_extracted_at'] = fallback_wisdom['extracted_at']
            
            # Update the artifact with new metadata
            updated_artifact = {
                'id': artifact_id,
                'url': artifact.get('url', ''),
                'title': artifact.get('title', ''),
                'content': artifact.get('content', ''),
                'source_type': artifact.get('source_type', ''),
                'collected_at': artifact.get('collected_at'),
                'metadata': metadata
            }
            db.save_artifact(updated_artifact)
            
            status.add_log("WARNING", f"Insufficient content for wisdom extraction: {title[:50]}... ({len(content)} chars)", "WISDOM")
            
            return jsonify({
                "wisdom": fallback_wisdom,
                "cached": False,
                "content_warning": "This entry has insufficient content for detailed analysis"
            })
        
        # Special handling for YouTube entries without transcripts
        if source_type == 'manual_youtube' and len(content) < 200:
            fallback_wisdom = {
                "key_wisdom": ["YouTube video content requires transcript extraction for analysis"],
                "career_implications": ["Video-based learning can be valuable but needs accessible content"],
                "actionable_takeaways": ["Try extracting captions or transcripts from YouTube videos", "Look for similar content in text format for detailed analysis"],
                "future_outlook": "Video content is increasingly important for professional development",
                "skill_recommendations": ["Develop skills in extracting insights from multimedia content"],
                "summary": "YouTube video detected but transcript content not available for detailed analysis.",
                "relevance_score": 0.3,
                "complexity_level": "intermediate",
                "extraction_error": "YouTube video without accessible transcript",
                "content_length": len(content),
                "extracted_at": datetime.now().isoformat(),
                "extraction_method": "fallback_youtube_no_transcript"
            }
            
            # Save fallback wisdom
            metadata['extracted_wisdom'] = fallback_wisdom
            metadata['wisdom_extracted_at'] = fallback_wisdom['extracted_at']
            
            # Update the artifact with new metadata
            updated_artifact = {
                'id': artifact_id,
                'url': artifact.get('url', ''),
                'title': artifact.get('title', ''),
                'content': artifact.get('content', ''),
                'source_type': artifact.get('source_type', ''),
                'collected_at': artifact.get('collected_at'),
                'metadata': metadata
            }
            db.save_artifact(updated_artifact)
            
            status.add_log("INFO", f"YouTube entry without transcript: {title[:50]}...", "WISDOM")
            
            return jsonify({
                "wisdom": fallback_wisdom,
                "cached": False,
                "content_warning": "YouTube video content requires transcript for detailed analysis"
            })
        
        # Extract wisdom using OpenAI
        try:
            import openai
            import os
            
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                return jsonify({"error": "OpenAI API key not configured"}), 500
            
            client = openai.OpenAI(api_key=api_key)
            
            # Truncate content if too long (keep within token limits)
            max_content_length = 6000
            if len(content) > max_content_length:
                content = content[:max_content_length] + "...[truncated]"
            
            wisdom_prompt = f"""
You are an expert cybersecurity career advisor analyzing content for 2025 graduates. Extract the most valuable, actionable wisdom from this article.

Title: {title}

Content: {content}

Provide your analysis as a structured JSON response with:

{{
    "key_wisdom": ["3-5 most important insights that would help a cybersecurity professional"],
    "career_implications": ["2-3 specific implications for career planning and development"],
    "actionable_takeaways": ["3-4 concrete actions someone could take based on this content"],
    "future_outlook": "Brief assessment of what this means for the cybersecurity field in 2025-2030",
    "skill_recommendations": ["2-3 specific skills to focus on based on this analysis"],
    "summary": "2-3 sentence executive summary of the core message",
    "relevance_score": 0.0-1.0,
    "complexity_level": "beginner|intermediate|advanced"
}}

Focus on practical, actionable insights that would genuinely help someone navigate their cybersecurity career. Avoid generic advice - be specific and forward-looking.
"""
            
            status.add_log("INFO", f"Extracting wisdom from: {title[:50]}...", "WISDOM")
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert cybersecurity career strategist. Provide deep, actionable insights that help professionals make informed career decisions. Always respond with valid JSON."},
                    {"role": "user", "content": wisdom_prompt}
                ],
                temperature=0.1,
                max_tokens=800
            )
            
            # Get the raw response
            raw_response = response.choices[0].message.content.strip()
            
            # Parse the AI response with better error handling
            try:
                wisdom_data = json.loads(raw_response)
                
                # Add extraction metadata
                wisdom_data['extracted_at'] = datetime.now().isoformat()
                wisdom_data['extraction_method'] = 'openai_gpt4_wisdom'
                wisdom_data['content_length'] = len(content)
                
            except json.JSONDecodeError as e:
                status.add_log("WARNING", f"JSON parsing failed, creating fallback response: {e}", "WISDOM")
                
                # Create a fallback wisdom response when JSON parsing fails
                wisdom_data = {
                    "key_wisdom": ["Analysis failed - content may be too complex or unstructured"],
                    "career_implications": ["Consider seeking clearer, more structured sources for career guidance"],
                    "actionable_takeaways": ["Look for alternative sources with similar topics", "Focus on well-structured cybersecurity career resources"],
                    "future_outlook": "Content analysis was unsuccessful due to formatting issues",
                    "skill_recommendations": ["Develop skills in information synthesis from multiple sources"],
                    "summary": "Content analysis failed due to parsing issues, but source may still contain valuable information.",
                    "relevance_score": 0.2,
                    "complexity_level": "intermediate",
                    "extraction_error": f"JSON parsing failed: {str(e)}",
                    "raw_response": raw_response[:200] + "..." if len(raw_response) > 200 else raw_response,
                    "extracted_at": datetime.now().isoformat(),
                    "extraction_method": "fallback_json_parse_error",
                    "content_length": len(content)
                }
            
            # Save wisdom to artifact metadata
            metadata['extracted_wisdom'] = wisdom_data
            metadata['wisdom_extracted_at'] = wisdom_data['extracted_at']
            
            # Update artifact
            artifact['metadata'] = metadata
            
            # Update the artifact with new metadata
            updated_artifact = {
                'id': artifact_id,
                'url': artifact.get('url', ''),
                'title': artifact.get('title', ''),
                'content': artifact.get('content', ''),
                'source_type': artifact.get('source_type', ''),
                'collected_at': artifact.get('collected_at'),
                'metadata': metadata
            }
            db.save_artifact(updated_artifact)
            
            # Track cost
            estimated_cost = 0.015  # Rough estimate for GPT-4o-mini with this prompt
            cost_tracker.track_api_call("openai", "gpt-4o-mini", tokens=800, custom_cost=estimated_cost)
            
            if wisdom_data.get('extraction_error'):
                status.add_log("WARNING", f"Wisdom extraction completed with fallback for: {title[:50]}...", "WISDOM")
            else:
                status.add_log("INFO", f"Wisdom extracted successfully for: {title[:50]}...", "WISDOM")
            
            return jsonify({
                "wisdom": wisdom_data,
                "cached": False,
                "cost": estimated_cost
            })
                
        except Exception as e:
            status.add_log("ERROR", f"Wisdom extraction failed: {e}", "WISDOM")
            return jsonify({"error": f"Wisdom extraction failed: {str(e)}"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/debug_report_import', methods=['GET'])
def debug_report_import():
    """Debug endpoint to test report generation imports."""
    try:
        import sys
        import importlib.util
        from pathlib import Path
        
        # Add current directory to Python path if not already there
        current_dir = str(Path(__file__).parent)
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
            
        debug_info = {
            "current_working_directory": str(Path.cwd()),
            "script_file_parent": str(Path(__file__).parent),
            "python_path": sys.path[:5],  # First 5 entries
            "script_exists": Path(__file__).parent.joinpath("scripts", "generate_student_report.py").exists(),
            "script_path": str(Path(__file__).parent / "scripts" / "generate_student_report.py")
        }
        
        # Try the import with explicit path
        script_path = Path(__file__).parent / "scripts" / "generate_student_report.py"
        spec = importlib.util.spec_from_file_location(
            "generate_student_report", 
            script_path
        )
        
        if spec is None:
            return jsonify({
                "error": "Could not create module spec",
                "debug_info": debug_info
            }), 500
            
        debug_info["spec_created"] = True
        
        generate_student_report = importlib.util.module_from_spec(spec)
        debug_info["module_created"] = True
        
        spec.loader.exec_module(generate_student_report)
        debug_info["module_executed"] = True
        debug_info["has_main_function"] = hasattr(generate_student_report, 'main')
        
        # Test calling main function
        filepath = generate_student_report.main()
        debug_info["report_generated"] = True
        debug_info["filepath"] = filepath
        
        return jsonify({
            "status": "success",
            "debug_info": debug_info,
            "filepath": filepath
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            "error": str(e),
            "traceback": traceback.format_exc(),
            "debug_info": debug_info if 'debug_info' in locals() else {}
        }), 500

@app.route('/api/run_quality_analysis', methods=['POST'])
def api_run_quality_analysis():
    """Run comprehensive quality distribution analysis."""
    try:
        import subprocess
        import sys
        
        # Use subprocess to run the analysis script
        script_path = "scripts/analysis/quality_distribution_analysis.py"
        
        # Run the script and capture output
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent)
        )
        
        if result.returncode == 0:
            # Parse the output to get key statistics
            output_lines = result.stdout.strip().split('\n')
            
            # Extract key metrics from output
            overall_quality = "Unknown"
            excellent_articles = "Unknown"
            total_analyzed = "Unknown"
            
            for line in output_lines:
                if "Overall Quality:" in line:
                    overall_quality = line.split("Overall Quality:")[-1].strip()
                elif "Excellent Articles:" in line:
                    excellent_articles = line.split("Excellent Articles:")[-1].strip()
                elif "Analyzed" in line and "articles" in line:
                    # Extract total analyzed from "Analyzed X articles across Y categories"
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == "Analyzed" and i + 1 < len(parts):
                            total_analyzed = parts[i + 1]
                            break
            
            # Look for the generated report file
            report_file = None
            for line in output_lines:
                if "Report saved to:" in line:
                    report_file = line.split("Report saved to:")[-1].strip()
                    break
            
            return jsonify({
                "message": "Quality distribution analysis completed successfully",
                "overall_quality": overall_quality,
                "excellent_articles": excellent_articles,
                "total_analyzed": total_analyzed,
                "report_file": report_file,
                "full_output": result.stdout
            })
        else:
            return jsonify({
                "error": f"Analysis script execution failed: {result.stderr}",
                "stdout": result.stdout,
                "returncode": result.returncode
            }), 500
            
    except Exception as e:
        import traceback
        return jsonify({
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

@app.route('/api/run_collection_monitoring', methods=['POST'])
def api_run_collection_monitoring():
    """Run enhanced collection monitoring analysis."""
    try:
        from scripts.analysis.collection_monitoring import CollectionMonitor
        
        # Get monitoring period from request (default 24 hours)
        hours = request.json.get('hours', 24) if request.is_json else 24
        
        # Initialize monitor
        monitor = CollectionMonitor()
        
        # Load recent data
        data_count = monitor.load_recent_data(hours=hours)
        
        if data_count == 0:
            return jsonify({
                "error": "No recent collection data available",
                "data_count": 0,
                "hours": hours
            }), 400
        
        # Run quick analysis for API response
        velocity = monitor.analyze_collection_velocity()
        source_health = monitor.analyze_source_health()
        efficiency = monitor.analyze_collection_efficiency()
        anomalies = monitor.detect_collection_anomalies()
        
        # Generate full report
        report = monitor.generate_monitoring_report()
        
        # Save report
        report_dir = Path('data/reports')
        report_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = report_dir / f'collection_monitoring_{timestamp}.md'
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        # Return summary metrics for real-time display
        return jsonify({
            "success": True,
            "report_file": str(report_file),
            "monitoring_period": f"{hours} hours",
            "data_analyzed": data_count,
            "collection_rate": f"{velocity['avg_per_hour']:.1f} articles/hour",
            "source_health": f"{source_health['healthy_sources']}/{source_health['total_sources']} healthy",
            "quality_score": f"{efficiency['overall_efficiency'].get('avg_quality', 0):.3f}",
            "efficiency_grade": efficiency['overall_efficiency'].get('efficiency_grade', 'Unknown'),
            "anomalies_detected": {
                "quality_issues": len(anomalies['quality_drops']),
                "source_issues": len(anomalies['source_failures']),
                "volume_issues": len(anomalies['volume_anomalies'])
            },
            "peak_performance": f"{velocity['peak_hour']} ({velocity['peak_collections']} articles)",
            "recommendations_count": len(monitor._generate_recommendations(velocity, source_health, efficiency, anomalies))
        })
        
    except Exception as e:
        return jsonify({
            "error": f"Monitoring analysis failed: {str(e)}",
            "success": False
        }), 500

@app.route('/api/run_trend_analysis', methods=['POST'])
def api_run_trend_analysis():
    """Run comprehensive trend analysis."""
    try:
        from scripts.analysis.trend_analysis import TrendAnalyzer
        
        # Get analysis parameters from request
        days_back = request.json.get('days_back', 365) if request.is_json else 365
        
        # Initialize analyzer
        analyzer = TrendAnalyzer()
        
        # Load data for analysis
        data_count = analyzer.load_all_data()
        
        if data_count == 0:
            return jsonify({
                "error": "No data available for trend analysis",
                "data_count": 0,
                "days_back": days_back
            })
        
        # Generate comprehensive trend report
        report_content = analyzer.generate_trend_report()
        
        # Save report to file
        from pathlib import Path
        from datetime import datetime
        
        report_dir = Path('data/reports')
        report_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = report_dir / f'trend_analysis_{timestamp}.md'
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        # Quick trend insights for immediate response
        quality_trends = analyzer.analyze_quality_trends()
        collection_patterns = analyzer.analyze_collection_patterns()
        sentiment_trends = analyzer.analyze_sentiment_trends()
        topic_evolution = analyzer.analyze_topic_evolution()
        
        return jsonify({
            "success": True,
            "data_count": data_count,
            "analysis_summary": {
                "quality_trend": quality_trends['trend_direction'],
                "quality_improvement": quality_trends['quality_improvement'],
                "collection_consistency": collection_patterns['consistency_score'],
                "positive_sentiment": sentiment_trends['overall_sentiment']['positive'],
                "emerging_topics": len(topic_evolution['emerging_terms']),
                "declining_topics": len(topic_evolution['declining_terms'])
            },
            "report_file": str(report_file),
            "timestamp": timestamp
        })
        
    except ImportError as e:
        return jsonify({
            "error": f"Trend analysis module not available: {str(e)}",
            "suggestion": "Please ensure scripts.analysis.trend_analysis is properly installed"
        }), 500
    except Exception as e:
        return jsonify({
            "error": f"Error running trend analysis: {str(e)}",
            "type": type(e).__name__
        }), 500

@app.route('/api/run_job_market_sentiment', methods=['POST'])
def api_run_job_market_sentiment():
    """Run job market sentiment tracking analysis."""
    try:
        import subprocess
        import sys
        
        # Use subprocess to run the analysis script
        script_path = "scripts/analysis/job_market_sentiment.py"
        
        # Run the script and capture output
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode != 0:
            # Script failed
            error_msg = f"Job market sentiment analysis failed: {result.stderr}"
            status.add_log("ERROR", error_msg, "ANALYSIS")
            return jsonify({
                "error": error_msg,
                "stderr": result.stderr,
                "stdout": result.stdout
            }), 500
        
        # Parse the results from stdout if script outputs JSON
        try:
            # For now, return basic success response
            # The actual report file will be generated by the script
            import os
            import glob
            
            # Find the most recent job market sentiment report
            report_pattern = "data/reports/job_market_sentiment_*.md"
            report_files = glob.glob(report_pattern)
            
            if report_files:
                latest_report = max(report_files, key=os.path.getctime)
                file_size = os.path.getsize(latest_report)
                
                # Extract key metrics from stdout if available
                output_lines = result.stdout.strip().split('\n')
                metrics = {}
                for line in output_lines:
                    if 'Articles analyzed:' in line:
                        metrics['total_analyzed'] = line.split(':')[1].strip()
                    elif 'Overall sentiment:' in line:
                        metrics['overall_sentiment'] = line.split(':')[1].strip()
                    elif 'Opportunity/threat ratio:' in line:
                        metrics['opportunity_threat_ratio'] = line.split(':')[1].strip()
                    elif 'Top skill:' in line:
                        metrics['top_skill'] = line.split(':')[1].strip()
                    elif 'Confidence level:' in line:
                        metrics['confidence_level'] = line.split(':')[1].strip()
                
                status.add_log("INFO", f"Job market sentiment analysis completed successfully - {latest_report}", "ANALYSIS")
                
                return jsonify({
                    "success": True,
                    "report_file": latest_report,
                    "file_size": file_size,
                    "metrics": metrics,
                    "message": "Job market sentiment analysis completed successfully"
                })
            else:
                return jsonify({
                    "error": "Analysis completed but no report file found",
                    "stdout": result.stdout
                }), 404
                
        except Exception as e:
            # Return basic success if we can't parse detailed results
            status.add_log("INFO", f"Job market sentiment analysis completed with parsing issues: {e}", "ANALYSIS")
            return jsonify({
                "success": True,
                "message": "Job market sentiment analysis completed",
                "stdout": result.stdout,
                "parsing_error": str(e)
            })
        
    except subprocess.TimeoutExpired:
        error_msg = "Job market sentiment analysis timed out after 5 minutes"
        status.add_log("ERROR", error_msg, "ANALYSIS")
        return jsonify({"error": error_msg}), 408
        
    except Exception as e:
        error_msg = f"Failed to run job market sentiment analysis: {str(e)}"
        status.add_log("ERROR", error_msg, "ANALYSIS")
        return jsonify({"error": error_msg}), 500

@app.route('/api/run_ai_adoption_predictions', methods=['POST'])
def api_run_ai_adoption_predictions():
    """Run AI adoption rate predictions analysis focusing on skill demand forecasting and workforce transformation."""
    try:
        import subprocess
        import sys
        
        # Use subprocess to run the analysis script
        script_path = "scripts/analysis/ai_adoption_predictions.py"
        
        status.add_log("INFO", "Starting AI adoption predictions analysis...", "ANALYSIS")
        
        # Run the script and capture output
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode != 0:
            # Script failed
            error_msg = f"AI adoption predictions analysis failed: {result.stderr}"
            status.add_log("ERROR", error_msg, "ANALYSIS")
            return jsonify({
                "error": error_msg,
                "stderr": result.stderr,
                "stdout": result.stdout
            }), 500
        
        # Parse the results from stdout
        try:
            import os
            import glob
            
            # Find the most recent AI adoption predictions report
            report_pattern = "data/reports/ai_adoption_predictions_*.md"
            report_files = glob.glob(report_pattern)
            
            if report_files:
                latest_report = max(report_files, key=os.path.getctime)
                file_size = os.path.getsize(latest_report)
                
                # Extract key metrics from stdout if available
                output_lines = result.stdout.strip().split('\n')
                metrics = {}
                for line in output_lines:
                    if 'Articles analyzed:' in line:
                        metrics['total_analyzed'] = line.split(':')[1].strip()
                    elif 'Current adoption phase:' in line:
                        metrics['adoption_phase'] = line.split(':')[1].strip()
                    elif 'Transformation speed:' in line:
                        metrics['transformation_speed'] = line.split(':')[1].strip()
                    elif 'Top high-demand skills:' in line:
                        metrics['top_skills'] = line.split(':')[1].strip()
                
                status.add_log("INFO", f"AI adoption predictions analysis completed successfully - {latest_report}", "ANALYSIS")
                
                return jsonify({
                    "success": True,
                    "report_file": latest_report,
                    "file_size": file_size,
                    "metrics": metrics,
                    "message": "AI adoption predictions analysis completed successfully",
                    "features": [
                        "Skill demand forecasting",
                        "Workforce transformation predictions", 
                        "Technology adoption curve analysis",
                        "Strategic recommendations"
                    ]
                })
            else:
                return jsonify({
                    "error": "Analysis completed but no report file found",
                    "stdout": result.stdout
                }), 404
                
        except Exception as e:
            # Return basic success if we can't parse detailed results
            status.add_log("INFO", f"AI adoption predictions analysis completed with parsing issues: {e}", "ANALYSIS")
            return jsonify({
                "success": True,
                "message": "AI adoption predictions analysis completed",
                "stdout": result.stdout,
                "parsing_error": str(e)
            })
        
    except subprocess.TimeoutExpired:
        error_msg = "AI adoption predictions analysis timed out after 5 minutes"
        status.add_log("ERROR", error_msg, "ANALYSIS")
        return jsonify({"error": error_msg}), 408
        
    except Exception as e:
        error_msg = f"Failed to run AI adoption predictions analysis: {str(e)}"
        status.add_log("ERROR", error_msg, "ANALYSIS")
        return jsonify({"error": error_msg}), 500

def run_server(host='127.0.0.1', port=5000, debug=False):
    """Run the status server."""
    logger = get_logger('status_server')
    logger.info(f"Starting AI-Horizon Status Server on http://{host}:{port}")
    
    # Connect cost tracker to status tracker
    cost_tracker.set_status_tracker(status)
    
    # Load historical costs into status tracker
    try:
        status.api_costs.update({
            "total_cost": cost_tracker.costs.get("total_cost", 0.0),
            "perplexity_cost": cost_tracker.costs.get("api_usage", {}).get("perplexity", {}).get("cost", 0.0),
            "perplexity_calls": cost_tracker.costs.get("api_usage", {}).get("perplexity", {}).get("calls", 0)
        })
    except Exception as e:
        logger.error(f"Error loading historical costs: {e}")
    
    # Initial database stats
    try:
        db = DatabaseManager()
        artifacts = db.get_artifacts()
        status.update_stats({"total_artifacts": len(artifacts)})
        status.add_log("INFO", f"Server started with {len(artifacts)} artifacts in database", "SERVER")
    except Exception as e:
        status.add_log("ERROR", f"Database initialization error: {e}", "SERVER")
    
    app.run(host=host, port=port, debug=debug, threaded=True)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='AI-Horizon Status Server')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    run_server(args.host, args.port, args.debug) 