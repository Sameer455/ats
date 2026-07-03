"""
hybrid_skill_matcher.py - Hybrid skill matching combining fuzzy + embedding similarity.

Combines RapidFuzz token_sort_ratio (syntactic) with sentence-transformer cosine
similarity (semantic) for robust skill gap analysis. This catches:
  - Typo variants and minor wording differences          (fuzzy)
  - Semantically equivalent skills with different names  (embeddings)
    e.g. "machine learning" ↔ "ml modeling"
    e.g. "rest api" ↔ "web services"
    e.g. "data visualization" ↔ "data viz"

Score formula:
    combined = α × fuzzy_score + (1 - α) × embedding_score
    α = FUZZY_WEIGHT (default 0.4) — embeddings are the stronger signal

Guards:
    FUZZY_FLOOR    — hard-reject if fuzzy < 0.30 (prevents embedding-only false positives)
    FUZZY_FASTPATH — auto-match if fuzzy > 0.90 (skips embedding for obvious matches)

All thresholds are env-configurable for runtime tuning without code changes.
Set in your .env file:
    SKILL_FUZZY_WEIGHT=0.4
    SKILL_MATCH_THRESHOLD=0.72
    SKILL_FUZZY_FLOOR=0.30
    SKILL_FUZZY_FASTPATH=0.90

Method labels in match_details:
    "fuzzy_fastpath"    — fuzzy > FUZZY_FASTPATH, embedding computation skipped
    "hybrid"            — both signals used, fuzzy was dominant
    "embedding_primary" — both signals used, embedding was dominant
    "unmatched"         — no resume skill scored above MATCH_THRESHOLD
    "rejected"          — fuzzy < FUZZY_FLOOR (internal, not exposed in match_details)

Reuses the model instance from semantic_matcher.get_model() —
no second copy of the model is loaded into memory.
"""

import os
from rapidfuzz import fuzz
from sentence_transformers import util as st_util


# ── Configurable thresholds ────────────────────────────────────────────────────
FUZZY_WEIGHT    = float(os.getenv("SKILL_FUZZY_WEIGHT",    "0.4"))
MATCH_THRESHOLD = float(os.getenv("SKILL_MATCH_THRESHOLD", "0.72"))
FUZZY_FLOOR     = float(os.getenv("SKILL_FUZZY_FLOOR",     "0.30"))
FUZZY_FASTPATH  = float(os.getenv("SKILL_FUZZY_FASTPATH",  "0.90"))


def _hybrid_score(
    skill_a: str,
    skill_b: str,
    emb_a,
    emb_b,
) -> tuple[float, str]:
    """
    Computes hybrid match score between two skills.

    Args:
        skill_a:  First skill string (e.g. JD skill).
        skill_b:  Second skill string (e.g. resume skill).
        emb_a:    Pre-computed embedding tensor for skill_a.
        emb_b:    Pre-computed embedding tensor for skill_b.

    Returns:
        (score: float [0.0–1.0], method: str)
    """
    fuzzy_score = fuzz.token_sort_ratio(skill_a, skill_b) / 100.0

    # Hard reject: too syntactically dissimilar to trust embedding alone.
    # Prevents "analysis" embedding-matching "machine learning" via coincidence.
    if fuzzy_score < FUZZY_FLOOR:
        return 0.0, "rejected"

    # Fast-path: strong fuzzy match — skip embedding to save latency.
    if fuzzy_score > FUZZY_FASTPATH:
        return fuzzy_score, "fuzzy_fastpath"

    # Hybrid: combine both signals
    embed_score = st_util.cos_sim(emb_a, emb_b).item()
    embed_score = max(0.0, min(1.0, embed_score))
    combined    = FUZZY_WEIGHT * fuzzy_score + (1.0 - FUZZY_WEIGHT) * embed_score

    method = "embedding_primary" if embed_score > fuzzy_score else "hybrid"
    return combined, method


