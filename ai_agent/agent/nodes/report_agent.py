"""
agent/nodes/report_agent.py — Node 7: Final report assembly.

Assembles the ``final_report`` dict from all state fields, adds timing
and audit trail, and ensures 100% backward compatibility with the
existing React frontend response format.
"""

from __future__ import annotations

import time
from typing import Any

from agent.state import ATSAgentState


def report_agent(state: ATSAgentState) -> dict[str, Any]:
    """
    Report Agent — assembles the final structured report.

    All existing response keys are preserved for frontend compatibility.
    New keys are added for the agentic features.

    Reads: all state fields
    Writes: final_report, processing_time_ms, agent_trace
    """
    trace: list[str] = list(state.get("agent_trace", []))
    start_ns: int = state.get("start_time_ns", 0)

    # ── Compute processing time ───────────────────────────────────────────────
    if start_ns > 0:
        processing_time_ms = round((time.perf_counter_ns() - start_ns) / 1_000_000, 1)
    else:
        processing_time_ms = 0.0

    trace.append(f"report: assembling final report — {processing_time_ms}ms total")

    # ── Compute backward-compatible fields ────────────────────────────────────
    composite_score = state.get("composite_score", 0.0)
    experience_years = state.get("experience_years", 0.0)
    resume_skills = state.get("resume_skills", [])
    jd_skills = state.get("jd_skills", [])
    resume_sections = state.get("resume_sections", {})

    # Per-section semantic scores (backward compat with existing pipeline)
    section_scores: dict[str, float] = {}
    try:
        from preprocessing.cleaner import clean_for_embedding
        from matching.semantic_matcher import compute_semantic_score

        embed_jd = clean_for_embedding(state.get("jd_text", ""))
        for section_name, section_text in resume_sections.items():
            if section_text and section_text.strip() and len(section_text.strip()) >= 20:
                section_clean = clean_for_embedding(section_text)
                raw_score = compute_semantic_score(section_clean, embed_jd, resume_sections=None)
                section_scores[section_name] = round(raw_score * 100, 1)
    except Exception:
        pass  # non-critical, skip if fails

    # ── Assemble final report ─────────────────────────────────────────────────
    final_report: dict[str, Any] = {
        # ── Primary scores (existing frontend expects these) ──────────────────
        "final_score": composite_score,
        "composite_score": composite_score,
        "fit_category": state.get("fit_category", "Unknown"),
        "semantic_score": state.get("semantic_score", 0.0),
        "skill_coverage_pct": state.get("skill_coverage_pct", 0.0),
        "experience_years": experience_years,
        "experience_gap": state.get("experience_gap", "N/A"),
        "experience_score": state.get("experience_score", 0.0),
        "education_score": state.get("education_score", 0.0),

        # ── Skills analysis ───────────────────────────────────────────────────
        "matched_skills": state.get("matched_skills", []),
        "missing_skills": state.get("missing_skills", []),
        "extra_skills": state.get("extra_skills", []),
        "match_details": state.get("match_details", []),
        "resume_skills": resume_skills,
        "jd_skills": jd_skills,

        # ── Requirements & extracted content ──────────────────────────────────
        "required_experience": state.get("required_experience", 0.0),
        "roles": state.get("roles", []),
        "education": state.get("education", []),
        "sections": resume_sections,
        "section_scores": section_scores,

        # ── LLM analysis (backward compat) ────────────────────────────────────
        "llm_analysis": state.get("llm_analysis", ""),

        # ── Reasoning Agent fields ────────────────────────────────────────────
        "risk_level": state.get("risk_level", "Unknown"),
        "transferable_skills": state.get("transferable_skills", []),
        "learning_capability": state.get("learning_capability", "Not assessed"),
        "red_flags": state.get("red_flags", []),
        "hiring_recommendation": state.get("hiring_recommendation", ""),
        "explanation": state.get("explanation", ""),

        # ── Extraction metadata ───────────────────────────────────────────────
        "ocr_used": state.get("ocr_used", False),
        "document_hash": state.get("document_hash", ""),
        "confidence_scores": state.get("confidence_scores", {}),

        # ── Adversarial detection ─────────────────────────────────────────────
        "adversarial_detection": {
            "flags": state.get("adversarial_flags", []),
            "is_suspicious": len(state.get("adversarial_flags", [])) > 0,
        },

        # ── JD Analysis fields ────────────────────────────────────────────────
        "jd_required_skills": state.get("jd_required_skills", []),
        "jd_preferred_skills": state.get("jd_preferred_skills", []),
        "jd_role_category": state.get("jd_role_category", "engineering"),
        "jd_seniority_level": state.get("jd_seniority_level", "mid"),

        # ── New agentic features ──────────────────────────────────────────────
        "interview_questions": state.get("interview_questions", []),
        "upskilling_plan": state.get("upskilling_plan", []),
        "candidate_rankings": state.get("candidate_rankings", []),
        "comparison_table": state.get("comparison_table", []),

        # ── Audit trail ───────────────────────────────────────────────────────
        "agent_trace": trace,
        "processing_time_ms": processing_time_ms,
    }

    # ── Handle input validation failure (short-circuit) ───────────────────────
    if not state.get("input_valid", True):
        final_report = {
            "error": True,
            "input_error": state.get("input_error", "Unknown validation error"),
            "final_score": 0.0,
            "composite_score": 0.0,
            "fit_category": "Invalid Input",
            "agent_trace": trace,
            "processing_time_ms": processing_time_ms,
        }

    return {
        "final_report": final_report,
        "processing_time_ms": processing_time_ms,
        "agent_trace": trace,
    }
