# AI-Horizon: Cybersecurity Workforce Intelligence System

A comprehensive system for analyzing AI's impact on cybersecurity workforce through automated data collection, expert curation, and academic-grade analysis with integrated quality scoring.

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
- **Quality Scoring**: Academic-grade content assessment with color-coded indicators

### 📊 Advanced Quality Ranking System
- **Document Quality Scores**: Real-time quality assessment for all content
- **Visual Quality Indicators**: Color-coded badges (Excellent/Good/Fair/Poor)
- **Quality-Based Sorting**: Highest quality content displayed first
- **Comprehensive Scoring Metrics**: Content depth, source credibility, relevance assessment

### 📝 Manual Entry System
- **Document Upload**: PDF, TXT, DOCX processing with full text extraction
- **YouTube Processing**: Automatic transcript extraction from videos
- **URL Collection**: Direct article link addition with duplicate checking
- **Expert Curation**: Human oversight for high-quality source selection

### 🎛️ Advanced Management
- **Real-time Web Interface**: Modern dashboard with live status updates
- **Comprehensive Logging**: Complete audit trail of all operations
- **Progress Tracking**: Detailed analytics on collection effectiveness
- **Cost Analysis**: API usage tracking and budget optimization tools

### 📊 Analysis & Reporting  
- **Interactive Dashboard**: Category-based analysis with quality indicators
- **Source Credibility**: Multi-factor authority assessment
- **Wisdom Extraction**: AI-powered insight generation from all content
- **Academic Rigor**: NSF-compliant documentation and citations

## 🚀 Quick Start

### Web Interface (Recommended)
```bash
# Start the comprehensive web interface
python status_server.py --host 0.0.0.0 --port 5000

# Access at http://localhost:5000
# Features: Dashboard, manual entry, quality scoring, reports
```

### Command Line Operations
```bash
# Generate analysis report
python scripts/generate_web_report.py

# Run quality analysis
python scripts/analysis/analyze_successful_articles.py

# Process manual entries
python scripts/manual_entry/manual_entry_processor.py
```

### Data Collection
```bash
# Comprehensive collection
python scripts/collection/collect_comprehensive.py

# Targeted high-value sources
python scripts/collection/collect_targeted_sources.py

# Student intelligence collection
python scripts/collection/collect_student_intelligence.py
```

## 📁 Project Structure

The project follows professional software engineering practices with organized directories:

```
AI-Horizon/
├── status_server.py              # Main web interface server
├── aih/                          # Core pipeline
│   ├── gather/                   # Data collection
│   ├── classify/                 # AI categorization  
│   └── utils/                    # Utilities & database
├── scripts/                      # Organized utility scripts
│   ├── fixes/                    # Bug fixes & repairs
│   ├── analysis/                 # Quality control & analysis
│   ├── collection/               # Data collection scripts
│   └── manual_entry/             # Manual entry processing
├── tests/                        # Test files
├── docs/                         # Documentation
├── templates/                    # Web interface templates
├── data/                         # Data storage
│   ├── reports/                  # Generated analysis reports
│   ├── uploads/                  # Uploaded documents
│   ├── rag_cache/                # RAG system cache
│   └── logs/                     # System logs
└── manual_entry/                 # Manual entry system
```

See [File Organization Guide](docs/FILE_ORGANIZATION.md) for detailed structure documentation.

## 🏆 Quality Scoring System

### Document Quality Metrics
- **Content Depth Score**: Text complexity and information density
- **Source Authority Score**: Domain credibility and publication standards  
- **Relevance Score**: Topic alignment and career applicability
- **Completeness Score**: Article structure and information coverage

### Visual Quality Indicators
- **🟢 Excellent (0.8+)**: High-quality, comprehensive content
- **🟡 Good (0.6-0.8)**: Solid content with good insights
- **🟠 Fair (0.4-0.6)**: Acceptable content, some limitations
- **🔴 Poor (<0.4)**: Low quality, needs review or removal

### Quality-Based Features
- Automatic sorting by quality score (highest first)
- Quality-filtered search and browsing
- Quality improvement recommendations
- Historical quality tracking

## 🔧 Installation

### Core Dependencies
```bash
pip install -r requirements.txt
```

### Environment Setup
```bash
# Copy environment template
cp env.example .env

# Edit with your API keys
# Required: PERPLEXITY_API_KEY
# Optional: OPENAI_API_KEY, ANTHROPIC_API_KEY
```

