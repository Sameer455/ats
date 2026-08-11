from sentence_transformers import SentenceTransformer, util

_model = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer("all-mpnet-base-v2")
    return _model


_get_model = get_model


def compute_semantic_score(
    resume_text: str,
    jd_text: str,
    resume_sections: dict = None,
) -> float:
    model  = get_model()
    jd_emb = model.encode(jd_text, convert_to_tensor=True)

    if resume_sections and any(v.strip() for v in resume_sections.values()):
        return _chunked_score(model, jd_emb, resume_sections)

    resume_emb = model.encode(resume_text, convert_to_tensor=True)
    similarity = util.cos_sim(resume_emb, jd_emb).item()
    return round(max(0.0, min(1.0, similarity)), 4)


def _chunked_score(model, jd_emb, sections: dict) -> float:
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