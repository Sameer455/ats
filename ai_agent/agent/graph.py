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
    graph = StateGraph(ATSAgentState)

    graph.add_node("intake", intake_agent)
    graph.add_node("extraction", extraction_agent)
    graph.add_node("jd_analysis", jd_analysis_agent)
    graph.add_node("scoring", scoring_agent)
    graph.add_node("reasoning", reasoning_agent)
    graph.add_node("deep_analysis", deep_analysis_agent)
    graph.add_node("batch_compare", batch_comparison_agent)
    graph.add_node("report", report_agent)

    graph.set_entry_point("intake")

    graph.add_conditional_edges(
        "intake",
        route_after_intake,
        {
            "extraction": "extraction",
            "report": "report",
        },
    )

    graph.add_conditional_edges(
        "extraction",
        route_after_extraction,
        {
            "extraction": "extraction",
            "jd_analysis": "jd_analysis",
        },
    )

    graph.add_edge("jd_analysis", "scoring")
    graph.add_edge("scoring", "reasoning")

    graph.add_conditional_edges(
        "reasoning",
        route_after_reasoning,
        {
            "reasoning": "reasoning",
            "deep_analysis": "deep_analysis",
            "batch_compare": "batch_compare",
        },
    )

    graph.add_edge("deep_analysis", "report")
    graph.add_edge("batch_compare", "report")
    graph.add_edge("report", END)

    return graph


_graph = build_ats_graph()
ats_agent = _graph.compile()
