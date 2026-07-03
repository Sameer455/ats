# -*- coding: utf-8 -*-
"""
scripts/download_hf_data.py
Run once from the repo root (ai_agent/) or from anywhere — paths are resolved
relative to this script's location so the output always lands in:
    <repo>/data/jd_pairs/

Datasets downloaded:
  1. jacob-hugging-face/job-descriptions  → job_descriptions.jsonl
     853 records | fields: position_title, company_name, job_description,
                            model_response (extracted skills/responsibilities)

  2. batuhanmtl/job-skill-set            → jd_skills_annotated.jsonl
     1,167 records | fields: job_id, category, job_title, job_description,
                             job_skill_set (hard + soft skills list)
     Source: LinkedIn job postings + RecAI skill-extraction API
     Replaces: DGurgurov/job_descriptions_skills (no longer on HF Hub)
"""
import os
from pathlib import Path

# Suppress symlink warning on Windows (cosmetic only)
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

# ── Resolve output directory relative to this script ─────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent          # .../ai_agent/scripts
REPO_ROOT   = SCRIPT_DIR.parent                       # .../ai_agent
OUTPUT_DIR  = REPO_ROOT / "data" / "jd_pairs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print(f"[download_hf_data] Output directory: {OUTPUT_DIR}")

from datasets import load_dataset  # noqa: E402

# ── Dataset 1: Job descriptions with skills ───────────────────────────────────
print("\n[1/2] Downloading jacob-hugging-face/job-descriptions …")
ds1 = load_dataset("jacob-hugging-face/job-descriptions")
out1 = OUTPUT_DIR / "job_descriptions.jsonl"
ds1["train"].to_json(str(out1))
print(f"  [OK] Saved {len(ds1['train'])} records -> {out1}")
print(f"  Fields: {list(ds1['train'].features.keys())}")

# ── Dataset 2: JD + skill annotations (LinkedIn postings) ────────────────────
# Replaces the defunct DGurgurov/job_descriptions_skills dataset.
# batuhanmtl/job-skill-set contains job_title, job_description, and
# job_skill_set (extracted hard + soft skills list) — 1,167 entries.
print("\n[2/2] Downloading batuhanmtl/job-skill-set …")
ds2 = load_dataset("batuhanmtl/job-skill-set")
out2 = OUTPUT_DIR / "jd_skills_annotated.jsonl"
# Dataset may use 'train' or 'default' split
split = "train" if "train" in ds2 else list(ds2.keys())[0]
ds2[split].to_json(str(out2))
print(f"  [OK] Saved {len(ds2[split])} records -> {out2}")
print(f"  Fields: {list(ds2[split].features.keys())}")

print(
    f"\n[download_hf_data] DONE."
    f" Total: {len(ds1['train']) + len(ds2[split])} records across 2 datasets."
)