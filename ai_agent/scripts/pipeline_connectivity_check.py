"""
scripts/pipeline_connectivity_check.py
────────────────────────────────────────
Verifies that the full upgraded LangGraph pipeline is correctly wired:

  intake → extraction → jd_analysis (+ ESCO) → scoring (+ evidence)
       → reasoning (+ ESCO context) → deep_analysis → report

Runs a SYNTHETIC resume + JD through every node without needing a
real PDF or a running LLM.  LLM calls are disabled (enable_llm=False)
so this runs offline in seconds.

Usage:
    venv\\Scripts\\python scripts\\pipeline_connectivity_check.py
"""

import sys
import time
import traceback
from pathlib import Path

# ── path setup ────────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

# ── colours for the console ───────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

def ok(msg):   print(f"  {GREEN}PASS{RESET}  {msg}")
def fail(msg): print(f"  {RED}FAIL{RESET}  {msg}")
def warn(msg): print(f"  {YELLOW}WARN{RESET}  {msg}")
def info(msg): print(f"  {CYAN}INFO{RESET}  {msg}")

# ── synthetic test data ───────────────────────────────────────────────────────
SYNTHETIC_RESUME_TEXT = """
John Doe
john.doe@email.com | linkedin.com/in/johndoe | GitHub: johndoe

SUMMARY
Senior Python Developer with 6 years of experience building scalable REST APIs
and microservices. Proven track record leading teams of 5+ engineers.

SKILLS
Python, FastAPI, Django, PostgreSQL, Redis, Docker, Kubernetes, AWS,
Machine Learning, Pandas, NumPy, Git, CI/CD, Terraform

EXPERIENCE
Senior Software Engineer – TechCorp Inc (2021–2024)
  - Led development of a FastAPI microservices platform serving 2M users
  - Architected PostgreSQL database schema handling 500K daily transactions
  - Built Docker/Kubernetes deployment pipeline reducing deploy time by 60%
  - Managed a team of 5 backend engineers across 3 time zones

Software Engineer – StartupXYZ (2018–2021)
  - Developed REST APIs using Python and Django for e-commerce platform
  - Designed Redis caching layer improving response time by 40%
  - Owned CI/CD pipeline using GitHub Actions and Terraform on AWS

EDUCATION
B.Sc. Computer Science – State University (2018)

PROJECTS
OpenSource ML Pipeline (2023)
  - Built end-to-end ML training pipeline processing 1B records monthly
  - Used Pandas, NumPy, and scikit-learn for feature engineering
"""

SYNTHETIC_JD_TEXT = """
Senior Python Developer

We are looking for a Senior Python Developer with 5+ years of experience.

Required:
- Python (must have, 5+ years)
- FastAPI or Django (required)
- PostgreSQL (required)
- Docker and Kubernetes (required)
- REST API design (required)
- Microservices architecture (required)

Preferred:
- AWS experience (preferred)
- Machine learning exposure (nice to have)
- Team leadership (desired)

Experience: 5+ years of professional experience required.
"""

SYNTHETIC_RESUME_SECTIONS = {
    "summary":    "Senior Python Developer with 6 years of experience building scalable REST APIs and microservices.",
    "skills":     "Python, FastAPI, Django, PostgreSQL, Redis, Docker, Kubernetes, AWS, Machine Learning, Pandas, NumPy, Git, CI/CD, Terraform",
    "experience": """Senior Software Engineer - TechCorp Inc (2021-2024)
Led development of a FastAPI microservices platform serving 2M users.
Architected PostgreSQL database schema handling 500K daily transactions.
Built Docker/Kubernetes deployment pipeline reducing deploy time by 60%.
Managed a team of 5 backend engineers.

Software Engineer - StartupXYZ (2018-2021)
Developed REST APIs using Python and Django.
Designed Redis caching layer improving response time by 40%.
Owned CI/CD pipeline using GitHub Actions and Terraform on AWS.""",
    "education":  "B.Sc. Computer Science - State University (2018)",
    "projects":   "OpenSource ML Pipeline (2023). Built end-to-end ML training pipeline processing 1B records monthly.",
}

# ── helpers ───────────────────────────────────────────────────────────────────

results = {}

