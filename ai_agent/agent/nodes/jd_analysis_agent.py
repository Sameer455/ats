from __future__ import annotations

import re
from typing import Any

from agent.state import ATSAgentState


_REQUIRED_SIGNALS = {"must", "required", "mandatory", "essential", "minimum"}
_PREFERRED_SIGNALS = {"preferred", "nice to have", "plus", "bonus", "desired"}

_ROLE_CATEGORY_PATTERNS: dict[str, list[str]] = {
    "data_science": [
        "data scien", "machine learning", "ml engineer", "deep learning",
        "nlp", "natural language", "computer vision", "ai research",
        "data analyst", "analytics", "statistical",
    ],
    "devops": [
        "devops", "sre", "site reliability", "cloud engineer", "infrastructure",
        "platform engineer", "kubernetes", "docker", "ci/cd", "terraform",
    ],
    "frontend": [
        "frontend", "front-end", "front end", "ui developer", "ui engineer",
        "react developer", "angular developer", "vue developer",
        "web developer", "ux engineer",
    ],
    "product": [
        "product manager", "product owner", "program manager",
        "product lead", "product director", "technical program",
    ],
    "engineering": [
        "software engineer", "software developer", "backend", "back-end",
        "full stack", "full-stack", "systems engineer", "staff engineer",
        "principal engineer", "tech lead",
    ],
}

_SENIORITY_PATTERNS: dict[str, list[str]] = {
    "intern":  ["intern", "internship", "trainee", "apprentice", "co-op"],
    "junior":  ["junior", "entry level", "entry-level", "associate", "graduate"],
    "mid":     ["mid-level", "mid level", "intermediate"],
    "senior":  ["senior", "sr.", "sr ", "lead", "staff", "principal", "distinguished", "expert"],
    "manager": ["manager", "director", "head of", "vp ", "vice president", "chief", "cto", "ceo"],
}

_EXP_REQUIREMENT_RE = re.compile(
    r"(\d{1,2})\+?\s*(?:[-–—]?\s*\d{1,2}\+?\s*)?(?:years?|yrs?)\s*"
    r"(?:of\s+)?(?:relevant\s+|professional\s+|hands[- ]on\s+|industry\s+)?"
    r"(?:experience|exp)\b",
    re.IGNORECASE,
)

_ESCO_CONFIDENCE_THRESHOLD = 0.70


def _classify_skill_requirement(skill: str, jd_text: str) -> str:
    jd_lower    = jd_text.lower()
    skill_lower = skill.lower()

    sentences = re.split(r"[.;\n]", jd_lower)
    for sentence in sentences:
        if skill_lower in sentence:
            has_required  = any(sig in sentence for sig in _REQUIRED_SIGNALS)
            has_preferred = any(sig in sentence for sig in _PREFERRED_SIGNALS)
            if has_preferred and not has_required:
                return "preferred"
            if has_required:
                return "required"

    return "required"


def _detect_role_category(jd_text: str) -> str:
    jd_lower = jd_text.lower()
    scores: dict[str, int] = {
        cat: sum(1 for p in patterns if p in jd_lower)
        for cat, patterns in _ROLE_CATEGORY_PATTERNS.items()
    }
    if not scores or max(scores.values()) == 0:
        return "engineering"
    return max(scores, key=scores.get)  # type: ignore


def _detect_seniority(jd_text: str) -> str:
    jd_lower = jd_text.lower()
    scores: dict[str, int] = {
        level: sum(1 for p in patterns if p in jd_lower)
        for level, patterns in _SENIORITY_PATTERNS.items()
    }
    if not scores or max(scores.values()) == 0:
        return "mid"
    return max(scores, key=scores.get)  # type: ignore


def _detect_required_experience(jd_text: str) -> float:
    matches = _EXP_REQUIREMENT_RE.findall(jd_text)
    if matches:
        try:
            return float(matches[0])
        except (ValueError, TypeError):
            pass
    return 0.0


