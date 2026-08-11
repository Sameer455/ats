import time
from datetime import datetime, timezone
from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    UploadFile,
    File,
    Form,
    status,
)
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import AnalysisHistory, User, JDLibrary
from ..auth.utils import get_current_user_email

router = APIRouter(prefix="/api", tags=["Batch Analysis"])

_ACCEPTED_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


@router.post("/analyze/batch")
async def analyze_batch(
    request: Request,
    resumes: list[UploadFile] = File(...),
    jd_text: Optional[str] = Form(None),
    jd_id: Optional[int] = Form(None),
    required_experience: float = Form(0.0),
    llm_provider: str = Form("ollama"),
    enable_llm: bool = Form(True),
    db: Session = Depends(get_db),
    current_email: str = Depends(get_current_user_email),
):
    user = db.query(User).filter(User.email == current_email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found in database",
        )

    if len(resumes) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Batch analysis requires at least 2 resumes",
        )
    if len(resumes) > 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 20 resumes per batch",
        )

    for resume in resumes:
        if resume.content_type not in _ACCEPTED_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type for {resume.filename}: {resume.content_type}. Accepted: PDF, DOCX",
            )

    jd_title: str = "Custom JD"
    if jd_id is not None:
        jd_entry = db.query(JDLibrary).filter(
            JDLibrary.id == jd_id,
            JDLibrary.is_active == True,
        ).first()
        if not jd_entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="JD not found in library",
            )
        jd_text = jd_entry.jd_text
        jd_title = jd_entry.title
        jd_entry.usage_count += 1
        db.commit()
    elif not jd_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide either jd_text or jd_id",
        )

    from agent.state import ATSAgentState, AnalysisMode
    from agent.graph import ats_agent

    esco_loader = getattr(request.app.state, "esco", None)
    jd_snippet: Optional[str] = None
    if jd_text:
        jd_snippet = jd_text[:200] + "..." if len(jd_text) > 200 else jd_text

    candidates: list[dict] = []
    for resume in resumes:
        try:
            resume_bytes = await resume.read()
            if not resume_bytes:
                candidates.append(_error_candidate(resume.filename or "unknown", "Empty file"))
                continue

            initial_state: ATSAgentState = {
                "resume_bytes":        resume_bytes,
                "resume_filename":     resume.filename or "",
                "jd_text":             jd_text or "",
                "required_experience": required_experience,
                "llm_provider":        llm_provider,
                "enable_llm":          enable_llm,
                "analysis_mode":       AnalysisMode.SINGLE,
                "batch_resumes":       None,
                "agent_trace":         [],
                "extraction_attempts": 0,
                "reasoning_attempts":  0,
                "start_time_ns":       time.perf_counter_ns(),
                "esco_loader":         esco_loader,
            }

            result_state = ats_agent.invoke(initial_state)
            final_report: dict = result_state.get("final_report", {})

            history_entry = AnalysisHistory(
                user_id=user.id,
                resume_filename=resume.filename,
                jd_snippet=jd_snippet,
                final_score=final_report.get("final_score", 0.0),
                fit_category=final_report.get("fit_category", "Unknown"),
                result_json=final_report,
            )
            db.add(history_entry)
            db.commit()
            db.refresh(history_entry)

            candidates.append({
                "rank":                 0,
                "resume_filename":      resume.filename or "unknown",
                "composite_score":      final_report.get("composite_score", 0.0),
                "skill_coverage_pct":   final_report.get("skill_coverage_pct", 0.0),
                "fit_category":         final_report.get("fit_category", "Unknown"),
                "risk_level":           final_report.get("risk_level", "Unknown"),
                "matched_skills":       final_report.get("matched_skills", []),
                "missing_skills":       final_report.get("missing_skills", []),
                "experience_years":     final_report.get("experience_years", 0.0),
                "experience_gap":       final_report.get("experience_gap", "N/A"),
                "top_evidenced_skills": final_report.get("top_evidenced_skills", []),
                "red_flags":            final_report.get("red_flags", []),
                "hiring_recommendation": final_report.get("hiring_recommendation", ""),
                "explanation":          final_report.get("explanation", ""),
                "analysis_id":          history_entry.id,
                "full_report":          final_report,
            })

        except Exception as exc:
            candidates.append(_error_candidate(resume.filename or "unknown", str(exc)))

    candidates.sort(key=lambda c: c.get("composite_score", 0.0), reverse=True)
    for idx, candidate in enumerate(candidates, start=1):
        candidate["rank"] = idx

    return {
        "total":        len(candidates),
        "jd_title":     jd_title,
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "candidates":   candidates,
    }


def _error_candidate(filename: str, error_msg: str) -> dict:
    return {
        "rank":                 0,
        "resume_filename":      filename,
        "composite_score":      0.0,
        "skill_coverage_pct":   0.0,
        "fit_category":         "Error",
        "risk_level":           "High",
        "matched_skills":       [],
        "missing_skills":       [],
        "experience_years":     0.0,
        "experience_gap":       "N/A",
        "top_evidenced_skills": [],
        "red_flags":            [f"Processing failed: {error_msg}"],
        "hiring_recommendation": "Unable to process",
        "explanation":          f"Analysis failed: {error_msg}",
        "analysis_id":          None,
        "full_report":          {},
    }