def compute_hybrid_skill_gap(
    resume_skills: list,
    jd_skills: list,
) -> dict:
    """
    Compares resume and JD skills using hybrid fuzzy + embedding matching.

    Key improvements over simple set-difference (old compute_skill_gap):
      - Catches semantically equivalent skills with different wording
      - Catches abbreviation variants not in the synonym table
      - Batch encodes all skills at once — O(n) embeddings not O(n²)
      - extra_skills correctly excludes hybrid-matched skills

    Args:
        resume_skills: Normalised skill strings from the resume.
        jd_skills:     Normalised skill strings from the JD.

    Returns:
        {
            matched_skills      : JD skills found in resume (direct or semantic)
            missing_skills      : JD skills NOT found in resume
            extra_skills        : Resume skills not satisfying any JD requirement
            skill_coverage_pct  : % of JD skills matched (float)
            match_details       : Per-JD-skill breakdown list
            match_method_summary: Counts by matching method
        }

    match_details entry format:
        {
            jd_skill  : str          — the JD skill being matched
            matched_to: str | None   — which resume skill it matched (None if unmatched)
            confidence: float        — score × 100, e.g. 87.3
            method    : str          — "fuzzy_fastpath" | "hybrid" |
                                       "embedding_primary" | "unmatched"
        }
    """
    # Normalise + deduplicate while preserving order
    jd_skills     = list(dict.fromkeys(s.lower().strip() for s in jd_skills     if s.strip()))
    resume_skills = list(dict.fromkeys(s.lower().strip() for s in resume_skills if s.strip()))

    empty_summary = {
        "fuzzy_fastpath_count":     0,
        "hybrid_count":             0,
        "embedding_primary_count":  0,
        "unmatched_count":          0,
    }

    if not jd_skills:
        return {
            "matched_skills":       [],
            "missing_skills":       [],
            "extra_skills":         sorted(resume_skills),
            "skill_coverage_pct":   0.0,
            "match_details":        [],
            "match_method_summary": empty_summary,
        }

    if not resume_skills:
        return {
            "matched_skills":       [],
            "missing_skills":       sorted(jd_skills),
            "extra_skills":         [],
            "skill_coverage_pct":   0.0,
            "match_details":        [
                {"jd_skill": s, "matched_to": None, "confidence": 0.0, "method": "unmatched"}
                for s in jd_skills
            ],
            "match_method_summary": {**empty_summary, "unmatched_count": len(jd_skills)},
        }

    # ── Batch-encode all skills in one forward pass ───────────────────────────
    # Import here to avoid circular import — semantic_matcher also imports nothing from here
    from matching.semantic_matcher import get_model
    model = get_model()

    all_skills     = jd_skills + resume_skills
    all_embeddings = model.encode(
        all_skills,
        convert_to_tensor=True,
        show_progress_bar=False,
        batch_size=64,
    )
    jd_embeddings     = all_embeddings[: len(jd_skills)]
    resume_embeddings = all_embeddings[len(jd_skills):]

    # ── Match each JD skill to best resume skill ─────────────────────────────
    matched_jd          = []
    missing_jd          = []
    match_details       = []
    matched_resume_idxs = set()

    counts = {
        "fuzzy_fastpath":    0,
        "hybrid":            0,
        "embedding_primary": 0,
        "unmatched":         0,
    }

    for jd_idx, jd_skill in enumerate(jd_skills):
        best_score        = 0.0
        best_method       = "rejected"
        best_resume_idx   = -1
        best_resume_skill = None

        for res_idx, res_skill in enumerate(resume_skills):
            score, method = _hybrid_score(
                jd_skill,
                res_skill,
                jd_embeddings[jd_idx],
                resume_embeddings[res_idx],
            )
            if score > best_score:
                best_score        = score
                best_method       = method
                best_resume_idx   = res_idx
                best_resume_skill = res_skill

        is_match = (best_score >= MATCH_THRESHOLD) and (best_resume_idx >= 0)

        if is_match:
            matched_jd.append(jd_skill)
            matched_resume_idxs.add(best_resume_idx)
            counts[best_method] = counts.get(best_method, 0) + 1
            match_details.append({
                "jd_skill":   jd_skill,
                "matched_to": best_resume_skill,
                "confidence": round(best_score * 100, 1),
                "method":     best_method,
            })
        else:
            missing_jd.append(jd_skill)
            counts["unmatched"] += 1
            match_details.append({
                "jd_skill":   jd_skill,
                "matched_to": None,
                "confidence": round(best_score * 100, 1),
                "method":     "unmatched",
            })

    # Extra skills: resume skills NOT used to satisfy any JD requirement.
    # Uses matched_resume_idxs so hybrid-matched skills are correctly excluded.
    extra = [
        res for idx, res in enumerate(resume_skills)
        if idx not in matched_resume_idxs
    ]

    jd_count = len(jd_skills)
    coverage = round(len(matched_jd) / jd_count * 100, 1) if jd_count else 0.0

    return {
        "matched_skills":  sorted(set(matched_jd)),
        "missing_skills":  sorted(set(missing_jd)),
        "extra_skills":    sorted(set(extra)),
        "skill_coverage_pct": coverage,
        "match_details":   match_details,
        "match_method_summary": {
            "fuzzy_fastpath_count":     counts["fuzzy_fastpath"],
            "hybrid_count":             counts["hybrid"],
            "embedding_primary_count":  counts["embedding_primary"],
            "unmatched_count":          counts["unmatched"],
        },
    }