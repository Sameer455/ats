"""
agent/router.py — Conditional routing functions for the ATS LangGraph pipeline.

Each function receives the current state and returns the name of the next
node (or END) based on the state values.
"""

from __future__ import annotations

from typing import Any

from langgraph.graph import END

from agent.state import ATSAgentState, AnalysisMode


def route_after_intake(state: ATSAgentState) -> str:
    """
    After Node 1 (Intake):
      - If input_valid is False → END (short-circuit via report)
      - Else → extraction
    """
    if not state.get("input_valid", False):
        return "report"
    return "extraction"


def route_after_extraction(state: ATSAgentState) -> str:
    """
    After Node 2 (Extraction):
      - If overall confidence < 0.5 AND extraction_attempts < 2 → loop back to extraction
        with force_ocr=True
      - Else → jd_analysis
    """
    confidence = (state.get("confidence_scores") or {}).get("overall", 1.0)
    attempts = state.get("extraction_attempts", 0)

    if confidence < 0.5 and attempts < 2:
        return "extraction"  # loop back with force_ocr (set by extraction node)
    return "jd_analysis"


def route_after_reasoning(state: ATSAgentState) -> str:
    """
    After Node 5 (Reasoning):
      - If fit_category == "Unable to determine" AND reasoning_attempts < 2
        → loop back to reasoning
      - Else check mode:
        - If analysis_mode == "batch" → batch_compare
        - Else → deep_analysis
    """
    fit_category = state.get("fit_category", "")
    attempts = state.get("reasoning_attempts", 0)

    # Retry logic
    if fit_category == "Unable to determine" and attempts < 2:
        return "reasoning"

    # Mode routing
    mode = state.get("analysis_mode", AnalysisMode.SINGLE)
    if mode == AnalysisMode.BATCH or mode == "batch":
        return "batch_compare"
    return "deep_analysis"
