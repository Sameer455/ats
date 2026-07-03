from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import AnalysisHistory, User
from ..auth.utils import get_current_user_email

router = APIRouter(prefix="/api", tags=["History"])

@router.get("/history")
def get_user_history(
    db: Session = Depends(get_db), 
    current_email: str = Depends(get_current_user_email)
):
    """Get all analysis history for the authenticated user, sorted by date (newest first)."""
    user = db.query(User).filter(User.email == current_email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    # Get all histories, descending date
    histories = db.query(AnalysisHistory)\
                  .filter(AnalysisHistory.user_id == user.id)\
                  .order_by(AnalysisHistory.created_at.desc())\
                  .all()
    
    # Return structured summary for dashboard
    return [
        {
            "id": h.id,
            "filename": h.resume_filename,
            "final_score": h.final_score,
            "fit_category": h.fit_category,
            "created_at": h.created_at,
            "jd_snippet": h.jd_snippet
        } for h in histories
    ]

@router.get("/history/{history_id}")
def get_history_detail(
    history_id: int,
    db: Session = Depends(get_db), 
    current_email: str = Depends(get_current_user_email)
):
    """Get detailed analysis results for a specific history entry."""
    user = db.query(User).filter(User.email == current_email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    history = db.query(AnalysisHistory).filter(
        AnalysisHistory.id == history_id, 
        AnalysisHistory.user_id == user.id
    ).first()

    if not history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis history not found"
        )

    return history.result_json
