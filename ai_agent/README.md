# AI-Based ATS Analyzer

An AI-powered resume-to-job-description analysis system using NLP, semantic embeddings, and LangChain LLM orchestration.

## Project Structure

```
ats-ai/
├── app.py                   # Streamlit frontend
├── pipeline.py              # Main orchestration pipeline
├── requirements.txt
├── .env                     # API keys (not committed)
│
├── parser/                  # PDF text extraction
│   └── pdf_parser.py
├── preprocessing/           # Text cleaning
│   └── cleaner.py
├── segmentation/            # Section detection
│   └── section_splitter.py
├── extraction/              # Entity extraction engines
│   ├── skills_extractor.py
│   ├── experience_extractor.py
│   ├── role_extractor.py
│   └── education_extractor.py
├── normalization/           # Skill normalization
│   └── normalizer.py
├── matching/                # Semantic similarity
│   └── semantic_matcher.py
├── llm/                     # LangChain LLM chain
│   └── llm_chain.py
└── utils/                   # Constants & shared data
    └── constants.py
```

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 2. Configure API Key
Edit `.env` and add your OpenAI API key:
```
OPENAI_API_KEY=sk-your-key-here
```
> **Alternatively**: Use Ollama (local, free). Install from https://ollama.com and pull a model:  
> `ollama pull llama3`

### 3. Run the application
```bash
streamlit run app.py
```

## Tech Stack

| Layer | Technology |
|---|---|
| PDF Parsing | PyMuPDF + pdfplumber (fallback) |
| Text Cleaning | Python `re`, unicode normalization |
| Section Detection | Heuristic heading detection |
| Entity Extraction | Keyword matching, regex, N-grams |
| Skill Normalization | Synonym dictionary |
| Semantic Matching | `sentence-transformers` (all-MiniLM-L6-v2) |
| AI Orchestration | LangChain (LCEL) |
| LLM | OpenAI GPT-4o-mini or Ollama (LLaMA 3) |
| Frontend | Streamlit |

## Output Metrics

- **ATS Composite Score** — Weighted: 50% semantic + 50% skill coverage
- **Semantic Match Score** — Cosine similarity of resume vs JD embeddings
- **Skill Coverage %** — Fraction of JD-required skills present in resume
- **Missing Skills** — Skills in JD not found in resume
- **Matched Skills** — Overlap between resume and JD
- **Experience Alignment** — Extracted vs required years
- **AI Evaluation** — LLM-generated: Candidate Fit, Risk Level, Hiring Recommendation
