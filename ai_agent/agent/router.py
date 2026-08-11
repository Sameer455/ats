from __future__ import annotations

from typing import Any

from langgraph.graph import END

from agent.state import ATSAgentState, AnalysisMode


def route_after_intake(state: ATSAgentState) -> str:
    if not state.get("input_valid", False):
        return "report"
    return "extraction"


def route_after_extraction(state: ATSAgentState) -> str:
    confidence = (state.get("confidence_scores") or {}).get("overall", 1.0)
    attempts = state.get("extraction_attempts", 0)

    if confidence < 0.5 and attempts < 2:
        return "extraction"
    return "jd_analysis"


def route_after_reasoning(state: ATSAgentState) -> str:
    fit_category = state.get("fit_category", "")
    attempts = state.get("reasoning_attempts", 0)

    if fit_category == "Unable to determine" and attempts < 2:
        return "reasoning"

    mode = state.get("analysis_mode", AnalysisMode.SINGLE)
    if mode == AnalysisMode.BATCH or mode == "batch":
        return "batch_compare"
    return "deep_analysis"
