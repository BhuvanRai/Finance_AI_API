from pydantic import BaseModel
from typing import List, Optional


class IncomeItem(BaseModel):
    monthly_amount: float
    is_active: bool = True


class ExpenseItem(BaseModel):
    monthly_amount: float


class AssetItem(BaseModel):
    type: str
    current_value: float
    liquidity_level: str  # "high", "medium", "low"


class LiabilityItem(BaseModel):
    emi_amount: float
    type: str
    interest_rate: Optional[float] = 0.0


class InsuranceItem(BaseModel):
    type: str  # "term", "health", "life", etc.
    coverage_amount: float


class FinancialHealthRequest(BaseModel):
    user_id: str
    incomes: List[IncomeItem] = []
    expenses: List[ExpenseItem] = []
    assets: List[AssetItem] = []
    liabilities: List[LiabilityItem] = []
    insurances: List[InsuranceItem] = []
    annual_income: float = 0.0


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