def _esco_enrich(
    jd_text: str,
    jd_required_skills: list[str],
    jd_preferred_skills: list[str],
    esco_loader: Any,
) -> dict[str, Any]:
    empty: dict[str, Any] = {
        "jd_esco_occupation":   "",
        "jd_esco_confidence":   0.0,
        "jd_implicit_skills":   [],
        "jd_esco_skill_profile": {},
        "jd_required_skills":   jd_required_skills,
        "jd_preferred_skills":  jd_preferred_skills,
    }

    if esco_loader is None or not getattr(esco_loader, "is_loaded", False):
        return empty

    try:
        from matching.semantic_matcher import get_model
        model = get_model()

        hits = esco_loader.find_closest_occupation(jd_text, model, top_k=1)
        if not hits:
            return empty

        best = hits[0]
        confidence: float = best["similarity_score"]

        if confidence < _ESCO_CONFIDENCE_THRESHOLD:
            return {
                **empty,
                "jd_esco_occupation": best["title"],
                "jd_esco_confidence": confidence,
            }

        profile = esco_loader.get_role_skill_profile(best["uri"])
        jd_lower = jd_text.lower()

        existing_required = {s.lower() for s in jd_required_skills}
        enriched_required = list(jd_required_skills)
        for s in profile.get("essential_skills", []):
            if s.lower() not in existing_required:
                enriched_required.append(s)
                existing_required.add(s.lower())

        existing_preferred = {s.lower() for s in jd_preferred_skills}
        enriched_preferred = list(jd_preferred_skills)
        for s in profile.get("optional_skills", []):
            if s.lower() not in existing_preferred:
                enriched_preferred.append(s)
                existing_preferred.add(s.lower())

        implicit = [
            s for s in profile.get("essential_skills", [])
            if s.lower() not in jd_lower
        ]

        return {
            "jd_esco_occupation":    best["title"],
            "jd_esco_confidence":    confidence,
            "jd_implicit_skills":    implicit,
            "jd_esco_skill_profile": profile,
            "jd_required_skills":    enriched_required,
            "jd_preferred_skills":   enriched_preferred,
        }

    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning("ESCO enrichment failed: %s", exc)
        return empty


def jd_analysis_agent(state: ATSAgentState) -> dict[str, Any]:
    trace: list[str] = list(state.get("agent_trace", []))
    jd_text: str     = state.get("jd_text", "")
    esco_loader: Any = state.get("esco_loader", None)

    try:
        from extraction.skills_extractor import extract_skills
        from normalization.normalizer import normalize_skills
        from preprocessing.cleaner import clean_text

        clean_jd      = clean_text(jd_text)
        jd_skills_raw = extract_skills(clean_jd)
        jd_skills     = normalize_skills(jd_skills_raw)

        jd_required_skills: list[str]  = []
        jd_preferred_skills: list[str] = []
        for skill in jd_skills:
            if _classify_skill_requirement(skill, clean_jd) == "preferred":
                jd_preferred_skills.append(skill)
            else:
                jd_required_skills.append(skill)

        jd_role_category  = _detect_role_category(clean_jd)
        jd_seniority_level = _detect_seniority(clean_jd)
        jd_required_exp   = _detect_required_experience(clean_jd)
        if jd_required_exp == 0.0:
            jd_required_exp = state.get("required_experience", 0.0)

        esco_result = _esco_enrich(
            jd_text            = clean_jd,
            jd_required_skills = jd_required_skills,
            jd_preferred_skills = jd_preferred_skills,
            esco_loader        = esco_loader,
        )

        jd_required_skills  = esco_result["jd_required_skills"]
        jd_preferred_skills = esco_result["jd_preferred_skills"]

        trace.append(
            f"jd_analysis: {len(jd_skills)} skills extracted "
            f"({len(jd_required_skills)} required, {len(jd_preferred_skills)} preferred), "
            f"category={jd_role_category}, seniority={jd_seniority_level}, "
            f"req_exp={jd_required_exp}y, "
            f"esco_occ={esco_result['jd_esco_occupation']!r}, "
            f"esco_conf={esco_result['jd_esco_confidence']:.3f}, "
            f"implicit={len(esco_result['jd_implicit_skills'])}"
        )

        return {
            "jd_skills":             jd_skills,
            "jd_required_skills":    jd_required_skills,
            "jd_preferred_skills":   jd_preferred_skills,
            "jd_role_category":      jd_role_category,
            "jd_seniority_level":    jd_seniority_level,
            "jd_required_exp":       jd_required_exp,
            "jd_esco_occupation":    esco_result["jd_esco_occupation"],
            "jd_esco_confidence":    esco_result["jd_esco_confidence"],
            "jd_implicit_skills":    esco_result["jd_implicit_skills"],
            "jd_esco_skill_profile": esco_result["jd_esco_skill_profile"],
            "agent_trace":           trace,
        }

    except Exception as exc:
        trace.append(f"jd_analysis: ERROR — {exc}")
        return {
            "jd_skills":             [],
            "jd_required_skills":    [],
            "jd_preferred_skills":   [],
            "jd_role_category":      "engineering",
            "jd_seniority_level":    "mid",
            "jd_required_exp":       state.get("required_experience", 0.0),
            "jd_esco_occupation":    "",
            "jd_esco_confidence":    0.0,
            "jd_implicit_skills":    [],
            "jd_esco_skill_profile": {},
            "agent_trace":           trace,
        }