def run_test(name, fn):
    """Run a single test function, capture result and timing."""
    t0 = time.perf_counter()
    try:
        detail = fn()
        elapsed = (time.perf_counter() - t0) * 1000
        ok(f"{name}  ({elapsed:.0f} ms)")
        if detail:
            for line in detail:
                info(f"       {line}")
        results[name] = "PASS"
        return True
    except Exception as exc:
        elapsed = (time.perf_counter() - t0) * 1000
        fail(f"{name}  ({elapsed:.0f} ms)")
        for line in traceback.format_exc().splitlines()[-6:]:
            print(f"         {RED}{line}{RESET}")
        results[name] = f"FAIL: {exc}"
        return False


# ══════════════════════════════════════════════════════════════════════════════
print(f"\n{BOLD}{CYAN}{'='*60}{RESET}")
print(f"{BOLD}  ATS Pipeline Connectivity Check{RESET}")
print(f"{BOLD}{CYAN}{'='*60}{RESET}\n")

# ── SECTION 1: Core imports ───────────────────────────────────────────────────
print(f"{BOLD}[1/8] Core Module Imports{RESET}")

def test_state_import():
    from agent.state import ATSAgentState, AnalysisMode
    assert "jd_esco_occupation" in ATSAgentState.__annotations__, \
        "ESCO fields missing from ATSAgentState"
    assert "skill_evidence" in ATSAgentState.__annotations__, \
        "Evidence fields missing from ATSAgentState"
    assert "esco_loader" in ATSAgentState.__annotations__, \
        "esco_loader missing from ATSAgentState"
    assert "headline" in ATSAgentState.__annotations__, \
        "reasoning upgrade fields missing from ATSAgentState"
    return [
        f"ATSAgentState has {len(ATSAgentState.__annotations__)} fields",
        "ESCO + evidence + reasoning fields present",
    ]
run_test("agent/state.py (ESCO + evidence fields)", test_state_import)

def test_graph_import():
    from agent.graph import ats_agent
    nodes = list(ats_agent.get_graph().nodes.keys())
    expected = {"intake", "extraction", "jd_analysis", "scoring",
                "reasoning", "deep_analysis", "batch_compare", "report", "__start__", "__end__"}
    missing = expected - set(nodes)
    if missing:
        raise AssertionError(f"Missing nodes: {missing}")
    return [f"LangGraph nodes: {[n for n in nodes if not n.startswith('__')]}"]
run_test("agent/graph.py (LangGraph compiled)", test_graph_import)

def test_esco_loader_import():
    from utils.esco_loader import ESCOLoader
    esco = ESCOLoader("data/esco/")
    return [
        f"ESCOLoader.is_loaded = {esco.is_loaded}",
        f"Occupations: {len(esco.occupations)}, Skills: {len(esco.skills)}",
    ]
run_test("utils/esco_loader.py (import + load)", test_esco_loader_import)

def test_evidence_extractor_import():
    from extraction.skill_evidence_extractor import SkillEvidenceExtractor, SkillEvidence
    ev = SkillEvidence.not_found("python")
    assert ev.depth_score == 0.0
    ext = SkillEvidenceExtractor()
    return ["SkillEvidence + SkillEvidenceExtractor instantiate OK"]
run_test("extraction/skill_evidence_extractor.py (import)", test_evidence_extractor_import)

# ── SECTION 2: Node-level tests ───────────────────────────────────────────────
print(f"\n{BOLD}[2/8] Node: intake_agent{RESET}")

def test_intake_node():
    from agent.nodes.intake_agent import intake_agent
    from agent.state import AnalysisMode
    # Build minimal state
    import io
    # Create a fake minimal PDF-like bytes (just text bytes — tests the intake path)
    fake_bytes = b"%PDF-1.4 fake pdf content for testing purposes only"
    state = {
        "resume_bytes": fake_bytes,
        "resume_filename": "test_resume.pdf",
        "jd_text": SYNTHETIC_JD_TEXT,
        "required_experience": 5.0,
        "llm_provider": "ollama",
        "enable_llm": False,
        "analysis_mode": AnalysisMode.SINGLE,
        "batch_resumes": None,
        "agent_trace": [],
        "extraction_attempts": 0,
        "reasoning_attempts": 0,
        "start_time_ns": time.perf_counter_ns(),
        "esco_loader": None,
    }
    result = intake_agent(state)
    assert "input_valid" in result, "intake_agent missing input_valid"
    assert "agent_trace" in result
    return [
        f"input_valid={result.get('input_valid')}",
        f"file_type={result.get('file_type')}",
        f"trace: {result['agent_trace'][-1] if result['agent_trace'] else 'empty'}",
    ]
