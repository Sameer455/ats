"""
tests/test_hybrid_matcher.py — Calibration and regression test suite.

Run from your project root:
    python tests/test_hybrid_matcher.py

Three test categories:
  1. True positives  — hybrid MUST catch these (fuzzy-only misses them)
  2. False positives — hybrid must NOT fire on these
  3. Exact matches   — basic matches must still work after hybrid changes
  4. Edge cases      — empty lists, single skills
  5. Method summary  — verify method counts are being tracked

If tests fail, use the tuning guide at the bottom to adjust thresholds in .env.
"""

import sys
import os

# Allow running directly from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from matching.hybrid_skill_matcher import compute_hybrid_skill_gap

PASS   = "\033[92mPASS\033[0m"
FAIL   = "\033[91mFAIL\033[0m"
errors = 0


def check(name, resume_skills, jd_skills, should_match=None, should_miss=None):
    """
    Run a test case and report pass/fail per expected skill.

    Args:
        name:          Test name for output
        resume_skills: Input resume skill list
        jd_skills:     Input JD skill list
        should_match:  JD skills that MUST appear in matched_skills
        should_miss:   JD skills that MUST appear in missing_skills
    """
    global errors
    result  = compute_hybrid_skill_gap(resume_skills, jd_skills)
    matched = set(result["matched_skills"])
    missing = set(result["missing_skills"])

    for skill in (should_match or []):
        ok = skill.lower() in matched
        print(f"  [{PASS if ok else FAIL}] {name}")
        print(f"         '{skill}' should be MATCHED — {'found ✓' if ok else 'not found ✗'}")
        if ok:
            # Print confidence for matched skill
            detail = next((d for d in result["match_details"] if d["jd_skill"] == skill.lower()), None)
            if detail:
                print(f"         matched_to='{detail['matched_to']}'  conf={detail['confidence']}%  method={detail['method']}")
        if not ok:
            errors += 1

    for skill in (should_miss or []):
        ok = skill.lower() in missing
        print(f"  [{PASS if ok else FAIL}] {name}")
        print(f"         '{skill}' should be MISSED — {'correctly missing ✓' if ok else 'incorrectly matched ✗'}")
        if not ok:
            # Show what it matched to
            detail = next((d for d in result["match_details"] if d["jd_skill"] == skill.lower()), None)
            if detail:
                print(f"         wrongly matched_to='{detail['matched_to']}'  conf={detail['confidence']}%  method={detail['method']}")
            errors += 1

    return result


# ══════════════════════════════════════════════════════════════
# 1. TRUE POSITIVES — semantic equivalents fuzzy-only misses
# ══════════════════════════════════════════════════════════════
print("\n=== 1. True Positives — semantic equivalents ===\n")

check(
    "ml modeling ↔ machine learning",
    resume_skills=["ml modeling", "python", "sql"],
    jd_skills=["machine learning", "python"],
    should_match=["machine learning"],
)

check(
    "data viz ↔ data visualization",
    resume_skills=["data viz", "tableau", "excel"],
    jd_skills=["data visualization", "tableau"],
    should_match=["data visualization"],
)

check(
    "web services ↔ rest api",
    resume_skills=["web services", "java", "spring boot"],
    jd_skills=["rest api", "java"],
    should_match=["rest api"],
)

check(
    "natural language processing ↔ nlp",
    resume_skills=["natural language processing", "python"],
    jd_skills=["nlp", "python"],
    should_match=["nlp"],
)

check(
    "k8s ↔ kubernetes",
    resume_skills=["k8s", "docker", "python"],
    jd_skills=["kubernetes", "docker"],
    should_match=["kubernetes"],
)

check(
    "deep learning ↔ neural networks",
    resume_skills=["deep learning", "tensorflow"],
    jd_skills=["neural networks", "tensorflow"],
    should_match=["neural networks"],
)

check(
    "ci/cd ↔ continuous integration",
    resume_skills=["ci/cd", "github actions", "python"],
    jd_skills=["continuous integration", "github actions"],
    should_match=["continuous integration"],
)

check(
    "object oriented programming ↔ oop",
    resume_skills=["object oriented programming", "java"],
    jd_skills=["oop", "java"],
    should_match=["oop"],
)


# ══════════════════════════════════════════════════════════════
# 2. FALSE POSITIVES — must NOT match these
# ══════════════════════════════════════════════════════════════
print("\n=== 2. False Positives — must NOT match ===\n")

check(
    "python ↔ java (different languages)",
    resume_skills=["python"],
    jd_skills=["java"],
    should_miss=["java"],
)

check(
    "docker ↔ kubernetes (related but distinct tools)",
    resume_skills=["docker"],
    jd_skills=["kubernetes"],
    should_miss=["kubernetes"],
)

check(
    "sql ↔ nosql (opposite paradigms)",
    resume_skills=["sql"],
    jd_skills=["nosql"],
    should_miss=["nosql"],
)

check(
    "react ↔ angular (different frameworks)",
    resume_skills=["react"],
    jd_skills=["angular"],
    should_miss=["angular"],
)

