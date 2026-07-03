"""
extraction/skill_evidence_extractor.py
───────────────────────────────────────
Evidence-based skill depth scorer for resume analysis.

For each target skill, the extractor:
  1. Searches all resume sections to locate the skill.
  2. Extracts surrounding sentences (±2) as evidence.
  3. Detects scale signals, seniority signals, year references, and recency.
  4. Assigns a depth_score (0.0–1.0) using the rules below.

Depth score rules (exact):
  0.1  skill mentioned in skills section only, no experience context
  0.3  skill mentioned in experience but no supporting detail
  0.6  skill mentioned with role context (job title + skill in same section)
  0.8  skill mentioned with scale or impact signal
  1.0  skill mentioned with scale + seniority signal + recency within 3 years

The SkillEvidence dataclass is JSON-serialisable via .to_dict().
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional
import logging
import datetime

logger = logging.getLogger(__name__)

# ── Current year for recency computation ──────────────────────────────────────
_CURRENT_YEAR = datetime.datetime.now().year

# ── Regex: scale signals ─────────────────────────────────────────────────────
_SCALE_RE = re.compile(
    r"""
    (?:
        \d[\d,\.]*\s*[KMBkmb]\+?       |  # 10K, 500M, 2B
        \d+\s*%                         |  # 40%
        \d[\d,\.]*\s*(?:million|billion)|  # 5 million
        \b(?:production|enterprise|large[-\s]?scale|millions?|billions?)\b
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)

# ── Regex: year mentions ──────────────────────────────────────────────────────
_YEAR_RE = re.compile(r"\b(20\d{2}|19\d{2})\b")

# ── Regex: years-of-experience mentions ──────────────────────────────────────
_EXP_YEARS_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)",
    re.IGNORECASE,
)

# ── Seniority / ownership signals ────────────────────────────────────────────
_SENIORITY_SIGNALS = {
    "led", "lead", "built", "architected", "designed", "owned", "managed",
    "established", "spearheaded", "founded", "launched", "created", "pioneered",
    "directed", "oversaw", "devised", "defined", "championed", "drove",
}

# ── Context / role signals ────────────────────────────────────────────────────
_ROLE_CONTEXT_SIGNALS = {
    "engineer", "developer", "architect", "analyst", "scientist", "manager",
    "lead", "head", "director", "senior", "junior", "principal", "staff",
    "intern", "consultant", "specialist",
}

# ── Sentence splitter ─────────────────────────────────────────────────────────
_SENT_END = re.compile(r"(?<=[.!?])\s+")


def _split_sentences(text: str) -> list[str]:
    """Split *text* into sentences, also splitting on bullet points."""
    cleaned = re.sub(r"[\r\n]+", " ", text)
    sents = _SENT_END.split(cleaned)
    result: list[str] = []
    for s in sents:
        parts = [p.strip() for p in re.split(r"[•\-–—|]", s) if p.strip()]
        result.extend(parts)
    return [s for s in result if len(s) > 5]


def _window(sentences: list[str], idx: int, half: int = 2) -> str:
    """Return a window of *2×half+1* sentences centred on *idx*."""
    start = max(0, idx - half)
    end   = min(len(sentences), idx + half + 1)
    return " ".join(sentences[start:end]).strip()


# ── SkillEvidence dataclass ───────────────────────────────────────────────────

@dataclass
class SkillEvidence:
    """
    Evidence record for a single skill mention in a resume.

    All float fields are in [0.0, 1.0] except years_used which is raw years.
    """

    skill:               str
    found:               bool
    depth_score:         float           # 0.0–1.0 per rules above
    years_used:          float           # years associated with this skill
    contexts:            list[str]       # job titles / domains where used
    scale_signals:       list[str]       # numbers/percentages found nearby
    seniority_signals:   list[str]       # "led", "architected", etc.
    recency_year:        int             # most recent year this skill appeared (0=unknown)
    evidence_sentences:  list[str]       # raw sentences containing the skill

    def to_dict(self) -> dict:
        """Return a JSON-serialisable dict."""
        return {
            "skill":              self.skill,
            "found":              self.found,
            "depth_score":        round(self.depth_score, 4),
            "years_used":         self.years_used,
            "contexts":           self.contexts,
            "scale_signals":      self.scale_signals,
            "seniority_signals":  self.seniority_signals,
            "recency_year":       self.recency_year,
            "evidence_sentences": self.evidence_sentences[:3],  # cap for JSON size
        }

    @classmethod
    def not_found(cls, skill: str) -> "SkillEvidence":
        """Factory: create a SkillEvidence for a skill not present in the resume."""
        return cls(
            skill=skill,
            found=False,
            depth_score=0.0,
            years_used=0.0,
            contexts=[],
            scale_signals=[],
            seniority_signals=[],
            recency_year=0,
            evidence_sentences=[],
        )


# ── SkillEvidenceExtractor ────────────────────────────────────────────────────

