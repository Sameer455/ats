"""
llm_chain.py - LangChain-powered LLM analysis chain for ATS insights.

Supports:
- Groq  (free API - default, set GROQ_API_KEY in .env)
- OpenAI (via OPENAI_API_KEY in .env)
- Ollama (local - needs Ollama running on localhost:11434)
"""

import os
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()


def _get_llm(provider: str = "ollama"):
    """
    Returns the correct LLM instance based on provider.

    Providers:
      - 'ollama' : Local Ollama server (default). Must be running on localhost:11434.
      - 'groq'   : Free Groq Cloud API. Get key at console.groq.com.
      - 'openai' : OpenAI API (paid). Requires OPENAI_API_KEY.
    """
    if provider == "ollama":
        try:
            from langchain_ollama import OllamaLLM as OllamaClass
        except ImportError:
            from langchain_community.llms import Ollama as OllamaClass
            
        return OllamaClass(
            model=os.getenv("OLLAMA_MODEL", "llama3.1"),
            temperature=0.1,
            base_url=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
        )

    elif provider == "groq":
        from langchain_groq import ChatGroq
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError(
                "GROQ_API_KEY not found in environment variables. "
                "Get a free key at https://console.groq.com and add it to your .env file."
            )
        return ChatGroq(
            model="llama-3.1-8b-instant",
            api_key=api_key,
            temperature=0.1,
        )

    elif provider == "openai":
        from langchain_openai import ChatOpenAI
        import httpx
        return ChatOpenAI(
            model="gpt-4o-mini",
            api_key=os.getenv("OPENAI_API_KEY"),
            temperature=0.1,
            http_client=httpx.Client(),
            http_async_client=httpx.AsyncClient(),
        )

    else:
        raise ValueError(f"Unsupported provider: {provider}")


# ──────────────────────────────────────────────
# Prompt Template
# ──────────────────────────────────────────────
_ATS_ANALYSIS_PROMPT = PromptTemplate(
    input_variables=[
        "job_role",
        "semantic_score",
        "skill_coverage",
        "matched_skills",
        "missing_skills",
        "experience_years",
        "required_experience",
        "education",
        "jd_text",
    ],
    template="""
You are a senior HR technology specialist and talent evaluation expert.

You have been given structured ATS analysis data for a job application. 
Analyze the data professionally and produce a structured evaluation report.

## Job Role
{job_role}

## Computed Metrics
- Semantic Match Score: {semantic_score}%
- Skill Coverage: {skill_coverage}%
- Candidate Experience: {experience_years} years
- Required Experience: {required_experience} years

## Skills
- Matched Skills: {matched_skills}
- Missing Skills: {missing_skills}

## Education
{education}

## Job Description Summary (Reference)
{jd_text}

---

Based on the above data, provide a comprehensive evaluation with the following clearly labeled sections:

### 1. Overall Assessment
Provide a 2-3 sentence professional summary of the candidate's alignment with the role.

### 2. Candidate Fit Level
Classify as exactly one of: **High Fit** | **Medium Fit** | **Low Fit**
Justify your classification in 1-2 sentences.

### 3. Risk Assessment
Classify hiring risk as exactly one of: **Low Risk** | **Moderate Risk** | **High Risk**
Briefly explain the key risk factors.

### 4. Critical Skill Gaps
List the top 3-5 most important missing competencies ranked by importance to the role.
For each, briefly explain why it matters for this specific role.

### 5. Experience Alignment
Comment on the candidate's experience relative to what the role requires.

### 6. Domain Compatibility
Assess how well the candidate's background aligns with the domain/industry of the role.

### 7. Hiring Recommendation
Provide a clear, actionable recommendation for the recruiter.

Be concise, objective, and professional. Do not add recommendations to improve the resume.
""",
)


def run_ats_analysis(
    job_role: str,
    semantic_score: float,
    skill_coverage: float,
    matched_skills: list,
    missing_skills: list,
    experience_years: float,
    required_experience: float,
    education: list,
    jd_text: str,
    provider: str = "ollama",
) -> str:
    """
    Runs the full LangChain ATS analysis and returns the LLM response as a string.
    """
    llm = _get_llm(provider)
    chain = _ATS_ANALYSIS_PROMPT | llm | StrOutputParser()

    result = chain.invoke({
        "job_role": job_role if job_role else "Not specified",
        "semantic_score": semantic_score,
        "skill_coverage": skill_coverage,
        "matched_skills": ", ".join(matched_skills) if matched_skills else "None detected",
        "missing_skills": ", ".join(missing_skills) if missing_skills else "None detected",
        "experience_years": experience_years,
        "required_experience": required_experience,
        "education": ", ".join(education) if education else "Not specified",
        "jd_text": jd_text[:1500],  # Truncate JD to avoid token limits
    })

    return result
