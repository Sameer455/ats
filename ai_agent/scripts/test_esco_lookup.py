"""
scripts/test_esco_lookup.py
───────────────────────────
Interactive test script for ESCO semantic role matching.

Usage (run from project root ai_agent/):
    python scripts/test_esco_lookup.py --jd "Senior Python Developer..."
    python scripts/test_esco_lookup.py --jd "Data Engineer with Spark and Kafka experience"

Prints:
  - Top matched ESCO occupation(s)
  - Full skill profile (essential / optional / knowledge)
  - Implicit skills: ESCO essential skills not mentioned in the JD
"""

import argparse
import sys
import logging
from pathlib import Path

# ── Ensure project root in sys.path ──────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT  = SCRIPT_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

logging.basicConfig(
    level=logging.WARNING,  # suppress library noise
    format="%(levelname)s: %(message)s",
)


def _skill_in_jd(skill: str, jd_text: str) -> bool:
    """Case-insensitive substring check."""
    return skill.lower() in jd_text.lower()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Test ESCO occupation lookup against a JD snippet."
    )
    parser.add_argument(
        "--jd",
        required=True,
        help="Job description text (quoted string)",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="Number of closest ESCO occupations to return (default: 3)",
    )
    parser.add_argument(
        "--confidence-threshold",
        type=float,
        default=0.55,
        help="Minimum similarity score to show skill profile (default: 0.55)",
    )
    args = parser.parse_args()
    jd_text: str = args.jd

    print("\n" + "=" * 60)
    print("ESCO Semantic Role Lookup")
    print("=" * 60)
    print(f"JD snippet: {jd_text[:120]}{'…' if len(jd_text) > 120 else ''}\n")

    # ── Load ESCO ─────────────────────────────────────────────────────────────
    from utils.esco_loader import ESCOLoader
    data_dir  = REPO_ROOT / "data" / "esco"
    cache_dir = data_dir / "cache"

    esco = ESCOLoader(str(data_dir))
    if not esco.is_loaded:
        print("ERROR: ESCO data not found. Run scripts/build_esco_index.py first.")
        sys.exit(1)

    # ── Load model ────────────────────────────────────────────────────────────
    print("Loading model …")
    from matching.semantic_matcher import get_model
    model = get_model()

    # ── Build / load index ────────────────────────────────────────────────────
    esco.build_index(model, str(cache_dir))

    # ── Find closest occupations ──────────────────────────────────────────────
    hits = esco.find_closest_occupation(jd_text, model, top_k=args.top_k)
    if not hits:
        print("No ESCO occupation matches found.")
        sys.exit(0)

    print(f"Top {args.top_k} ESCO Occupation Match(es):")
    print("-" * 60)
    for rank, h in enumerate(hits, 1):
        confidence_tag = (
            " [HIGH CONFIDENCE]" if h["similarity_score"] >= 0.70
            else " [MODERATE]" if h["similarity_score"] >= args.confidence_threshold
            else " [LOW]"
        )
        print(f"  #{rank}  {h['title']}")
        print(f"       Score : {h['similarity_score']:.4f}{confidence_tag}")
        print(f"       URI   : {h['uri']}")
        print()

    # ── Full skill profile for best match ────────────────────────────────────
    best = hits[0]
    if best["similarity_score"] < args.confidence_threshold:
        print(
            f"Best match confidence ({best['similarity_score']:.4f}) is below "
            f"threshold ({args.confidence_threshold}) — skipping skill profile."
        )
        sys.exit(0)

    print("=" * 60)
    print(f"Skill Profile for: {best['title']}")
    print("=" * 60)
    profile = esco.get_role_skill_profile(best["uri"])

    # Essential skills
    print(f"\nEssential Skills ({len(profile['essential_skills'])}):")
    for s in profile["essential_skills"][:20]:
        tag = "" if _skill_in_jd(s, jd_text) else "  [IMPLICIT - not in JD]"
        print(f"  - {s}{tag}")

    # Optional skills
    print(f"\nOptional Skills ({len(profile['optional_skills'])}):")
    for s in profile["optional_skills"][:15]:
        print(f"  - {s}")

    # Knowledge areas
    if profile["knowledge_areas"]:
        print(f"\nKnowledge Areas ({len(profile['knowledge_areas'])}):")
        for s in profile["knowledge_areas"][:10]:
            print(f"  - {s}")

    # Implicit skills summary
    implicit = [
        s for s in profile["essential_skills"]
        if not _skill_in_jd(s, jd_text)
    ]
    print("\n" + "=" * 60)
    print(f"Implicit Requirements ({len(implicit)} essential ESCO skills not stated in JD):")
    for s in implicit[:15]:
        defn = esco.get_skill_definition(s)
        defn_snippet = f" — {defn[:80]}…" if defn else ""
        print(f"  * {s}{defn_snippet}")

    # Related skills for top 3 explicit skills
    print("\n" + "=" * 60)
    explicit_in_jd = [
        s for s in profile["essential_skills"] if _skill_in_jd(s, jd_text)
    ][:3]
    if explicit_in_jd:
        print("Related skills for top JD skills (ESCO co-occurrence):")
        for s in explicit_in_jd:
            related = esco.get_related_skills(s, n=5)
            if related:
                print(f"  {s}: {', '.join(related)}")

    print("\nTotal ESCO skills for this role:", profile["total_skills"])
    print("Done.\n")


if __name__ == "__main__":
    main()