check(
    "analysis ↔ machine learning (generic word, floor guard)",
    resume_skills=["analysis"],
    jd_skills=["machine learning"],
    should_miss=["machine learning"],
)

check(
    "aws ↔ azure (different cloud providers)",
    resume_skills=["aws"],
    jd_skills=["azure"],
    should_miss=["azure"],
)

check(
    "flask ↔ django (related but different frameworks)",
    resume_skills=["flask"],
    jd_skills=["django"],
    should_miss=["django"],
)


# ══════════════════════════════════════════════════════════════
# 3. EXACT MATCHES — must still work
# ══════════════════════════════════════════════════════════════
print("\n=== 3. Exact Matches — basic matching intact ===\n")

check(
    "python ↔ python (exact)",
    resume_skills=["python", "fastapi", "postgresql"],
    jd_skills=["python", "fastapi"],
    should_match=["python", "fastapi"],
)

check(
    "all skills present",
    resume_skills=["docker", "kubernetes", "aws", "terraform"],
    jd_skills=["docker", "kubernetes", "aws"],
    should_match=["docker", "kubernetes", "aws"],
)


# ══════════════════════════════════════════════════════════════
# 4. EDGE CASES
# ══════════════════════════════════════════════════════════════
print("\n=== 4. Edge Cases ===\n")

result_empty = compute_hybrid_skill_gap([], [])
ok = result_empty["skill_coverage_pct"] == 0.0
print(f"  [{PASS if ok else FAIL}] Both empty → 0% coverage")
if not ok: errors += 1

result_no_jd = compute_hybrid_skill_gap(["python", "java"], [])
ok = set(result_no_jd["extra_skills"]) == {"python", "java"}
print(f"  [{PASS if ok else FAIL}] Empty JD → all resume skills go to extra_skills")
if not ok: errors += 1

result_no_resume = compute_hybrid_skill_gap([], ["python", "fastapi"])
ok = set(result_no_resume["missing_skills"]) == {"python", "fastapi"}
print(f"  [{PASS if ok else FAIL}] Empty resume → all JD skills go to missing_skills")
if not ok: errors += 1

result_perfect = compute_hybrid_skill_gap(["python", "fastapi"], ["python", "fastapi"])
ok = result_perfect["skill_coverage_pct"] == 100.0
print(f"  [{PASS if ok else FAIL}] Identical lists → 100% coverage")
if not ok: errors += 1


# ══════════════════════════════════════════════════════════════
# 5. METHOD SUMMARY + MATCH DETAILS
# ══════════════════════════════════════════════════════════════
print("\n=== 5. Method Summary Verification ===\n")

result_mixed = compute_hybrid_skill_gap(
    resume_skills=["python", "ml modeling", "data viz", "react", "docker"],
    jd_skills=["python", "machine learning", "data visualization", "angular", "kubernetes"],
)

summary = result_mixed["match_method_summary"]
print(f"  Match method summary: {summary}")

ok_fastpath = summary["fuzzy_fastpath_count"] >= 1
print(f"  [{PASS if ok_fastpath else FAIL}] At least 1 fuzzy_fastpath (python↔python)")
if not ok_fastpath: errors += 1

ok_hybrid = (summary["hybrid_count"] + summary["embedding_primary_count"]) >= 1
print(f"  [{PASS if ok_hybrid else FAIL}] At least 1 hybrid/embedding_primary (semantic equivalents)")
if not ok_hybrid: errors += 1

print("\n  Full match details:")
print(f"  {'JD Skill':30s} {'Matched To':30s} {'Conf':8s} {'Method'}")
print(f"  {'-'*30} {'-'*30} {'-'*8} {'-'*20}")
for d in result_mixed["match_details"]:
    status = "✓" if d["matched_to"] else "✗"
    print(
        f"  {status} {d['jd_skill']:28s} "
        f"{str(d['matched_to'] or '—'):28s} "
        f"{d['confidence']:6.1f}%  "
        f"{d['method']}"
    )


# ══════════════════════════════════════════════════════════════
# FINAL SUMMARY
# ══════════════════════════════════════════════════════════════
print(f"\n{'=' * 60}")
if errors == 0:
    print("✅  All tests passed — thresholds are well-calibrated.\n")
else:
    print(f"❌  {errors} test(s) failed.\n")
    print("Tuning guide:")
    print("  Too many false positives  → raise SKILL_MATCH_THRESHOLD (try 0.75–0.80)")
    print("                            → raise SKILL_FUZZY_FLOOR (try 0.35)")
    print("  Missing semantic matches  → lower SKILL_MATCH_THRESHOLD (try 0.68)")
    print("                            → lower SKILL_FUZZY_FLOOR (try 0.25)")
    print("  Fast-path fires too much  → lower SKILL_FUZZY_FASTPATH (try 0.85)")
    print("  Embeddings underweighted  → lower SKILL_FUZZY_WEIGHT (try 0.3)")
    print()
    print("  Set these in your .env file and re-run this test.")
    print()

sys.exit(0 if errors == 0 else 1)