from fastapi import APIRouter, HTTPException
from typing import List, Optional
from app.models.score_schema import (
    CamelModel, AssetItem, LiabilityItem, IncomeItem,
    ExpenseItem, FinancialGoalItem, UserProfile
)
from datetime import date
from app.services.engines.net_worth import compute_net_worth
from app.services.engines.goal_engine import compute_goal_feasibility
from app.services.engines.portfolio_engine import check_portfolio_alignment

router = APIRouter()


# ── Shared request models ────────────────────────────────────────────────

class NetWorthRequest(CamelModel):
    """Backend sends: { userId, assets, liabilities }"""
    user_id: Optional[str] = "anonymous"
    assets: List[AssetItem] = []
    liabilities: List[LiabilityItem] = []


class GoalFeasibilityRequest(CamelModel):
    """Backend sends: { userId, incomes, expenses, financialGoals }"""
    user_id: Optional[str] = "anonymous"
    incomes: List[IncomeItem] = []
    expenses: List[ExpenseItem] = []
    financial_goals: List[FinancialGoalItem] = []  # camelCase: financialGoals


class _GoalItemAdapter:
    """Adapter so goal_engine.py receives objects with the right attribute names."""
    def __init__(self, g: FinancialGoalItem):
        self.goal_type = g.goal_type
        self.target_amount = g.target_amount or 0.0
        self.target_date = date.fromisoformat(g.target_date) if g.target_date else None
        self.priority_level = g.priority_level
        self.inflation_rate = g.inflation_rate or 6.0
        self.current_savings_for_goal = g.current_savings_for_goal or 0.0
        self.status = g.status or "active"


class PortfolioAlignmentRequest(CamelModel):
    """Backend sends: { userId, riskProfile, assets }"""
    user_id: Optional[str] = "anonymous"
    risk_profile: Optional[str] = "conservative"   # camelCase: riskProfile
    assets: List[AssetItem] = []


# ── Endpoints ────────────────────────────────────────────────────────────

@router.post("/net-worth")
def net_worth(req: NetWorthRequest):
    """
    Computes net worth, liquidity ratio, asset allocation %, debt-to-asset ratio.
    Backend: POST { userId, assets, liabilities }
    """
    try:
        result = compute_net_worth(req.assets, req.liabilities)
        return {"user_id": req.user_id, "net_worth_analysis": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/goal-feasibility")
def goal_feasibility(req: GoalFeasibilityRequest):
    """
    Per-goal: required SIP, funding gap, goal risk, feasibility flag.
    Backend: POST { userId, incomes, expenses, financialGoals }
    """
    try:
        # Skip goals with no target_date — cannot compute SIP without a timeline
        adapted_goals = [
            _GoalItemAdapter(g) for g in req.financial_goals
            if g.target_date is not None
        ]
        result = compute_goal_feasibility(adapted_goals, req.incomes, req.expenses)
        return {"user_id": req.user_id, "goal_feasibility": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/portfolio-alignment")
def portfolio_alignment(req: PortfolioAlignmentRequest):
    """
    Checks risk_profile vs actual asset allocation.
    Backend: POST { userId, riskProfile, assets }
    """
    try:
        result = check_portfolio_alignment(req.risk_profile or "conservative", req.assets)
        return {"user_id": req.user_id, "portfolio_alignment": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
