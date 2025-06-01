# AI-Horizon: Cybersecurity Workforce Intelligence System

A comprehensive system for analyzing AI's impact on cybersecurity workforce through automated data collection, expert curation, and academic-grade analysis.

## 🎯 System Overview

AI-Horizon combines automated search capabilities with manual curation to provide evidence-based insights into how artificial intelligence is transforming cybersecurity roles. The system categorizes AI impact into four key areas:

- **🤖 REPLACE**: Tasks completely automated by AI
- **🤝 AUGMENT**: Human-AI collaboration enhancing capabilities  
- **⭐ NEW TASKS**: Jobs created due to AI technology
- **👤 HUMAN-ONLY**: Tasks requiring uniquely human expertise

## ✨ Key Features

### 🔍 Automated Data Collection
- **Multi-Query Search**: Task-focused searches across all categories
- **Real Source URLs**: Authentic source links with publication dates
- **Duplicate Detection**: Intelligent filtering to grow unique dataset
- **Quality Scoring**: Academic-grade content assessment algorithms

### 📝 Manual Entry System
- **Document Upload**: PDF, TXT, DOCX processing with full text extraction
- **YouTube Processing**: Automatic transcript extraction from videos
- **URL Collection**: Direct article link addition with duplicate checking
- **Expert Curation**: Human oversight for high-quality source selection

### 🎛️ Advanced Management
- **Prompts Management**: View, edit, and test search prompts in real-time
- **Comprehensive Logging**: Complete audit trail of all search operations
- **Academic Citations**: Proper references for all scoring methodologies
- **Progress Tracking**: Detailed analytics on collection effectiveness

### 📊 Analysis & Reporting  
- **Interactive Dashboard**: Category-based analysis with clickable indicators
- **Source Credibility**: Multi-factor authority assessment
- **Trend Analysis**: Temporal patterns in AI workforce impact
- **Academic Rigor**: NSF-compliant documentation and citations

## 🚀 Quick Start

### Option 1: Automated Reports Only
```bash
# Generate analysis report
python generate_web_report.py

# Start web server (reports available at localhost:8080)
python -m http.server 8080 --directory data/reports
```

### Option 2: Manual Entry System
```bash
# Launch comprehensive interface
python launch_manual_entry.py

# Access at http://localhost:5000
# Features: URL entry, file upload, YouTube processing, prompts management
```

### Option 3: Data Collection
```bash
# Collect new articles (multi-query with duplicates filtering)  
python -m aih.gather.cli collect --multi-query --skip-duplicates --max-results 20

# Run strategic analysis
python test_strategic_simple.py
```

## 📁 Project Structure

```
AI-Horizon/
├── aih/                          # Core pipeline
│   ├── gather/                   # Data collection
│   ├── classify/                 # AI categorization  
│   └── utils/                    # Utilities
│       ├── academic_references.py  # Academic citations
│       └── search_logger.py       # Comprehensive logging
├── manual_entry/                 # Manual curation system
│   ├── manual_entry_app.py       # Flask web interface
│   ├── manual_entry_processors.py # Document processing
│   └── templates/                # Web interface templates
├── data/                         # Data storage
│   ├── reports/                  # Generated analysis reports
│   ├── uploads/                  # Uploaded documents
│   └── logs/searches/            # Search operation logs
├── generate_web_report.py        # Report generation
├── launch_manual_entry.py        # Manual entry launcher
└── share_reports.py              # Public sharing via ngrok
```

## 🔧 Installation

### Core Dependencies
```bash
pip install -r requirements.txt
```

### Manual Entry Additional Dependencies  
```bash
pip install Flask PyPDF2 pdfplumber python-docx youtube-transcript-api yt-dlp
```

### Environment Setup
```bash
# Copy environment template
cp env.example .env

# Edit with your API keys
# Required: PERPLEXITY_API_KEY
# Optional: OPENAI_API_KEY, ANTHROPIC_API_KEY
```

## 📚 Academic Foundation

The system employs academically rigorous methodologies with proper citations:

### Scoring Algorithms
- **Content Quality**: Flesch-Kincaid readability + TF-IDF weighting + information theory
- **Source Credibility**: Multi-factor assessment based on domain authority research  
- **Semantic Similarity**: BERT embeddings with cosine similarity measurement
- **Category Confidence**: Logistic regression with sigmoid normalization

### Key References
- Salton & Buckley (1988): TF-IDF term weighting
- Reimers & Gurevych (2019): Sentence-BERT embeddings
- Castillo et al. (2011): Information credibility assessment
- Manning et al. (2008): Information retrieval metrics

*Full bibliography available in methodology documentation.*

## 🎯 NSF Project Integration

Designed specifically for NSF research requirements:

- **Reproducible Methods**: Complete workflow documentation with academic citations
- **Audit Trails**: Comprehensive logging of all search operations and decisions
- **Quality Assurance**: Multi-layer validation through automated and manual processes
- **Transparent Analysis**: Open methodology with documented assumptions and limitations

## 📊 Usage Examples

### Automated Weekly Collection
```bash
python -m aih.gather.cli collect-weekly --max-results 20 --skip-duplicates
```

### Manual Expert Curation
```bash
python launch_manual_entry.py
# Access web interface for document upload, YouTube processing, prompt management
```

### Analysis Report Generation
```bash
python generate_web_report.py
# Creates interactive HTML dashboard with methodology documentation
```

### Public Report Sharing
```bash
python share_reports.py
# Uses ngrok to create public URLs for stakeholder access
```

## 🔍 System Capabilities

### Data Sources
- **Automated**: Perplexity AI aggregated search results
- **Manual**: Expert-curated documents, videos, and articles
- **Media**: YouTube transcripts from conferences and webinars
- **Documents**: Research papers, reports, whitepapers

### Processing Pipeline
1. **Collection**: Multi-source data gathering with quality filters
2. **Processing**: Text extraction, cleaning, and normalization  
3. **Classification**: AI-powered categorization with confidence scoring
4. **Analysis**: Statistical analysis and trend identification
5. **Reporting**: Interactive dashboards with source attribution

### Quality Assurance
- **Duplicate Detection**: URL-based deduplication across all sources
- **Source Validation**: Authority assessment and credibility scoring
- **Content Analysis**: Readability, completeness, and relevance metrics
- **Expert Review**: Manual oversight and validation processes

## 🚀 Future Enhancements

- **Longitudinal Analysis**: Multi-temporal trend tracking
- **Advanced NLP**: Enhanced classification with latest transformer models
- **API Integration**: Real-time data feeds from industry sources
- **Collaborative Features**: Multi-user annotation and validation
- **Export Capabilities**: Academic paper and report generation

## 📄 License

MIT License - See LICENSE file for details.

## 🤝 Contributing

Contributions welcome! Please read contributing guidelines and submit pull requests for review.

---

*AI-Horizon: Evidence-based cybersecurity workforce intelligence for the AI era.* 