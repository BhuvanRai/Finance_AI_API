from fastapi import APIRouter, HTTPException
from typing import List

from app.models.user_schema import (
    UserBasedRetrievalRequest,
    UserBasedRetrievalResponse,
    IncomeItem,
    ExpenseItem,
    AssetItem,
    LiabilityItem,
    InsuranceItem,
)
from app.services.rag.pipeline import RAGPipeline

router = APIRouter()
pipeline = RAGPipeline()


# ─────────────────────────────────────────────
# Profile Context Builder (deterministic)
# ─────────────────────────────────────────────

def _build_profile_context(req: UserBasedRetrievalRequest) -> str:
    """
    Converts the user's financial profile into a structured plain-text block
    to be injected into the RAG prompt for personalized answers.
    """
    u = req.user

    # Income summary
    active_income = [i for i in req.income if i.is_active]
    total_income = sum(i.monthly_amount for i in active_income)
    income_sources = ", ".join(set(i.source_type for i in active_income)) or "None"

    # Expense summary
    total_expense = sum(e.monthly_amount for e in req.expense)
    savings = total_income - total_expense
    savings_rate = (savings / total_income * 100) if total_income > 0 else 0

    # Asset summary
    asset_types = ", ".join(set(a.type for a in req.asset)) or "None"
    total_asset_value = sum(a.current_value for a in req.asset)

    # Liability summary
    total_emi = sum(l.emi_amount for l in req.liability)
    debt_ratio = (total_emi / total_income * 100) if total_income > 0 else 0

    # Insurance summary
    term_coverage = sum(
        i.coverage_amount for i in req.insurance if i.type == "term"
    )

    # Goals summary
    active_goals = [g for g in req.financial_goal if g.status == "active"]
    goal_types = ", ".join(set(g.goal_type for g in active_goals)) or "None"

    # Health score
    score_text = ""
    if req.financial_health_score:
        score_text = f"\n  Financial Health Score: {req.financial_health_score.score}/100"

    return f"""
=== USER FINANCIAL PROFILE ===
Name: {u.name} | Age: {u.age} | Gender: {u.gender}
Marital Status: {u.marital_status} | Dependents: {u.dependents}
Employment: {u.employment_type} | Annual Income: ₹{u.annual_income:,.0f}
Risk Profile: {u.risk_profile.upper()}
Location: {u.city}, {u.state}, {u.country}
{score_text}

=== FINANCIAL SNAPSHOT ===
Monthly Income : ₹{total_income:,.0f} ({income_sources})
Monthly Expenses: ₹{total_expense:,.0f}
Monthly Savings : ₹{savings:,.0f} ({savings_rate:.1f}% rate)
Total EMI       : ₹{total_emi:,.0f} ({debt_ratio:.1f}% debt ratio)
Total Assets    : ₹{total_asset_value:,.0f} ({asset_types})
Term Coverage   : ₹{term_coverage:,.0f}
Active Goals    : {goal_types}
==============================
""".strip()


# (Removed _build_profile_snapshot as history compressor no longer stores profile data)


# ─────────────────────────────────────────────
# History Parser
# ─────────────────────────────────────────────

def _parse_history_turns(history_str: str) -> List[dict]:
    """Convert compressed history string ([Q]/[A] format) into message dicts."""
    turns = []
    if not history_str:
        return turns
    lines = history_str.strip().split("\n")
    i = 0
    while i < len(lines):
        if lines[i].startswith("[Q]:"):
            q = lines[i][4:].strip()
            a = ""
            if i + 1 < len(lines) and lines[i + 1].startswith("[A]:"):
                a = lines[i + 1][4:].strip()
                i += 1
            turns.append({"role": "user", "content": q})
            if a:
                turns.append({"role": "assistant", "content": a})
        i += 1
    return turns


# ─────────────────────────────────────────────
# Endpoint
# ─────────────────────────────────────────────

@router.post("/", response_model=UserBasedRetrievalResponse)
async def user_based_retrieval(request: UserBasedRetrievalRequest):
    """
    Personalized RAG endpoint.

    Accepts the user's full financial profile + optional previous history,
    retrieves relevant regulatory/financial context, generates a personalized answer,
    and returns a compressed history for persistence in your database.

    Behaviours:
    - Relevant chunks found  → cited, personalized answer with [CHUNK X]
    - No relevant chunks     → LLM knowledge fallback with profile-aware advice + disclaimer
    - Off-topic question     → polite decline
    """
    try:
        # 1. Build structured user profile context
        profile_context = _build_profile_context(request)

        # 2. Parse previous conversation history
        history_turns = _parse_history_turns(request.history or "")

        # 3. Retrieve context from ChromaDB
        #    (handles follow-up contextualization + query augmentation internally)
        retrieval_result = await pipeline.retrieve_context(
            request.query,
            history_turns if history_turns else None,
        )

        # 4. Generate a profile-aware, personalized answer
        #    Note: We pass the ORIGINAL query (not any enriched prompt) so the LLM
        #    sees what the user actually asked. Profile context is injected separately.
        answer = await pipeline.llm_service.generate_answer_with_profile(
            query=request.query,
            chunks=retrieval_result["chunks"],
            distances=retrieval_result["distances"],
            profile_context=profile_context,
            history=request.history,
        )

        # 5. Build new compressed history log
        new_history = await pipeline.llm_service.compress_history(
            previous_history=request.history or "",
            query=request.query,   # store original user question, not the augmented one
            answer=answer,
        )

        return UserBasedRetrievalResponse(answer=answer, history=new_history)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
