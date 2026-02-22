from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel
from typing import List, Optional
from datetime import date


# Shared config: accepts both camelCase (from client) and snake_case (Python-native)
class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class UserProfile(CamelModel):
    name: str
    age: int
    gender: str
    address: str
    city: str
    state: str
    zip: str
    country: str
    marital_status: str
    dependents: int
    employment_type: str
    annual_income: float
    risk_profile: str = "conservative"  # conservative | moderate | aggressive


class IncomeItem(CamelModel):
    source_type: str  # salary | freelance | investment | rental | business | other
    monthly_amount: float
    growth_rate: float
    is_active: bool = True


class ExpenseItem(CamelModel):
    category: str   # housing | transportation | food | utilities | ...
    monthly_amount: float
    type: str       # fixed | variable


class AssetItem(CamelModel):
    type: str       # stock | mutual_fund | crypto | fd | real_estate | gold
    name: str
    current_value: float
    invested_amount: float
    expected_return_rate: float
    liquidity_level: str  # high | medium | low


class LiabilityItem(CamelModel):
    type: str             # loan | credit_card | other
    principal_amount: float
    outstanding_amount: float
    interest_rate: float
    emi_amount: float
    tenure_remaining: int  # months


class FinancialGoalItem(CamelModel):
    goal_type: str          # house | retirement | car | travel | emergency_fund
    target_amount: float
    target_date: date
    priority_level: str     # high | medium | low
    inflation_rate: float
    current_savings_for_goal: float
    status: str             # active | achieved


class InsuranceItem(CamelModel):
    type: str               # health | term | vehicle
    provider: str
    coverage_amount: float
    premium_amount: float
    maturity_date: date


class FinancialHealthScoreInput(CamelModel):
    score: float
    breakdown: dict


class UserBasedRetrievalRequest(CamelModel):
    query: str
    history: Optional[str] = None   # Compressed history string from previous response

    user: UserProfile
    income: List[IncomeItem] = []
    expense: List[ExpenseItem] = []
    asset: List[AssetItem] = []
    liability: List[LiabilityItem] = []
    financial_goal: List[FinancialGoalItem] = []
    insurance: List[InsuranceItem] = []
    financial_health_score: Optional[FinancialHealthScoreInput] = None


class UserBasedRetrievalResponse(CamelModel):
    answer: str
    history: str   # Compressed, to be stored and sent back in next request
