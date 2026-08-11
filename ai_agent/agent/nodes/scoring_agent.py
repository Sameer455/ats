from __future__ import annotations

import re
from typing import Any

from agent.state import ATSAgentState


_ROLE_WEIGHTS: dict[str, dict[str, float]] = {
    "data_science":  {"skills": 0.30, "experience": 0.25, "education": 0.30, "semantic": 0.15},
    "devops":        {"skills": 0.45, "experience": 0.40, "education": 0.05, "semantic": 0.10},
    "frontend":      {"skills": 0.45, "experience": 0.35, "education": 0.10, "semantic": 0.10},
    "product":       {"skills": 0.25, "experience": 0.40, "education": 0.20, "semantic": 0.15},
    "engineering":   {"skills": 0.40, "experience": 0.35, "education": 0.15, "semantic": 0.10},
}

_SENIORITY_MULTIPLIERS: dict[str, float] = {
    "intern":  0.6,
    "junior":  0.8,
    "mid":     1.0,
    "senior":  1.15,
    "manager": 1.25,
}


def _detect_adversarial_flags(
    resume_skills: list[str],
    resume_text: str,
) -> list[str]:
    flags: list[str] = []

    if len(resume_skills) > 60:
        flags.append(
            f"Unusually high skill count ({len(resume_skills)}). "
            "Possible keyword stuffing."
        )

    text_lower = resume_text.lower()
    for skill in resume_skills[:20]:
        occurrences = len(re.findall(re.escape(skill.lower()), text_lower))
        if occurrences > 8:
            flags.append(
                f"Skill '{skill}' appears {occurrences} times. "
                "Possible keyword stuffing."
            )

    if len(resume_text) > 15000 and len(resume_skills) > 40:
        flags.append(
            "Resume is unusually long with high skill density. "
            "Recommend manual review."
        )

    return flags


def _run_evidence_scoring(
    resume_text: str,
    resume_sections: dict[str, str],
    jd_required_skills: list[str],
    jd_implicit_skills: list[str],
    skill_coverage_pct: float,
) -> dict[str, Any]:
    empty: dict[str, Any] = {
        "skill_evidence":         {},
        "evidence_skill_score":   skill_coverage_pct,
        "top_evidenced_skills":   [],
        "shallow_claimed_skills": [],
        "blended_skill_score":    skill_coverage_pct,
    }

    if not jd_required_skills:
        return empty

    try:
        from extraction.skill_evidence_extractor import SkillEvidenceExtractor
        extractor = SkillEvidenceExtractor()

        evidence_map = extractor.extract_evidence(
            resume_text     = resume_text,
            resume_sections = resume_sections,
            target_skills   = jd_required_skills,
        )

        implicit_set = {s.lower() for s in jd_implicit_skills}
        scores: list[float] = []

        for skill, ev in evidence_map.items():
            is_implicit = skill.lower() in implicit_set
            if not ev.found:
                score = 0.0
            elif is_implicit:
                score = ev.depth_score * 0.5
            else:
                score = ev.depth_score
            scores.append(score)

        evidence_skill_score = (sum(scores) / len(scores) * 100) if scores else skill_coverage_pct

        skill_evidence_dicts = {
            skill: ev.to_dict()
            for skill, ev in evidence_map.items()
        }

        top_evidenced   = [s for s, ev in evidence_map.items() if ev.found and ev.depth_score >= 0.8]
        shallow_claimed = [s for s, ev in evidence_map.items() if ev.found and ev.depth_score <= 0.3]

        blended = round(
            0.6 * evidence_skill_score + 0.4 * skill_coverage_pct, 1
        )

        return {
            "skill_evidence":         skill_evidence_dicts,
            "evidence_skill_score":   round(evidence_skill_score, 1),
            "top_evidenced_skills":   top_evidenced,
            "shallow_claimed_skills": shallow_claimed,
            "blended_skill_score":    blended,
        }

    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning("Evidence scoring failed: %s", exc)
        return empty


