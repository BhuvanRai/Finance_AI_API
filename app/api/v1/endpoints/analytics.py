from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel
from typing import List, Optional, Any, Dict
from app.models.user_schema import (
    IncomeItem, ExpenseItem, AssetItem,
    LiabilityItem, FinancialGoalItem, CamelModel,
)
from app.services.engines.net_worth import compute_net_worth
from app.services.engines.goal_engine import compute_goal_feasibility
from app.services.engines.portfolio_engine import check_portfolio_alignment

router = APIRouter()


# ── Shared Input ────────────────────────────────────────────────────────

class AnalyticsRequest(CamelModel):
    user_id: str
    risk_profile: Optional[str] = "conservative"
    annual_income: Optional[float] = 0.0
    incomes: List[IncomeItem] = []
    expenses: List[ExpenseItem] = []
    assets: List[AssetItem] = []
    liabilities: List[LiabilityItem] = []
    financial_goals: List[FinancialGoalItem] = []


# ── 1. Net Worth ────────────────────────────────────────────────────────

@router.post("/net-worth")
def net_worth(req: AnalyticsRequest):
    """
    Computes net worth, liquidity ratio, asset allocation %, and debt-to-asset ratio.
    Pure math — no LLM.
    """
    try:
        result = compute_net_worth(req.assets, req.liabilities)
        return {"user_id": req.user_id, "net_worth_analysis": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── 2. Goal Feasibility ─────────────────────────────────────────────────

@router.post("/goal-feasibility")
def goal_feasibility(req: AnalyticsRequest):
    """
    Per-goal analysis: required SIP, funding gap, goal risk, and feasibility flag.
    Pure math — no LLM.
    """
    try:
        result = compute_goal_feasibility(req.financial_goals, req.incomes, req.expenses)
        return {"user_id": req.user_id, "goal_feasibility": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── 3. Portfolio Alignment ──────────────────────────────────────────────

@router.post("/portfolio-alignment")
def portfolio_alignment(req: AnalyticsRequest):
    """
    Checks alignment between declared risk_profile and actual asset allocation.
    Flags behavioral inconsistencies.
    Pure math — no LLM.
    """
    try:
        result = check_portfolio_alignment(req.risk_profile or "conservative", req.assets)
        return {"user_id": req.user_id, "portfolio_alignment": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
