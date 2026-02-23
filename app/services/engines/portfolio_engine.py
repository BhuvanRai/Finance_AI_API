"""
Portfolio Alignment Engine — Pure math, no LLM.
Checks mismatch between declared risk_profile and actual asset allocation.
Flags behavioral inconsistencies.
"""
from typing import List, Dict, Any
from app.models.user_schema import AssetItem

# Expected allocation bands per risk profile
_PROFILE_BANDS: Dict[str, Dict[str, tuple]] = {
    "conservative": {
        "high_risk": (0, 20),    # stock, mutual_fund, crypto
        "medium_risk": (0, 40),  # gold, real_estate
        "low_risk": (40, 100),   # fd
    },
    "moderate": {
        "high_risk": (20, 60),
        "medium_risk": (10, 40),
        "low_risk": (10, 50),
    },
    "aggressive": {
        "high_risk": (50, 100),
        "medium_risk": (0, 40),
        "low_risk": (0, 30),
    },
}

_HIGH_RISK_TYPES = {"stock", "mutual_fund", "crypto"}
_MEDIUM_RISK_TYPES = {"gold", "real_estate"}
_LOW_RISK_TYPES = {"fd"}


def check_portfolio_alignment(
    risk_profile: str,
    assets: List[AssetItem],
) -> Dict[str, Any]:
    profile = risk_profile.lower()
    total_value = sum((a.current_value or 0) for a in assets)

    if total_value == 0:
        return {"error": "No assets provided for alignment check."}

    # Compute actual allocation by bucket
    high_risk_val = sum((a.current_value or 0) for a in assets if (a.type or "") in _HIGH_RISK_TYPES)
    medium_risk_val = sum((a.current_value or 0) for a in assets if (a.type or "") in _MEDIUM_RISK_TYPES)
    low_risk_val = sum((a.current_value or 0) for a in assets if (a.type or "") in _LOW_RISK_TYPES)

    actual = {
        "high_risk_pct": round(high_risk_val / total_value * 100, 1),
        "medium_risk_pct": round(medium_risk_val / total_value * 100, 1),
        "low_risk_pct": round(low_risk_val / total_value * 100, 1),
    }

    bands = _PROFILE_BANDS.get(profile, _PROFILE_BANDS["conservative"])
    flags = []

    # Check high-risk band
    lo, hi = bands["high_risk"]
    if actual["high_risk_pct"] < lo:
        flags.append(f"Under-exposed to high-risk assets ({actual['high_risk_pct']}% vs expected {lo}–{hi}%) for a {profile} profile.")
    elif actual["high_risk_pct"] > hi:
        flags.append(f"Over-exposed to high-risk assets ({actual['high_risk_pct']}% vs expected {lo}–{hi}%) for a {profile} profile.")

    # Check low-risk band
    lo, hi = bands["low_risk"]
    if actual["low_risk_pct"] > hi:
        flags.append(f"Over-concentrated in low-risk assets ({actual['low_risk_pct']}%) — typical for defensive investors, not {profile}.")

    # Crypto-specific flag for conservative
    crypto_val = sum((a.current_value or 0) for a in assets if (a.type or "") == "crypto")
    crypto_pct = round(crypto_val / total_value * 100, 1)
    if profile == "conservative" and crypto_pct > 5:
        flags.append(f"Conservative profile holding {crypto_pct}% crypto — high behavioral inconsistency.")

    alignment = "ALIGNED" if not flags else "MISALIGNED"

    return {
        "risk_profile": profile,
        "actual_allocation": actual,
        "expected_bands": {
            k: {"min": v[0], "max": v[1]} for k, v in bands.items()
        },
        "alignment_status": alignment,
        "flags": flags,
        "recommendation": (
            "Your portfolio matches your declared risk tolerance."
            if alignment == "ALIGNED"
            else "Consider rebalancing to align with your risk profile."
        ),
    }
