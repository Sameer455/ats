from __future__ import annotations

from enum import Enum
from typing import Any, Optional
from typing_extensions import TypedDict


class AnalysisMode(str, Enum):
    SINGLE = "single"
    BATCH = "batch"


class ATSAgentState(TypedDict, total=False):

    # Inputs
    resume_bytes: bytes
    resume_filename: str
    jd_text: str
    required_experience: float
    llm_provider: str
    enable_llm: bool
    analysis_mode: AnalysisMode

    batch_resumes: Optional[list[dict[str, Any]]]
    esco_loader: Optional[Any]

    # Control / counters
    agent_trace: list[str]
    extraction_attempts: int
    reasoning_attempts: int
    start_time_ns: int

    # Intake
    file_type: Optional[str]
    input_valid: bool
    input_error: Optional[str]
    document_hash: Optional[str]

    # Extraction
    resume_text: Optional[str]
    resume_sections: Optional[dict[str, str]]
    resume_skills: Optional[list[str]]
    experience_years: Optional[float]
    education: Optional[list[str]]
    roles: Optional[list[str]]
    confidence_scores: Optional[dict[str, float]]
    ocr_used: Optional[bool]
    force_ocr: Optional[bool]

    # JD Analysis
    jd_skills: Optional[list[str]]
    jd_required_skills: Optional[list[str]]
    jd_preferred_skills: Optional[list[str]]
    jd_role_category: Optional[str]
    jd_seniority_level: Optional[str]
    jd_required_exp: Optional[float]
    jd_esco_occupation: Optional[str]
    jd_esco_confidence: Optional[float]
    jd_implicit_skills: Optional[list[str]]
    jd_esco_skill_profile: Optional[dict[str, Any]]

    # Scoring
    composite_score: Optional[float]
    semantic_score: Optional[float]
    skill_coverage_pct: Optional[float]
    experience_score: Optional[float]
    education_score: Optional[float]
    matched_skills: Optional[list[str]]
    missing_skills: Optional[list[str]]
    extra_skills: Optional[list[str]]
    match_details: Optional[list[dict[str, Any]]]
    adversarial_flags: Optional[list[str]]
    experience_gap: Optional[str]
    skill_evidence: Optional[dict[str, Any]]
    evidence_skill_score: Optional[float]
    top_evidenced_skills: Optional[list[str]]
    shallow_claimed_skills: Optional[list[str]]

    # Reasoning
    fit_category: Optional[str]
    risk_level: Optional[str]
    transferable_skills: Optional[list[str]]
    learning_capability: Optional[str]
    red_flags: Optional[list[str]]
    hiring_recommendation: Optional[str]
    explanation: Optional[str]
    llm_analysis: Optional[str]
    headline: Optional[str]
    strengths: Optional[list[str]]
    concerns: Optional[list[str]]
    trajectory_assessment: Optional[str]
    recommendation: Optional[str]
    confidence: Optional[float]
    interview_focus: Optional[list[str]]

    # Deep Analysis
    interview_questions: Optional[list[dict[str, Any]]]
    upskilling_plan: Optional[list[dict[str, Any]]]

    # Batch Comparison
    candidate_rankings: Optional[list[dict[str, Any]]]
    comparison_table: Optional[list[dict[str, Any]]]
    batch_results: Optional[list[dict[str, Any]]]

    # Report
    final_report: Optional[dict[str, Any]]
    processing_time_ms: Optional[float]
