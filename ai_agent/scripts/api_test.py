"""Quick end-to-end API test for the ATS backend."""
import requests, json, sys

base = "http://localhost:8000"
print("=== ATS API End-to-End Test ===\n")

passed = 0
failed = 0

def check(label, cond, detail=""):
    global passed, failed
    if cond:
        print(f"  PASS  {label}")
        passed += 1
    else:
        print(f"  FAIL  {label}  {detail}")
        failed += 1

# 1. Health
r = requests.get(f"{base}/", timeout=5)
check("Health check", r.status_code == 200, r.text[:60])

# 2. Swagger UI
r = requests.get(f"{base}/docs", timeout=5)
check("Swagger UI (/docs)", r.status_code == 200)

# 3. OpenAPI schema + routes
r = requests.get(f"{base}/openapi.json", timeout=5)
paths = list(r.json().get("paths", {}).keys())
print(f"\n  Registered routes: {paths}\n")
check("OpenAPI schema", r.status_code == 200)

# 4. Signup
r = requests.post(f"{base}/auth/signup",
    json={"email": "tester@ats.dev", "password": "Test1234!"},
    timeout=5)
check("Signup (POST /auth/signup)", r.status_code in (201, 400), r.text[:80])

# 5. Login
r = requests.post(f"{base}/auth/login",
    json={"email": "tester@ats.dev", "password": "Test1234!"},
    timeout=5)
check("Login (POST /auth/login)", r.status_code == 200, r.text[:80])
token = r.json().get("access_token", "") if r.status_code == 200 else ""

# 6. Protected history endpoint
if token:
    r = requests.get(f"{base}/api/history",
        headers={"Authorization": f"Bearer {token}"}, timeout=5)
    check("History (GET /api/history)", r.status_code == 200, str(r.json())[:80])
else:
    print("  SKIP  History — no token")

print(f"\n{'='*40}")
print(f"Results: {passed} passed, {failed} failed")
sys.exit(0 if failed == 0 else 1)
