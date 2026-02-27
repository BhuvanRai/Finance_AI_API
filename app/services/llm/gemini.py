import asyncio
from typing import List, Dict, Optional

import google.generativeai as genai
from loguru import logger

from app.core.config import settings


class GeminiLLMService:
    """
    LLM service backed by Google Gemini.

    Key capabilities:
    - Query augmentation (domain-specific expansion for better vector recall)
    - Follow-up contextualization (rewrites follow-ups as standalone queries)
    - Relevance-aware answer generation:
        • If good chunks exist  → cites them via [CHUNK X]
        • If no/weak chunks but LLM is ≥95% confident → answers from own knowledge with disclaimer
        • If totally off-topic → politely declines
    - Profile-aware answer generation for personalized financial advice
    - Conversation history compression
    """

    # Finance-domain stop-words / signals that indicate an off-topic question
    _FINANCE_KEYWORDS = {
        "tax", "sebi", "rbi", "mutual fund", "sip", "equity", "debt", "nps",
        "ppf", "epf", "insurance", "premium", "investment", "portfolio",
        "dividend", "bond", "stock", "share", "emi", "loan", "mortgage",
        "income", "expense", "savings", "retirement", "pension", "inflation",
        "fd", "fixed deposit", "gold", "real estate", "demat", "kyc",
        "broker", "ipo", "nifty", "sensex", "budget", "finance", "financial",
        "wealth", "asset", "liability", "net worth", "credit", "debit",
        "bank", "interest rate", "return", "yield", "risk", "goal",
        "regulation", "compliance", "itr", "gst", "tds", "section 80c",
        "hra", "gratuity", "pf", "pfms", "amfi", "irda", "irdai",
    }

    def __init__(self, api_key: str = settings.GEMINI_API_KEY):
        genai.configure(api_key=api_key)
        self.model_name = "models/gemini-2.5-flash-lite"
        self.model = genai.GenerativeModel(self.model_name)

    # ─────────────────────────────────────────────────────────────────
    # Internal helpers
    # ─────────────────────────────────────────────────────────────────

    def _is_simple_query(self, query: str) -> bool:
        """Short query with no complex analytical keywords → classified as simple."""
        query_lower = query.lower()
        complex_keywords = [
            "explain", "compare", "analyze", "analyse", "detail", "list",
            "requirement", "process", "difference", "how", "why", "what are",
            "describe", "elaborate", "summarize", "recommend", "should i",
        ]
        if len(query) < 60 and not any(w in query_lower for w in complex_keywords):
            return True
        return False

    def _is_finance_related(self, query: str) -> bool:
        """Heuristic: does the query touch any finance/investment domain keyword?"""
        query_lower = query.lower()
        return any(kw in query_lower for kw in self._FINANCE_KEYWORDS)

    def _compute_context_relevance(self, distances: Optional[List[float]]) -> str:
        """
        Given ChromaDB L2 distances (lower = closer = more relevant), 
        return 'high', 'medium', or 'none'.
        """
        if not distances:
            return "none"
        best = min(distances)
        if best < 0.5:
            return "high"
        if best < 1.2:
            return "medium"
        return "none"

    async def _call_llm(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Robust LLM call with retry on rate-limit."""
        generation_config = {
            "max_output_tokens": max_tokens,
            "temperature": temperature,
        }
        max_retries = 3
        delay = 2
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(prompt, generation_config=generation_config)
                return response.text.strip()
            except Exception as e:
                if ("429" in str(e) or "ResourceExhausted" in str(e)) and attempt < max_retries - 1:
                    logger.warning(f"Rate limit hit. Retrying in {delay}s... ({attempt + 1}/{max_retries})")
                    await asyncio.sleep(delay)
                    delay *= 2
                    continue
                logger.error(f"Gemini LLM error: {e}")
                raise

    # ─────────────────────────────────────────────────────────────────
    # Public methods
    # ─────────────────────────────────────────────────────────────────

    async def augment_query(self, query: str) -> str:
        """
        Augments any standalone financial query with domain-specific expansion.
        This is called BEFORE embedding to improve vector-recall.

        Adds: synonyms, related regulation references, scope clarifications,
        relevant acronyms, and specific Indian financial context when applicable.
        """
        prompt = f"""You are a financial search query optimizer specializing in Indian finance, \
SEBI/RBI regulations, and personal financial planning.

Your task: Expand the user's question into a RICHER search query that will retrieve \
the most relevant documents from a financial knowledge base.

Rules:
1. Keep the original intent INTACT.
2. Add 3-6 related financial terms, regulation names, or concepts (comma-separated).
3. Include relevant Indian regulatory bodies if applicable (SEBI, RBI, IRDAI, AMFI, PFRDA).
4. Add common acronym expansions where helpful (e.g., SIP = Systematic Investment Plan).
5. Output ONLY the expanded query — nothing else, no explanations, no bullet points.

Original Query: {query}

Expanded Query:"""

        try:
            expanded = await self._call_llm(prompt, max_tokens=120, temperature=0.0)
            # Safety: fall back to original if expansion is too short or something went wrong
            if expanded and len(expanded) > len(query):
                logger.debug(f"Query augmented: '{query}' → '{expanded}'")
                return expanded
        except Exception as e:
            logger.warning(f"Query augmentation failed, using original: {e}")
        return query

    async def contextualize_query(self, query: str, history: List[Dict[str, str]]) -> str:
        """
        If history exists, rewrite follow-up as a standalone expanded query (1 combined LLM call).
        If no history, just augment the query (1 LLM call).
        This reduces API calls from 2 to 1 for follow-up queries.
        """
        if not history:
            return await self.augment_query(query)

        history_text = ""
        for turn in history[-3:]:  # last 3 turns only
            role = "User" if turn["role"] == "user" else "Assistant"
            history_text += f"{role}: {turn['content']}\n"

        prompt = f"""You are a financial search query optimizer.
Given this conversation history and a new follow-up question, rewrite the follow-up into a \
STANDALONE question that is fully self-contained AND expand it with relevant financial terms \
to retrieve the best documents from a financial knowledge base.

Rules:
1. Make the question understandable without history.
2. Keep the original intent INTACT.
3. Add 3-6 related financial terms, regulation names, or concepts.
4. Output ONLY the finalized expanded query — nothing else, no explanations.

Conversation History:
{history_text}

Follow-up Question: {query}

Standalone Expanded Query:"""
        try:
            rewritten_expanded = await self._call_llm(prompt, max_tokens=150, temperature=0.0)
            if rewritten_expanded and len(rewritten_expanded) > 5:
                return rewritten_expanded
        except Exception as e:
            logger.warning(f"Contextualize & augment failed, using original: {e}")
            pass
            
        # Fallback if the combined prompt fails
        return query

    async def generate_answer(
        self,
        query: str,
        chunks: List[str],
        distances: Optional[List[float]] = None,
        profile_context: Optional[str] = None,
    ) -> str:
        """
        Generate an answer using retrieved chunks + optional user profile context.

        Behaviour:
        - Good chunks available         → cite them with [CHUNK X]
        - Weak/no chunks + finance topic → use LLM's own knowledge with disclaimer
        - Weak/no chunks + off-topic     → politely decline
        """
        is_simple = self._is_simple_query(query)
        relevance = self._compute_context_relevance(distances)
        is_finance = self._is_finance_related(query)

        # ── Case 1: No/weak chunks ────────────────────────────────
        if not chunks or relevance == "none":
            if not is_finance:
                return (
                    "I'm sorry, I don't have enough information to answer that question. "
                    "I'm specialized in Indian personal finance, investments, and regulatory topics. "
                    "Please ask me something related to finance, investments, insurance, or taxation."
                )
            # Finance topic but nothing in DB — use LLM knowledge with disclaimer
            logger.info("No relevant chunks found; using LLM knowledge fallback for finance query.")
            fallback_prompt = f"""You are a professional Indian Personal Finance and Regulatory Compliance Expert.

The user asked a financial question but no relevant documents were found in the knowledge base.
Answer naturally using your training knowledge ONLY if you are highly confident (>90-95%).
If not sufficiently confident, clearly say so.

IMPORTANT RULES:
- Be accurate, concise, and actionable. Do not mention that no documents were retrieved.
- Do NOT hallucinate regulations or specific numbers you're not sure about.
- If unsure, say: "I don't have enough reliable information to answer this accurately."

{f"User Financial Profile:\\n{profile_context}\\n" if profile_context else ""}

User Question: {query}

Answer:"""
            token_limit = 800 if not is_simple else 200
            return await self._call_llm(fallback_prompt, max_tokens=token_limit, temperature=0.1)

        # ── Case 2: Relevant chunks available ────────────────────
        context_text = ""
        for i, chunk in enumerate(chunks):
            context_text += f"--- [CHUNK {i + 1}] ---\n{chunk}\n\n"

        is_simple = self._is_simple_query(query)
        token_limit = 150 if is_simple else 1500
        conciseness_hint = (
            "BE EXTREMELY CONCISE (max 2 sentences). Answer directly."
            if is_simple
            else "Provide a detailed, well-reasoned, and analytical answer."
        )

        profile_section = ""
        if profile_context:
            profile_section = f"""
=== USER FINANCIAL PROFILE ===
{profile_context}
==============================
"""

        prompt = f"""You are a professional Indian Personal Finance and Regulatory Compliance Expert.
{conciseness_hint}

{profile_section}
INSTRUCTIONS:
1. Answer the user's question naturally using the provided Context Chunks and your own expert knowledge.
2. DO NOT mention or cite the source documents (e.g. do not say "Based on the context" or "According to chunk X") in your answer. Provide a direct, authoritative response.
3. If the context partially answers the question or fails to, and you are highly confident (>90-95%) in the correct answer from your own knowledge, you must provide it.
4. If you do not have enough reliable information to answer properly, say: "I don't have enough reliable information to answer this accurately."
5. NEVER fabricate regulations, numbers, or names.
{"6. Tailor your answer to the user's specific financial numbers (income, savings, risk, assets, goals) shown in the profile above." if profile_context else ""}

Context Chunks for reference:
{context_text}

User Question: {query}

Answer:"""

        temperature = 0.1 if is_simple else 0.4
        return await self._call_llm(prompt, max_tokens=token_limit, temperature=temperature)

    async def generate_answer_with_profile(
        self,
        query: str,
        chunks: List[str],
        distances: Optional[List[float]] = None,
        profile_context: str = "",
        history: Optional[str] = None,
    ) -> str:
        """
        Profile-aware wrapper for the user-based RAG endpoint.
        Builds a self-contained, personalized prompt and delegates to generate_answer.
        """
        # Build the query that incorporates the user's context for best retrieval
        personalized_query = f"{query}\n\n[User context already provided in profile section]"
        return await self.generate_answer(
            query=personalized_query,
            chunks=chunks,
            distances=distances,
            profile_context=profile_context,
        )

    async def compress_history(
        self,
        previous_history: str,
        query: str,
        answer: str,
    ) -> str:
        """
        Creates a rolling history log. Just appends the raw Q&A turn to the previous history.
        This completely eliminates the 1 LLM call used for summarization, saving cost and time.
        """
        # We just keep it simple without any LLM call to save tokens and latency.
        # Ensure we don't store massive amounts of text by taking the first 150 chars of Q and 300 of A.
        clean_q = query[:150].replace('\n', ' ')
        clean_a = answer[:300].replace('\n', ' ')
        raw_turn = f"[Q]: {clean_q}\n[A]: {clean_a}"
        
        if previous_history:
            lines = previous_history.strip().split('\n')
            # Keep the last 16 lines (8 Q&A turns)
            if len(lines) > 16:
                lines = lines[-16:]
            kept_history = "\n".join(lines)
            return f"{kept_history}\n{raw_turn}"
        else:
            return raw_turn