### Web Interface Dependencies
```bash
# All web interface dependencies included in requirements.txt
# Flask, quality ranking, cost tracking, etc.
```

## 📚 Academic Foundation

The system employs academically rigorous methodologies with proper citations:

### Scoring Algorithms
- **Content Quality**: Multi-dimensional assessment including readability, depth, and completeness
- **Source Credibility**: Domain authority, publication standards, and citation patterns
- **Semantic Similarity**: Advanced embedding-based content analysis
- **Category Confidence**: Machine learning classification with uncertainty quantification

### Quality Ranking Implementation
- **DocumentQualityRanker**: Comprehensive scoring system in `scripts/analysis/implement_quality_ranking.py`
- **Real-time Calculation**: Quality scores computed on-demand for all content
- **Multi-factor Assessment**: Combines multiple quality dimensions for robust evaluation
- **Continuous Improvement**: Quality metrics refined based on expert feedback

### Key References
- Academic citations maintained in methodology documentation
- Quality scoring methodology based on information retrieval research
- Source credibility assessment following established frameworks
- Content analysis using validated NLP techniques

## 🎯 NSF Project Integration

Designed specifically for NSF research requirements:

- **Reproducible Methods**: Complete workflow documentation with academic citations
- **Quality Assurance**: Automated quality scoring with manual validation
- **Audit Trails**: Comprehensive logging of all operations and decisions
- **Transparent Analysis**: Open methodology with documented assumptions and limitations
- **Professional Standards**: Organized codebase following software engineering best practices

## 📊 Web Interface Features

### Main Dashboard
- **Real-time Status**: Live collection progress and system health
- **Database Statistics**: Current content counts by category
- **Quality Overview**: Distribution of content quality scores
- **Cost Tracking**: API usage and budget monitoring

### Browse & Manage Content
- **Quality-Sorted Browsing**: Content ordered by quality score
- **Visual Quality Indicators**: Color-coded quality badges
- **Detailed View**: Full content analysis with quality metrics
- **Manual Entry**: Upload documents, URLs, and YouTube videos

### Collection Operations
- **Automated Collection**: Background data gathering with progress tracking
- **Targeted Sources**: High-value source collection
- **Student Intelligence**: Career-focused content collection
- **Manual Processing**: Expert curation and validation

### Reports & Analysis
- **Interactive Reports**: Dynamic analysis with quality filters
- **Export Capabilities**: Multiple format support for sharing
- **Quality Analytics**: Content quality trends and improvements
- **Cost Analysis**: Budget optimization and usage patterns

## 🔍 System Capabilities

### Data Sources
- **Automated**: Perplexity AI aggregated search results
- **Manual**: Expert-curated documents, videos, and articles
- **Media**: YouTube transcripts from conferences and webinars
- **Documents**: Research papers, reports, whitepapers

### Processing Pipeline
1. **Collection**: Multi-source data gathering with quality filters
2. **Processing**: Text extraction, cleaning, and normalization  
3. **Quality Assessment**: Real-time quality scoring and ranking
4. **Classification**: AI-powered categorization with confidence scoring
5. **Wisdom Extraction**: AI-generated insights and career implications
6. **Analysis**: Statistical analysis and trend identification
7. **Reporting**: Interactive dashboards with quality indicators

### Quality Assurance
- **Real-time Quality Scoring**: Continuous assessment of all content
- **Duplicate Detection**: URL-based deduplication across all sources
- **Source Validation**: Authority assessment and credibility scoring
- **Content Analysis**: Readability, completeness, and relevance metrics
- **Expert Review**: Manual oversight and validation processes

## 🚀 Future Enhancements

- **Advanced Quality Metrics**: Machine learning-based quality prediction
- **Collaborative Quality Assessment**: Multi-expert quality validation
- **Quality Trend Analysis**: Longitudinal quality improvement tracking
- **Enhanced NLP**: Latest transformer models for content analysis
- **API Integration**: Real-time data feeds from industry sources
- **Export Capabilities**: Academic paper and report generation

## 📄 License

MIT License - See LICENSE file for details.

## 🤝 Contributing

Contributions welcome! The organized file structure makes it easy to contribute:
- Bug fixes: `scripts/fixes/`
- Analysis tools: `scripts/analysis/`
- Collection improvements: `scripts/collection/`
- Tests: `tests/`
- Documentation: `docs/`

## 📞 Support

For questions about the quality scoring system, file organization, or any other features, please refer to the documentation in the `docs/` directory or examine the well-organized code structure. 