"""
Comprehensive endpoint test runner.
Tests all 9 endpoints with 3 test cases each.
Saves full input + output + history to output.txt as JSON.
"""
import json, time, asyncio, httpx
from pathlib import Path
from datetime import datetime

BASE = "http://localhost:8000"
OUT  = Path(__file__).parent.parent / "output.txt"
DELAY = 4   # seconds between LLM calls (rate-limit buffer)

# ── Shared profile blocks ────────────────────────────────────────────────────

USERS = [
    {
        "name": "Raj Sharma",   "age": 28, "gender": "male",
        "annualIncome": 1200000, "riskProfile": "moderate",
        "employmentType": "salaried", "maritalStatus": "single",
        "dependents": 0, "city": "Mumbai", "state": "Maharashtra", "country": "India"
    },
    {
        "name": "Priya Patel",  "age": 34, "gender": "female",
        "annualIncome": 1800000, "riskProfile": "aggressive",
        "employmentType": "salaried", "maritalStatus": "married",
        "dependents": 1, "city": "Bangalore", "state": "Karnataka", "country": "India"
    },
    {
        "name": "Amit Verma",   "age": 45, "gender": "male",
        "annualIncome": 2400000, "riskProfile": "conservative",
        "employmentType": "self_employed", "maritalStatus": "married",
        "dependents": 2, "city": "Delhi", "state": "Delhi", "country": "India"
    },
]

INCOMES = [
    [{"sourceType": "salary",   "monthlyAmount": 90000,  "growthRate": 8,  "isActive": True}],
    [{"sourceType": "salary",   "monthlyAmount": 130000, "growthRate": 10, "isActive": True},
     {"sourceType": "rental",   "monthlyAmount": 20000,  "growthRate": 3,  "isActive": True}],
    [{"sourceType": "business", "monthlyAmount": 180000, "growthRate": 5,  "isActive": True}],
]

EXPENSES = [
    [{"category": "rent",  "monthlyAmount": 25000, "type": "fixed"},
     {"category": "food",  "monthlyAmount": 12000, "type": "variable"}],
    [{"category": "rent",  "monthlyAmount": 35000, "type": "fixed"},
     {"category": "food",  "monthlyAmount": 18000, "type": "variable"},
     {"category": "education", "monthlyAmount": 10000, "type": "fixed"}],
    [{"category": "rent",  "monthlyAmount": 50000, "type": "fixed"},
     {"category": "food",  "monthlyAmount": 25000, "type": "variable"},
     {"category": "utilities", "monthlyAmount": 8000, "type": "fixed"}],
]

ASSETS = [
    [{"type": "mutual_fund", "name": "SBI MF",    "currentValue": 350000,  "investedAmount": 280000, "expectedReturnRate": 10, "liquidityLevel": "high"},
     {"type": "fd",           "name": "HDFC FD",   "currentValue": 150000,  "investedAmount": 150000, "expectedReturnRate": 6,  "liquidityLevel": "medium"}],
    [{"type": "stock",       "name": "Nifty ETF",  "currentValue": 800000,  "investedAmount": 600000, "expectedReturnRate": 14, "liquidityLevel": "high"},
     {"type": "mutual_fund", "name": "Axis MF",    "currentValue": 500000,  "investedAmount": 420000, "expectedReturnRate": 11, "liquidityLevel": "high"},
     {"type": "real_estate", "name": "Flat Blr",   "currentValue": 6000000, "investedAmount": 4000000, "expectedReturnRate": 7, "liquidityLevel": "low"}],
    [{"type": "gold",        "name": "Sovereign Bond", "currentValue": 400000, "investedAmount": 300000, "expectedReturnRate": 8, "liquidityLevel": "medium"},
     {"type": "fd",          "name": "SBI FD",     "currentValue": 1000000, "investedAmount": 1000000, "expectedReturnRate": 7, "liquidityLevel": "high"},
     {"type": "real_estate", "name": "Office DL",  "currentValue": 8000000, "investedAmount": 5000000, "expectedReturnRate": 6, "liquidityLevel": "low"}],
]

LIABILITIES = [
    [],
    [{"type": "loan", "principalAmount": 2500000, "outstandingAmount": 2000000, "interestRate": 8.5, "emiAmount": 30000, "tenureRemaining": 84}],
    [{"type": "loan", "principalAmount": 5000000, "outstandingAmount": 3500000, "interestRate": 9.0, "emiAmount": 55000, "tenureRemaining": 96},
     {"type": "credit_card", "principalAmount": 100000, "outstandingAmount": 80000, "interestRate": 36.0, "emiAmount": 8000, "tenureRemaining": 12}],
]

