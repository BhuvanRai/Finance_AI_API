from fastapi import APIRouter
from app.models.score_schema import (
    FinancialHealthRequest,
    FinancialHealthResponse,
    FinancialHealthScore,
    ScoreBreakdown,
)

router = APIRouter()


def _score_savings_rate(total_income: float, total_expense: float) -> int:
    """Score savings rate out of 25."""
    if total_income <= 0:
        return 0
    rate = (total_income - total_expense) / total_income
    if rate >= 0.40:
        return 25
    elif rate >= 0.30:
        return 20
    elif rate >= 0.20:
        return 15
    elif rate >= 0.10:
        return 8
    elif rate >= 0:
        return 4
    return 0


def _score_emergency_fund(liquid_assets: float, total_expense: float) -> int:
    """Score emergency fund coverage out of 20."""
    if total_expense <= 0:
        return 0
    ratio = liquid_assets / total_expense
    if ratio >= 6:
        return 20
    elif ratio >= 3:
        return 15
    elif ratio >= 1:
        return 8
    elif ratio >= 0.5:
        return 4
    return 0


def _score_debt_ratio(total_emi: float, total_income: float, liabilities) -> int:
    """Score debt burden out of 20 with optional credit card penalty."""
    if total_income <= 0:
        return 0
    ratio = total_emi / total_income
    if ratio < 0.20:
        score = 20
    elif ratio < 0.35:
        score = 15
    elif ratio < 0.50:
        score = 8
    else:
        score = 0

    # Penalty for high-interest credit card debt
    for liability in liabilities:
        if liability.type == "credit_card" and (liability.interest_rate or 0) > 24:
            score -= 5
            break  # Apply penalty once

    return max(0, score)


def _score_diversification(asset_types: set) -> int:
    """Score diversification based on unique asset types out of 15."""
    count = len(asset_types)
    if count >= 3:
        return 15
    elif count == 2:
        return 10
    elif count == 1:
        return 5
    return 0


def _score_insurance(total_term_coverage: float, annual_income: float, total_all_coverage: float) -> int:
    """Score insurance coverage out of 20.
    Uses term-to-income ratio when income is available.
    Falls back to raw total coverage when income is 0.
    """
    if annual_income > 0:
        ratio = total_term_coverage / annual_income
        if ratio >= 10:
            return 20
        elif ratio >= 5:
            return 15
        elif ratio >= 2:
            return 8
        # Has income but low/no term insurance — check any coverage
        if total_all_coverage > 0:
            return 4
        return 0
    else:
        # No income data — score based on whether any insurance exists
        if total_all_coverage >= 2_000_000:
            return 15
        elif total_all_coverage >= 500_000:
            return 10
        elif total_all_coverage > 0:
            return 5
        return 0


@router.post("/financial-health", response_model=FinancialHealthResponse)
def calculate_financial_health(request: FinancialHealthRequest):
    """
    Deterministic Financial Health Score (0–100).
    No LLM. Pure math. Fully auditable.
    """
    # --- Aggregate Inputs ---
    total_income = sum(
        (inc.monthly_amount or 0) for inc in request.incomes if (inc.is_active or True)
    )
    total_expense = sum((exp.monthly_amount or 0) for exp in request.expenses)

    liquid_assets = sum(
        (ast.current_value or 0)
        for ast in request.assets
        if (ast.liquidity_level or "") == "high"
    )
    asset_types = {ast.type for ast in request.assets if ast.type}

    total_emi = sum((lib.emi_amount or 0) for lib in request.liabilities)

    total_term_coverage = sum(
        (ins.coverage_amount or 0)
        for ins in request.insurances
        if (ins.type or "") == "term"
    )
    total_all_coverage = sum((ins.coverage_amount or 0) for ins in request.insurances)

    # --- Score Each Component ---
    savings_score = _score_savings_rate(total_income, total_expense)
    emergency_score = _score_emergency_fund(liquid_assets, total_expense)
    debt_score = _score_debt_ratio(total_emi, total_income, request.liabilities)
    diversification_score = _score_diversification(asset_types)
    insurance_score = _score_insurance(
        total_term_coverage,
        request.user.annual_income or 0,
        total_all_coverage,
    )

    # --- Final Score (clamped 0–100) ---
    final_score = max(
        0,
        min(
            100,
            savings_score
            + emergency_score
            + debt_score
            + diversification_score
            + insurance_score,
        ),
    )

    return FinancialHealthResponse(
        financial_health_score=FinancialHealthScore(
            user=request.user.name or "Unknown",
            score=final_score,
            breakdown=ScoreBreakdown(
                savings_rate=savings_score,
                emergency_fund=emergency_score,
                debt_ratio=debt_score,
                diversification=diversification_score,
                insurance_coverage=insurance_score,
            ),
        )
    )
