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


# ─────────────────────────────────────────────
# Profile Snapshot for History Compression
# ─────────────────────────────────────────────

def _build_profile_snapshot(req: UserBasedRetrievalRequest) -> str:
    """Builds a compact one-paragraph profile string for the LLM history compressor."""
    u = req.user
    active_income = [i for i in req.income if i.is_active]
    total_income = sum(i.monthly_amount for i in active_income)
    total_expense = sum(e.monthly_amount for e in req.expense)
    savings_pct = ((total_income - total_expense) / total_income * 100) if total_income > 0 else 0
    total_emi = sum(l.emi_amount for l in req.liability)
    debt_pct = (total_emi / total_income * 100) if total_income > 0 else 0
    asset_types = ", ".join(set(a.type for a in req.asset)) or "none"
    goals = ", ".join(set(g.goal_type for g in req.financial_goal if g.status == "active")) or "none"
    score = req.financial_health_score.score if req.financial_health_score else "N/A"

    return (
        f"{u.name}, {u.age}y, {u.employment_type}, {u.risk_profile} risk. "
        f"Annual income: ₹{u.annual_income:,.0f}. "
        f"Monthly income: ₹{total_income:,.0f}, savings: {savings_pct:.0f}%, "
        f"debt ratio: {debt_pct:.0f}%, EMI: ₹{total_emi:,.0f}. "
        f"Assets: {asset_types}. Goals: {goals}. "
        f"Health score: {score}/100. Dependents: {u.dependents}."
    )


# ─────────────────────────────────────────────
# Endpoint
# ─────────────────────────────────────────────

@router.post("/", response_model=UserBasedRetrievalResponse)
async def user_based_retrieval(request: UserBasedRetrievalRequest):
    """
    Personalized RAG endpoint.

    Accepts the user's full financial profile + optional previous history,
    retrieves relevant regulatory/financial context, generates an answer,
    and returns a compressed history for persistence in your database.
    """
    try:
        # 1. Build structured user profile context
        profile_context = _build_profile_context(request)

        # 2. Build conversation history for query contextualization
        history_turns = []
        if request.history:
            # Parse previous [Q]/[A] turns into message dicts for contextualize_query
            lines = request.history.strip().split("\n")
            i = 0
            while i < len(lines):
                if lines[i].startswith("[Q]:"):
                    q = lines[i][4:].strip()
                    a = ""
                    if i + 1 < len(lines) and lines[i + 1].startswith("[A]:"):
                        a = lines[i + 1][4:].strip()
                        i += 1
                    history_turns.append({"role": "user", "content": q})
                    if a:
                        history_turns.append({"role": "assistant", "content": a})
                i += 1

        # 3. Retrieve context from ChromaDB (handles follow-ups via history)
        retrieval_result = await pipeline.retrieve_context(
            request.query, history_turns if history_turns else None
        )

        # 4. Build enriched prompt with user profile + retrieved chunks
        chunk_text = ""
        for idx, chunk in enumerate(retrieval_result["chunks"]):
            chunk_text += f"--- [CHUNK {idx + 1}] ---\n{chunk}\n\n"

        enriched_prompt = f"""
You are a professional Personal Financial Advisor AI.

Use the user's financial profile and the retrieved regulatory/knowledge context below to give a precise, personalized answer.

{profile_context}

=== PREVIOUS CONTEXT ===
{request.history if request.history else "No previous conversation."}
========================

Context Chunks (cite using [CHUNK X]):
{chunk_text}

User Question: {request.query}

Instructions:
- Tailor your answer using the user's specific financial numbers (income, savings, risk profile, assets, goals).
- Cite relevant chunks with [CHUNK X].
- Be concise and actionable.

Answer:
"""

        # 5. Generate answer using LLM (via existing service)
        answer = await pipeline.llm_service.generate_answer(
            enriched_prompt,
            retrieval_result["chunks"]
        )

        # 6. Build new compressed history using LLM
        profile_snapshot = _build_profile_snapshot(request)
        new_history = await pipeline.llm_service.compress_history(
            previous_history=request.history or "",
            query=request.query,
            answer=answer,
            profile_snapshot=profile_snapshot,
        )

        return UserBasedRetrievalResponse(answer=answer, history=new_history)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
