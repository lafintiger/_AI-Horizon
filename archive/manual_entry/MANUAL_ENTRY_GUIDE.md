# AI-Horizon Manual Entry System

A comprehensive web interface for manually adding articles, documents, and media sources to the AI-Horizon database.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Install additional dependencies for manual entry
pip install Flask PyPDF2 pdfplumber python-docx youtube-transcript-api yt-dlp
```

### 2. Test the System

```bash
# Run the test script to verify everything works
python test_manual_entry.py
```

### 3. Start the Web Interface

```bash
# Start the Flask web server
python manual_entry_app.py
```

### 4. Open in Browser

Navigate to [http://localhost:5000](http://localhost:5000) in your web browser.

## ✨ Features

### 📝 Manual URL Entry
- Add any article or webpage URL
- Automatic duplicate detection
- YouTube URLs automatically redirected to video processor
- Category classification for AI impact analysis

### 📄 Document Upload
- **Supported formats:** PDF, TXT, DOCX, DOC
- **Drag & drop interface** with file validation
- **Text extraction** from all document types
- **50MB maximum file size**

### 🎥 YouTube Video Processing
- **Transcript extraction** from YouTube videos
- Support for auto-generated and manual captions
- **Video preview** with embedded player
- **Metadata collection** (title, channel, duration)

### 🔍 Smart Features
- **Duplicate detection** across all entry types
- **Category classification** for AI impact analysis
- **Metadata preservation** for source tracking
- **Content search and filtering**

## 📋 Supported File Types

| Type | Extensions | Processing Method |
|------|------------|-------------------|
| **Text** | `.txt` | Direct text import with encoding detection |
| **PDF** | `.pdf` | Text extraction using PyPDF2 or pdfplumber |
| **Word** | `.docx`, `.doc` | Full document parsing with python-docx |
| **Video** | YouTube URLs | Transcript extraction via API |

## 🎯 AI Impact Categories

When adding content, classify it into these categories:

- **Replace:** Tasks that AI will completely replace
- **Augment:** Tasks requiring AI assistance to perform effectively  
- **New Tasks:** Jobs/roles created because of AI developments
- **Human-Only:** Tasks that remain predominantly human-driven

## 🛠 Technical Details

### File Processing

The system uses multiple libraries for robust document processing:

- **PDF:** PyPDF2 (primary) → pdfplumber (fallback)
- **DOCX:** python-docx for full document parsing
- **TXT:** Built-in with multi-encoding support
- **YouTube:** youtube-transcript-api (primary) → yt-dlp (fallback)

### Database Integration

All manually entered content is automatically:

1. **Stored** in the SQLite database
2. **Indexed** with metadata and categories
3. **Made available** for AI classification
4. **Included** in analysis reports

### Web Interface

Built with Flask and Bootstrap 5:

- **Responsive design** works on desktop and mobile
- **Real-time validation** for URLs and files
- **Progress indicators** for long operations
- **Error handling** with helpful messages

## 📊 Integration with AI-Horizon

### Workflow Integration

```mermaid
graph LR
    A[Manual Entry] --> B[Database Storage]
    B --> C[AI Classification]
    C --> D[Analysis Reports]
    D --> E[Strategic Insights]
```

### Data Flow

1. **Manual Entry** → Content added via web interface
2. **Processing** → Text extraction and metadata collection
3. **Storage** → Saved to database with duplicate detection
4. **Classification** → AI analysis of content categories
5. **Reporting** → Included in comprehensive analysis reports

## 🔧 Troubleshooting

### Common Issues

**Dependencies Missing:**
```bash
pip install PyPDF2 pdfplumber python-docx youtube-transcript-api yt-dlp
```

**Port Already in Use:**
```bash
# Change port in manual_entry_app.py
app.run(debug=True, host='0.0.0.0', port=5001)
```

**File Upload Fails:**
- Check file size (50MB limit)
- Verify file format is supported
- Ensure sufficient disk space

**YouTube Transcript Fails:**
- Video may not have captions enabled
- Network connectivity issues
- Video may be private/restricted

### Dependency Issues

| Issue | Solution |
|-------|----------|
| PDF processing fails | `pip install PyPDF2 pdfplumber` |
| DOCX processing fails | `pip install python-docx` |
| YouTube processing fails | `pip install youtube-transcript-api yt-dlp` |
| Flask import error | `pip install Flask` |

## 💡 Best Practices

### Content Quality

- **Use descriptive titles** for better organization
- **Add relevant notes** about why content is important
- **Choose appropriate categories** for AI impact analysis
- **Verify URLs** before submission

### File Management

- **Use clear filenames** for uploaded documents
- **Keep files under 50MB** for optimal performance
- **Prefer text-based formats** (PDF, DOCX) over images
- **Check document quality** before upload

### YouTube Videos

- **Verify captions exist** before processing
- **Use conference/webinar videos** for better content
- **Check video accessibility** (not private/restricted)
- **Prefer educational content** over casual videos

## 🔗 Integration Examples

### Adding Research Papers

1. **Find PDF** from academic source (arXiv, IEEE, etc.)
2. **Download** and upload via file interface
3. **Categorize** based on AI impact focus
4. **Add notes** about key findings

### Processing Conference Videos

1. **Find YouTube URL** from cybersecurity conference
2. **Verify captions** are available
3. **Process** via YouTube interface
4. **Review transcript** for accuracy

### Curating News Articles

1. **Copy article URL** from news site
2. **Add via URL interface** 
3. **Classify impact category**
4. **Note relevance** to workforce analysis

## 📈 Analytics Integration

The manual entry system seamlessly integrates with the AI-Horizon analytics pipeline:

- **Content Analysis:** All manually added content is processed through the same AI classification system
- **Source Diversity:** Manual entries add breadth to automated collection
- **Quality Control:** Human curation ensures high-quality sources
- **Gap Filling:** Manual entry can target specific topics missing from automated searches

## 🔄 Updates and Maintenance

### Regular Tasks

- **Monitor disk usage** for uploaded files
- **Review duplicate detection** effectiveness
- **Update dependencies** as needed
- **Check processing accuracy** periodically

### System Health

Run the test script regularly to ensure all components are working:

```bash
python test_manual_entry.py
```

This validates:
- ✅ Dependency availability
- ✅ File processing capabilities
- ✅ YouTube API connectivity
- ✅ Database integration
- ✅ Web interface functionality

## 🎉 Conclusion

The AI-Horizon Manual Entry System provides a powerful, user-friendly way to enhance your cybersecurity workforce analysis with curated content. By combining automated collection with manual curation, you can ensure comprehensive coverage of the evolving AI impact landscape. 