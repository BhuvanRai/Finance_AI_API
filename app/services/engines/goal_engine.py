"""
Goal Engine — Pure math, no LLM.
Computes: required SIP, funding gap, goal risk score.
"""
from typing import List, Dict, Any
from datetime import date
from app.models.user_schema import FinancialGoalItem, IncomeItem, ExpenseItem


def _required_sip(
    target_amount: float,
    current_savings: float,
    months_remaining: int,
    annual_return_rate: float = 0.12,
    annual_inflation_rate: float = 0.06,
) -> float:
    """
    Calculates the required monthly SIP to reach an inflation-adjusted target.
    Uses the Future Value of Annuity formula:
        FV = P * [((1+r)^n - 1) / r]
    Solving for P (SIP amount).
    """
    if months_remaining <= 0:
        return 0.0

    # Inflate the target
    years = months_remaining / 12
    inflated_target = target_amount * ((1 + annual_inflation_rate) ** years)

    # Gap after accounting for current savings growing at return rate
    future_value_of_savings = current_savings * ((1 + annual_return_rate / 12) ** months_remaining)
    remaining_gap = max(0, inflated_target - future_value_of_savings)

    if remaining_gap <= 0:
        return 0.0

    # SIP formula
    r = annual_return_rate / 12
    sip = remaining_gap * r / (((1 + r) ** months_remaining) - 1)
    return round(sip, 2)


def _goal_risk_score(months_remaining: int, gap_ratio: float) -> str:
    """
    gap_ratio = funding_gap / target_amount
    """
    if months_remaining < 12 and gap_ratio > 0.5:
        return "critical"
    elif months_remaining < 24 and gap_ratio > 0.3:
        return "high"
    elif gap_ratio > 0.5:
        return "medium"
    return "low"


def compute_goal_feasibility(
    goals: List[FinancialGoalItem],
    incomes: List[IncomeItem],
    expenses: List[ExpenseItem],
) -> List[Dict[str, Any]]:
    total_income = sum(i.monthly_amount for i in incomes if i.is_active)
    total_expense = sum(e.monthly_amount for e in expenses)
    monthly_surplus = total_income - total_expense

    today = date.today()
    results = []

    for goal in goals:
        if (goal.status or "active") != "active":
            continue
        # Skip goals with no date or zero target — nothing to compute
        if goal.target_date is None or (goal.target_amount or 0) <= 0:
            continue

        delta = goal.target_date - today
        months_remaining = max(0, int(delta.days / 30.44))

        required_sip = _required_sip(
            target_amount=goal.target_amount,
            current_savings=goal.current_savings_for_goal,
            months_remaining=months_remaining,
            annual_return_rate=0.12,
            annual_inflation_rate=goal.inflation_rate / 100,
        )

        funding_gap = max(0, required_sip - monthly_surplus)
        inflated_target = goal.target_amount * (
            (1 + goal.inflation_rate / 100) ** (months_remaining / 12)
        )
        gap_ratio = funding_gap / inflated_target if inflated_target > 0 else 0
        risk = _goal_risk_score(months_remaining, gap_ratio)

        results.append({
            "goal_type": goal.goal_type,
            "priority": goal.priority_level,
            "target_date": str(goal.target_date),
            "months_remaining": months_remaining,
            "inflation_adjusted_target": round(inflated_target, 2),
            "current_savings_for_goal": goal.current_savings_for_goal,
            "required_monthly_sip": required_sip,
            "monthly_surplus_available": round(monthly_surplus, 2),
            "funding_gap": round(funding_gap, 2),
            "goal_risk": risk,
            "is_feasible": funding_gap <= 0,
        })

    return results
