# AI-Based ATS Analyzer - Complete Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Technology Stack](#technology-stack)
4. [Project Structure](#project-structure)
5. [Setup & Installation](#setup--installation)
6. [Configuration](#configuration)
7. [How to Run](#how-to-run)
8. [API Documentation](#api-documentation)
9. [Database Schema](#database-schema)
10. [Frontend Components](#frontend-components)
11. [Analysis Pipeline](#analysis-pipeline)
12. [Key Features](#key-features)
13. [Troubleshooting](#troubleshooting)

---

## Project Overview

**AI-Based ATS Analyzer** is an intelligent Applicant Tracking System that leverages NLP, semantic embeddings, and Large Language Models to analyze resumes against job descriptions. The system provides comprehensive matching scores, skill gap analysis, and AI-generated hiring recommendations.

### Core Functionality
- **Resume Parsing**: Extract text from PDF resumes with intelligent section detection
- **Entity Extraction**: Identify skills, experience, education, and roles using multiple strategies
- **Semantic Matching**: Compare resume and job description using embeddings (all-MiniLM-L6-v2)
- **Skill Analysis**: Perform exact and fuzzy matching with synonym expansion
- **AI Evaluation**: Generate hiring recommendations using LLM (OpenAI GPT-4o-mini or Ollama)
- **User Management**: JWT-based authentication with user history tracking

### Output Metrics
| Metric | Description |
|--------|-------------|
| **ATS Composite Score** | Weighted: 50% semantic + 50% skill coverage |
| **Semantic Match Score** | Cosine similarity of resume vs JD embeddings (0-100%) |
| **Skill Coverage %** | Fraction of JD-required skills present in resume |
| **Missing Skills** | Skills in JD not found in resume |
| **Matched Skills** | Overlap between resume and JD skills |
| **Experience Alignment** | Extracted vs required years of experience |
| **AI Evaluation** | LLM-generated candidate fit, risk level, hiring recommendation |

---

## Architecture

### System Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React)                         │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐  │
│  │   Login      │   Upload     │   Analysis   │   History    │  │
│  │   Page       │   Area       │   Results    │   Page       │  │
│  └──────────────┴──────────────┴──────────────┴──────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓ HTTP/REST
┌─────────────────────────────────────────────────────────────────┐
│                      BACKEND (FastAPI)                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Authentication Routes (JWT)                 │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │          Analysis Routes (Resume Processing)             │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │           History Routes (Query & Storage)               │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │          ANALYSIS PIPELINE                               │  │
│  │  ┌────────────┬────────────┬────────────┬────────────┐   │  │
│  │  │ PDF Parser │ Cleaning   │ Segmentation│ Extraction│   │  │
│  │  └────────────┴────────────┴────────────┴────────────┘   │  │
│  │                         ↓                                 │  │
│  │  ┌────────────┬────────────┬────────────┐               │  │
│  │  │Normalization│ Semantic   │  LLM       │               │  │
│  │  │            │  Matching  │  Analysis  │               │  │
│  │  └────────────┴────────────┴────────────┘               │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   DATABASE (PostgreSQL)                         │
│  ┌──────────────┬──────────────┬──────────────┐                │
│  │ Users        │ Analysis     │ Audit Log    │                │
│  │ - email      │ History      │ (optional)   │                │
│  │ - password   │ - results    │              │                │
│  │              │ - scores     │              │                │
│  └──────────────┴──────────────┴──────────────┘                │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
Resume PDF → Parser → Cleaner → Segmenter → Extractors → Normalizer
                                                              ↓
                                              ┌──────────────┴──────────────┐
                                              ↓                             ↓
                                    Semantic Matcher              Hybrid Skill Matcher
                                              ↓                             ↓
                                              └──────────────┬──────────────┘
                                                             ↓
                                                   LLM Chain (Analysis)
                                                             ↓
                                              Final Results + Scoring
                                                             ↓
                                                  Store in PostgreSQL
```

---

## Technology Stack

### Backend
| Component | Technology |
|-----------|-----------|
| **Web Framework** | FastAPI |
| **Server** | Uvicorn |
| **Authentication** | JWT (python-jose) + bcrypt |
| **Database** | PostgreSQL 12+ |
| **ORM** | SQLAlchemy |
| **Database Driver** | psycopg2 |

### NLP & Processing
| Component | Technology |
|-----------|-----------|
| **PDF Parsing** | PyMuPDF + pdfplumber (fallback) |
| **Text Cleaning** | Python `re`, Unicode normalization |
| **NER & Segmentation** | spaCy (en_core_web_sm) |
| **Tokenization** | NLTK |
| **Semantic Embeddings** | sentence-transformers (all-MiniLM-L6-v2) |
| **Fuzzy Matching** | rapidfuzz |

### AI/ML
| Component | Technology |
|-----------|-----------|
| **LLM Orchestration** | LangChain (LCEL) |
| **LLM Providers** | OpenAI GPT-4o-mini OR Ollama (local) |
| **Vector Search** | FAISS |
| **Tensor Operations** | PyTorch |

### Frontend
| Component | Technology |
|-----------|-----------|
| **Framework** | React 19.2.4 |
| **Build Tool** | Vite 8.0.4 |
| **CSS Framework** | Tailwind CSS 4.2.2 |
| **Linting** | ESLint 9.39.4 |

### Development
| Component | Technology |
|-----------|-----------|
| **Python Version** | 3.8+ |
| **Environment Management** | python-dotenv |
| **Async SQL** | aiosqlite |
| **Migrations** | Alembic |

---

## Project Structure

```
ai_agent/
├── app.py                          # Streamlit demo (legacy)
├── DOCUMENTATION.md                # This file
├── README.md                       # Quick start guide
├── CLEANUP_SUMMARY.md              # Refactoring notes
├── requirements.txt                # Python dependencies
├── setup_db.py                     # Database initialization
├── .env.example                    # Environment variables template
│
├── backend/
│   ├── main.py                     # FastAPI app setup
│   ├── database.py                 # SQLAlchemy setup
│   ├── models.py                   # Database models
│   ├── pipeline.py                 # Orchestration logic
│   ├── auth/
│   │   ├── routes.py               # Login, signup, token refresh
│   │   └── utils.py                # Password hashing, JWT creation
│   └── routes/
│       ├── analyze.py              # POST /analyze (main endpoint)
│       └── history.py              # GET /history (retrieve past analyses)
│
├── frontend/
│   ├── package.json                # npm dependencies
│   ├── vite.config.js              # Vite configuration
│   ├── eslint.config.js            # Linting rules
│   ├── index.html                  # Entry point
│   ├── src/
│   │   ├── main.jsx                # React entry
│   │   ├── App.jsx                 # Root component
│   │   ├── api.js                  # Backend API calls
│   │   ├── auth.js                 # Authentication utilities
│   │   ├── index.css               # Global styles
│   │   ├── assets/                 # Static assets
│   │   └── components/
│   │       ├── LoginPage.jsx       # User login
│   │       ├── UploadArea.jsx      # File upload
│   │       ├── ConfigPanel.jsx     # Job description input
│   │       ├── ExtractedProfile.jsx# Extracted entities display
│   │       ├── LLMAnalysis.jsx     # AI recommendations
│   │       ├── SkillAnalysis.jsx   # Skill matching visualization
│   │       ├── ScoreCards.jsx      # Score display
│   │       ├── ScoreBreakdown.jsx  # Score details
│   │       ├── RawJson.jsx         # Raw results viewer
│   │       ├── Header.jsx          # Navigation
│   │       └── HistoryPage.jsx     # Past analyses
│   └── public/                     # Static files
│
├── extraction/
│   ├── __init__.py
│   ├── skills_extractor.py         # Multi-pass skill extraction
│   ├── experience_extractor.py     # Years of experience
│   ├── role_extractor.py           # Job role/title extraction
│   └── education_extractor.py      # Degree & field extraction
│
├── llm/
│   ├── __init__.py
│   └── llm_chain.py                # LangChain orchestration
│
├── matching/
│   ├── __init__.py
│   ├── semantic_matcher.py         # Embedding-based matching
│   └── hybrid_skill_matcher.py     # Combined skill matching
│
├── normalization/
│   ├── __init__.py
│   └── normalizer.py               # Skill normalization
│
├── parser/
│   ├── __init__.py
│   └── pdf_parser.py               # PDF text extraction
│
├── preprocessing/
│   ├── __init__.py
│   └── cleaner.py                  # Text cleaning
│
├── segmentation/
│   ├── __init__.py
│   └── section_splitter.py         # Resume section detection
│
└── utils/
    ├── __init__.py
    └── constants.py                # Skills DB, synonyms, constants
```

---

## Setup & Installation

### Prerequisites
- **Python 3.8+**
- **PostgreSQL 12+**
- **Node.js 18+** (for frontend)
- **Git**

### Step 1: Clone Repository

```bash
cd /path/to/workspace
git clone <repository-url>
cd ai_agent
```

### Step 2: Backend Setup

#### Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

#### Install Python Dependencies
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

#### Initialize Database
```bash
# Make sure PostgreSQL is running
python setup_db.py
```

This will:
- Create `ats_analyzer` database
- Create tables for `users` and `analysis_history`
- Initialize schema

### Step 3: Frontend Setup

```bash
cd frontend
npm install
```

### Step 4: Configure Environment

Create a `.env` file in the project root:

```env
# Backend Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/ats_analyzer
SECRET_KEY=your-super-secret-jwt-key-min-32-chars

# LLM Provider (choose one)
OPENAI_API_KEY=sk-your-openai-key-here
# OR
GROQ_API_KEY=your-groq-api-key-here
GROQ_MODEL=mixtral-8x7b-32768

# Optional: Ollama (local)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3

# Frontend
VITE_API_URL=http://localhost:8000
```

---

## Configuration

### Environment Variables

| Variable | Type | Required | Description |
|----------|------|----------|-------------|
| `DATABASE_URL` | string | Yes | PostgreSQL connection string |
| `SECRET_KEY` | string | Yes | JWT signing secret (min 32 chars) |
| `OPENAI_API_KEY` | string | No | OpenAI API key for GPT-4o-mini |
| `GROQ_API_KEY` | string | No | Groq API key for cloud inference |
| `OLLAMA_BASE_URL` | string | No | Ollama server URL (default: http://localhost:11434) |
| `OLLAMA_MODEL` | string | No | Ollama model name (default: llama3) |
| `VITE_API_URL` | string | No | Backend API URL for frontend |

### Choosing LLM Provider

#### Option 1: OpenAI (Cloud) ✨ Recommended for Production
```bash
pip install langchain-openai
export OPENAI_API_KEY=sk-your-key
```

#### Option 2: Groq (Cloud, Free, Fast)
```bash
pip install langchain-groq
export GROQ_API_KEY=your-key
```

#### Option 3: Ollama (Local, Free, Private) 🔒
```bash
# Install Ollama from https://ollama.com
ollama pull llama3
ollama serve  # Start Ollama in another terminal
```

---

## How to Run

### Start PostgreSQL
```bash
# Windows
net start PostgreSQL-14

# macOS (via Homebrew)
brew services start postgresql

# Linux
sudo service postgresql start
```

### Start Backend (Terminal 1)
```bash
cd ai_agent
source venv/bin/activate  # or venv\Scripts\activate on Windows
uvicorn backend.main:app --reload --port 8000
```

**Expected Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

### Start Frontend (Terminal 2)
```bash
cd ai_agent/frontend
npm run dev
```

**Expected Output:**
```
  VITE v8.0.4  ready in 234 ms

  ➜  Local:   http://localhost:5173/
```

### Start Ollama (Optional, Terminal 3)
```bash
ollama serve
```

### Access Application
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## API Documentation

### Authentication Endpoints

#### 1. Register New User
```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "strongpassword123"
}
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "email": "user@example.com",
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### 2. Login
```http
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=strongpassword123
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### 3. Refresh Token
```http
POST /auth/refresh
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Analysis Endpoints

#### 1. Analyze Resume vs Job Description
```http
POST /analyze
Authorization: Bearer <access_token>
Content-Type: multipart/form-data

Form Fields:
- resume: <PDF file>
- job_description: "Assistant Manager, 5+ years experience required..."
- use_groq: false (optional, default: false)
- use_ollama: false (optional, default: false)
```

**Response:** `200 OK`
```json
{
  "final_score": 78.5,
  "fit_category": "Strong Fit",
  "semantic_match_score": 82.3,
  "skill_coverage_percent": 75.0,
  "matched_skills": ["Python", "FastAPI", "PostgreSQL"],
  "missing_skills": ["Kubernetes", "Docker"],
  "experience_summary": "5 years (required: 5 years)",
  "education": "Bachelor's in Computer Science",
  "role": "Software Engineer",
  "ai_analysis": {
    "candidate_fit": "The candidate meets the core requirements...",
    "risk_level": "Low",
    "hiring_recommendation": "PROCEED TO INTERVIEW",
    "strengths": ["Strong technical skills", "Relevant experience"],
    "concerns": ["Limited cloud deployment experience"],
    "questions_to_ask": ["Tell us about your CI/CD pipeline..."]
  },
  "analysis_id": 42
}
```

#### 2. Get Analysis History
```http
GET /history?skip=0&limit=10
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "total": 15,
  "items": [
    {
      "id": 42,
      "resume_filename": "john_doe.pdf",
      "jd_snippet": "Senior Python Developer...",
      "final_score": 78.5,
      "fit_category": "Strong Fit",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

#### 3. Get Detailed Analysis Result
```http
GET /history/{analysis_id}
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "id": 42,
  "result_json": {
    "final_score": 78.5,
    "matched_skills": [...],
    "ai_analysis": {...}
  },
  "created_at": "2024-01-15T10:30:00Z"
}
```

### Error Responses

#### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

#### 422 Unprocessable Entity
```json
{
  "detail": [
    {
      "loc": ["body", "resume"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

#### 500 Internal Server Error
```json
{
  "detail": "Error processing resume: [specific error message]"
}
```

---

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

**Columns:**
- `id`: Primary key (auto-increment)
- `email`: Unique email address
- `password`: bcrypt-hashed password
- `created_at`: Account creation timestamp

### Analysis History Table
```sql
CREATE TABLE analysis_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    resume_filename VARCHAR(255),
    jd_snippet TEXT,
    final_score FLOAT,
    fit_category VARCHAR(50),
    result_json JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

**Columns:**
- `id`: Primary key (auto-increment)
- `user_id`: Foreign key to users table
- `resume_filename`: Original filename of uploaded resume
- `jd_snippet`: Job description text analyzed
- `final_score`: Composite matching score (0-100)
- `fit_category`: "Strong Fit", "Good Fit", "Moderate Fit", "Weak Fit"
- `result_json`: Full analysis results as JSONB (queryable)
- `created_at`: Analysis timestamp

---

## Frontend Components

### Component Hierarchy
```
App
├── Header
├── LoginPage (if not authenticated)
├── MainLayout
│   ├── UploadArea
│   │   └── File input for resume
│   ├── ConfigPanel
│   │   └── Job description text area
│   ├── ExtractedProfile
│   │   ├── Role display
│   │   ├── Education display
│   │   └── Experience summary
│   ├── ScoreCards
│   │   ├── Composite Score
│   │   ├── Semantic Match
│   │   └── Skill Coverage
│   ├── ScoreBreakdown
│   │   └── Detailed score metrics
│   ├── SkillAnalysis
│   │   ├── Matched Skills (green)
│   │   ├── Missing Skills (red)
│   │   └── Fuzzy Matches (yellow)
│   ├── LLMAnalysis
│   │   ├── Candidate Fit
│   │   ├── Risk Level
│   │   ├── Hiring Recommendation
│   │   ├── Strengths
│   │   ├── Concerns
│   │   └── Interview Questions
│   ├── RawJson
│   │   └── Full API response display
│   └── HistoryPage
│       └── Past analysis list
└── Footer
```

### Key Components

#### LoginPage.jsx
- Email/password form
- Sign up option
- JWT token storage
- Redirect to main on success

#### UploadArea.jsx
- Drag-and-drop PDF upload
- File validation
- Upload progress
- Error handling

#### ConfigPanel.jsx
- Job description textarea
- LLM provider selection (OpenAI, Groq, Ollama)
- Analysis trigger button
- Loading state

#### ScoreCards.jsx
- Displays composite score with color coding
- Semantic match percentage
- Skill coverage percentage
- Visual card layout

#### SkillAnalysis.jsx
- Matched skills (green badges)
- Missing skills (red badges)
- Fuzzy matches (yellow badges)
- Organized in columns

#### LLMAnalysis.jsx
- AI-generated fit assessment
- Risk level indicator
- Hiring recommendation
- Strengths and concerns list
- Interview questions

#### HistoryPage.jsx
- Table of past analyses
- Date, filename, score display
- Click to view detailed results
- Pagination support

---

## Analysis Pipeline

### Step-by-Step Process

#### 1. Resume Parsing
**File:** `parser/pdf_parser.py`

- Extract text from PDF using PyMuPDF
- Fallback to pdfplumber if needed
- Preserve text structure and formatting
- Handle multiple page resumes

```python
from parser.pdf_parser import extract_resume_text

text = extract_resume_text("resume.pdf")
# Output: "John Doe\n\nSummary:\n5+ years Python development..."
```

#### 2. Text Cleaning
**File:** `preprocessing/cleaner.py`

- Remove extra whitespace
- Normalize Unicode characters
- Remove special characters where appropriate
- Fix encoding issues
- Lowercase for consistency

#### 3. Section Segmentation
**File:** `segmentation/section_splitter.py`

- Detect resume sections (Summary, Experience, Skills, Education)
- Use heuristic heading detection
- Split content by section
- Handle variations in section naming

**Output:**
```python
{
    "SUMMARY": "5+ years software engineer...",
    "EXPERIENCE": "Senior Developer at TechCorp 2020-2024...",
    "SKILLS": "Python, FastAPI, PostgreSQL...",
    "EDUCATION": "BS Computer Science, State University 2018"
}
```

#### 4. Entity Extraction
**File:** `extraction/`

Extract specialized information using multiple strategies:

##### Skills Extraction (`skills_extractor.py`)
- **Multi-pass approach:**
  1. Exact phrase matching with word boundaries
  2. Synonym expansion (e.g., "artificial intelligence" → "AI")
  3. Safe alias resolution (e.g., "k8s" → "Kubernetes")
  4. Special handling for ambiguous terms (R language)

**Output:**
```python
["Python", "FastAPI", "PostgreSQL", "Docker", "AWS", "Machine Learning"]
```

##### Experience Extraction (`experience_extractor.py`)
- Extract years of overall experience
- Calculate from job dates if available
- Handle various date formats
- Consider current vs. previous roles

**Output:**
```python
{
    "years": 5.5,
    "positions": [
        {"title": "Senior Engineer", "duration": "2020-2024"},
        {"title": "Junior Engineer", "duration": "2018-2020"}
    ]
}
```

##### Role Extraction (`role_extractor.py`)
- Identify current/most recent job title
- Extract role keywords
- Match against common role patterns

**Output:**
```python
"Senior Software Engineer"
```

##### Education Extraction (`education_extractor.py`)
- Identify degree level (BS, MS, PhD, etc.)
- Extract field of study
- Find institution name

**Output:**
```python
{
    "degree": "Bachelor's",
    "field": "Computer Science",
    "institution": "State University"
}
```

#### 5. Skill Normalization
**File:** `normalization/normalizer.py`

- Map skills to canonical forms
- Resolve synonyms
- Combine variations (e.g., "JavaScript" + "JS" → "JavaScript")
- Standardize naming conventions

**Input:** `["python", "js", "react.js", "artificial intelligence"]`
**Output:** `["python", "javascript", "react", "machine learning"]`

#### 6. Semantic Matching
**File:** `matching/semantic_matcher.py`

- Generate embeddings for entire resume and job description
- Use sentence-transformers (all-MiniLM-L6-v2 model)
- Calculate cosine similarity
- Score range: 0-100%

```python
from matching.semantic_matcher import calculate_semantic_score

score = calculate_semantic_score(
    resume_text="5+ years Python development with FastAPI...",
    jd_text="Senior Python Engineer with 5+ years FastAPI experience..."
)
# Output: 82.3
```

#### 7. Hybrid Skill Matching
**File:** `matching/hybrid_skill_matcher.py`

- Extract required skills from job description
- Match against resume skills
- Use multiple matching strategies:
  1. **Exact matching** - "Python" → "Python" ✓
  2. **Fuzzy matching** - "machine learning" → "ML" (90% similarity)
  3. **Semantic matching** - "AI" → "machine learning" (from embeddings)

**Output:**
```python
{
    "matched": ["Python", "FastAPI", "PostgreSQL"],
    "missing": ["Kubernetes", "Docker"],
    "fuzzy_matches": [("machine learning", "ML", 0.95)],
    "coverage_percent": 75.0
}
```

#### 8. LLM Analysis
**File:** `llm/llm_chain.py`

- Use LangChain LCEL (Language Expression Language)
- Pass structured data to LLM
- Generate hiring recommendation
- Extract AI insights

**LLM Prompt:**
```
Analyze this candidate:
- Resume Skills: [...]
- Required Skills: [...]
- Missing Skills: [...]
- Experience: [...]
- Semantic Fit: 82%

Provide:
1. Candidate Fit assessment
2. Risk Level (Low/Medium/High)
3. Hiring Recommendation (PROCEED/REVIEW/REJECT)
4. Strengths
5. Concerns
6. Interview Questions
```

#### 9. Composite Scoring
**File:** `backend/pipeline.py`

Final score calculation:
```
Final Score = (Semantic Match × 0.5) + (Skill Coverage × 100 × 0.5)
```

**Example:**
- Semantic Match: 82%
- Skill Coverage: 75%
- Final Score: (82 × 0.5) + (75 × 0.5) = **78.5**

**Fit Categories:**
- **90-100**: Perfect Fit
- **80-89**: Strong Fit
- **70-79**: Good Fit
- **60-69**: Moderate Fit
- **Below 60**: Weak Fit

#### 10. Database Storage
```python
analysis = AnalysisHistory(
    user_id=user.id,
    resume_filename="john_doe.pdf",
    jd_snippet="Senior Python Engineer...",
    final_score=78.5,
    fit_category="Good Fit",
    result_json={
        "matched_skills": [...],
        "ai_analysis": {...}
    }
)
db.add(analysis)
db.commit()
```

---

## Key Features

### 🎯 Intelligent Resume Analysis
- Multi-stage NLP pipeline for accurate data extraction
- Handles various resume formats and layouts
- Robust error handling and fallbacks

### 🤖 AI-Powered Recommendations
- LLM integration (OpenAI, Groq, or local Ollama)
- Context-aware hiring recommendations
- Structured interview questions generation

### 🔍 Advanced Skill Matching
- Exact matching, fuzzy matching, and semantic matching
- Synonym and alias resolution
- Skill normalization and standardization

### 📊 Comprehensive Scoring
- Composite ATS score (0-100)
- Semantic similarity metrics
- Skill coverage analysis
- Visual score breakdown

### 🔐 User Authentication
- JWT-based authentication
- Secure password hashing (bcrypt)
- Token refresh mechanism

### 📈 Analysis History
- Store and retrieve past analyses
- JSONB database support for rich queries
- Pagination for large datasets

### 🌍 Multi-LLM Support
- OpenAI GPT-4o-mini (recommended)
- Groq cloud inference (free, fast)
- Ollama local deployment (private)

### 🎨 Modern UI
- React with Vite for fast development
- Tailwind CSS for responsive design
- Real-time feedback and loading states

---

## Troubleshooting

### Database Connection Issues

#### Problem: `psycopg2.OperationalError: could not connect to server`

**Solution:**
```bash
# Check PostgreSQL is running
psql -U postgres -c "SELECT version();"

# On Windows, use Services Manager
# On Mac: brew services list | grep postgresql
# On Linux: sudo systemctl status postgresql
```

#### Problem: `database "ats_analyzer" does not exist`

**Solution:**
```bash
python setup_db.py
```

### LLM Provider Issues

#### OpenAI API Error: `Invalid API Key`

```bash
# Verify API key
export OPENAI_API_KEY=sk-...
python -c "import openai; print(openai.api_key)"
```

#### Ollama Connection Error: `Connection refused`

```bash
# Make sure Ollama is running in another terminal
ollama serve

# Or check if it's listening
curl http://localhost:11434/api/tags
```

#### Groq Rate Limit: `429 Too Many Requests`

```bash
# Wait a moment before retrying
# Check your Groq dashboard for usage limits
```

### Frontend Issues

#### Problem: `CORS error: No 'Access-Control-Allow-Origin'`

**Solution:** Check backend CORS configuration in `backend/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### Problem: API requests timeout

**Solution:** Increase timeout in `frontend/src/api.js`:
```javascript
const timeout = 60000; // 60 seconds for heavy analysis
```

### Resume Parsing Issues

#### Problem: `Text extraction returns blank`

**Solution:** Check PDF quality
```bash
# Try fallback parser
python -c "
from parser.pdf_parser import extract_resume_text
text = extract_resume_text('resume.pdf', use_pdfplumber=True)
print(text[:500])
"
```

#### Problem: Special characters appearing as `?` or `[]`

**Solution:** Encoding issue in cleaner
```python
# In preprocessing/cleaner.py, ensure UTF-8 handling
text = text.encode('utf-8', errors='ignore').decode('utf-8')
```

### Performance Issues

#### Problem: Analysis takes >30 seconds

**Optimization strategies:**
1. Use Groq instead of OpenAI (faster)
2. Reduce embedding model size (use distilbert instead of MiniLM)
3. Cache embeddings for JD descriptions
4. Use async processing for multiple analyses

#### Problem: High memory usage

**Solution:**
```bash
# Monitor memory
import psutil
print(psutil.virtual_memory())

# Optimize:
# 1. Batch process resumes
# 2. Clear embeddings cache periodically
# 3. Use smaller language models
```

### JWT Authentication Issues

#### Problem: `Invalid token` or `Token expired`

```bash
# Generate new token
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=yourpassword"
```

#### Problem: Token not stored in frontend

**Check localStorage:**
```javascript
// In browser console
localStorage.getItem('token')
// Should return: "eyJhbGciOiJIUzI1NiI..."
```

---

## Performance Optimization Tips

### Backend Optimization
1. **Database Indexing**
   ```sql
   CREATE INDEX idx_user_id ON analysis_history(user_id);
   CREATE INDEX idx_created_at ON analysis_history(created_at DESC);
   ```

2. **Embedding Caching**
   ```python
   # Cache JD embeddings to avoid recomputing
   @functools.cache
   def get_jd_embedding(jd_text):
       return embedder.encode(jd_text)
   ```

3. **Async Processing**
   ```python
   # Use async for I/O operations
   async def process_resume_async(file):
       text = await extract_text_async(file)
       return await analyze_async(text)
   ```

### Frontend Optimization
1. **Lazy Loading**
   ```javascript
   const HistoryPage = lazy(() => import('./components/HistoryPage'));
   ```

2. **Result Caching**
   ```javascript
   const cache = new Map();
   cache.set(analysisId, result);
   ```

### General Tips
- Use connection pooling for database
- Batch multiple analyses
- Implement rate limiting
- Monitor and log slow queries
- Use CDN for static assets

---

## Security Considerations

### 🔒 Best Practices

1. **Environment Variables**
   - Never commit `.env` file
   - Use `.env.example` as template
   - Rotate secrets regularly

2. **Password Security**
   - Use bcrypt with salt rounds ≥ 10
   - Enforce minimum password length
   - Implement password reset flow

3. **JWT Tokens**
   - Use strong SECRET_KEY (32+ characters)
   - Set reasonable token expiry (15-30 minutes)
   - Implement token refresh mechanism
   - Store tokens securely (httpOnly cookies)

4. **Database**
   - Use parameterized queries (SQLAlchemy handles this)
   - Implement least privilege access
   - Enable SSL for PostgreSQL connections
   - Regular backups

5. **API Security**
   - Implement rate limiting
   - Validate and sanitize all inputs
   - Use HTTPS in production
   - Implement CORS properly

6. **File Upload**
   - Validate file types (check magic numbers, not just extension)
   - Limit file size
   - Scan for malware
   - Store in secure location

---

## Contributing

### Development Workflow

1. Create feature branch:
   ```bash
   git checkout -b feature/new-feature
   ```

2. Make changes and test:
   ```bash
   pytest tests/ -v
   ```

3. Format code:
   ```bash
   black .
   isort .
   ```

4. Create pull request with description

### Testing

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_skills_extractor.py -v

# Run with coverage
pytest --cov=. tests/
```

---

## Deployment

### Production Checklist

- [ ] Set `DEBUG=False` in production
- [ ] Use strong `SECRET_KEY`
- [ ] Configure HTTPS
- [ ] Set up PostgreSQL backup
- [ ] Configure monitoring and logging
- [ ] Implement rate limiting
- [ ] Set up SSL certificates
- [ ] Configure CORS for production domain
- [ ] Use environment-specific settings
- [ ] Test thoroughly before deployment

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt
RUN python -m spacy download en_core_web_sm

COPY . .

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Support & Resources

### Documentation
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/)
- [LangChain Documentation](https://python.langchain.com/)
- [React Documentation](https://react.dev/)
- [Vite Documentation](https://vitejs.dev/)

### External APIs
- [OpenAI API](https://platform.openai.com/docs/)
- [Groq API](https://console.groq.com/)
- [Ollama Documentation](https://ollama.com/)

### Common Errors & Solutions
- See [Troubleshooting](#troubleshooting) section above

---

## License

This project is proprietary. All rights reserved.

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.0 | 2024-01-15 | FastAPI backend, PostgreSQL, JWT auth, multi-LLM support |
| 1.0 | 2023-12-01 | Initial Streamlit version, single LLM support |

---

## Contact & Support

For issues, feature requests, or technical support, please contact the development team.

**Last Updated:** April 22, 2026
