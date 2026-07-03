"""Quick audit of the data directory layout."""
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent   # ai_agent/

def section(title):
    print(f"\n{'='*40}")
    print(f"  {title}")
    print('='*40)

# ESCO
section("data/esco/")
esco = BASE / "data" / "esco"
if esco.exists():
    for f in sorted(esco.iterdir()):
        print(f"  {f.name}  ({f.stat().st_size // 1024} KB)")
else:
    print("  [MISSING]")

# Resumes
section("data/resumes/")
resumes = BASE / "data" / "resumes"
if resumes.exists():
    for f in resumes.rglob("*"):
        rel = f.relative_to(resumes)
        size = f"  ({f.stat().st_size // 1024} KB)" if f.is_file() else "/"
        print(f"  {rel}{size}")
else:
    print("  [MISSING]")

# JD pairs
section("data/jd_pairs/")
jd = BASE / "data" / "jd_pairs"
if jd.exists():
    files = list(jd.iterdir())
    if files:
        for f in files:
            print(f"  {f.name}")
    else:
        print("  [EMPTY - run scripts/download_hf_data.py]")
else:
    print("  [MISSING]")

# New files
section("utils/  &  extraction/")
for p in [
    BASE / "utils" / "esco_loader.py",
    BASE / "extraction" / "skill_evidence_extractor.py",
    BASE / "scripts" / "download_hf_data.py",
]:
    status = "OK" if p.exists() else "MISSING"
    print(f"  [{status}]  {p.relative_to(BASE)}")