run_test("intake_agent (validation + hash)", test_intake_node)

# ── SECTION 3: JD Analysis (with ESCO fallback) ───────────────────────────────
print(f"\n{BOLD}[3/8] Node: jd_analysis_agent (ESCO enrichment){RESET}")

def test_jd_analysis_node():
    from agent.nodes.jd_analysis_agent import jd_analysis_agent
    from agent.state import AnalysisMode
    state = {
        "jd_text": SYNTHETIC_JD_TEXT,
        "required_experience": 5.0,
        "agent_trace": [],
        "esco_loader": None,  # test graceful fallback
        "analysis_mode": AnalysisMode.SINGLE,
    }
    result = jd_analysis_agent(state)
    assert "jd_skills" in result
    assert "jd_required_skills" in result
    assert "jd_preferred_skills" in result
    assert "jd_role_category" in result
    assert "jd_esco_occupation" in result,  "ESCO field missing from jd_analysis output"
    assert "jd_implicit_skills" in result,  "implicit_skills missing from jd_analysis output"
    assert "jd_esco_skill_profile" in result, "esco_skill_profile missing"
    return [
        f"jd_skills: {result['jd_skills'][:4]}",
        f"required: {result['jd_required_skills'][:3]}  preferred: {result['jd_preferred_skills'][:2]}",
        f"role={result['jd_role_category']}, seniority={result['jd_seniority_level']}",
        f"ESCO occupation='{result['jd_esco_occupation']}' (conf={result['jd_esco_confidence']:.3f})",
        f"implicit_skills count: {len(result['jd_implicit_skills'])}",
    ]
run_test("jd_analysis_agent (ESCO graceful fallback)", test_jd_analysis_node)

# ── SECTION 4: Scoring with evidence ─────────────────────────────────────────
print(f"\n{BOLD}[4/8] Node: scoring_agent (evidence scoring){RESET}")

def test_scoring_node():
    from agent.nodes.scoring_agent import scoring_agent
    state = {
        "resume_text": SYNTHETIC_RESUME_TEXT,
        "resume_sections": SYNTHETIC_RESUME_SECTIONS,
        "resume_skills": ["python", "fastapi", "postgresql", "docker",
                          "kubernetes", "aws", "redis", "machine learning"],
        "jd_text": SYNTHETIC_JD_TEXT,
        "jd_skills": ["python", "fastapi", "postgresql", "docker",
                      "kubernetes", "rest api", "microservices", "aws"],
        "jd_required_skills": ["python", "fastapi", "postgresql", "docker",
                                "kubernetes", "rest api", "microservices"],
        "jd_preferred_skills": ["aws", "machine learning"],
        "jd_implicit_skills": [],
        "jd_role_category": "engineering",
        "jd_seniority_level": "senior",
        "jd_required_exp": 5.0,
        "experience_years": 6.0,
        "education": ["B.Sc. Computer Science"],
        "required_experience": 5.0,
        "agent_trace": [],
    }
    result = scoring_agent(state)
    # Existing fields
    assert "composite_score" in result
    assert "skill_coverage_pct" in result
    assert "matched_skills" in result
    assert "missing_skills" in result
    # NEW evidence fields
    assert "skill_evidence" in result,          "skill_evidence missing from scoring output"
    assert "evidence_skill_score" in result,    "evidence_skill_score missing"
    assert "top_evidenced_skills" in result,    "top_evidenced_skills missing"
    assert "shallow_claimed_skills" in result,  "shallow_claimed_skills missing"
    return [
        f"composite_score={result['composite_score']}",
        f"skill_coverage_pct={result['skill_coverage_pct']}",
        f"evidence_skill_score={result['evidence_skill_score']}",
        f"top_evidenced={result['top_evidenced_skills'][:3]}",
        f"shallow_claimed={result['shallow_claimed_skills'][:3]}",
        f"skill_evidence keys: {list(result['skill_evidence'].keys())[:4]}",
    ]
