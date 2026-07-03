import time
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import AnalysisHistory, User, JDLibrary
from ..auth.utils import get_current_user_email

router = APIRouter(prefix="/api", tags=["Analysis"])


@router.post("/analyze")
async def analyze_resume(
    request: Request,
    resume: UploadFile = File(...),
    jd_text: Optional[str] = Form(None),
    jd_id: Optional[int] = Form(None),
    required_experience: float = Form(0.0),
    llm_provider: str = Form("ollama"),
    enable_llm: bool = Form(True),
    db: Session = Depends(get_db),
    current_email: str = Depends(get_current_user_email),
):
    """Analyze a resume against a JD using the LangGraph agent pipeline."""
    try:
        user = db.query(User).filter(User.email == current_email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found in database",
            )

        # Resolve JD text from library or direct input
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
            jd_text = jd_entry.jd_text  # type: ignore
            jd_entry.usage_count += 1  # type: ignore
            db.commit()
        elif jd_text:
            jd_text = jd_text
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provide either jd_text or jd_id",
            )

        resume_bytes = await resume.read()
        if not resume_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Resume file is empty",
            )

        filename = resume.filename

        from agent.state import ATSAgentState, AnalysisMode
        from agent.graph import ats_agent

        initial_state: ATSAgentState = {
            "resume_bytes":        resume_bytes,
            "resume_filename":     filename or "",
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
            "esco_loader":         getattr(request.app.state, "esco", None),
        }

        result_state = ats_agent.invoke(initial_state)
        final_report = result_state.get("final_report", {})

        # Save result to history
        jd_snippet = None
        if jd_text:
            jd_snippet = jd_text[:200] + "..." if len(jd_text) > 200 else jd_text

        history_entry = AnalysisHistory(
            user_id=user.id,
            resume_filename=filename,
            jd_snippet=jd_snippet,
            final_score=final_report.get("final_score", 0.0),
            fit_category=final_report.get("fit_category", "Unknown"),
            result_json=final_report,
        )
        db.add(history_entry)
        db.commit()
        db.refresh(history_entry)

        return final_report

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}",
        )
