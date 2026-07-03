"""
scripts/validate_role_detection.py
───────────────────────────────────
Validation script: measures ESCO skill detection quality against
the annotated ground-truth in data/jd_pairs/jd_skills_annotated.jsonl.

Usage (run from project root ai_agent/):
    python scripts/validate_role_detection.py
    python scripts/validate_role_detection.py --samples 200

Outputs:
    - Per-category precision / recall / F1 printed to console
    - data/validation/esco_validation_results.json
"""

import argparse
import json
import sys
import logging
import time
from collections import defaultdict
from pathlib import Path

# ── Ensure project root in sys.path ──────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT  = SCRIPT_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
logger = logging.getLogger("validate_role_detection")


def _normalise(skill: str) -> str:
    """Lowercase + strip for fuzzy comparison."""
    return skill.lower().strip()


def _precision_recall_f1(tp: int, fp: int, fn: int) -> dict:
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall    = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1        = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )
    return {
        "precision": round(precision, 4),
        "recall":    round(recall, 4),
        "f1":        round(f1, 4),
        "tp":        tp,
        "fp":        fp,
        "fn":        fn,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate ESCO role detection against annotated JD dataset."
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=500,
        help="Number of samples to evaluate (default: 500)",
    )
    parser.add_argument(
        "--confidence",
        type=float,
        default=0.55,
        help="Minimum ESCO similarity score to use profile (default: 0.55)",
    )
    args = parser.parse_args()

    jd_file     = REPO_ROOT / "data" / "jd_pairs" / "jd_skills_annotated.jsonl"
    out_dir     = REPO_ROOT / "data" / "validation"
    out_file    = out_dir / "esco_validation_results.json"
    data_dir    = REPO_ROOT / "data" / "esco"
    cache_dir   = data_dir / "cache"

    if not jd_file.exists():
        print(f"ERROR: {jd_file} not found. Run scripts/download_hf_data.py first.")
        sys.exit(1)

    out_dir.mkdir(parents=True, exist_ok=True)

    # ── Load samples ──────────────────────────────────────────────────────────
    print(f"Loading up to {args.samples} samples from {jd_file.name} …")
    samples: list[dict] = []
    with open(jd_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                samples.append(json.loads(line))
            except json.JSONDecodeError:
                continue
            if len(samples) >= args.samples:
                break
    print(f"Loaded {len(samples)} samples.")

    # ── Load ESCO ─────────────────────────────────────────────────────────────
    from utils.esco_loader import ESCOLoader
    esco = ESCOLoader(str(data_dir))
    if not esco.is_loaded:
        print("ERROR: ESCO data not loaded. Check data/esco/ directory.")
        sys.exit(1)

    print("Loading sentence-transformers model …")
    from matching.semantic_matcher import get_model
    model = get_model()

    print("Building / loading ESCO index …")
    esco.build_index(model, str(cache_dir))

    # ── Evaluate ──────────────────────────────────────────────────────────────
    category_stats: dict[str, dict] = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0})
    global_tp = global_fp = global_fn = 0
    per_sample_results: list[dict] = []

    print(f"Evaluating {len(samples)} samples …")
    t0 = time.perf_counter()

    for idx, sample in enumerate(samples):
        job_title: str = str(sample.get("job_title", ""))
        category:  str = str(sample.get("category", "unknown")).upper()

        # Ground-truth skills (normalised set)
        raw_gt = sample.get("job_skill_set", [])
        if isinstance(raw_gt, str):
            try:
                raw_gt = json.loads(raw_gt)
            except Exception:
                raw_gt = [s.strip() for s in raw_gt.split(",")]
        gt_skills: set[str] = {_normalise(s) for s in raw_gt if s}

        if not job_title or not gt_skills:
            continue

        # ESCO prediction
        hits = esco.find_closest_occupation(job_title, model, top_k=1)
        predicted_skills: set[str] = set()

        if hits and hits[0]["similarity_score"] >= args.confidence:
            profile = esco.get_role_skill_profile(hits[0]["uri"])
            all_esco_skills = (
                profile["essential_skills"]
                + profile["optional_skills"]
                + profile["knowledge_areas"]
            )
            predicted_skills = {_normalise(s) for s in all_esco_skills}

        # TP / FP / FN (token-level substring match)
        tp = sum(
            1 for p in predicted_skills
            if any(p in g or g in p for g in gt_skills)
        )
        fp = len(predicted_skills) - tp
        fn = sum(
            1 for g in gt_skills
            if not any(g in p or p in g for p in predicted_skills)
        )

        category_stats[category]["tp"] += tp
        category_stats[category]["fp"] += fp
        category_stats[category]["fn"] += fn
        global_tp += tp
        global_fp += fp
        global_fn += fn

        per_sample_results.append({
            "idx":              idx,
            "job_title":        job_title,
            "category":         category,
            "esco_match":       hits[0]["title"] if hits else None,
            "esco_confidence":  hits[0]["similarity_score"] if hits else 0.0,
            "gt_skill_count":   len(gt_skills),
            "predicted_count":  len(predicted_skills),
            "tp": tp, "fp": fp, "fn": fn,
        })

        if (idx + 1) % 50 == 0:
            elapsed = time.perf_counter() - t0
            print(f"  Processed {idx + 1}/{len(samples)} samples … ({elapsed:.1f}s)")

    # ── Compute metrics ───────────────────────────────────────────────────────
    global_metrics = _precision_recall_f1(global_tp, global_fp, global_fn)
    cat_metrics: dict[str, dict] = {}
    for cat, counts in category_stats.items():
        cat_metrics[cat] = _precision_recall_f1(
            counts["tp"], counts["fp"], counts["fn"]
        )

    # ── Print results ─────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("ESCO Skill Detection Validation Results")
    print("=" * 60)
    print(f"Samples evaluated   : {len(per_sample_results)}")
    print(f"Confidence threshold: {args.confidence}")
    print()
    print(f"Global  — Precision: {global_metrics['precision']:.4f}  "
          f"Recall: {global_metrics['recall']:.4f}  "
          f"F1: {global_metrics['f1']:.4f}")
    print()
    print("Per-category breakdown:")
    print(f"  {'Category':<25} {'P':>7} {'R':>7} {'F1':>7}  {'Samples':>7}")
    print("  " + "-" * 55)
    for cat in sorted(cat_metrics):
        m = cat_metrics[cat]
        n = category_stats[cat]["tp"] + category_stats[cat]["fn"]
        print(
            f"  {cat:<25} {m['precision']:>7.4f} {m['recall']:>7.4f} "
            f"{m['f1']:>7.4f}  {n:>7}"
        )

    # ── Save JSON ─────────────────────────────────────────────────────────────
    output = {
        "config": {
            "samples":             len(per_sample_results),
            "confidence_threshold": args.confidence,
            "dataset":             str(jd_file),
        },
        "global_metrics":    global_metrics,
        "category_metrics":  cat_metrics,
        "per_sample":        per_sample_results[:200],  # cap to keep file small
    }
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to: {out_file}")
    print("Done.")


if __name__ == "__main__":
    main()
