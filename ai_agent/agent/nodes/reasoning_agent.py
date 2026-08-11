from __future__ import annotations

import re
from typing import Any

from agent.state import ATSAgentState


def _parse_llm_response(raw: str) -> dict[str, Any]:
    result: dict[str, Any] = {
        "fit_category":        "Unable to determine",
        "risk_level":          "Unknown",
        "transferable_skills": [],
        "learning_capability": "Not assessed",
        "red_flags":           [],
        "hiring_recommendation": "",
        "explanation":         raw,
    }

    if not raw or not raw.strip():
        return result

    raw_lower = raw.lower()

    for pattern, category in [
        (r"(?:high|strong)\s*fit",                  "Strong Fit"),
        (r"(?:medium|moderate|partial)\s*fit",      "Partial Fit"),
        (r"(?:low|weak|poor|not\s+a)\s*fit",        "Not a Fit"),
    ]:
        if re.search(pattern, raw_lower):
            result["fit_category"] = category
            break

    for pattern, level in [
        (r"low\s*risk",      "Low Risk"),
        (r"moderate\s*risk", "Moderate Risk"),
        (r"high\s*risk",     "High Risk"),
    ]:
        if re.search(pattern, raw_lower):
            result["risk_level"] = level
            break

    rec_match = re.search(
        r"(?:###?\s*\d*\.?\s*)?hiring\s+recommendation\s*[:\-—]?\s*\n?(.*?)(?:\n###|\Z)",
        raw, re.IGNORECASE | re.DOTALL,
    )
    if rec_match:
        result["hiring_recommendation"] = rec_match.group(1).strip()[:500]
    else:
        paragraphs = [p.strip() for p in raw.split("\n\n") if p.strip()]
        if paragraphs:
            result["hiring_recommendation"] = paragraphs[-1][:500]

    assess_match = re.search(
        r"(?:###?\s*\d*\.?\s*)?overall\s+assessment\s*[:\-—]?\s*\n?(.*?)(?:\n###|\n\n|\Z)",
        raw, re.IGNORECASE | re.DOTALL,
    )
    if assess_match:
        result["explanation"] = assess_match.group(1).strip()[:1000]

    red_flags: list[str] = []
    for pattern in [
        r"(?:risk|concern|gap|flag|warning|issue)\s*(?:factor|area)?s?\s*[:—\-]\s*(.+?)(?:\n|$)",
    ]:
        for match in re.finditer(pattern, raw, re.IGNORECASE):
            flag_text = match.group(1).strip()
            if flag_text and len(flag_text) > 5:
                red_flags.append(flag_text[:200])
    result["red_flags"] = red_flags[:10]

    return result


def _parse_upgraded_response(raw: str) -> dict[str, Any]:
    base = _parse_llm_response(raw)

    hl_match = re.search(
        r"(?:###?\s*)?headline\s*[:\-—]?\s*\n?(.+?)(?:\n|$)",
        raw, re.IGNORECASE,
    )
    headline = hl_match.group(1).strip()[:300] if hl_match else base["hiring_recommendation"][:200]

    str_match = re.search(
        r"(?:###?\s*)?strengths?\s*[:\-—]?\s*\n(.*?)(?:\n###|\n\n|\Z)",
        raw, re.IGNORECASE | re.DOTALL,
    )
    strengths: list[str] = []
    if str_match:
        for line in str_match.group(1).splitlines():
            line = re.sub(r"^[-•*\d.]+\s*", "", line).strip()
            if line:
                strengths.append(line[:200])
    strengths = strengths[:8]

    con_match = re.search(
        r"(?:###?\s*)?concerns?\s*[:\-—]?\s*\n(.*?)(?:\n###|\n\n|\Z)",
        raw, re.IGNORECASE | re.DOTALL,
    )
    concerns: list[str] = []
    if con_match:
        for line in con_match.group(1).splitlines():
            line = re.sub(r"^[-•*\d.]+\s*", "", line).strip()
            if line:
                concerns.append(line[:200])
    concerns = concerns[:8] or base["red_flags"]

    traj_match = re.search(
        r"(?:###?\s*)?trajectory\s*[:\-—]?\s*\n?(.+?)(?:\n###|\n\n|\Z)",
        raw, re.IGNORECASE | re.DOTALL,
    )
    trajectory_assessment = (
        traj_match.group(1).strip()[:400] if traj_match else "Not assessed"
    )

    rec_map = [
        (r"\bstrong\s+hire\b", "Strong Hire"),
        (r"\bhire\b",          "Hire"),
        (r"\bmaybe\b",         "Maybe"),
        (r"\bpass\b",          "Pass"),
    ]
    recommendation = base["hiring_recommendation"][:100]
    for pattern, label in rec_map:
        if re.search(pattern, raw, re.IGNORECASE):
            recommendation = label
            break

    conf_match = re.search(r"confidence\s*[:\-—]?\s*([\d.]+)", raw, re.IGNORECASE)
    try:
        confidence = min(1.0, max(0.0, float(conf_match.group(1)))) if conf_match else 0.7
    except (ValueError, AttributeError):
        confidence = 0.7

    focus_match = re.search(
        r"(?:###?\s*)?interview\s+focus\s*[:\-—]?\s*\n(.*?)(?:\n###|\n\n|\Z)",
        raw, re.IGNORECASE | re.DOTALL,
    )
    interview_focus: list[str] = []
    if focus_match:
        for line in focus_match.group(1).splitlines():
            line = re.sub(r"^[-•*\d.]+\s*", "", line).strip()
            if line:
                interview_focus.append(line[:200])
    interview_focus = interview_focus[:6]

    return {
        **base,
        "headline":               headline,
        "strengths":              strengths,
        "concerns":               concerns,
        "trajectory_assessment":  trajectory_assessment,
        "recommendation":         recommendation,
        "confidence":             confidence,
        "interview_focus":        interview_focus,
    }


