"""
agent/graph.py — LangGraph StateGraph compilation for the ATS agent pipeline.

Builds and compiles the full agent graph with all nodes and conditional edges.
Exports ``ats_agent`` — the compiled, ready-to-invoke graph.
"""

from __future__ import annotations

from langgraph.graph import StateGraph, END

from agent.state import ATSAgentState
from agent.nodes.intake_agent import intake_agent
from agent.nodes.extraction_agent import extraction_agent
from agent.nodes.jd_analysis_agent import jd_analysis_agent
from agent.nodes.scoring_agent import scoring_agent
from agent.nodes.reasoning_agent import reasoning_agent
from agent.nodes.deep_analysis_agent import deep_analysis_agent
from agent.nodes.batch_comparison_agent import batch_comparison_agent
from agent.nodes.report_agent import report_agent
from agent.router import (
    route_after_intake,
    route_after_extraction,
    route_after_reasoning,
)


def build_ats_graph() -> StateGraph:
    """
    Constructs the ATS agent graph with all nodes and edges.

    Graph topology::

        intake
          │
          ├─ [input_valid=False] ──────────────────────── report ──→ END
          │
          └─ [input_valid=True] → extraction
                                    │
                                    ├─ [confidence<0.5 & attempts<2] ─→ extraction (loop)
                                    │
                                    └─ jd_analysis → scoring → reasoning
                                                                  │
                                                     ┌─ [retry] ──┤
                                                     │             │
                                                     └─ reasoning  ├─ [batch] → batch_compare → report → END
                                                                   │
                                                                   └─ [single] → deep_analysis → report → END
    """
    graph = StateGraph(ATSAgentState)

    # ── Add all nodes ─────────────────────────────────────────────────────────
    graph.add_node("intake", intake_agent)
    graph.add_node("extraction", extraction_agent)
    graph.add_node("jd_analysis", jd_analysis_agent)
    graph.add_node("scoring", scoring_agent)
    graph.add_node("reasoning", reasoning_agent)
    graph.add_node("deep_analysis", deep_analysis_agent)
    graph.add_node("batch_compare", batch_comparison_agent)
    graph.add_node("report", report_agent)

    # ── Entry point ───────────────────────────────────────────────────────────
    graph.set_entry_point("intake")

    # ── Conditional edges ─────────────────────────────────────────────────────
    graph.add_conditional_edges(
        "intake",
        route_after_intake,
        {
            "extraction": "extraction",
            "report": "report",       # short-circuit on invalid input
        },
    )

    graph.add_conditional_edges(
        "extraction",
        route_after_extraction,
        {
            "extraction": "extraction",   # retry loop
            "jd_analysis": "jd_analysis",
        },
    )

    # ── Fixed edges ───────────────────────────────────────────────────────────
    graph.add_edge("jd_analysis", "scoring")
    graph.add_edge("scoring", "reasoning")

    # ── Reasoning conditional edges ───────────────────────────────────────────
    graph.add_conditional_edges(
        "reasoning",
        route_after_reasoning,
        {
            "reasoning": "reasoning",       # retry loop
            "deep_analysis": "deep_analysis",
            "batch_compare": "batch_compare",
        },
    )

    # ── Both analysis paths lead to report ────────────────────────────────────
    graph.add_edge("deep_analysis", "report")
    graph.add_edge("batch_compare", "report")
    graph.add_edge("report", END)

    return graph


# ── Compile the graph ─────────────────────────────────────────────────────────
_graph = build_ats_graph()
ats_agent = _graph.compile()
