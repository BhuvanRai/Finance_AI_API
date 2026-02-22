from fastapi import APIRouter, HTTPException
from typing import List, Optional
from app.models.user_schema import IncomeItem, ExpenseItem, AssetItem, LiabilityItem, CamelModel
from app.services.engines.stress_engine import run_stress_test

router = APIRouter()


class StressTestRequest(CamelModel):
    user_id: str
    incomes: List[IncomeItem] = []
    expenses: List[ExpenseItem] = []
    assets: List[AssetItem] = []
    liabilities: List[LiabilityItem] = []


@router.post("/stress-test")
def stress_test(req: StressTestRequest):
    """
    Simulates three financial stress scenarios:
    - Recession: 30% equity crash + 20% income drop
    - Job Loss: primary salary income drops to zero
    - Rate Hike: all loan EMIs increase by 20%

    Returns monthly surplus/shortfall, runway months, and verdict per scenario.
    Pure math — no LLM.
    """
    try:
        result = run_stress_test(req.incomes, req.expenses, req.assets, req.liabilities)
        return {"user_id": req.user_id, "stress_test": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