class SkillEvidenceExtractor:
    """
    Extracts evidence for a list of target skills from a resume.

    Parameters
    ----------
    context_window : int
        Number of sentences to include on each side of a skill mention.
    """

    def __init__(self, context_window: int = 2) -> None:
        self._window = context_window

    # ------------------------------------------------------------------

    def extract_evidence(
        self,
        resume_text: str,
        resume_sections: dict[str, str],
        target_skills: list[str],
    ) -> dict[str, SkillEvidence]:
        """
        Extract and score evidence for every skill in *target_skills*.

        Parameters
        ----------
        resume_text     : full resume text (concatenated)
        resume_sections : dict of section_name → section_text
        target_skills   : list of skill labels to look for

        Returns
        -------
        dict mapping skill → SkillEvidence
        (skills not found get SkillEvidence.not_found())
        """
        results: dict[str, SkillEvidence] = {}

        for skill in target_skills:
            ev = self._extract_one(skill, resume_text, resume_sections)
            results[skill] = ev

        return results

    # ------------------------------------------------------------------
    # Internal per-skill extraction
    # ------------------------------------------------------------------

    def _extract_one(
        self,
        skill: str,
        resume_text: str,
        resume_sections: dict[str, str],
    ) -> SkillEvidence:
        """Run the full evidence pipeline for a single *skill*."""
        skill_lower = skill.lower()
        pattern     = re.compile(
            r"(?<!\w)" + re.escape(skill_lower) + r"(?!\w)",
            re.IGNORECASE,
        )

        # ── Locate skill in each section ─────────────────────────────
        sections_found: list[str] = []
        all_evidence_sentences: list[str] = []

        for section_name, text in (resume_sections or {}).items():
            if not text or not pattern.search(text.lower()):
                continue
            sections_found.append(section_name)
            sents = _split_sentences(text)
            for i, s in enumerate(sents):
                if pattern.search(s.lower()):
                    all_evidence_sentences.append(_window(sents, i, self._window))

        # Fallback: check full text
        if not sections_found and resume_text and pattern.search(resume_text.lower()):
            sections_found.append("__unclassified__")
            sents = _split_sentences(resume_text)
            for i, s in enumerate(sents):
                if pattern.search(s.lower()):
                    all_evidence_sentences.append(_window(sents, i, self._window))

        if not sections_found:
            return SkillEvidence.not_found(skill)

        # ── Aggregate evidence from all windows ───────────────────────
        combined_evidence = " ".join(all_evidence_sentences)
        ev_lower          = combined_evidence.lower()
        ev_tokens         = set(re.findall(r"\b\w+\b", ev_lower))

        # Scale signals
        scale_signals = list(dict.fromkeys(
            m.group(0) for m in _SCALE_RE.finditer(combined_evidence)
        ))

        # Seniority signals
        seniority_signals = list(dict.fromkeys(
            t for t in ev_tokens if t in _SENIORITY_SIGNALS
        ))

        # Years of experience nearby
        years_used = 0.0
        for m in _EXP_YEARS_RE.finditer(combined_evidence):
            try:
                years_used = max(years_used, float(m.group(1)))
            except ValueError:
                pass

        # Recency: most recent calendar year found
        recency_year = 0
        for m in _YEAR_RE.finditer(combined_evidence):
            y = int(m.group(1))
            if y <= _CURRENT_YEAR:
                recency_year = max(recency_year, y)

        # Role context signals
        contexts = list(dict.fromkeys(
            t for t in ev_tokens if t in _ROLE_CONTEXT_SIGNALS
        ))

        # ── Depth score ───────────────────────────────────────────────
        depth_score = self._compute_depth_score(
            sections_found  = sections_found,
            scale_signals   = scale_signals,
            seniority_signals = seniority_signals,
            contexts        = contexts,
            recency_year    = recency_year,
        )

        return SkillEvidence(
            skill               = skill,
            found               = True,
            depth_score         = depth_score,
            years_used          = years_used,
            contexts            = contexts,
            scale_signals       = scale_signals,
            seniority_signals   = seniority_signals,
            recency_year        = recency_year,
            evidence_sentences  = list(dict.fromkeys(all_evidence_sentences)),
        )

    # ------------------------------------------------------------------
    # Depth score rules (exact specification)
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_depth_score(
        sections_found:    list[str],
        scale_signals:     list[str],
        seniority_signals: list[str],
        contexts:          list[str],
        recency_year:      int,
    ) -> float:
        """
        Assign depth_score per the specification:

        0.1  → skills section only, no experience context
        0.3  → appears in experience, but no supporting detail
        0.6  → experience + role context (job title / domain token present)
        0.8  → experience + scale or impact signal
        1.0  → experience + scale + seniority signal + recency within 3 years
        """
        in_experience = any(
            s in ("experience", "work experience", "professional experience", "__unclassified__")
            for s in sections_found
        )
        in_skills_only = (
            not in_experience
            and all(s in ("skills", "technical skills", "competencies") for s in sections_found)
        )

        has_scale    = len(scale_signals) > 0
        has_seniority = len(seniority_signals) > 0
        has_context  = len(contexts) > 0
        is_recent    = recency_year > 0 and (_CURRENT_YEAR - recency_year) <= 3

        if in_skills_only:
            return 0.1

        if not in_experience:
            # found in projects/certifications etc. — treat like mid-evidence
            return 0.3 if not has_context else 0.6

        # In experience section:
        if has_scale and has_seniority and is_recent:
            return 1.0
        if has_scale:
            return 0.8
        if has_context:
            return 0.6
        return 0.3


# ── Module-level shortcut ─────────────────────────────────────────────────────

def extract_skill_evidence(
    resume_text: str,
    resume_sections: dict[str, str],
    target_skills: list[str],
    context_window: int = 2,
) -> dict[str, SkillEvidence]:
    """
    Convenience wrapper.

    Example
    -------
    >>> from extraction.skill_evidence_extractor import extract_skill_evidence
    >>> ev = extract_skill_evidence(resume_text, sections, ["python", "spark"])
    >>> print(ev["python"].depth_score)
    """
    return SkillEvidenceExtractor(context_window).extract_evidence(
        resume_text, resume_sections, target_skills
    )