run_test("scoring_agent (evidence scoring + blending)", test_scoring_node)

# ── SECTION 5: Reasoning (LLM disabled = fallback path) ──────────────────────
print(f"\n{BOLD}[5/8] Node: reasoning_agent (LLM-off fallback + ESCO context){RESET}")

def test_reasoning_node():
    from agent.nodes.reasoning_agent import reasoning_agent
    state = {
        "composite_score": 82.5,
        "semantic_score": 78.0,
        "skill_coverage_pct": 87.5,
        "matched_skills": ["python", "fastapi", "postgresql", "docker"],
        "missing_skills": ["microservices"],
        "experience_years": 6.0,
        "required_experience": 5.0,
        "education": ["B.Sc. Computer Science"],
        "jd_text": SYNTHETIC_JD_TEXT,
        "roles": ["Senior Software Engineer"],
        "enable_llm": False,   # disable LLM → uses score-based fallback
        "llm_provider": "ollama",
        "adversarial_flags": [],
        "reasoning_attempts": 0,
        "agent_trace": [],
        # ESCO/evidence context
        "jd_esco_occupation": "",
        "jd_esco_confidence": 0.0,
        "jd_esco_skill_profile": {},
        "jd_implicit_skills": [],
        "skill_evidence": {},
        "top_evidenced_skills": ["python", "fastapi"],
        "shallow_claimed_skills": [],
    }
    result = reasoning_agent(state)
    # Existing fields
    assert "fit_category" in result,          "fit_category missing"
    assert "risk_level" in result,            "risk_level missing"
    assert "hiring_recommendation" in result, "hiring_recommendation missing"
    assert "explanation" in result,           "explanation missing"
    # NEW fields (should be present even in fallback)
    assert "headline" in result,              "headline missing from reasoning output"
    assert "strengths" in result,             "strengths missing"
    assert "concerns" in result,              "concerns missing"
    assert "recommendation" in result,        "recommendation missing"
    assert "confidence" in result,            "confidence missing"
    assert "interview_focus" in result,       "interview_focus missing"
    return [
        f"fit_category={result['fit_category']}",
        f"risk_level={result['risk_level']}",
        f"recommendation={result['recommendation']}",
        f"confidence={result['confidence']}",
        f"headline='{result['headline'][:60]}...'",
    ]
run_test("reasoning_agent (fallback + new schema fields)", test_reasoning_node)

# ── SECTION 6: SkillEvidence scoring rules ────────────────────────────────────
print(f"\n{BOLD}[6/8] SkillEvidenceExtractor — depth score rules{RESET}")

def test_evidence_depth_scoring():
    from extraction.skill_evidence_extractor import SkillEvidenceExtractor
    ext = SkillEvidenceExtractor()
    skills = ["python", "fastapi", "redis", "nonexistent_xyz_skill"]
    ev = ext.extract_evidence(
        resume_text     = SYNTHETIC_RESUME_TEXT,
        resume_sections = SYNTHETIC_RESUME_SECTIONS,
        target_skills   = skills,
    )
    assert ev["python"].found,               "python should be found"
    assert ev["python"].depth_score > 0.0,   "python depth_score should be > 0"
    assert ev["nonexistent_xyz_skill"].found == False, "fake skill should not be found"
    assert ev["nonexistent_xyz_skill"].depth_score == 0.0

    # Verify JSON serialisation
    d = ev["python"].to_dict()
    import json
    json.dumps(d)  # must not raise

    depth_map = {s: round(ev[s].depth_score, 1) for s in skills}
    return [
        f"depth scores: {depth_map}",
        f"python evidence sentences: {len(ev['python'].evidence_sentences)}",
        f"python scale_signals: {ev['python'].scale_signals[:2]}",
        f"python seniority_signals: {ev['python'].seniority_signals[:2]}",
    ]
run_test("SkillEvidenceExtractor depth scoring + JSON serialisation", test_evidence_depth_scoring)

# ── SECTION 7: ESCO loader graceful fallback ──────────────────────────────────
print(f"\n{BOLD}[7/8] ESCOLoader — fallback safety{RESET}")

