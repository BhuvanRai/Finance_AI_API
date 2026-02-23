from fastapi import APIRouter, HTTPException
from typing import List, Optional
from app.models.score_schema import CamelModel, IncomeItem, ExpenseItem, AssetItem, LiabilityItem
from app.services.engines.stress_engine import run_stress_test

router = APIRouter()


class StressTestRequest(CamelModel):
    """Backend sends: { userId, incomes, expenses, assets, liabilities }"""
    user_id: Optional[str] = "anonymous"
    incomes: List[IncomeItem] = []
    expenses: List[ExpenseItem] = []
    assets: List[AssetItem] = []
    liabilities: List[LiabilityItem] = []


@router.post("/stress-test")
def stress_test(req: StressTestRequest):
    """
    Simulates 3 scenarios: Recession, Job Loss, Rate Hike.
    Backend: POST { userId, incomes, expenses, assets, liabilities }
    Pure math — no LLM.
    """
    try:
        result = run_stress_test(req.incomes, req.expenses, req.assets, req.liabilities)
        return {"user_id": req.user_id, "stress_test": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