INSURANCES = [
    [{"type": "term", "provider": "LIC",  "coverageAmount": 10000000, "premiumAmount": 12000}],
    [{"type": "term", "provider": "HDFC", "coverageAmount": 20000000, "premiumAmount": 18000},
     {"type": "health", "provider": "Star", "coverageAmount": 1000000, "premiumAmount": 15000}],
    [{"type": "term",   "provider": "Max", "coverageAmount": 25000000, "premiumAmount": 22000},
     {"type": "health", "provider": "Care", "coverageAmount": 2000000, "premiumAmount": 25000}],
]

GOALS = [
    [{"goalType": "house",      "targetAmount": 5000000,  "targetDate": "2030-12-31", "priorityLevel": "high",   "inflationRate": 6, "currentSavingsForGoal": 400000, "status": "active"}],
    [{"goalType": "retirement", "targetAmount": 20000000, "targetDate": "2045-12-31", "priorityLevel": "high",   "inflationRate": 6, "currentSavingsForGoal": 2000000, "status": "active"},
     {"goalType": "car",        "targetAmount": 1500000,  "targetDate": "2027-06-30", "priorityLevel": "medium", "inflationRate": 5, "currentSavingsForGoal": 200000,  "status": "active"}],
    [{"goalType": "retirement", "targetAmount": 30000000, "targetDate": "2035-12-31", "priorityLevel": "high",   "inflationRate": 6, "currentSavingsForGoal": 5000000, "status": "active"}],
]

RAG_QUERIES = [
    "What are RBI KYC guidelines for opening a bank account?",
    "What documents are required for a home loan in India?",
    "Explain the rules for nomination in mutual fund investments.",
]

UBR_QUERIES = [
    "Evaluate my financial profile and suggest next steps.",
    "Am I ready to invest in equity mutual funds given my risk profile?",
    "What should be my emergency fund target and how do I build it?",
]


async def post(client, path, body, label):
    """POST and return (input, output, error, duration_ms)."""
    start = time.time()
    try:
        r = await client.post(f"{BASE}{path}", json=body, headers={"Content-Type": "application/json"})
        r.raise_for_status()
        return body, r.json(), None, int((time.time()-start)*1000)
    except httpx.HTTPStatusError as e:
        return body, None, f"HTTP {e.response.status_code}: {e.response.text[:300]}", int((time.time()-start)*1000)
    except Exception as e:
        return body, None, str(e), int((time.time()-start)*1000)


async def get(client, path, label):
    start = time.time()
    try:
        r = await client.get(f"{BASE}{path}")
        r.raise_for_status()
        return {}, r.json(), None, int((time.time()-start)*1000)
    except Exception as e:
        return {}, None, str(e), int((time.time()-start)*1000)


def record(endpoint, method, case_num, inp, out, err, ms):
    return {
        "endpoint": endpoint,
        "method":   method,
        "case":     case_num,
        "duration_ms": ms,
        "input":    inp,
        "output":   out,
        "error":    err,
    }


