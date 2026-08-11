from __future__ import annotations

import hashlib
import os
from typing import Any

from agent.state import ATSAgentState


def intake_agent(state: ATSAgentState) -> dict[str, Any]:
    trace: list[str] = list(state.get("agent_trace", []))

    resume_bytes: bytes | None = state.get("resume_bytes")
    resume_filename: str = state.get("resume_filename", "")
    jd_text: str = state.get("jd_text", "")

    if not resume_bytes or len(resume_bytes) == 0:
        trace.append("intake: FAIL — resume bytes empty or missing")
        return {
            "input_valid": False,
            "input_error": "Resume file is empty or missing.",
            "agent_trace": trace,
        }

    if not jd_text or len(jd_text.strip()) < 50:
        trace.append("intake: FAIL — JD text too short (< 50 chars)")
        return {
            "input_valid": False,
            "input_error": "Job description must be at least 50 characters.",
            "agent_trace": trace,
        }

    ext = os.path.splitext(resume_filename)[-1].lower() if resume_filename else ""
    file_type = "unknown"

    if ext == ".pdf":
        try:
            sample = resume_bytes[:4096].decode("latin-1", errors="replace")
            printable_count = sum(1 for ch in sample if ch.isalnum())
            if printable_count < 100:
                file_type = "scanned_pdf"
            else:
                file_type = "pdf"
        except Exception:
            file_type = "pdf"
    elif ext == ".docx":
        file_type = "docx"
    elif ext in (".doc",):
        file_type = "doc"
    else:
        file_type = ext.lstrip(".") if ext else "unknown"

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
