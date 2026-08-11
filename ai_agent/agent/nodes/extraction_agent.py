from __future__ import annotations

from typing import Any

from agent.state import ATSAgentState


def extraction_agent(state: ATSAgentState) -> dict[str, Any]:
    trace: list[str] = list(state.get("agent_trace") or [])
    attempts: int = (state.get("extraction_attempts") or 0) + 1
    force_ocr: bool = state.get("force_ocr") or False

    resume_bytes: bytes = state["resume_bytes"]
    resume_filename: str = state.get("resume_filename") or "resume.pdf"

    try:
        from parser.pdf_parser import extract_text_from_bytes

        raw_text = extract_text_from_bytes(resume_bytes, resume_filename)
        ocr_used = False

        if force_ocr and len(raw_text.strip()) < 100:
            try:
                import tempfile
                import os
                ext = os.path.splitext(resume_filename)[-1].lower()
                with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                    tmp.write(resume_bytes)
                    tmp_path = tmp.name
                try:
                    import pytesseract
                    from PIL import Image
                    import fitz
                    doc = fitz.open(tmp_path)
                    ocr_texts = []
                    for page in doc:
                        pix = page.get_pixmap(dpi=300)
                        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
                        ocr_texts.append(pytesseract.image_to_string(img))
                    doc.close()
                    ocr_result = "\n".join(ocr_texts)
                    if len(ocr_result.strip()) > len(raw_text.strip()):
                        raw_text = ocr_result
                        ocr_used = True
                finally:
                    os.unlink(tmp_path)
            except Exception as ocr_err:
                trace.append(f"extraction: OCR fallback failed — {ocr_err}")

        from preprocessing.cleaner import clean_text
        clean_resume = clean_text(raw_text)

        from segmentation.section_splitter import split_sections
        resume_sections = split_sections(clean_resume)

        from extraction.skills_extractor import extract_skills
        from extraction.experience_extractor import extract_experience
        from extraction.role_extractor import extract_roles
        from extraction.education_extractor import extract_education
        from normalization.normalizer import normalize_skills

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

        experience_section = resume_sections.get("experience", "").strip()
        experience_years = extract_experience(
            experience_section if experience_section else clean_resume
        )

        roles = extract_roles(clean_resume)
        education = extract_education(
            resume_sections.get("education", "") or clean_resume
        )

        skills_conf = min(len(resume_skills) / 5.0, 1.0) if resume_skills else 0.0
        exp_conf = 1.0 if experience_years > 0 else 0.0
        edu_conf = 1.0 if education else 0.0
        text_conf = min(len(clean_resume) / 200.0, 1.0)
        overall_conf = round(
            0.35 * skills_conf + 0.25 * exp_conf + 0.20 * edu_conf + 0.20 * text_conf,
            3,
        )

        confidence_scores = {
            "skills": round(skills_conf, 3),
            "experience": round(exp_conf, 3),
            "education": round(edu_conf, 3),
            "text_density": round(text_conf, 3),
            "overall": overall_conf,
        }

        trace.append(
            f"extraction: attempt {attempts} — "
            f"skills={len(resume_skills)}, exp={experience_years}y, "
            f"edu={len(education)}, roles={len(roles)}, "
            f"confidence={overall_conf:.2f}, ocr={ocr_used}"
        )

        needs_retry_ocr = overall_conf < 0.5 and attempts < 2

        return {
            "resume_text": clean_resume,
            "resume_sections": resume_sections,
            "resume_skills": resume_skills,
            "experience_years": experience_years,
            "education": education,
            "roles": roles,
            "confidence_scores": confidence_scores,
            "ocr_used": ocr_used,
            "extraction_attempts": attempts,
            "force_ocr": needs_retry_ocr,
            "agent_trace": trace,
        }


    except Exception as exc:
        trace.append(f"extraction: ERROR on attempt {attempts} — {exc}")
        return {
            "resume_text": "",
            "resume_sections": {},
            "resume_skills": [],
            "experience_years": 0.0,
            "education": [],
            "roles": [],
            "confidence_scores": {
                "skills": 0.0,
                "experience": 0.0,
                "education": 0.0,
                "text_density": 0.0,
                "overall": 0.0,
            },
            "ocr_used": False,
            "extraction_attempts": attempts,
            "agent_trace": trace,
        }
