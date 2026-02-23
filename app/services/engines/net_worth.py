"""
Net Worth Engine — Pure math, no LLM.
Computes: net worth, liquidity ratio, asset allocation %, debt-to-asset ratio.
"""
from typing import List, Dict, Any
from app.models.user_schema import AssetItem, LiabilityItem


def compute_net_worth(
    assets: List[AssetItem],
    liabilities: List[LiabilityItem],
) -> Dict[str, Any]:
    total_assets = sum((a.current_value or 0) for a in assets)
    total_liabilities = sum((l.outstanding_amount or 0) for l in liabilities)
    net_worth = total_assets - total_liabilities

    # Liquidity ratio: high-liquidity assets / total monthly liabilities (EMI)
    liquid_assets = sum((a.current_value or 0) for a in assets if (a.liquidity_level or "") == "high")
    total_emi = sum((l.emi_amount or 0) for l in liabilities)
    liquidity_ratio = round(liquid_assets / total_emi, 2) if total_emi > 0 else None

    # Asset allocation %
    allocation: Dict[str, float] = {}
    if total_assets > 0:
        for asset in assets:
            atype = asset.type or "other"
            allocation[atype] = round(
                allocation.get(atype, 0) + ((asset.current_value or 0) / total_assets) * 100, 2
            )

    # Debt-to-asset ratio
    debt_to_asset = round(total_liabilities / total_assets, 4) if total_assets > 0 else None

    return {
        "total_assets": round(total_assets, 2),
        "total_liabilities": round(total_liabilities, 2),
        "net_worth": round(net_worth, 2),
        "liquid_assets": round(liquid_assets, 2),
        "liquidity_ratio_months": liquidity_ratio,
        "debt_to_asset_ratio": debt_to_asset,
        "asset_allocation_percent": allocation,
    }