async def main():
    results = []

    async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as c:
        total_endpoints = 9
        ep = 0

        # ── 1. Health ──────────────────────────────────────────────────────
        ep += 1
        print(f"\n[{ep}/{total_endpoints}] GET /api/v1/health")
        inp, out, err, ms = await get(c, "/api/v1/health", "health")
        results.append(record("/api/v1/health", "GET", 1, inp, out, err, ms))
        print(f"   {'✅' if not err else '❌'} {ms}ms")

        # ── 2. RAG Ask (3 cases) ──────────────────────────────────────────
        ep += 1
        print(f"\n[{ep}/{total_endpoints}] POST /api/v1/rag/ask")
        for i, q in enumerate(RAG_QUERIES, 1):
            body = {"query": q, "history": []}
            inp, out, err, ms = await post(c, "/api/v1/rag/ask", body, f"rag/ask #{i}")
            results.append(record("/api/v1/rag/ask", "POST", i, inp, out, err, ms))
            print(f"   Case {i}: {'✅' if not err else '❌'} {ms}ms")
            if i < 3: time.sleep(DELAY)

        # ── 3. RAG Retrieve (3 cases) ─────────────────────────────────────
        ep += 1
        print(f"\n[{ep}/{total_endpoints}] POST /api/v1/rag/retrieve")
        for i, q in enumerate(RAG_QUERIES, 1):
            body = {"query": q, "history": []}
            inp, out, err, ms = await post(c, "/api/v1/rag/retrieve", body, f"rag/retrieve #{i}")
            results.append(record("/api/v1/rag/retrieve", "POST", i, inp, out, err, ms))
            print(f"   Case {i}: {'✅' if not err else '❌'} {ms}ms")
            if i < 3: time.sleep(1)

        # ── 4. Financial Health Score (3 cases) ───────────────────────────
        ep += 1
        print(f"\n[{ep}/{total_endpoints}] POST /api/v1/score/financial-health")
        for i in range(3):
            body = {
                "user": USERS[i],
                "incomes": INCOMES[i],
                "expenses": EXPENSES[i],
                "assets": ASSETS[i],
                "liabilities": LIABILITIES[i],
                "insurances": INSURANCES[i],
                "financialGoals": GOALS[i],
            }
            inp, out, err, ms = await post(c, "/api/v1/score/financial-health", body, f"score #{i+1}")
            results.append(record("/api/v1/score/financial-health", "POST", i+1, inp, out, err, ms))
            print(f"   Case {i+1}: {'✅' if not err else '❌'} {ms}ms")

        # ── 5. Net Worth (3 cases) ────────────────────────────────────────
        ep += 1
        print(f"\n[{ep}/{total_endpoints}] POST /api/v1/analytics/net-worth")
        for i in range(3):
            body = {"userId": USERS[i]["name"].replace(" ", "_"), "assets": ASSETS[i], "liabilities": LIABILITIES[i]}
            inp, out, err, ms = await post(c, "/api/v1/analytics/net-worth", body, f"net-worth #{i+1}")
            results.append(record("/api/v1/analytics/net-worth", "POST", i+1, inp, out, err, ms))
            print(f"   Case {i+1}: {'✅' if not err else '❌'} {ms}ms")

        # ── 6. Goal Feasibility (3 cases) ─────────────────────────────────
        ep += 1
        print(f"\n[{ep}/{total_endpoints}] POST /api/v1/analytics/goal-feasibility")
        for i in range(3):
            body = {"userId": USERS[i]["name"].replace(" ", "_"), "incomes": INCOMES[i], "expenses": EXPENSES[i], "financialGoals": GOALS[i]}
            inp, out, err, ms = await post(c, "/api/v1/analytics/goal-feasibility", body, f"goal #{i+1}")
            results.append(record("/api/v1/analytics/goal-feasibility", "POST", i+1, inp, out, err, ms))
            print(f"   Case {i+1}: {'✅' if not err else '❌'} {ms}ms")

        # ── 7. Portfolio Alignment (3 cases) ──────────────────────────────
        ep += 1
        print(f"\n[{ep}/{total_endpoints}] POST /api/v1/analytics/portfolio-alignment")
        for i in range(3):
            body = {"userId": USERS[i]["name"].replace(" ", "_"), "riskProfile": USERS[i]["riskProfile"], "assets": ASSETS[i]}
            inp, out, err, ms = await post(c, "/api/v1/analytics/portfolio-alignment", body, f"portfolio #{i+1}")
            results.append(record("/api/v1/analytics/portfolio-alignment", "POST", i+1, inp, out, err, ms))
            print(f"   Case {i+1}: {'✅' if not err else '❌'} {ms}ms")

        # ── 8. Stress Test (3 cases) ──────────────────────────────────────
        ep += 1
        print(f"\n[{ep}/{total_endpoints}] POST /api/v1/simulate/stress-test")
        for i in range(3):
            body = {"userId": USERS[i]["name"].replace(" ", "_"), "incomes": INCOMES[i], "expenses": EXPENSES[i], "assets": ASSETS[i], "liabilities": LIABILITIES[i]}
            inp, out, err, ms = await post(c, "/api/v1/simulate/stress-test", body, f"stress #{i+1}")
            results.append(record("/api/v1/simulate/stress-test", "POST", i+1, inp, out, err, ms))
            print(f"   Case {i+1}: {'✅' if not err else '❌'} {ms}ms")

        # ── 9. User-Based Retrieval v2 (3 cases, chained history) ─────────
        ep += 1
        print(f"\n[{ep}/{total_endpoints}] POST /api/v2/user-based-retrieval/")
        history = ""
        for i in range(3):
            body = {
                "query":   UBR_QUERIES[i],
                "history": history,
                "user":    USERS[i],
                "income":  INCOMES[i],
                "expense": EXPENSES[i],
                "asset":   ASSETS[i],
                "liability":      LIABILITIES[i],
                "financialGoal":  GOALS[i],
                "insurance":      INSURANCES[i],
                "financialHealthScore": {"score": 0, "breakdown": {}},
            }
            inp, out, err, ms = await post(c, "/api/v2/user-based-retrieval/", body, f"ubr #{i+1}")
            # Chain the returned history into the next request
            if out and "history" in out:
                history = out["history"]
            results.append(record(
                "/api/v2/user-based-retrieval/", "POST", i+1, inp, out, err, ms
            ))
            print(f"   Case {i+1}: {'✅' if not err else '❌'} {ms}ms")
            if i < 2: time.sleep(DELAY)

    # ── Write output ─────────────────────────────────────────────────────────
    summary = {
        "run_at":   datetime.now().isoformat(),
        "total":    len(results),
        "success":  sum(1 for r in results if r["error"] is None),
        "errors":   sum(1 for r in results if r["error"] is not None),
        "results":  results,
    }
    OUT.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n{'='*55}")
    print(f"✅ Done — {summary['success']}/{summary['total']} passed   |   {summary['errors']} errors")
    print(f"📄 Output: {OUT}")


if __name__ == "__main__":
    asyncio.run(main())
