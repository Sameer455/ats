"""
backend/pipeline.py - Orchestration pipeline for the new ATS backend.
"""

from parser.pdf_parser import extract_text_from_bytes
from preprocessing.cleaner import clean_text, clean_for_embedding
from segmentation.section_splitter import split_sections
from extraction.skills_extractor import extract_skills
from extraction.experience_extractor import extract_experience
from extraction.role_extractor import extract_roles
from extraction.education_extractor import extract_education
from normalization.normalizer import normalize_skills
from matching.semantic_matcher import compute_semantic_score
from matching.hybrid_skill_matcher import compute_hybrid_skill_gap

import requests

def run_pipeline(
    resume_bytes: bytes,
    resume_filename: str,
    jd_text: str,
    required_experience: float = 0.0,
) -> dict:
    """
    Full end-to-end ATS analysis pipeline.
    """

    # 1: Extract Raw Text
    raw_resume_text = extract_text_from_bytes(resume_bytes, resume_filename)

    # 2: Clean
    clean_resume = clean_text(raw_resume_text)
    clean_jd = clean_text(jd_text)

    # 3: Section Segmentation
    resume_sections = split_sections(clean_resume)

    # 4: Extract Entities
    skills_text_parts = [
        resume_sections.get("skills", ""),
        resume_sections.get("projects", ""),
        resume_sections.get("certifications", ""),
        resume_sections.get("summary", ""),
        resume_sections.get("experience", ""),
    ]
    skills_text = "\n".join(p for p in skills_text_parts if p.strip()) or clean_resume
    resume_skills_raw = extract_skills(skills_text)
    resume_skills = normalize_skills(resume_skills_raw)

    jd_skills_raw = extract_skills(clean_jd)
    jd_skills = normalize_skills(jd_skills_raw)

    experience_section = resume_sections.get("experience", "").strip()
    experience_years = extract_experience(
        experience_section if experience_section else clean_resume
    )
    roles = extract_roles(clean_resume)
    education = extract_education(resume_sections.get("education", "") or clean_resume)

    # 5: Semantic Matching
    embed_resume = clean_for_embedding(clean_resume)
    embed_jd = clean_for_embedding(clean_jd)
    embed_sections = {k: clean_for_embedding(v) for k, v in resume_sections.items() if v.strip()}
    
    # Semantic score now returns a float 0.0 - 1.0, so multiply by 100
    semantic_score_raw = compute_semantic_score(embed_resume, embed_jd, resume_sections=embed_sections)
    semantic_score = round(semantic_score_raw * 100, 1)

    # 6: Skill Gap Analysis
    gap_result = compute_hybrid_skill_gap(resume_skills, jd_skills)
    skill_score = gap_result["skill_coverage_pct"]

    # 6b: Per-section semantic scores (each section vs JD)
    section_scores = {}
    for section_name, section_text in resume_sections.items():
        if section_text and section_text.strip() and len(section_text.strip()) >= 20:
            section_clean = clean_for_embedding(section_text)
            raw = compute_semantic_score(section_clean, embed_jd, resume_sections={})
            section_scores[section_name] = round(raw * 100, 1)

    # 7: Experience & Education Scores
    exp_score = min(experience_years / required_experience, 1.0) * 100 if required_experience > 0 else 100.0
    
    # Simple rule for education
    has_education = len(education) > 0
    edu_score = 100.0 if has_education else 30.0

    # 8: Final Weighted Score
    # Semantic 40%, Skill gap 25%, Experience 25%, Education 10%
    final_score = round(
        (semantic_score * 0.40) + 
        (skill_score * 0.25) + 
        (exp_score * 0.25) + 
        (edu_score * 0.10), 1
    )

    if final_score >= 80:
        fit = "Strong Fit"
    elif final_score >= 60:
        fit = "Partial Fit"
    else:
        fit = "Not a Fit"

    # 9: LLM Analysis directly via Ollama
    job_role = roles[0] if roles else "Not specified"
    prompt = f"""
    You are a senior HR technology specialist.
    Analyze the candidate for the role of {job_role}.
    
    Overall Score: {final_score}%
    Semantic Score: {semantic_score}%
    Skill Coverage: {skill_score}%
    Experience: {experience_years} years (Required: {required_experience})
    Matched Skills: {gap_result['matched_skills']}
    Missing Skills: {gap_result['missing_skills']}
    Education: {education}
    
    Provide:
    1. A short candidate summary.
    2. Missing critical skills and risk factors.
    3. Final recommendation.
    Be concise.
    """
    
    llm_analysis = ""
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3",
                "prompt": prompt,
                "stream": False
            },
            timeout=180
        )
        if response.status_code == 200:
            llm_analysis = response.json().get("response", "")
        else:
            llm_analysis = f"⚠️ LLM Error: Status {response.status_code}"
    except Exception as e:
        llm_analysis = f"⚠️ LLM Unavailable (Ollama must be running on localhost:11434): {str(e)}"

    # Calculate experience gap description
    exp_gap = round(required_experience - experience_years, 1)
    if exp_gap <= 0:
        experience_gap = f"+{abs(exp_gap)} yrs over requirement"
    else:
        experience_gap = f"-{exp_gap} yrs short"

    return {
        # Primary scores (for frontend display)
        "final_score": final_score,
        "composite_score": final_score,  # Same as final_score for UI consistency
        "fit_category": fit,
        "semantic_score": semantic_score,
        "skill_coverage_pct": skill_score,  # Frontend expects this name
        "experience_years": experience_years,
        "experience_gap": experience_gap,
        "experience_score": round(exp_score, 1),
        "education_score": edu_score,
        
        # Skills analysis
        "matched_skills": gap_result["matched_skills"],
        "missing_skills": gap_result["missing_skills"],
        "extra_skills": gap_result["extra_skills"],
        "match_details": gap_result.get("match_details", []),
        "match_method_summary": gap_result.get("match_method_summary", {}),
        "resume_skills": resume_skills,
        "jd_skills": jd_skills,
        
        # Requirements & Extracted content
        "required_experience": required_experience,
        "roles": roles,
        "education": education,
        "sections": resume_sections,        # Raw text per section
        "section_scores": section_scores,   # Per-section semantic score vs JD
        
        # LLM analysis
        "llm_analysis": llm_analysis,
    }
