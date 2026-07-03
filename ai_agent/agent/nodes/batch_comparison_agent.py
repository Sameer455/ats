"""
agent/nodes/batch_comparison_agent.py — Node 6b: Batch candidate ranking & comparison.

Only runs in BATCH analysis mode.  Receives pre-analyzed candidates from
state, ranks them by composite_score, and generates a comparative summary
using the LLM.
"""

from __future__ import annotations

import json
import re
from typing import Any

from agent.state import ATSAgentState


_COMPARISON_PROMPT = """You are a senior HR technology specialist comparing multiple candidates.

## Candidates (ranked by score)
{candidates_summary}

## Job Requirements
{jd_text}

Based on the data above, provide:
1. A brief comparative summary (3-5 sentences) explaining who is the strongest candidate and why.
2. Key differentiators between the top candidates.
3. Any notable risks or concerns across candidates.

Be concise, data-driven, and professional. Return plain text, not JSON.
"""


def batch_comparison_agent(state: ATSAgentState) -> dict[str, Any]:
    """
    Batch Comparison Agent — ranks and compares multiple analyzed candidates.

    Reads:
        batch_results (list of per-candidate analysis dicts),
        jd_text, llm_provider, enable_llm
    Writes:
        candidate_rankings, comparison_table, agent_trace
    """
    trace: list[str] = list(state.get("agent_trace", []))
    batch_results: list[dict[str, Any]] = state.get("batch_results", []) # type: ignore
    enable_llm: bool = state.get("enable_llm", True)
    llm_provider: str = state.get("llm_provider", "ollama")
    jd_text: str = state.get("jd_text", "")

    if not batch_results:
        trace.append("batch_compare: no candidates to compare")
        return {
            "candidate_rankings": [],
            "comparison_table": [],
            "agent_trace": trace,
        }

    try:
        # ── Sort candidates by composite score ────────────────────────────────
        sorted_candidates = sorted(
            batch_results,
            key=lambda c: c.get("composite_score", 0.0),
            reverse=True,
        )

        # ── Build comparison table ────────────────────────────────────────────
        comparison_table: list[dict[str, Any]] = []
        candidate_rankings: list[dict[str, Any]] = []

        for rank, candidate in enumerate(sorted_candidates, start=1):
            missing = candidate.get("missing_skills", [])
            top_gap = missing[0] if missing else "None"

            table_row = {
                "rank": rank,
                "name": candidate.get("resume_filename", f"Candidate {rank}"),
                "score": candidate.get("composite_score", 0.0),
                "fit_category": candidate.get("fit_category", "Unknown"),
                "top_gap": top_gap,
            }
            comparison_table.append(table_row)

            ranking_entry = {
                "rank": rank,
                "resume_filename": candidate.get("resume_filename", f"Candidate {rank}"),
                "composite_score": candidate.get("composite_score", 0.0),
                "fit_category": candidate.get("fit_category", "Unknown"),
                "semantic_score": candidate.get("semantic_score", 0.0),
                "skill_coverage_pct": candidate.get("skill_coverage_pct", 0.0),
                "experience_years": candidate.get("experience_years", 0.0),
                "matched_skills": candidate.get("matched_skills", []),
                "missing_skills": missing,
            }
            candidate_rankings.append(ranking_entry)

        # ── Generate comparative summary via LLM ──────────────────────────────
        comparative_summary = ""
        if enable_llm and len(sorted_candidates) > 1:
            try:
                from llm.llm_chain import _get_llm
                from langchain_core.prompts import PromptTemplate
                from langchain_core.output_parsers import StrOutputParser

                # Build summary text for the prompt
                cand_lines = []
                for row in comparison_table:
                    cand_lines.append(
                        f"#{row['rank']} {row['name']}: "
                        f"Score={row['score']}%, Fit={row['fit_category']}, "
                        f"Top Gap={row['top_gap']}"
                    )
                candidates_summary = "\n".join(cand_lines)

                llm = _get_llm(llm_provider)
                cmp_prompt = PromptTemplate(
                    input_variables=["candidates_summary", "jd_text"],
                    template=_COMPARISON_PROMPT,
                )
                cmp_chain = cmp_prompt | llm | StrOutputParser()
                comparative_summary = cmp_chain.invoke({
                    "candidates_summary": candidates_summary,
                    "jd_text": jd_text[:1500],
                })

                trace.append(
                    f"batch_compare: ranked {len(sorted_candidates)} candidates, "
                    f"generated comparative summary via LLM"
                )
            except Exception as llm_err:
                trace.append(f"batch_compare: LLM comparison failed — {llm_err}")
                comparative_summary = (
                    f"Top candidate: {comparison_table[0]['name']} "
                    f"with score {comparison_table[0]['score']}%."
                )
        else:
            trace.append(
                f"batch_compare: ranked {len(sorted_candidates)} candidates "
                f"(LLM comparison skipped)"
            )

        # Add comparative summary to rankings
        for entry in candidate_rankings:
            entry["comparative_summary"] = comparative_summary

        return {
            "candidate_rankings": candidate_rankings,
            "comparison_table": comparison_table,
            "agent_trace": trace,
        }

    except Exception as exc:
        trace.append(f"batch_compare: ERROR — {exc}")
        return {
            "candidate_rankings": [],
            "comparison_table": [],
            "agent_trace": trace,
        }
