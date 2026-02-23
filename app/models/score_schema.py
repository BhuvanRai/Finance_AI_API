from pydantic import BaseModel
from pydantic.alias_generators import to_camel
from pydantic import ConfigDict
from typing import List, Optional


class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


# ── Nested user profile (sent by backend) ───────────────────────────────

class UserProfile(CamelModel):
    name: Optional[str] = ""
    age: Optional[int] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    country: Optional[str] = None
    marital_status: Optional[str] = None
    dependents: Optional[int] = 0
    employment_type: Optional[str] = None
    annual_income: Optional[float] = 0.0
    risk_profile: Optional[str] = "conservative"


# ── Sub-items ────────────────────────────────────────────────────────────

class IncomeItem(CamelModel):
    source_type: Optional[str] = "salary"
    monthly_amount: Optional[float] = 0.0
    growth_rate: Optional[float] = 0.0
    is_active: Optional[bool] = True


class ExpenseItem(CamelModel):
    category: Optional[str] = "other"
    monthly_amount: Optional[float] = 0.0
    type: Optional[str] = "fixed"


class AssetItem(CamelModel):
    type: Optional[str] = "other"      # stock|mutual_fund|crypto|fd|real_estate|gold
    name: Optional[str] = ""
    current_value: Optional[float] = 0.0
    invested_amount: Optional[float] = 0.0
    expected_return_rate: Optional[float] = 0.0
    liquidity_level: Optional[str] = "low"  # high|medium|low


class LiabilityItem(CamelModel):
    type: Optional[str] = "loan"       # loan|credit_card|other
    principal_amount: Optional[float] = 0.0
    outstanding_amount: Optional[float] = 0.0
    interest_rate: Optional[float] = 0.0
    emi_amount: Optional[float] = 0.0
    tenure_remaining: Optional[int] = 0


class InsuranceItem(CamelModel):
    type: Optional[str] = "other"      # term|health|vehicle|life
    provider: Optional[str] = None
    coverage_amount: Optional[float] = 0.0
    premium_amount: Optional[float] = 0.0
    maturity_date: Optional[str] = None


class FinancialGoalItem(CamelModel):
    goal_type: Optional[str] = "other"
    target_amount: Optional[float] = 0.0
    target_date: Optional[str] = None  # ISO date string e.g. "2032-12-31"
    priority_level: Optional[str] = "medium"
    inflation_rate: Optional[float] = 6.0
    current_savings_for_goal: Optional[float] = 0.0
    status: Optional[str] = "active"


# ── Request models ───────────────────────────────────────────────────────

class FinancialHealthRequest(CamelModel):
    """
    Matches backend payload:
    { user: {...}, incomes: [...], expenses: [...], assets: [...],
      liabilities: [...], insurances: [...], financialGoals: [...] }
    """
    user: UserProfile
    incomes: List[IncomeItem] = []
    expenses: List[ExpenseItem] = []
    assets: List[AssetItem] = []
    liabilities: List[LiabilityItem] = []
    insurances: List[InsuranceItem] = []
    financial_goals: List[FinancialGoalItem] = []  # camelCase: financialGoals


# ── Response models ──────────────────────────────────────────────────────

class ScoreBreakdown(BaseModel):
    savings_rate: int
    emergency_fund: int
    debt_ratio: int
    diversification: int
    insurance_coverage: int


class FinancialHealthScore(BaseModel):
    user: str
    score: int
    breakdown: ScoreBreakdown


class FinancialHealthResponse(BaseModel):
    financial_health_score: FinancialHealthScore
