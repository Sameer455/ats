from __future__ import annotations

import json
import re
from typing import Any

from agent.state import ATSAgentState


_INTERVIEW_PROMPT = """You are a senior technical interviewer.

Based on the following candidate analysis, generate exactly 8 targeted interview questions.

## Candidate Profile
- Matched Skills: {matched_skills}
- Missing Skills: {missing_skills}
- Experience: {experience_years} years (Required: {required_experience})
- Fit Category: {fit_category}
- Red Flags: {red_flags}
- Role: {job_role}

## Question Categories
Generate questions across these categories:
- "technical" — verify claimed skills with depth
- "behavioural" — assess soft skills and team fit
- "gap_probe" — explore identified skill gaps and how the candidate would address them

## Output Format
Return a JSON array of exactly 8 objects. Each object must have:
- "question": the interview question (string)
- "category": one of "technical", "behavioural", "gap_probe" (string)
- "skill_target": the specific skill or area being tested (string)
- "why": brief reason this question matters for this candidate (string)

Return ONLY the JSON array, no other text.
"""

_UPSKILLING_PROMPT = """You are a career development advisor.

Based on the candidate's current skills and identified gaps, create an upskilling plan.

## Current Skills
{matched_skills}

## Missing Skills (gaps to address)
{missing_skills}

## Extra Skills (candidate has but JD doesn't require)
{extra_skills}

## Role Target
{job_role}

## Output Format
Return a JSON array of objects for each missing skill that needs upskilling.
Each object must have:
- "skill": the skill to learn (string)
- "priority": "high", "medium", or "low" based on importance for the role (string)
- "estimated_weeks": estimated weeks to achieve competency (integer)
- "resources": array of 2-3 recommended learning resources (array of strings)
- "leverages_existing": which existing candidate skill(s) would help learn this faster (string or null)

Return ONLY the JSON array, no other text.
"""


def _safe_parse_json_array(raw: str) -> list[dict[str, Any]]:
    if not raw or not raw.strip():
        return []

    cleaned = re.sub(r"```(?:json)?\s*", "", raw)
    cleaned = re.sub(r"```\s*$", "", cleaned)
    cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\[.*\]", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    return []


def _generate_fallback_questions(state: ATSAgentState) -> list[dict[str, Any]]:
    questions: list[dict[str, Any]] = []
    missing = state.get("missing_skills") or []
    matched = state.get("matched_skills") or []
    red_flags = state.get("red_flags") or []

    for skill in matched[:3]:
        questions.append({
            "question": f"Can you describe a project where you extensively used {skill}?",
            "category": "technical",
            "skill_target": skill,
            "why": "Verify depth of claimed skill through practical experience."
        })

    for skill in missing[:3]:
        questions.append({
            "question": f"How would you approach learning {skill} for this role?",
            "category": "gap_probe",
            "skill_target": skill,
            "why": "Assess candidate's plan to address identified skill gap."
        })

    if red_flags:
        questions.append({
            "question": "Can you walk me through your most impactful contribution in your recent role?",
            "category": "behavioural",
            "skill_target": "impact verification",
            "why": "Verify claims that triggered red flags."
        })

    questions.append({
        "question": "How do you stay current with new technologies in your field?",
        "category": "behavioural",
        "skill_target": "learning agility",
        "why": "Assess growth mindset and continuous learning ability."
    })

    return questions[:8]


def _generate_fallback_upskilling(state: ATSAgentState) -> list[dict[str, Any]]:
    missing = state.get("missing_skills") or []
    plan: list[dict[str, Any]] = []

    for i, skill in enumerate(missing[:8]):
        priority = "high" if i < 3 else ("medium" if i < 6 else "low")
        plan.append({
            "skill": skill,
            "priority": priority,
            "estimated_weeks": 4 if priority == "high" else 6,
            "resources": [
                f"Online course on {skill}",
                f"Official {skill} documentation",
            ],
            "leverages_existing": None,
        })

    return plan


