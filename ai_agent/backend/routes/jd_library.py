"""
backend/routes/jd_library.py — JD Library CRUD endpoints.

All endpoints require JWT auth. The library is shared across all users —
every logged-in recruiter can see all JDs, but only the uploader can delete.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, JDCategory, JDLibrary
from ..auth.utils import get_current_user_email

router = APIRouter(prefix="/api/jd-library", tags=["JD Library"])


# ── Auth helper: resolve email → User object ──────────────────────────────────

def get_current_user(
    email: str = Depends(get_current_user_email),
    db: Session = Depends(get_db),
) -> User:
    """Resolve the JWT email claim into a full User row."""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found in database",
        )
    return user


# ── Request / response schemas ─────────────────────────────────────────────────

class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class JDCreate(BaseModel):
    category_id: int
    title: str = Field(..., min_length=1, max_length=200)
    jd_text: str = Field(..., min_length=1)

class JDUpdate(BaseModel):
    category_id: Optional[int] = None
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    jd_text: Optional[str] = Field(None, min_length=1)


# ── Category endpoints ─────────────────────────────────────────────────────────

@router.post("/categories", status_code=status.HTTP_201_CREATED)
def create_category(
    body: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Create a new JD category."""
    existing = db.query(JDCategory).filter(JDCategory.name == body.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category with this name already exists",
        )

    category = JDCategory(
        name=body.name,
        created_by=current_user.id,
    )
    db.add(category)
    db.commit()
    db.refresh(category)

    return {
        "id": category.id,
        "name": category.name,
        "created_at": category.created_at.isoformat(),
    }


@router.get("/categories")
def list_categories(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> list[dict]:
    """List all categories with the count of active JDs in each."""
    categories = db.query(JDCategory).order_by(JDCategory.name).all()

    result: list[dict] = []
    for cat in categories:
        jd_count = (
            db.query(func.count(JDLibrary.id))
            .filter(JDLibrary.category_id == cat.id, JDLibrary.is_active == True)
            .scalar()
        )
        result.append({
            "id": cat.id,
            "name": cat.name,
            "jd_count": jd_count,
        })

    return result


# ── JD CRUD endpoints ──────────────────────────────────────────────────────────

@router.post("", status_code=status.HTTP_201_CREATED)
def create_jd(
    body: JDCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Upload a new JD to the library."""
    # Validate category exists
    category = db.query(JDCategory).filter(JDCategory.id == body.category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category not found",
        )

    # Check title uniqueness within category
    duplicate = (
        db.query(JDLibrary)
        .filter(
            JDLibrary.category_id == body.category_id,
            JDLibrary.title == body.title,
            JDLibrary.is_active == True,
        )
        .first()
    )
    if duplicate:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A JD with this title already exists in the selected category",
        )

    jd = JDLibrary(
        category_id=body.category_id,
        title=body.title,
        jd_text=body.jd_text,
        uploaded_by=current_user.id,
    )
    db.add(jd)
    db.commit()
    db.refresh(jd)

    return {
        "id": jd.id,
        "title": jd.title,
        "category_id": jd.category_id,
        "created_at": jd.created_at.isoformat(),
    }


@router.get("")
def list_jds(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> list[dict]:
    """
    Return all active JDs grouped by category.
    Categories sorted alphabetically; JDs sorted by usage_count desc, then title asc.
    """
    categories = db.query(JDCategory).order_by(JDCategory.name).all()

    result: list[dict] = []
    for cat in categories:
        jds = (
            db.query(JDLibrary)
            .filter(JDLibrary.category_id == cat.id, JDLibrary.is_active == True)
            .order_by(JDLibrary.usage_count.desc(), JDLibrary.title.asc())
            .all()
        )

        jd_list: list[dict] = []
        for jd in jds:
            uploader = db.query(User).filter(User.id == jd.uploaded_by).first()
            jd_list.append({
                "id": jd.id,
                "title": jd.title,
                "uploaded_by_name": uploader.email if uploader else "Unknown",
                "uploaded_by_id": jd.uploaded_by,
                "usage_count": jd.usage_count,
                "created_at": jd.created_at.isoformat(),
            })

        result.append({
            "category_id": cat.id,
            "category_name": cat.name,
            "jds": jd_list,
        })

    return result


@router.get("/{jd_id}")
def get_jd(
    jd_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> dict:
    """Return the full JD record including jd_text."""
    jd = (
        db.query(JDLibrary)
        .filter(JDLibrary.id == jd_id, JDLibrary.is_active == True)
        .first()
    )
    if not jd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="JD not found",
        )

    category = db.query(JDCategory).filter(JDCategory.id == jd.category_id).first()
    uploader = db.query(User).filter(User.id == jd.uploaded_by).first()

    return {
        "id": jd.id,
        "title": jd.title,
        "jd_text": jd.jd_text,
        "category_id": jd.category_id,
        "category_name": category.name if category else "Unknown",
        "usage_count": jd.usage_count,
        "uploaded_by_name": uploader.email if uploader else "Unknown",
        "uploaded_by_id": jd.uploaded_by,
        "created_at": jd.created_at.isoformat(),
    }


@router.put("/{jd_id}")
def update_jd(
    jd_id: int,
    body: JDUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Update an existing JD. Only the original uploader can edit."""
    jd = (
        db.query(JDLibrary)
        .filter(JDLibrary.id == jd_id, JDLibrary.is_active == True)
        .first()
    )
    if not jd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="JD not found",
        )

    if jd.uploaded_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit JDs you uploaded",
        )

    # Determine the target category (may change or stay the same)
    target_category_id = body.category_id if body.category_id is not None else jd.category_id

    # Validate category exists if changing
    if body.category_id is not None:
        category = db.query(JDCategory).filter(JDCategory.id == body.category_id).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category not found",
            )

    # Check title uniqueness within target category (exclude self)
    new_title = body.title if body.title is not None else jd.title
    duplicate = (
        db.query(JDLibrary)
        .filter(
            JDLibrary.category_id == target_category_id,
            JDLibrary.title == new_title,
            JDLibrary.is_active == True,
            JDLibrary.id != jd_id,
        )
        .first()
    )
    if duplicate:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A JD with this title already exists in the selected category",
        )

    # Apply updates
    if body.category_id is not None:
        jd.category_id = body.category_id  # type: ignore
    if body.title is not None:
        jd.title = body.title  # type: ignore
    if body.jd_text is not None:
        jd.jd_text = body.jd_text  # type: ignore

    db.commit()
    db.refresh(jd)

    category = db.query(JDCategory).filter(JDCategory.id == jd.category_id).first()

    return {
        "id": jd.id,
        "title": jd.title,
        "jd_text": jd.jd_text,
        "category_id": jd.category_id,
        "category_name": category.name if category else "Unknown",
        "message": "JD updated successfully",
    }


@router.delete("/{jd_id}")
def delete_jd(
    jd_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Soft-delete a JD. Only the uploader can delete their own JD."""
    jd = (
        db.query(JDLibrary)
        .filter(JDLibrary.id == jd_id, JDLibrary.is_active == True)
        .first()
    )
    if not jd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="JD not found",
        )

    if jd.uploaded_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete JDs you uploaded",
        )

    jd.is_active = False  # type: ignore
    db.commit()

    return {"message": "JD deleted"}

