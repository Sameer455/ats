from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, JSON, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    analyses = relationship("AnalysisHistory", back_populates="user")


class AnalysisHistory(Base):
    __tablename__ = "analysis_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    resume_filename = Column(String, nullable=True)
    jd_snippet = Column(String, nullable=True)
    final_score = Column(Float, nullable=True)
    fit_category = Column(String, nullable=True)
    result_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="analyses")


# JD Library models
class JDCategory(Base):
    __tablename__ = "jd_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    jd_entries = relationship("JDLibrary", back_populates="category")


class JDLibrary(Base):
    __tablename__ = "jd_library"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("jd_categories.id"), nullable=False)
    title = Column(String(200), nullable=False)
    jd_text = Column(Text, nullable=False)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    usage_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    category = relationship("JDCategory", back_populates="jd_entries")
    uploader = relationship("User")
