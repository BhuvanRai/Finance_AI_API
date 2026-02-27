from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict

from app.services.rag.pipeline import RAGPipeline

router = APIRouter()
pipeline = RAGPipeline()


class QueryRequest(BaseModel):
    query: str
    history: Optional[List[Dict[str, str]]] = []


class QueryResponse(BaseModel):
    answer: str
    sources: List[str] = []
    rewritten_query: Optional[str] = None


class RetrievalResponse(BaseModel):
    sources: List[str]
    chunks: List[str]
    rewritten_query: Optional[str] = None


@router.post("/retrieve", response_model=RetrievalResponse)
async def retrieve_context(request: QueryRequest):
    """
    Retrieve relevant context chunks for a query.
    Handles follow-ups via history and augments queries for better recall.
    """
    try:
        result = await pipeline.retrieve_context(request.query, request.history or None)
        return RetrievalResponse(
            sources=result["sources"],
            chunks=result["chunks"],
            rewritten_query=(
                result["search_query"] if result["search_query"] != request.query else None
            ),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ask", response_model=QueryResponse)
async def ask_question(request: QueryRequest):
    """
    Ask a financial question. Returns an answer with citations, source documents,
    and the rewritten/augmented query used for retrieval.

    Behaviors:
    - Relevant finance question + chunks → cited answer with [CHUNK X] references
    - Relevant finance question + no chunks → LLM knowledge fallback with disclaimer
    - Off-topic question → polite decline message
    """
    try:
        result = await pipeline.run(request.query, request.history or None)
        return QueryResponse(
            answer=result["answer"],
            sources=result["sources"],
            rewritten_query=result["rewritten_query"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
