"""
Stress Test Engine — Pure math, no LLM.
Simulates: Recession, Job Loss, Rate Hike.
"""
from typing import List, Dict, Any
from app.models.user_schema import IncomeItem, ExpenseItem, AssetItem, LiabilityItem


def _months_of_runway(liquid_assets: float, monthly_shortfall: float) -> float:
    if monthly_shortfall <= 0:
        return float("inf")
    return round(liquid_assets / monthly_shortfall, 1)


def run_stress_test(
    incomes: List[IncomeItem],
    expenses: List[ExpenseItem],
    assets: List[AssetItem],
    liabilities: List[LiabilityItem],
) -> Dict[str, Any]:
    total_income = sum((i.monthly_amount or 0) for i in incomes if (i.is_active if i.is_active is not None else True))
    total_expense = sum((e.monthly_amount or 0) for e in expenses)
    total_emi = sum((l.emi_amount or 0) for l in liabilities)
    total_assets = sum((a.current_value or 0) for a in assets)
    liquid_assets = sum((a.current_value or 0) for a in assets if (a.liquidity_level or "") == "high")
    normal_surplus = total_income - total_expense

    results: Dict[str, Any] = {}

    # ── Scenario 1: Recession ───────────────────────────────────────────
    # Equity/crypto drop 30%, income drops 20%, expenses stay flat
    recession_asset_loss = sum(
        (a.current_value or 0) * 0.30
        for a in assets
        if (a.type or "") in ("stock", "mutual_fund", "crypto")
    )
    recession_income = total_income * 0.80
    recession_surplus = recession_income - total_expense
    results["recession"] = {
        "scenario": "30% equity crash + 20% income drop",
        "impacted_income": round(recession_income, 2),
        "asset_value_drop": round(recession_asset_loss, 2),
        "monthly_surplus": round(recession_surplus, 2),
        "months_of_runway": _months_of_runway(liquid_assets, -recession_surplus)
        if recession_surplus < 0 else "Positive surplus — no runway risk",
        "verdict": "AT RISK" if recession_surplus < 0 else "STABLE",
    }

    # ── Scenario 2: Job Loss ────────────────────────────────────────────
    # Primary income (salary) drops to 0, only other sources remain
    non_salary_income = sum(
        (i.monthly_amount or 0) for i in incomes
        if (i.is_active if i.is_active is not None else True) and (i.source_type or "") != "salary"
    )
    job_loss_surplus = non_salary_income - total_expense
    results["job_loss"] = {
        "scenario": "Primary salary income lost",
        "remaining_income": round(non_salary_income, 2),
        "monthly_shortfall": round(abs(job_loss_surplus), 2) if job_loss_surplus < 0 else 0,
        "months_of_runway": _months_of_runway(liquid_assets, -job_loss_surplus)
        if job_loss_surplus < 0 else "Positive surplus — no runway risk",
        "verdict": "AT RISK" if job_loss_surplus < 0 else "STABLE",
    }

    # ── Scenario 3: Interest Rate Hike ──────────────────────────────────
    # All loan EMIs increase by 20% (floating rate impact)
    hiked_emi = total_emi * 1.20
    emi_increase = hiked_emi - total_emi
    rate_hike_expense = total_expense + emi_increase
    rate_hike_surplus = total_income - rate_hike_expense
    results["rate_hike"] = {
        "scenario": "20% EMI increase on all loans",
        "new_total_emi": round(hiked_emi, 2),
        "additional_monthly_burden": round(emi_increase, 2),
        "new_monthly_surplus": round(rate_hike_surplus, 2),
        "new_debt_ratio_percent": round(hiked_emi / total_income * 100, 1) if total_income > 0 else None,
        "verdict": "AT RISK" if rate_hike_surplus < 0 else "STABLE",
    }

    # ── Summary ─────────────────────────────────────────────────────────
    at_risk_count = sum(
        1 for s in results.values() if s.get("verdict") == "AT RISK"
    )
    results["summary"] = {
        "scenarios_at_risk": at_risk_count,
        "overall_resilience": "LOW" if at_risk_count >= 2 else "MEDIUM" if at_risk_count == 1 else "HIGH",
        "liquid_emergency_fund": round(liquid_assets, 2),
    }

    return results
