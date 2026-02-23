"""
V3 Endpoint Test Runner
Tests 4 pure-math v3 endpoints with 10 cases each.
No LLM used — runs fast with no rate limits.
Output saved to output.txt
"""
import json, asyncio, httpx
from pathlib import Path
from datetime import datetime

BASE = "http://localhost:8000"
OUT  = Path(__file__).parent.parent / "output.txt"

# ── 10 diverse user profiles ─────────────────────────────────────────────────
PROFILES = [
    # id, name, age, risk, annual_income
    ("u01", "Raj Sharma",     23, "conservative",  480000),
    ("u02", "Priya Patel",    27, "moderate",       840000),
    ("u03", "Amit Verma",     32, "aggressive",    1440000),
    ("u04", "Sneha Rao",      35, "moderate",      1800000),
    ("u05", "Vikram Singh",   40, "conservative",  2400000),
    ("u06", "Neha Gupta",     28, "aggressive",     960000),
    ("u07", "Rohan Mehta",    45, "moderate",      3000000),
    ("u08", "Anita Joshi",    30, "conservative",  1200000),
    ("u09", "Karan Kapoor",   38, "aggressive",    2160000),
    ("u10", "Divya Sharma",   50, "moderate",      3600000),
]

# ── 10 income sets (monthly) ──────────────────────────────────────────────────
INCOMES = [
    [{"sourceType": "salary",   "monthlyAmount": 35000,  "growthRate": 5,  "isActive": True}],
    [{"sourceType": "salary",   "monthlyAmount": 60000,  "growthRate": 8,  "isActive": True}],
    [{"sourceType": "salary",   "monthlyAmount": 100000, "growthRate": 10, "isActive": True},
     {"sourceType": "freelance","monthlyAmount": 20000,  "growthRate": 5,  "isActive": True}],
    [{"sourceType": "salary",   "monthlyAmount": 130000, "growthRate": 9,  "isActive": True},
     {"sourceType": "rental",   "monthlyAmount": 20000,  "growthRate": 3,  "isActive": True}],
    [{"sourceType": "business", "monthlyAmount": 180000, "growthRate": 6,  "isActive": True}],
    [{"sourceType": "salary",   "monthlyAmount": 70000,  "growthRate": 12, "isActive": True},
     {"sourceType": "freelance","monthlyAmount": 10000,  "growthRate": 8,  "isActive": True}],
    [{"sourceType": "business", "monthlyAmount": 220000, "growthRate": 5,  "isActive": True},
     {"sourceType": "rental",   "monthlyAmount": 30000,  "growthRate": 3,  "isActive": True}],
    [{"sourceType": "salary",   "monthlyAmount": 90000,  "growthRate": 7,  "isActive": True}],
    [{"sourceType": "salary",   "monthlyAmount": 160000, "growthRate": 8,  "isActive": True},
     {"sourceType": "rental",   "monthlyAmount": 20000,  "growthRate": 4,  "isActive": True}],
    [{"sourceType": "business", "monthlyAmount": 280000, "growthRate": 4,  "isActive": True},
     {"sourceType": "rental",   "monthlyAmount": 20000,  "growthRate": 3,  "isActive": True}],
]

# ── 10 expense sets (monthly) ─────────────────────────────────────────────────
EXPENSES = [
    [{"category": "rent", "monthlyAmount": 10000, "type": "fixed"},
     {"category": "food", "monthlyAmount":  8000, "type": "variable"}],
    [{"category": "rent", "monthlyAmount": 18000, "type": "fixed"},
     {"category": "food", "monthlyAmount": 12000, "type": "variable"},
     {"category": "utilities", "monthlyAmount": 3000, "type": "fixed"}],
    [{"category": "rent", "monthlyAmount": 28000, "type": "fixed"},
     {"category": "food", "monthlyAmount": 15000, "type": "variable"},
     {"category": "education", "monthlyAmount": 8000, "type": "fixed"}],
    [{"category": "rent", "monthlyAmount": 35000, "type": "fixed"},
     {"category": "food", "monthlyAmount": 18000, "type": "variable"},
     {"category": "travel", "monthlyAmount": 10000, "type": "variable"}],
    [{"category": "rent", "monthlyAmount": 45000, "type": "fixed"},
     {"category": "food", "monthlyAmount": 25000, "type": "variable"},
     {"category": "education", "monthlyAmount": 15000, "type": "fixed"}],
    [{"category": "rent", "monthlyAmount": 22000, "type": "fixed"},
     {"category": "food", "monthlyAmount": 13000, "type": "variable"}],
    [{"category": "rent", "monthlyAmount": 55000, "type": "fixed"},
     {"category": "food", "monthlyAmount": 30000, "type": "variable"},
     {"category": "utilities", "monthlyAmount": 8000, "type": "fixed"}],
    [{"category": "rent", "monthlyAmount": 25000, "type": "fixed"},
     {"category": "food", "monthlyAmount": 14000, "type": "variable"},
     {"category": "utilities", "monthlyAmount": 4000, "type": "fixed"}],
    [{"category": "rent", "monthlyAmount": 40000, "type": "fixed"},
     {"category": "food", "monthlyAmount": 22000, "type": "variable"},
     {"category": "travel", "monthlyAmount": 12000, "type": "variable"}],
    [{"category": "rent", "monthlyAmount": 60000, "type": "fixed"},
     {"category": "food", "monthlyAmount": 35000, "type": "variable"},
     {"category": "education", "monthlyAmount": 20000, "type": "fixed"}],
]