def scoring_agent(state: ATSAgentState) -> dict[str, Any]:
    trace: list[str] = list(state.get("agent_trace", []))

    try:
        resume_skills    = state.get("resume_skills", [])
        jd_skills        = state.get("jd_skills", [])
        jd_required      = state.get("jd_required_skills", jd_skills)
        experience_years = state.get("experience_years", 0.0)
        education        = state.get("education", [])
        resume_text      = state.get("resume_text", "")
        resume_sections  = state.get("resume_sections", {})
        jd_text          = state.get("jd_text", "")
        role_category    = state.get("jd_role_category", "engineering")
        seniority        = state.get("jd_seniority_level", "mid")
        jd_implicit      = state.get("jd_implicit_skills", [])

        required_experience = state.get("jd_required_exp", 0.0)
        if required_experience == 0.0:
            required_experience = state.get("required_experience", 0.0)

        from matching.hybrid_skill_matcher import compute_hybrid_skill_gap
        gap_result        = compute_hybrid_skill_gap(resume_skills, jd_skills)
        skill_coverage_pct = gap_result["skill_coverage_pct"]

        from matching.semantic_matcher import compute_semantic_score
        from preprocessing.cleaner import clean_for_embedding

        embed_resume   = clean_for_embedding(resume_text)
        embed_jd       = clean_for_embedding(jd_text)
        embed_sections = {
            k: clean_for_embedding(v)
            for k, v in resume_sections.items()
            if v and v.strip()
        }
        semantic_score = round(
            compute_semantic_score(embed_resume, embed_jd, resume_sections=embed_sections) * 100,
            1,
        )

        if required_experience > 0:
            exp_score = min(experience_years / required_experience, 1.0) * 100
        else:
            exp_score = 100.0
        seniority_mult = _SENIORITY_MULTIPLIERS.get(seniority, 1.0)
        exp_score      = min(exp_score * seniority_mult, 100.0)

        edu_score = 100.0 if len(education) > 0 else 30.0

        ev_result = _run_evidence_scoring(
            resume_text        = resume_text,
            resume_sections    = resume_sections,
            jd_required_skills = jd_required,
            jd_implicit_skills = jd_implicit,
            skill_coverage_pct = skill_coverage_pct,
        )
        effective_skill_score = ev_result["blended_skill_score"]

        weights = _ROLE_WEIGHTS.get(role_category, _ROLE_WEIGHTS["engineering"])
        composite_score = round(
            effective_skill_score * weights["skills"]
            + exp_score            * weights["experience"]
            + edu_score            * weights["education"]
            + semantic_score       * weights["semantic"],
            1,
        )

        exp_gap_val    = round(required_experience - experience_years, 1)
        experience_gap = (
            f"+{abs(exp_gap_val)} yrs over requirement"
            if exp_gap_val <= 0
            else f"-{exp_gap_val} yrs short"
        )

        adversarial_flags = _detect_adversarial_flags(resume_skills, resume_text)

        trace.append(
            f"scoring: composite={composite_score}, "
            f"weights={role_category}, seniority_mult={seniority_mult}, "
            f"skill_cov={skill_coverage_pct}%, evidence={ev_result['evidence_skill_score']}%, "
            f"blended_skill={effective_skill_score}%, "
            f"semantic={semantic_score}%, exp={round(exp_score, 1)}%, edu={edu_score}%, "
            f"top_evidenced={len(ev_result['top_evidenced_skills'])}, "
            f"shallow={len(ev_result['shallow_claimed_skills'])}, "
            f"adversarial={len(adversarial_flags)}"
        )

        return {
            "composite_score":    composite_score,
            "semantic_score":     semantic_score,
            "skill_coverage_pct": skill_coverage_pct,
            "experience_score":   round(exp_score, 1),
            "education_score":    edu_score,
            "matched_skills":     gap_result["matched_skills"],
            "missing_skills":     gap_result["missing_skills"],
            "extra_skills":       gap_result["extra_skills"],
            "match_details":      gap_result.get("match_details", []),
            "adversarial_flags":  adversarial_flags,
            "experience_gap":     experience_gap,
            "skill_evidence":         ev_result["skill_evidence"],
            "evidence_skill_score":   ev_result["evidence_skill_score"],
            "top_evidenced_skills":   ev_result["top_evidenced_skills"],
            "shallow_claimed_skills": ev_result["shallow_claimed_skills"],
            "agent_trace":            trace,
        }

    except Exception as exc:
        trace.append(f"scoring: ERROR — {exc}")
        return {
            "composite_score":        0.0,
            "semantic_score":         0.0,
            "skill_coverage_pct":     0.0,
            "experience_score":       0.0,
            "education_score":        0.0,
            "matched_skills":         [],
            "missing_skills":         state.get("jd_skills", []),
            "extra_skills":           state.get("resume_skills", []),
            "match_details":          [],
            "adversarial_flags":      [],
            "experience_gap":         "Unable to compute",
            "skill_evidence":         {},
            "evidence_skill_score":   0.0,
            "top_evidenced_skills":   [],
            "shallow_claimed_skills": [],
            "agent_trace":            trace,
        }