def _build_esco_context(state: ATSAgentState) -> str:
    esco_occ      = state.get("jd_esco_occupation", "")
    esco_conf     = state.get("jd_esco_confidence", 0.0)
    esco_profile  = state.get("jd_esco_skill_profile", {})
    implicit      = state.get("jd_implicit_skills", [])
    skill_ev      = state.get("skill_evidence", {})
    top_evidenced = state.get("top_evidenced_skills", [])
    shallow       = state.get("shallow_claimed_skills", [])

    if not esco_occ:
        return ""

    lines: list[str] = [
        f"\n## ESCO Role Profile (confidence={esco_conf:.2f})",
        f"Matched ESCO occupation: {esco_occ}",
    ]

    if esco_profile.get("essential_skills"):
        lines.append(
            "Essential skills per ESCO: "
            + ", ".join(esco_profile["essential_skills"][:15])
        )

    if implicit:
        lines.append(
            "\nImplicit requirements (ESCO essential, not stated in JD): "
            + ", ".join(implicit[:10])
        )

    if skill_ev:
        lines.append("\n## Skill Evidence Summary")
        for skill, ev_dict in list(skill_ev.items())[:8]:
            score  = ev_dict.get("depth_score", 0.0)
            found  = ev_dict.get("found", False)
            years  = ev_dict.get("years_used", 0)
            status = f"found (depth={score:.1f}" + (f", {years}y" if years else "") + ")" \
                     if found else "NOT found in resume"
            lines.append(f"  - {skill}: {status}")

    if top_evidenced:
        lines.append(
            "\nStrongly evidenced skills (depth≥0.8): " + ", ".join(top_evidenced[:8])
        )
    if shallow:
        lines.append(
            "Shallow/listed-only skills (depth≤0.3): " + ", ".join(shallow[:8])
        )

    years_by_skill = {
        s: d.get("recency_year", 0)
        for s, d in skill_ev.items()
        if d.get("recency_year", 0) > 0
    }
    if years_by_skill:
        newest_skill = max(years_by_skill, key=years_by_skill.get)  # type: ignore
        lines.append(
            f"\nTrajectory signals: Most recently evidenced skill is '{newest_skill}' "
            f"({years_by_skill[newest_skill]}). "
            "Assess whether skills are becoming more complex over time."
        )

    return "\n".join(lines)


def _safe_fallback(
    composite_score: float,
    adversarial_flags: list[str],
) -> dict[str, Any]:
    if composite_score >= 80:
        fit, risk = "Strong Fit", "Low Risk"
        rec = "Strong candidate based on quantitative scoring. LLM analysis unavailable."
    elif composite_score >= 60:
        fit, risk = "Partial Fit", "Moderate Risk"
        rec = "Moderate candidate. Manual review recommended. LLM analysis unavailable."
    else:
        fit, risk = "Not a Fit", "High Risk"
        rec = "Weak match based on quantitative scoring. LLM analysis unavailable."

    return {
        "fit_category":          fit,
        "risk_level":            risk,
        "transferable_skills":   [],
        "learning_capability":   "Not assessed (LLM unavailable)",
        "red_flags":             adversarial_flags if adversarial_flags else [],
        "hiring_recommendation": rec,
        "explanation":           f"Score-based assessment: {composite_score}% composite score.",
        "llm_analysis":          "LLM analysis was not available after retry attempts.",
        "headline":              rec[:200],
        "strengths":             [],
        "concerns":              [],
        "trajectory_assessment": "Not assessed",
        "recommendation":        "Maybe" if composite_score >= 60 else "Pass",
        "confidence":            0.5,
        "interview_focus":       [],
    }