def deep_analysis_agent(state: ATSAgentState) -> dict[str, Any]:
    trace: list[str] = list(state.get("agent_trace", []))
    enable_llm: bool = state.get("enable_llm", True)
    llm_provider: str = state.get("llm_provider", "ollama")

    matched_skills = state.get("matched_skills", [])
    missing_skills = state.get("missing_skills", [])
    extra_skills = state.get("extra_skills", [])
    roles = state.get("roles", [])
    job_role = roles[0] if roles else "Not specified"

    interview_questions: list[dict[str, Any]] = []
    upskilling_plan: list[dict[str, Any]] = []

    if not enable_llm:
        trace.append("deep_analysis: LLM disabled — using fallback generation")
        return {
            "interview_questions": _generate_fallback_questions(state),
            "upskilling_plan": _generate_fallback_upskilling(state),
            "agent_trace": trace,
        }

    try:
        from llm.llm_chain import _get_llm
        from langchain_core.prompts import PromptTemplate
        from langchain_core.output_parsers import StrOutputParser

        llm = _get_llm(llm_provider)

        try:
            iq_prompt = PromptTemplate(
                input_variables=[
                    "matched_skills", "missing_skills", "experience_years",
                    "required_experience", "fit_category", "red_flags", "job_role",
                ],
                template=_INTERVIEW_PROMPT,
            )
            iq_chain = iq_prompt | llm | StrOutputParser()
            iq_raw = iq_chain.invoke({
                "matched_skills": ", ".join(matched_skills) if matched_skills else "None",
                "missing_skills": ", ".join(missing_skills) if missing_skills else "None",
                "experience_years": state.get("experience_years") or 0.0,
                "required_experience": state.get("required_experience") or 0.0,
                "fit_category": state.get("fit_category") or "Unknown",
                "red_flags": ", ".join(state.get("red_flags") or []) or "None",
                "job_role": job_role,
            })
            interview_questions = _safe_parse_json_array(iq_raw)
            if not interview_questions:
                trace.append("deep_analysis: interview questions JSON parse failed — using fallback")
                interview_questions = _generate_fallback_questions(state)
            else:
                trace.append(f"deep_analysis: generated {len(interview_questions)} interview questions via LLM")
        except Exception as iq_err:
            trace.append(f"deep_analysis: interview question generation failed — {iq_err}")
            interview_questions = _generate_fallback_questions(state)

        try:
            up_prompt = PromptTemplate(
                input_variables=[
                    "matched_skills", "missing_skills", "extra_skills", "job_role",
                ],
                template=_UPSKILLING_PROMPT,
            )
            up_chain = up_prompt | llm | StrOutputParser()
            up_raw = up_chain.invoke({
                "matched_skills": ", ".join(matched_skills) if matched_skills else "None",
                "missing_skills": ", ".join(missing_skills) if missing_skills else "None",
                "extra_skills": ", ".join(extra_skills) if extra_skills else "None",
                "job_role": job_role,
            })
            upskilling_plan = _safe_parse_json_array(up_raw)
            if not upskilling_plan:
                trace.append("deep_analysis: upskilling plan JSON parse failed — using fallback")
                upskilling_plan = _generate_fallback_upskilling(state)
            else:
                trace.append(f"deep_analysis: generated {len(upskilling_plan)} upskilling items via LLM")
        except Exception as up_err:
            trace.append(f"deep_analysis: upskilling plan generation failed — {up_err}")
            upskilling_plan = _generate_fallback_upskilling(state)

    except Exception as exc:
        trace.append(f"deep_analysis: LLM init failed — {exc}")
        interview_questions = _generate_fallback_questions(state)
        upskilling_plan = _generate_fallback_upskilling(state)

    return {
        "interview_questions": interview_questions,
        "upskilling_plan": upskilling_plan,
        "agent_trace": trace,
    }
