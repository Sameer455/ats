"""
semantic_matcher.py - Section-level chunked semantic matching.

Instead of embedding the entire resume as a single vector (which dilutes
relevant content with noise for long resumes), this module:
  1. Splits resume into section-level chunks.
  2. Computes per-section cosine similarity against the JD.
  3. Returns a weighted average score based on section importance.

Changes from v1:
  - _get_model() renamed to get_model() — exported so hybrid_skill_matcher
    can reuse the same model instance without loading it twice.
  - compute_semantic_score() returns 0.0–1.0 float (not 0–100).
    Pipeline multiplies by 100 when building the result dict.
  - Removed old compute_skill_gap() and is_match() — moved to hybrid module.
  - Section weight for 'experience' raised from 0.30 to 0.35 (stronger signal).
"""

from sentence_transformers import SentenceTransformer, util

_model = None


def get_model() -> SentenceTransformer:
    """
    Returns the shared SentenceTransformer model instance.
    Loaded once at first call, reused for all subsequent calls.
    Exported (no leading underscore) so hybrid_skill_matcher can import it
    and avoid loading a second copy of the model into memory.
    """
    global _model
    if _model is None:
        _model = SentenceTransformer("all-mpnet-base-v2")
    return _model


# Keep old name as alias so any existing imports don't break
_get_model = get_model


def compute_semantic_score(
    resume_text: str,
    jd_text: str,
    resume_sections: dict = None,
) -> float:
    """
    Computes semantic similarity between resume and JD.

    If resume_sections is provided, uses section-level chunked embedding
    with weighted averaging for more accurate scores on long resumes.
    Falls back to single-vector comparison if sections are not provided.

    Returns a float in [0.0, 1.0] — NOT a percentage.
    Caller (pipeline.py) multiplies by 100 when building the result dict.
    """
    model  = get_model()
    jd_emb = model.encode(jd_text, convert_to_tensor=True)

    if resume_sections and any(v.strip() for v in resume_sections.values()):
        return _chunked_score(model, jd_emb, resume_sections)

    resume_emb = model.encode(resume_text, convert_to_tensor=True)
    similarity = util.cos_sim(resume_emb, jd_emb).item()
    return round(max(0.0, min(1.0, similarity)), 4)


def _chunked_score(model, jd_emb, sections: dict) -> float:
    """
    Weighted average of per-section cosine similarities.

    Section weights reflect hiring signal strength:
      experience 0.35 — actual work history (raised from 0.30)
      skills     0.25 — direct overlap
      projects   0.20 — practical proof
      summary    0.15 — candidate positioning
      other      0.05 — certifications, education, misc
    """
    weights = {
        "experience": 0.35,
        "skills":     0.25,
        "projects":   0.20,
        "summary":    0.15,
    }
    other_weight = 0.05

    weighted_sum = 0.0
    total_weight = 0.0

    for section_name, text in sections.items():
        text = text.strip()
        if not text or len(text) < 20:
            continue

        section_emb = model.encode(text, convert_to_tensor=True)
        similarity  = util.cos_sim(section_emb, jd_emb).item()
        similarity  = max(0.0, min(1.0, similarity))

        weight        = weights.get(section_name, other_weight)
        weighted_sum += similarity * weight
        total_weight += weight

    if total_weight == 0:
        return 0.0

    return round(weighted_sum / total_weight, 4)