def reasoning_agent(state: ATSAgentState) -> dict[str, Any]:
    trace: list[str]        = list(state.get("agent_trace", []))
    attempts: int           = state.get("reasoning_attempts", 0) + 1
    enable_llm: bool        = state.get("enable_llm", True)
    llm_provider: str       = state.get("llm_provider", "ollama")
    composite_score: float  = state.get("composite_score", 0.0)
    adversarial_flags       = state.get("adversarial_flags", [])
    has_esco: bool          = bool(state.get("jd_esco_occupation", ""))

    if not enable_llm:
        trace.append("reasoning: LLM disabled — using score-based fallback")
        fallback = _safe_fallback(composite_score, adversarial_flags)
        fallback["reasoning_attempts"] = attempts
        fallback["agent_trace"]        = trace
        return fallback

    try:
        from llm.llm_chain import run_ats_analysis

        roles    = state.get("roles", [])
        job_role = roles[0] if roles else "Not specified"

        jd_text = state.get("jd_text", "")
        if adversarial_flags:
            jd_text += "\n\n⚠️ RED FLAG HINTS:\n" + "\n".join(
                f"- {f}" for f in adversarial_flags
            )

        esco_context = _build_esco_context(state)
        jd_with_context = jd_text + esco_context if esco_context else jd_text

        raw_analysis = run_ats_analysis(
            job_role           = job_role,
            semantic_score     = state.get("semantic_score", 0.0),
            skill_coverage     = state.get("skill_coverage_pct", 0.0),
            matched_skills     = state.get("matched_skills", []),
            missing_skills     = state.get("missing_skills", []),
            experience_years   = state.get("experience_years", 0.0),
            required_experience = state.get("required_experience", 0.0),
            education          = state.get("education", []),
            jd_text            = jd_with_context,
            provider           = llm_provider,
        )

        parsed = (
            _parse_upgraded_response(raw_analysis)
            if has_esco
            else _parse_llm_response(raw_analysis)
        )

        trace.append(
            f"reasoning: attempt {attempts} — "
            f"fit={parsed['fit_category']}, risk={parsed['risk_level']}, "
            f"provider={llm_provider}, esco_context={has_esco}"
        )

        base_return: dict[str, Any] = {
            "fit_category":          parsed["fit_category"],
            "risk_level":            parsed["risk_level"],
            "transferable_skills":   parsed["transferable_skills"],
            "learning_capability":   parsed["learning_capability"],
            "red_flags":             parsed["red_flags"] + adversarial_flags,
            "hiring_recommendation": parsed["hiring_recommendation"],
            "explanation":           parsed["explanation"],
            "llm_analysis":          raw_analysis,
            "reasoning_attempts":    attempts,
            "headline":              parsed.get("headline", ""),
            "strengths":             parsed.get("strengths", []),
            "concerns":              parsed.get("concerns", parsed["red_flags"]),
            "trajectory_assessment": parsed.get("trajectory_assessment", "Not assessed"),
            "recommendation":        parsed.get("recommendation", parsed["hiring_recommendation"][:100]),
            "confidence":            parsed.get("confidence", 0.7),
            "interview_focus":       parsed.get("interview_focus", []),
            "agent_trace":           trace,
        }
        return base_return

    except Exception as exc:
        trace.append(f"reasoning: ERROR on attempt {attempts} — {exc}")

        if attempts >= 2:
            trace.append("reasoning: max attempts reached — using safe fallback")
            fallback = _safe_fallback(composite_score, adversarial_flags)
            fallback["reasoning_attempts"] = attempts
            fallback["agent_trace"]        = trace
            return fallback

        return {
            "fit_category":          "Unable to determine",
            "risk_level":            "Unknown",
            "transferable_skills":   [],
            "learning_capability":   "Not assessed",
            "red_flags":             adversarial_flags,
            "hiring_recommendation": "",
            "explanation":           f"LLM analysis failed: {exc}",
            "llm_analysis":          f"Error: {exc}",
            "reasoning_attempts":    attempts,
            "headline":              "",
            "strengths":             [],
            "concerns":              [],
            "trajectory_assessment": "Not assessed",
            "recommendation":        "Maybe",
            "confidence":            0.0,
            "interview_focus":       [],
            "agent_trace":           trace,
        }