# ── 10 asset sets ─────────────────────────────────────────────────────────────
ASSETS = [
    [{"type": "fd",           "name": "SBI FD",       "currentValue":  80000, "investedAmount":  80000, "expectedReturnRate": 6,  "liquidityLevel": "medium"}],
    [{"type": "mutual_fund",  "name": "HDFC MF",      "currentValue": 250000, "investedAmount": 200000, "expectedReturnRate": 11, "liquidityLevel": "high"},
     {"type": "fd",           "name": "Axis FD",      "currentValue": 100000, "investedAmount": 100000, "expectedReturnRate": 6,  "liquidityLevel": "medium"}],
    [{"type": "stock",        "name": "Nifty ETF",    "currentValue": 600000, "investedAmount": 450000, "expectedReturnRate": 14, "liquidityLevel": "high"},
     {"type": "mutual_fund",  "name": "Axis MF",      "currentValue": 300000, "investedAmount": 260000, "expectedReturnRate": 11, "liquidityLevel": "high"}],
    [{"type": "stock",        "name": "Blue Chips",   "currentValue": 900000, "investedAmount": 700000, "expectedReturnRate": 13, "liquidityLevel": "high"},
     {"type": "real_estate",  "name": "Flat Pune",    "currentValue":3500000, "investedAmount":2500000, "expectedReturnRate": 7,  "liquidityLevel": "low"},
     {"type": "fd",           "name": "HDFC FD",      "currentValue": 200000, "investedAmount": 200000, "expectedReturnRate": 7,  "liquidityLevel": "high"}],
    [{"type": "gold",         "name": "Sovereign",    "currentValue": 500000, "investedAmount": 400000, "expectedReturnRate": 8,  "liquidityLevel": "medium"},
     {"type": "fd",           "name": "SBI FD",       "currentValue": 800000, "investedAmount": 800000, "expectedReturnRate": 7,  "liquidityLevel": "high"},
     {"type": "real_estate",  "name": "Office Del",   "currentValue":6000000, "investedAmount":4000000, "expectedReturnRate": 6,  "liquidityLevel": "low"}],
    [{"type": "mutual_fund",  "name": "Parag MF",     "currentValue": 420000, "investedAmount": 350000, "expectedReturnRate": 12, "liquidityLevel": "high"},
     {"type": "crypto",       "name": "Bitcoin",      "currentValue": 150000, "investedAmount":  80000, "expectedReturnRate": 25, "liquidityLevel": "high"}],
    [{"type": "real_estate",  "name": "Flat Mumbai",  "currentValue":9000000, "investedAmount":6000000, "expectedReturnRate": 7,  "liquidityLevel": "low"},
     {"type": "stock",        "name": "Portfolio",    "currentValue":1500000, "investedAmount":1200000, "expectedReturnRate": 14, "liquidityLevel": "high"},
     {"type": "fd",           "name": "ICICI FD",     "currentValue": 500000, "investedAmount": 500000, "expectedReturnRate": 7,  "liquidityLevel": "high"}],
    [{"type": "mutual_fund",  "name": "SBI MF",       "currentValue": 550000, "investedAmount": 450000, "expectedReturnRate": 10, "liquidityLevel": "high"},
     {"type": "gold",         "name": "Gold ETF",     "currentValue": 180000, "investedAmount": 150000, "expectedReturnRate": 8,  "liquidityLevel": "medium"}],
    [{"type": "stock",        "name": "Mid Cap",      "currentValue":1200000, "investedAmount": 900000, "expectedReturnRate": 16, "liquidityLevel": "high"},
     {"type": "mutual_fund",  "name": "Mirae MF",     "currentValue": 700000, "investedAmount": 600000, "expectedReturnRate": 12, "liquidityLevel": "high"},
     {"type": "real_estate",  "name": "Plot Chennai", "currentValue":2500000, "investedAmount":1800000, "expectedReturnRate": 8,  "liquidityLevel": "low"}],
    [{"type": "fd",           "name": "Fixed Dep",    "currentValue":2000000, "investedAmount":2000000, "expectedReturnRate": 7,  "liquidityLevel": "high"},
     {"type": "gold",         "name": "Gold Bond",    "currentValue": 800000, "investedAmount": 600000, "expectedReturnRate": 8,  "liquidityLevel": "medium"},
     {"type": "real_estate",  "name": "Villa Goa",    "currentValue":12000000,"investedAmount":8000000, "expectedReturnRate": 6,  "liquidityLevel": "low"}],
]

