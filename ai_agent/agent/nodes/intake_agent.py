"""
agent/nodes/intake_agent.py — Node 1: Input validation, file-type detection, hashing.

Validates that the resume bytes and JD text are present and well-formed.
Detects file type (PDF, DOCX, scanned PDF) and computes a SHA-256 document
hash for downstream caching.  If validation fails, sets ``input_valid=False``
so the router can short-circuit to END.
"""

from __future__ import annotations

import hashlib
import os
from typing import Any

from agent.state import ATSAgentState


def intake_agent(state: ATSAgentState) -> dict[str, Any]:
    """
    Intake Agent — validates inputs and prepares metadata.

    Writes:
        file_type, input_valid, input_error, document_hash, agent_trace
    """
    trace: list[str] = list(state.get("agent_trace", []))

    resume_bytes: bytes | None = state.get("resume_bytes")
    resume_filename: str = state.get("resume_filename", "")
    jd_text: str = state.get("jd_text", "")

    # ── Validate resume bytes ─────────────────────────────────────────────────
    if not resume_bytes or len(resume_bytes) == 0:
        trace.append("intake: FAIL — resume bytes empty or missing")
        return {
            "input_valid": False,
            "input_error": "Resume file is empty or missing.",
            "agent_trace": trace,
        }

    # ── Validate JD text ──────────────────────────────────────────────────────
    if not jd_text or len(jd_text.strip()) < 50:
        trace.append("intake: FAIL — JD text too short (< 50 chars)")
        return {
            "input_valid": False,
            "input_error": "Job description must be at least 50 characters.",
            "agent_trace": trace,
        }

    # ── Detect file type ──────────────────────────────────────────────────────
    ext = os.path.splitext(resume_filename)[-1].lower() if resume_filename else ""
    file_type = "unknown"

    if ext == ".pdf":
        # Heuristic: extract enough text to check density.
        # We do a cheap check — if the first 4 bytes are the PDF magic %PDF
        # and we can't decode meaningful ASCII from the raw bytes, it's scanned.
        try:
            # Quick text density check: decode a sample of the raw bytes.
            sample = resume_bytes[:4096].decode("latin-1", errors="replace")
            # Count printable alphanumeric characters in the sample
            printable_count = sum(1 for ch in sample if ch.isalnum())
            if printable_count < 100:
                file_type = "scanned_pdf"
            else:
                file_type = "pdf"
        except Exception:
            file_type = "pdf"  # assume regular PDF on failure
    elif ext == ".docx":
        file_type = "docx"
    elif ext in (".doc",):
        file_type = "doc"
    else:
        # Allow processing but flag the type
        file_type = ext.lstrip(".") if ext else "unknown"

    # ── Compute SHA-256 hash ──────────────────────────────────────────────────
    document_hash = hashlib.sha256(resume_bytes).hexdigest()

    trace.append(
        f"intake: OK — file_type={file_type}, "
        f"size={len(resume_bytes)} bytes, hash={document_hash[:12]}…"
    )

    return {
        "file_type": file_type,
        "input_valid": True,
        "input_error": None,
        "document_hash": document_hash,
        "agent_trace": trace,
    }
