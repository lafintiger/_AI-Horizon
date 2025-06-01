# AI Horizon Forecasting Pipeline
Forecasting the Evolution of Cybersecurity Work in the Age of AI
Last updated: May 27, 2025
AI Horizon Forecasting Pipeline Forecasting the Evolution of Cybersecurity Work in the Age of AI Last updated: May 27, 2025
I. Foundational Assumptions (Logically Sequenced)
A. Global and Economic Drivers
Market forces drive the adoption of AI. Companies have a fiduciary duty to maximize profit. Labor is a cost, and AI adoption becomes imperative when it can reduce this cost or increase output.
Organizations will adopt AI where it is faster, better, safer, or cheaper. If AI improves performance without increasing risk, organizations are compelled to use it. Non-adoption becomes a competitive disadvantage.
Nations will not voluntarily slow AI development. Geopolitical competition (economic, military, informational) incentivizes acceleration of AI research, deployment, and integration. National security depends on it.
B. Organizational and Educational Consequences
AI will displace or augment many cybersecurity tasks. This is already observable in automation of coding, compliance, monitoring, and report generation.
Educational lag is a critical national security risk. Curriculum updates currently take years. Students may graduate with outdated skills, weakening national cyber-readiness.
New tasks and job roles will emerge as AI advances. Innovation doesn’t just destroy — it creates. Emerging technologies historically birth entire new categories of work.
C. Task and Role Structure
Work evolves at the task level, not just the role level. Roles are aggregations of tasks. Understanding the AI impact requires analyzing task transformation, not job titles.
The DCWF task list provides a universal model of cybersecurity work. Despite variability in job titles across sectors, the DCWF offers a stable taxonomy of discrete, transferable job tasks.
D. Observability and Methodology
AI's impact on cybersecurity can be observed through public digital artifacts. Public reports, job posts, blogs, whitepapers, and videos provide sufficient visibility into industry trends and behaviors.
Some claims about AI’s impact are overstated or speculative. Evidence must be critically evaluated. Hype must be separated from reality to avoid poor forecasting.
Human cognitive capabilities (e.g., ethics, ambiguity-resolution, empathy) will remain essential. These qualities are unlikely to be replicated by current AI and will preserve human relevance in many tasks.
II. Key Indicators for Forecasting
Indicators define what the agents will scan for. The quality of indicators determines the success of evidence acquisition.
Primary Indicators
Cybersecurity layoffs or downsizing, especially tied to automation or AI.
Job postings that require AI familiarity, no longer list legacy skills, or cluster around new roles.
Reports or blogs demonstrating new AI capabilities.
Statements from CEOs, CTOs, CISOs about hiring changes or AI implementation.
Technical documentation showing AI completing former human tasks.
Videos (e.g., on YouTube) demonstrating AI replacing work.
Government regulations affecting AI adoption or requiring AI skills.
Evidence of major gains in productivity from AI that reduce task volume.
Clear creation of new job roles or skillsets.
Additional Indicators
Patent filings (USPTO, WIPO) on AI-driven security automation.
Academic conference abstracts on AI replacing analyst or engineering tasks.
Product launch announcements from major vendors marketing AI-replacement tools.
Job boards shrinking listings for certain roles (e.g., SOC Tier 1).
Online course catalogs (Coursera, Pluralsight, Udemy) showing rising demand for “AI + Cyber” skills.
Mentions of AI in breach reports (both attacker and defender context).
AI startup funding rounds specifically citing elimination of human analysts.
III. Forecasting Pipeline: End-to-End Process
Artifact Acquisition Layer Weekly scans via web search, APIs, RSS, YouTube, etc. Input: curated keyword–indicator mappings. Includes manual upload option for committee assistants.
Artifact Scoring & Classification Each artifact is tagged and scored on Credibility, Recency, Impact, and Specificity. Classified into Replace, Augment, Remain Human, New Task. Each task gets a confidence score and explanation.
DCWF Task Mapping Parse the DCWF spreadsheet and map each artifact to specific tasks, then aggregate into work roles.
Reporting Output Generate narrative summaries per role and structured CSVs listing task ID, forecast, confidence, rationale, source URL, and impact score. Reports are generated weekly and posted to a website or internal portal.
Human Oversight & Querying Assistants and committee members can view/edit artifact classifications, add new artifacts, override AI decisions, and query task forecasts.
Logging & Evaluation Support Track artifacts, edits, commonly referenced summaries. Feed evaluation metrics to Redwood Consulting for process audit and performance measurement.
Transparency and Versioning Contradictory evidence will be retained and reflected. Every recommendation must be traceable to the specific artifacts that informed it, how each was scored, and how the recommendation was determined.
Feedback Loop and Continuous Improvement The dashboard updates weekly. Program Committee engagement, corrections, and educational outcomes feed back into the pipeline. This feedback informs future search parameters, indicator weights, and task-impact assumptions.
IV. Program Committee Role and Interaction
The Program Committee will:
Review forecasts and summaries produced by the Forecasting Committee.
Ask questions, challenge assumptions, or request clarification by querying specific artifacts or task classifications.
Use structured outputs to:
Identify which tasks should be emphasized, de-emphasized, or removed from cybersecurity curricula.
Propose learning resources to address new or augmented tasks.
Identify skills gaps to be filled through institutional training or resource development.
Although Program Committee members will not directly operate the forecasting system, they will receive:
A narrative summary and accompanying CSV for each work role or task group.
Evidence trail links and rationale for each major recommendation.
Access to dashboards or interfaces (read-only or read-with-comment) for deeper exploration of logic and sources.
V. Final Outputs
VI. Glossary
Artifact – A piece of publicly available evidence (e.g., article, video, job post) that informs the AI impact on cybersecurity tasks.
DCWF – Department of Homeland Security’s Cybersecurity Workforce Framework; a taxonomy of work roles and tasks.
Replace – A task that AI is forecast to perform without human involvement.
Augment – A task that AI will support or accelerate, but not fully automate.
Remain Human – A task expected to remain in human hands due to complexity, judgment, ethics, or other constraints.
New Task – A job duty that did not exist before and is emerging because of AI advances.
Indicator – A signal or data type that prompts search and evaluation of artifacts.
Confidence Score – A quantified measure of how strongly an artifact supports a given task classification.
Versioning – Retention and labeling of multiple, possibly contradictory interpretations over time for transparency.
Dashboard – The user-facing interface that aggregates current findings and recommendations and links them to source artifacts.
VII. Program Specification: Forecasting Pipeline (Detailed)
A. Overview The AI Horizon Forecasting Pipeline is a modular software system designed to continuously gather and analyze publicly available digital artifacts that suggest how artificial intelligence is transforming cybersecurity work. It is intended to:
Classify tasks using an AI-driven decision engine
Crosswalk those tasks to the National Cybersecurity Workforce Framework (DCWF)
Generate structured, reviewable weekly reports and dashboards for educational alignment and workforce planning
Provide full traceability for every recommendation through artifact linkage and scoring
B. Scope The forecasting system automates evidence discovery, classification, mapping, and summarization of AI’s influence on the cybersecurity workforce. This specification includes:
Input/output formats
Module responsibilities
Configuration system
Operational and non-functional requirements
Human interaction roles
It does not cover downstream deliberations or instructional implementations by the Program Committee.
C. Stakeholders
Forecasting Committee (strategic reviewers, decision-makers)
Assistant reviewers (manual verification, oversight)
Software development team (developers, testers)
Evaluation partner (Redwood Consulting: impact, validity, process fidelity)
External evaluators (e.g., Redwood Consulting)
D. System Architecture Modules include:
Data Ingestion Engine
RSS, News APIs (e.g., Bing News), YouTube (via yt-dlp), PDF/web manual upload
Configured with a YAML file for keyword and indicator combinations
Output format per artifact:
{
"id": "artifact_001",
"source_url": "https://example.com/article",
"source_type": "news_article",
"content": "Full text or transcript...",
"retrieved_on": "2025-05-27"
}
Artifact Classifier and Scoring Engine
Accepts text artifacts and evaluates them with:
Classification: Replace, Augment, Remain Human, or New Task
Scoring: credibility (0-1), recency (timestamp), impact (0-1), specificity (0-1)
Uses a transformer-based LLM or fine-tuned classifier for extraction
Output format:
{
"artifact_id": "artifact_001",
"classification": "augment",
"confidence": 0.87,
"rationale": "AI tools assist in detecting anomalous traffic patterns...",
"scores": {
"credibility": 0.9,
"recency": "2025-05-25",
"impact": 0.7,
"specificity": 0.85
}
}
Task Mapping Module
Loads structured DCWF task-role mapping from Excel/CSV
Matches classification output to task_ids using NLP (e.g., keyword vector matching or semantic search)
Aggregates to role level as needed
Output augmentation:
{
"task_ids": ["TVM-001", "ANL-004"],
"work_roles": ["Vulnerability Assessment Analyst", "Threat Analyst"]
}
Report Generator
Weekly schedule triggers generation of:
Markdown and HTML summaries by work role
CSV with all classified tasks and scores: | Task ID | Work Role | Classification | Confidence | Rationale | Artifact ID | Date |
Stores all outputs under ./reports/YYYY-MM-DD/
Pushes to static site repo or protected web folder
Human-in-the-Loop Review
UI for assistants to view/edit classifications
Allows override with comment
Writes logs for:
artifact_id, timestamp, original vs. edited values, reviewer_id
Logging and Versioning
Every artifact gets a version record
Differences from prior recommendations are noted
Enables historical comparisons for evaluators
Feedback Loop and Dashboard
Dashboard is updated weekly with:
Task-level summaries
Drilldowns to artifact rationale
Feedback widgets for reviewers to tag errors or propose reclassification
Analyst feedback is logged and triggers retraining/parameter updates over time Modules include:
Data Ingestion Engine (RSS, APIs, YouTube, manual)
Artifact Classifier and Scoring Engine
Task Mapping
Loads DCWF task-role schema from structured Excel/CSV
Uses keyword and vector similarity to map artifact content to task IDs
Allows for many-to-many task mappings and annotations
Output: Augmented classification JSON with tasks:
{
"task_ids": ["TVM-001", "ANL-004"],
"work_roles": ["Vulnerability Assessment Analyst", "Threat Analyst"]
}
Reporting Output
Weekly report job triggers automatic generation of:
Markdown/HTML summaries per role
CSV file:
All reports and files stored under ./reports/YYYY-MM-DD/
Uploaded to internal site or version-controlled portal (e.g., GitHub Pages with Auth)
Human-in-the-Loop Review
Assistants can override AI decisions
Comments and justifications can be stored
Changes logged with timestamps and user IDs
Logging and Versioning
Retains all original artifacts and classifications
Tracks overrides and editorial history
Supports diff-based version comparison
Feedback Loop
Dashboard receives comments and feedback
Updates to search logic, indicators, or mapping rules are version-controlled
Analyst feedback used to tune system over time
F. Non-Functional Requirements
Language: Python 3.11+
Platform: CLI first, Flask/Django dashboard later, then containerized deployment (e.g., Docker)
Authentication: Required for editor users
Storage: SQLite for local use, optional Postgres for multi-user deployment
Privacy: Only open-source/public domain data is ingested
Transparency: All decisions are traceable; logic is auditable
Usability: Interfaces must support non-programmers in reviewing AI outputs
Language: Python 3.11+
Platform: Local first, then deployable to cloud
Privacy: Only open-source/public data
Transparency: All logic auditable by users
Accessibility: Non-technical UI for assistant reviewers
G. Dependencies
LLM or local NLP model
Libraries: feedparser, newspaper3k, yt-dlp, pandas, spaCy, etc.
Hosting: Secure internal website or GitHub Pages + authentication
H. Deliverables
Functional codebase with setup docs
Configurable pipeline jobs
Admin dashboard
Weekly automation with cron/scheduler
Logs, CSVs, and narrative reports
Evaluation instrumentation for Redwood Consulting