# ── 10 liability sets ─────────────────────────────────────────────────────────
LIABILITIES = [
    [],
    [{"type": "loan", "principalAmount": 500000,  "outstandingAmount": 400000,  "interestRate": 8.0, "emiAmount": 8000,  "tenureRemaining": 60}],
    [{"type": "loan", "principalAmount": 1000000, "outstandingAmount": 800000,  "interestRate": 8.5, "emiAmount": 15000, "tenureRemaining": 72}],
    [{"type": "loan", "principalAmount": 2500000, "outstandingAmount": 2000000, "interestRate": 8.8, "emiAmount": 30000, "tenureRemaining": 84}],
    [{"type": "loan", "principalAmount": 5000000, "outstandingAmount": 3500000, "interestRate": 9.0, "emiAmount": 55000, "tenureRemaining": 96},
     {"type": "credit_card", "principalAmount": 100000, "outstandingAmount": 80000, "interestRate": 36.0, "emiAmount": 8000, "tenureRemaining": 12}],
    [{"type": "loan", "principalAmount": 800000,  "outstandingAmount": 600000,  "interestRate": 9.5, "emiAmount": 12000, "tenureRemaining": 60}],
    [{"type": "loan", "principalAmount": 7000000, "outstandingAmount": 5500000, "interestRate": 8.5, "emiAmount": 80000, "tenureRemaining": 108}],
    [{"type": "loan", "principalAmount": 1500000, "outstandingAmount": 1200000, "interestRate": 8.3, "emiAmount": 20000, "tenureRemaining": 72}],
    [{"type": "loan", "principalAmount": 3500000, "outstandingAmount": 2800000, "interestRate": 9.0, "emiAmount": 45000, "tenureRemaining": 84},
     {"type": "credit_card", "principalAmount": 200000, "outstandingAmount": 150000, "interestRate": 30.0, "emiAmount": 15000, "tenureRemaining": 12}],
    [{"type": "loan", "principalAmount": 8000000, "outstandingAmount": 6000000, "interestRate": 8.8, "emiAmount": 90000, "tenureRemaining": 120}],
]

