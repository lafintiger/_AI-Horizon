#!/usr/bin/env python3
"""
Manual Entry Web Application for AI-Horizon

Provides a web interface for manually adding articles, documents, and media sources
to the AI-Horizon pipeline database.
"""

import os
import tempfile
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from werkzeug.utils import secure_filename

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask import send_from_directory

# Adjust imports for the new folder structure
import sys
sys.path.append(str(Path(__file__).parent.parent))

from aih.utils.database import DatabaseManager
from aih.config import get_data_path
from aih.utils.logging import get_logger
from aih.chat.rag_chat import RAGChatSystem

logger = get_logger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'ai-horizon-manual-entry-secret-key'  # Change in production

# Use main project's data path instead of local one
main_project_data_path = Path(__file__).parent.parent / "data"
app.config['UPLOAD_FOLDER'] = main_project_data_path / "uploads"
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Ensure upload directory exists
app.config['UPLOAD_FOLDER'].mkdir(parents=True, exist_ok=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf', 'txt', 'docx', 'doc'}

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
    """Main dashboard showing recent entries and options."""
    db = DatabaseManager()
    
    # Get recent artifacts
    recent_artifacts = db.get_artifacts(limit=10)
    
    # Get statistics
    all_artifacts = db.get_artifacts()
    total_count = len(all_artifacts)
    
    # Count by source type
    source_counts = {}
    for artifact in all_artifacts:
        source_type = artifact.get('source_type', 'unknown')
        source_counts[source_type] = source_counts.get(source_type, 0) + 1
    
    return render_template('index.html', 
                         recent_artifacts=recent_artifacts,
                         total_count=total_count,
                         source_counts=source_counts)

@app.route('/reports')
@app.route('/reports/')
def reports_dashboard():
    """Serve the main analysis reports dashboard."""
    reports_dir = Path(__file__).parent.parent / "data" / "reports"
    report_file = reports_dir / "ai_horizon_analysis_report.html"
    
    if report_file.exists():
        return send_from_directory(reports_dir, "ai_horizon_analysis_report.html")
    else:
        flash('Analysis report not found. Please generate it first using generate_web_report.py', 'error')
        return redirect(url_for('index'))

@app.route('/reports/<path:filename>')
def serve_reports(filename):
    """Serve report files (CSS, images, methodology, etc.)."""
    reports_dir = Path(__file__).parent.parent / "data" / "reports"
    return send_from_directory(reports_dir, filename)

@app.route('/manage_prompts')
def manage_prompts():
    """Manage search prompts interface."""
    try:
        # Get current prompts from config or defaults
        prompts = {
            'replace': """CYBERSECURITY TASK AUTOMATION 2024-2025:

Find authoritative sources on AI COMPLETELY REPLACING cybersecurity tasks:

KEY INDICATORS:
• SIEM/log analysis fully automated (no human analysts needed)
• AI threat detection replacing human SOC analysis entirely  
• Autonomous incident response eliminating human decision-making
• Vulnerability management completely automated
• "Lights-out" security operations (no human oversight)
• AI taking over compliance checking and reporting

FOCUS: Look for evidence of cybersecurity TASKS being eliminated, not just job roles changing.

PRIORITY SOURCES: Gartner, Forrester, SANS, NIST publications, academic studies""",
            
            'augment': """CYBERSECURITY TASK AUGMENTATION 2024-2025:

Find sources on AI ASSISTING and ENHANCING cybersecurity task performance:

KEY INDICATORS:
• AI copilots for threat analysis tasks
• ML-enhanced log analysis requiring human oversight
• AI-assisted incident investigation with human decision-making
• Automated threat hunting with human validation
• AI-enhanced compliance monitoring with human review
• Human-AI collaboration in vulnerability assessment

FOCUS: Look for evidence of cybersecurity TASKS being enhanced or made more efficient through AI assistance.

PRIORITY SOURCES: SANS surveys, vendor case studies, practitioner reports""",
            
            'new_tasks': """EMERGING CYBERSECURITY TASKS 2024-2025:

Find sources on NEW cybersecurity tasks created by AI technology adoption:

KEY INDICATORS:
• AI model security and adversarial testing tasks
• AI governance and ethics tasks in cybersecurity
• Prompt engineering for security applications
• AI bias detection and mitigation in security tools
• AI model validation and monitoring tasks
• AI-related compliance and audit tasks

FOCUS: Look for evidence of completely NEW cybersecurity tasks that didn't exist before AI adoption.

PRIORITY SOURCES: Job market reports, DCWF updates, skills framework studies""",
            
            'human_only': """HUMAN-ESSENTIAL CYBERSECURITY TASKS 2024-2025:

Find sources on cybersecurity tasks that REMAIN purely human-driven:

KEY INDICATORS:
• Strategic security planning requiring human judgment
• Crisis communication and stakeholder management tasks
• Legal and ethical decision-making in security incidents
• Creative threat modeling and red team strategy development
• Complex forensic investigation requiring human intuition
• High-stakes incident command and coordination

FOCUS: Look for evidence of cybersecurity TASKS that cannot be automated and require uniquely human capabilities.

PRIORITY SOURCES: CISO perspectives, DCWF task specifications, security leadership studies"""
        }
        
        return render_template('manage_prompts.html', prompts=prompts)
    except Exception as e:
        logger.error(f"Error loading prompts management: {e}")
        flash(f'Error loading prompts: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/process_pipeline')
def process_pipeline():
    """Process collected articles through the AI categorization pipeline."""
    try:
        # Get unprocessed articles from database
        db = DatabaseManager()
        artifacts = db.get_artifacts(limit=100)
        
        if not artifacts:
            flash('No articles found to process. Please add some content first.', 'warning')
            return redirect(url_for('index'))
        
        # Count articles by type
        manual_artifacts = [a for a in artifacts if a.get('source_type', '').startswith('manual_')]
        
        if not manual_artifacts:
            flash('No manually entered articles found to process.', 'warning')
            return redirect(url_for('index'))
        
        # For now, show processing interface (can be enhanced to actually run pipeline)
        return render_template('process_pipeline.html', 
                             artifacts=manual_artifacts,
                             total_count=len(manual_artifacts))
        
    except Exception as e:
        logger.error(f"Error in process pipeline: {e}")
        flash(f'Error accessing pipeline: {str(e)}', 'error')
        return redirect(url_for('index'))

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
                return redirect(url_for('index'))
            
            # Check if it's a YouTube URL
            if is_youtube_url(url):
                return redirect(url_for('add_youtube', prefill_url=url, 
                                      prefill_title=title, prefill_category=category))
            
            # Try to fetch actual content from URL
            content = f"Manual URL entry. Notes: {notes}" if notes else "Manual URL entry."
            try:
                import requests
                from bs4 import BeautifulSoup
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Extract title if not provided
                    if not title:
                        title_tag = soup.find('title')
                        if title_tag:
                            title = title_tag.get_text().strip()
                    
                    # Extract main content
                    # Try common content selectors
                    content_selectors = [
                        'article', '.article-content', '.post-content', 
                        '.content', 'main', '.story-body', '.entry-content'
                    ]
                    
                    extracted_content = ""
                    for selector in content_selectors:
                        content_elem = soup.select_one(selector)
                        if content_elem:
                            # Get text and clean it up
                            extracted_content = content_elem.get_text(separator=' ', strip=True)
                            break
                    
                    # If no specific content area found, try to get paragraphs
                    if not extracted_content:
                        paragraphs = soup.find_all('p')
                        if paragraphs:
                            extracted_content = ' '.join([p.get_text(strip=True) for p in paragraphs[:10]])  # First 10 paragraphs
                    
                    if extracted_content and len(extracted_content) > 100:  # Only use if substantial content
                        content = extracted_content
                        if notes:
                            content += f"\n\nNotes: {notes}"
                        flash('Successfully fetched article content from URL!', 'success')
                    else:
                        flash('Could not extract substantial content from URL, saved with notes only.', 'warning')
                        
            except Exception as e:
                logger.warning(f"Could not fetch content from {url}: {e}")
                flash('Could not fetch content from URL, saved with notes only.', 'info')
            
            # Create artifact entry
            artifact_data = {
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
            
            # Save to database
            artifact_id = db.save_artifact(artifact_data)
            
            flash(f'Successfully added URL: {title or url}', 'success')
            logger.info(f"Manual URL added: {artifact_id} - {url}")
            
            return redirect(url_for('index'))
            
        except Exception as e:
            flash(f'Error adding URL: {str(e)}', 'error')
            logger.error(f"Error adding URL {url}: {e}")
    
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
            from manual_entry_processors import process_document
            content = process_document(file_path)
            
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
            logger.info(f"Manual file added: {artifact_id} - {filename}")
            
            return redirect(url_for('index'))
            
        except Exception as e:
            flash(f'Error processing file: {str(e)}', 'error')
            logger.error(f"Error processing file {file.filename}: {e}")
    
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
                return redirect(url_for('index'))
            
            # Extract transcript
            from manual_entry_processors import extract_youtube_transcript
            transcript_data = extract_youtube_transcript(url)
            
            if not transcript_data:
                flash('Could not extract transcript from YouTube video. Video may not have captions.', 'error')
                return render_template('add_youtube.html', 
                                     prefill_url=url, prefill_title=title, prefill_category=category)
            
            # Create artifact entry
            artifact_data = {
                'id': f"manual_youtube_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'url': url,
                'title': title or transcript_data.get('title', f"YouTube Video: {url}"),
                'content': transcript_data.get('transcript', ''),
                'source_type': 'manual_youtube',
                'collected_at': datetime.now(),
                'metadata': {
                    'entry_method': 'manual_youtube',
                    'category': category,
                    'notes': notes,
                    'video_id': extract_youtube_id(url),
                    'video_title': transcript_data.get('title', ''),
                    'duration': transcript_data.get('duration', ''),
                    'channel': transcript_data.get('channel', ''),
                    'added_by': 'manual_interface'
                }
            }
            
            # Save to database
            artifact_id = db.save_artifact(artifact_data)
            
            flash(f'Successfully added YouTube video with transcript: {title or transcript_data.get("title", url)}', 'success')
            logger.info(f"Manual YouTube added: {artifact_id} - {url}")
            
            return redirect(url_for('index'))
            
        except Exception as e:
            flash(f'Error adding YouTube video: {str(e)}', 'error')
            logger.error(f"Error adding YouTube {url}: {e}")
    
    return render_template('add_youtube.html', 
                         prefill_url=prefill_url, 
                         prefill_title=prefill_title, 
                         prefill_category=prefill_category)

@app.route('/view_artifact/<artifact_id>')
def view_artifact(artifact_id):
    """View detailed information about an artifact."""
    db = DatabaseManager()
    artifact = db.get_artifact_by_id(artifact_id)
    
    if not artifact:
        flash('Artifact not found!', 'error')
        return redirect(url_for('index'))
    
    return render_template('view_artifact.html', artifact=artifact)

@app.route('/delete_artifact/<artifact_id>', methods=['POST'])
def delete_artifact(artifact_id):
    """Delete an artifact from the database."""
    try:
        db = DatabaseManager()
        artifact = db.get_artifact_by_id(artifact_id)
        
        if not artifact:
            flash('Artifact not found!', 'error')
            return redirect(url_for('index'))
        
        # TODO: Implement delete functionality in database manager
        flash('Delete functionality will be implemented soon!', 'info')
        
    except Exception as e:
        flash(f'Error deleting artifact: {str(e)}', 'error')
        logger.error(f"Error deleting artifact {artifact_id}: {e}")
    
    return redirect(url_for('index'))

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
    """RAG chat interface for talking with collected articles."""
    try:
        # Initialize RAG system with Claude 3.7 as default
        rag_system = RAGChatSystem(model="claude-3-7-sonnet-20250219")
        
        # Get article summary for context
        summary = rag_system.get_article_summary()
        
        return render_template('chat.html', 
                             article_summary=summary,
                             available_models=[
                                 'claude-3-7-sonnet-20250219',  # Latest Claude 3.7
                                 'claude-4-sonnet-20250514',    # Claude 4 Sonnet  
                                 'claude-4-opus-20250514',      # Claude 4 Opus
                                 'claude-3-5-sonnet-20241022',  # Previous Claude 3.5
                                 'gpt-4o',                       # GPT-4o
                                 'gpt-4',                        # GPT-4
                                 'gpt-3.5-turbo'                # GPT-3.5 Turbo
                             ])
    except Exception as e:
        logger.error(f"Error loading chat interface: {e}")
        flash(f'Error loading chat interface: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/api/chat', methods=['POST'])
def api_chat():
    """API endpoint for RAG chat functionality."""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        model = data.get('model', 'claude-3-7-sonnet-20250219')
        category_filter = data.get('category_filter')
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        # Initialize RAG system with selected model
        rag_system = RAGChatSystem(model=model)
        
        # Process chat query
        result = rag_system.chat(query, category_filter)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in chat API: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/article_summary')
def api_article_summary():
    """API endpoint to get article summary for chat context."""
    try:
        category = request.args.get('category')
        rag_system = RAGChatSystem()
        summary = rag_system.get_article_summary(category)
        return jsonify(summary)
    except Exception as e:
        logger.error(f"Error getting article summary: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting AI-Horizon Manual Entry Interface")
    print("=" * 50)
    print("📝 Features:")
    print("  • Manual URL entry")
    print("  • File uploads (PDF, TXT, DOCX)")
    print("  • YouTube transcript extraction")
    print("  • Database integration")
    print("  • Search prompts management")
    print("  • RAG chat interface")
    print("=" * 50)
    print("🌐 Open http://localhost:5000 in your browser")
    print("⚠️  Press Ctrl+C to stop the server")
    
    app.run(debug=True, host='0.0.0.0', port=5000) 