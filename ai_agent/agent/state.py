"""
agent/state.py — ATSAgentState TypedDict for the LangGraph agent pipeline.

This is the single shared state object that flows through every node in the graph.
Each node reads from and writes to this state. Fields are Optional where they are
not populated until their respective node runs.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional
from typing_extensions import TypedDict


class AnalysisMode(str, Enum):
    """Analysis mode: single resume or batch comparison."""
    SINGLE = "single"
    BATCH = "batch"


class ATSAgentState(TypedDict, total=False):
    """
    Shared state for the ATS LangGraph agent pipeline.

    Every node reads from and writes to this dict.  Fields use ``total=False``
    so that nodes only need to populate the keys they own.
    """

    # ── Inputs (set before graph invocation) ──────────────────────────────────
    resume_bytes: bytes
    resume_filename: str
    jd_text: str
    required_experience: float
    llm_provider: str
    enable_llm: bool
    analysis_mode: AnalysisMode

    # Batch mode: list of dicts with keys {resume_bytes, resume_filename}
    batch_resumes: Optional[list[dict[str, Any]]]

    # ESCO loader instance (injected at startup via app.state.esco)
    esco_loader: Optional[Any]

    # ── Control / counters ────────────────────────────────────────────────────
    agent_trace: list[str]
    extraction_attempts: int
    reasoning_attempts: int
    start_time_ns: int  # time.perf_counter_ns() at graph start

    # ── Node 1 — Intake Agent ────────────────────────────────────────────────
    file_type: Optional[str]         # "pdf" | "docx" | "scanned_pdf"
    input_valid: bool
    input_error: Optional[str]
    document_hash: Optional[str]     # SHA-256 hex digest

    # ── Node 2 — Extraction Agent ────────────────────────────────────────────
    resume_text: Optional[str]
    resume_sections: Optional[dict[str, str]]
    resume_skills: Optional[list[str]]
    experience_years: Optional[float]
    education: Optional[list[str]]
    roles: Optional[list[str]]
    confidence_scores: Optional[dict[str, float]]  # per-field + overall
    ocr_used: Optional[bool]
    force_ocr: Optional[bool]

    # ── Node 3 — JD Analysis Agent ───────────────────────────────────────────
    jd_skills: Optional[list[str]]
    jd_required_skills: Optional[list[str]]
    jd_preferred_skills: Optional[list[str]]
    jd_role_category: Optional[str]     # data_science|devops|frontend|product|engineering
    jd_seniority_level: Optional[str]   # intern|junior|mid|senior|manager
    jd_required_exp: Optional[float]
    # ESCO enrichment fields (additive)
    jd_esco_occupation: Optional[str]       # matched ESCO occupation title
    jd_esco_confidence: Optional[float]     # semantic similarity score (0–1)
    jd_implicit_skills: Optional[list[str]] # ESCO essential skills not in JD text
    jd_esco_skill_profile: Optional[dict[str, Any]]  # full ESCO profile dict

    # ── Node 4 — Scoring Agent ───────────────────────────────────────────────
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
    # Evidence-based scoring fields (additive)
    skill_evidence: Optional[dict[str, Any]]         # skill → SkillEvidence.to_dict()
    evidence_skill_score: Optional[float]            # 0–100 evidence-weighted mean
    top_evidenced_skills: Optional[list[str]]        # depth_score >= 0.8
    shallow_claimed_skills: Optional[list[str]]      # found but depth_score <= 0.3

    # ── Node 5 — Reasoning Agent ─────────────────────────────────────────────
    fit_category: Optional[str]
    risk_level: Optional[str]
    transferable_skills: Optional[list[str]]
    learning_capability: Optional[str]
    red_flags: Optional[list[str]]
    hiring_recommendation: Optional[str]
    explanation: Optional[str]
    llm_analysis: Optional[str]   # raw LLM text (backward compat)
    # ESCO-aware reasoning fields (additive)
    headline: Optional[str]                   # one-sentence hiring manager summary
    strengths: Optional[list[str]]            # evidence-backed positives
    concerns: Optional[list[str]]             # evidence-backed concerns
    trajectory_assessment: Optional[str]      # skill trajectory analysis
    recommendation: Optional[str]             # Strong Hire|Hire|Maybe|Pass
    confidence: Optional[float]               # 0–1 confidence in assessment
    interview_focus: Optional[list[str]]      # probing questions for gaps

    # ── Node 6a — Deep Analysis Agent ────────────────────────────────────────
    interview_questions: Optional[list[dict[str, Any]]]
    upskilling_plan: Optional[list[dict[str, Any]]]

    # ── Node 6b — Batch Comparison Agent ─────────────────────────────────────
    candidate_rankings: Optional[list[dict[str, Any]]]
    comparison_table: Optional[list[dict[str, Any]]]
    batch_results: Optional[list[dict[str, Any]]]  # pre-analyzed per-candidate results

    # ── Node 7 — Report Agent ────────────────────────────────────────────────
    final_report: Optional[dict[str, Any]]
    processing_time_ms: Optional[float]
