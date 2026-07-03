"""
scripts/build_esco_index.py
───────────────────────────
One-time script to encode all ESCO occupation labels and cache them to disk.

Usage (run from project root ai_agent/):
    python scripts/build_esco_index.py

Outputs written to:  data/esco/cache/
  - occupation_embeddings.npy   float32 matrix (N, 768)
  - occupation_index.json       {uris: [...], titles: [...]}
  - skills_index.json           {skill_uri: {label, description, skill_type}}

On subsequent runs the cache is loaded instantly instead of re-encoding.
"""

import sys
import time
import logging
from pathlib import Path

# ── Ensure project root is in sys.path so imports work ───────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT  = SCRIPT_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("build_esco_index")


def main() -> None:
    """Load ESCO data, build (or load) the embedding cache, and print stats."""
    data_dir  = REPO_ROOT / "data" / "esco"
    cache_dir = data_dir / "cache"

    logger.info("=== ESCO Index Builder ===")
    logger.info("Data directory : %s", data_dir)
    logger.info("Cache directory: %s", cache_dir)

    # ── 1. Load ESCO CSVs ─────────────────────────────────────────────────────
    from utils.esco_loader import ESCOLoader

    t0 = time.perf_counter()
    esco = ESCOLoader(str(data_dir))

    if not esco.is_loaded:
        logger.error(
            "ESCO data files not found in %s.\n"
            "Download them from https://esco.ec.europa.eu/en/use-esco/download\n"
            "and place occupations_en.csv, skills_en.csv, and\n"
            "occupationSkillRelations_en.csv in %s",
            data_dir, data_dir,
        )
        sys.exit(1)

    logger.info(
        "CSVs loaded in %.2f s — %d occupations, %d skills, %d relations",
        time.perf_counter() - t0,
        len(esco.occupations),
        len(esco.skills),
        len(esco.relations),
    )

    # ── 2. Load sentence-transformers model ───────────────────────────────────
    logger.info("Loading sentence-transformers model (all-mpnet-base-v2) …")
    t1 = time.perf_counter()
    from matching.semantic_matcher import get_model
    model = get_model()
    logger.info("Model loaded in %.2f s", time.perf_counter() - t1)

    # ── 3. Build / load index ─────────────────────────────────────────────────
    logger.info("Building ESCO index (cached to %s) …", cache_dir)
    t2 = time.perf_counter()
    esco.build_index(model, str(cache_dir))
    elapsed = time.perf_counter() - t2
    logger.info("Index ready in %.2f s", elapsed)

    # ── 4. Quick sanity check ─────────────────────────────────────────────────
    test_queries = [
        "Senior Python Developer with machine learning experience",
        "DevOps engineer Kubernetes CI/CD",
        "Data scientist NLP deep learning",
    ]
    logger.info("\n=== Sanity Check ===")
    for q in test_queries:
        hits = esco.find_closest_occupation(q, model, top_k=2)
        logger.info("Query: %r", q)
        for h in hits:
            logger.info(
                "  -> %-50s  (score=%.4f)",
                h["title"][:50], h["similarity_score"],
            )

    # ── 5. Final stats ────────────────────────────────────────────────────────
    logger.info("\n=== Index Stats ===")
    logger.info("Occupation embeddings: %d", len(esco._occ_uris))
    logger.info("Skills indexed       : %d", len(esco._skills_index))
    logger.info("Co-occurrence pairs  : %d", sum(len(v) for v in esco._cooccurrence.values()))
    logger.info("Cache files saved to : %s", cache_dir)
    logger.info("Done.")


if __name__ == "__main__":
    main()