def test_esco_fallback():
    from utils.esco_loader import ESCOLoader
    # Point to non-existent dir → should not crash
    esco_bad = ESCOLoader("data/does_not_exist/")
    assert esco_bad.is_loaded == False, "should be False when files missing"
    # All methods should return safe empty values
    assert esco_bad.find_closest_occupation("python developer", None) == []
    profile = esco_bad.get_role_skill_profile("http://fake/uri")
    assert profile["essential_skills"] == []
    assert esco_bad.get_skill_definition("python") == ""
    assert esco_bad.get_related_skills("python") == []
    return ["All fallback methods return safe empty values when data missing"]
run_test("ESCOLoader graceful fallback (no data dir)", test_esco_fallback)

# ── SECTION 8: Full graph invocation (synthetic, LLM off) ────────────────────
print(f"\n{BOLD}[8/8] Full LangGraph Pipeline (end-to-end, LLM disabled){RESET}")

def test_full_pipeline():
    from agent.graph import ats_agent
    from agent.state import ATSAgentState, AnalysisMode

    # Create a minimal valid PDF-like bytes that will be passed to intake
    # (intake will fail text extraction on fake bytes, which tests the fallback path)
    fake_pdf = b"%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\n%%EOF"

    initial_state: ATSAgentState = {
        "resume_bytes":       fake_pdf,
        "resume_filename":    "synthetic_test.pdf",
        "jd_text":            SYNTHETIC_JD_TEXT,
        "required_experience": 5.0,
        "llm_provider":       "groq",
        "enable_llm":         False,
        "analysis_mode":      AnalysisMode.SINGLE,
        "batch_resumes":      None,
        "agent_trace":        [],
        "extraction_attempts": 0,
        "reasoning_attempts":  0,
        "start_time_ns":      time.perf_counter_ns(),
        "esco_loader":        None,   # ESCO fallback mode
    }

    t0 = time.perf_counter()
    final_state = ats_agent.invoke(initial_state)
    elapsed = (time.perf_counter() - t0) * 1000

    # Verify final_report exists and has required keys
    report = final_state.get("final_report", {})
    trace  = final_state.get("agent_trace", [])

    required_report_keys = [
        "final_score", "fit_category", "semantic_score",
        "skill_coverage_pct", "matched_skills", "missing_skills",
    ]
    missing_keys = [k for k in required_report_keys if k not in report]
    if missing_keys:
        raise AssertionError(f"final_report missing keys: {missing_keys}")

    # Check new ESCO + evidence fields are present in state
    assert "jd_esco_occupation"    in final_state, "jd_esco_occupation missing from state"
    assert "skill_evidence"        in final_state, "skill_evidence missing from state"
    assert "evidence_skill_score"  in final_state, "evidence_skill_score missing from state"
    assert "top_evidenced_skills"  in final_state, "top_evidenced_skills missing from state"
    assert "headline"              in final_state, "headline missing from state"
    assert "recommendation"        in final_state, "recommendation missing from state"

    return [
        f"Pipeline completed in {elapsed:.0f} ms",
        f"Agent trace ({len(trace)} steps): {' -> '.join(t.split(':')[0] for t in trace)}",
        f"final_report keys: {list(report.keys())}",
        f"fit_category={report.get('fit_category')}",
        f"final_score={report.get('final_score')}",
        f"evidence_skill_score={final_state.get('evidence_skill_score')}",
        f"ESCO occupation='{final_state.get('jd_esco_occupation', '')}'"
    ]
run_test("FULL LangGraph pipeline (7 nodes, LLM disabled)", test_full_pipeline)

# ── Summary ───────────────────────────────────────────────────────────────────
print(f"\n{BOLD}{CYAN}{'='*60}{RESET}")
passed = sum(1 for v in results.values() if v == "PASS")
failed = sum(1 for v in results.values() if v != "PASS")
total  = len(results)
color  = GREEN if failed == 0 else RED
print(f"{BOLD}  Results: {color}{passed}/{total} passed{RESET}", end="")
if failed:
    print(f"  {RED}{failed} failed{RESET}")
    print(f"\n  Failed tests:")
    for name, res in results.items():
        if res != "PASS":
            print(f"    {RED}x{RESET} {name}")
            print(f"      {res}")
else:
    print(f"  {GREEN}All checks passed!{RESET}")
print(f"{BOLD}{CYAN}{'='*60}{RESET}\n")
sys.exit(0 if failed == 0 else 1)