# ── 10 goal sets ──────────────────────────────────────────────────────────────
GOALS = [
    [{"goalType": "emergency_fund", "targetAmount": 200000,  "targetDate": "2026-12-31", "priorityLevel": "high",   "inflationRate": 5,  "currentSavingsForGoal": 50000,   "status": "active"}],
    [{"goalType": "house",          "targetAmount": 3000000,  "targetDate": "2030-12-31", "priorityLevel": "high",   "inflationRate": 6,  "currentSavingsForGoal": 300000,  "status": "active"}],
    [{"goalType": "car",            "targetAmount": 1000000,  "targetDate": "2027-06-30", "priorityLevel": "medium", "inflationRate": 5,  "currentSavingsForGoal": 150000,  "status": "active"},
     {"goalType": "house",          "targetAmount": 5000000,  "targetDate": "2032-12-31", "priorityLevel": "high",   "inflationRate": 6,  "currentSavingsForGoal": 500000,  "status": "active"}],
    [{"goalType": "retirement",     "targetAmount": 20000000, "targetDate": "2045-12-31", "priorityLevel": "high",   "inflationRate": 6,  "currentSavingsForGoal": 2000000, "status": "active"},
     {"goalType": "travel",         "targetAmount": 500000,   "targetDate": "2028-12-31", "priorityLevel": "low",    "inflationRate": 5,  "currentSavingsForGoal": 50000,   "status": "active"}],
    [{"goalType": "retirement",     "targetAmount": 30000000, "targetDate": "2035-12-31", "priorityLevel": "high",   "inflationRate": 6,  "currentSavingsForGoal": 8000000, "status": "active"}],
    [{"goalType": "house",          "targetAmount": 4000000,  "targetDate": "2029-12-31", "priorityLevel": "high",   "inflationRate": 6,  "currentSavingsForGoal": 400000,  "status": "active"},
     {"goalType": "car",            "targetAmount": 800000,   "targetDate": "2027-01-31", "priorityLevel": "medium", "inflationRate": 5,  "currentSavingsForGoal": 100000,  "status": "active"}],
    [{"goalType": "retirement",     "targetAmount": 50000000, "targetDate": "2035-12-31", "priorityLevel": "high",   "inflationRate": 6,  "currentSavingsForGoal": 12000000,"status": "active"}],
    [{"goalType": "education",      "targetAmount": 2000000,  "targetDate": "2030-06-30", "priorityLevel": "high",   "inflationRate": 8,  "currentSavingsForGoal": 300000,  "status": "active"},
     {"goalType": "retirement",     "targetAmount": 15000000, "targetDate": "2040-12-31", "priorityLevel": "high",   "inflationRate": 6,  "currentSavingsForGoal": 2000000, "status": "active"}],
    [{"goalType": "house",          "targetAmount": 8000000,  "targetDate": "2028-12-31", "priorityLevel": "high",   "inflationRate": 6,  "currentSavingsForGoal": 2000000, "status": "active"}],
    [{"goalType": "retirement",     "targetAmount": 80000000, "targetDate": "2030-12-31", "priorityLevel": "high",   "inflationRate": 6,  "currentSavingsForGoal": 25000000,"status": "active"},
     {"goalType": "travel",         "targetAmount": 2000000,  "targetDate": "2027-06-30", "priorityLevel": "medium", "inflationRate": 5,  "currentSavingsForGoal": 500000,  "status": "active"}],
]


async def post(client, path, body):
    try:
        r = await client.post(f"{BASE}{path}", json=body, headers={"Content-Type": "application/json"})
        r.raise_for_status()
        return r.json(), None
    except httpx.HTTPStatusError as e:
        return None, f"HTTP {e.response.status_code}: {e.response.text[:300]}"
    except Exception as e:
        return None, str(e)


async def main():
    results = {"run_at": datetime.now().isoformat(), "endpoints": {}}

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as c:

        for ep_path, ep_key, build_body in [
            (
                "/api/v3/analytics/net-worth",
                "net_worth",
                lambda i: {
                    "userId": PROFILES[i][0],
                    "assets": ASSETS[i],
                    "liabilities": LIABILITIES[i],
                },
            ),
            (
                "/api/v3/analytics/goal-feasibility",
                "goal_feasibility",
                lambda i: {
                    "userId": PROFILES[i][0],
                    "incomes": INCOMES[i],
                    "expenses": EXPENSES[i],
                    "financialGoals": GOALS[i],
                },
            ),
            (
                "/api/v3/analytics/portfolio-alignment",
                "portfolio_alignment",
                lambda i: {
                    "userId": PROFILES[i][0],
                    "riskProfile": PROFILES[i][3],
                    "assets": ASSETS[i],
                },
            ),
            (
                "/api/v3/simulate/stress-test",
                "stress_test",
                lambda i: {
                    "userId": PROFILES[i][0],
                    "incomes": INCOMES[i],
                    "expenses": EXPENSES[i],
                    "assets": ASSETS[i],
                    "liabilities": LIABILITIES[i],
                },
            ),
        ]:
            print(f"\nPOST {ep_path}")
            cases = []
            for i in range(10):
                uid, name, age, risk, income = PROFILES[i]
                body = build_body(i)
                out, err = await post(c, ep_path, body)
                icon = "✅" if not err else "❌"
                print(f"  Case {i+1:02d} | {name:15s} | age={age} | risk={risk:12s} | {icon}")
                cases.append({
                    "case": i + 1,
                    "user": {"id": uid, "name": name, "age": age, "risk_profile": risk, "annual_income": income},
                    "input": body,
                    "output": out,
                    "error": err,
                })
            results["endpoints"][ep_key] = {"endpoint": ep_path, "cases": cases}

    total   = sum(len(v["cases"]) for v in results["endpoints"].values())
    success = sum(1 for v in results["endpoints"].values() for c in v["cases"] if c["error"] is None)
    results["summary"] = {"total": total, "success": success, "errors": total - success}

    OUT.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n{'='*55}")
    print(f"✅ {success}/{total} passed | 📄 {OUT}")


if __name__ == "__main__":
    asyncio.run(main())
