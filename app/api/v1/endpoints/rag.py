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

class RetrievalResponse(BaseModel):
    sources: List[str]
    chunks: List[str]
    rewritten_query: Optional[str] = None

@router.post("/retrieve", response_model=RetrievalResponse)
async def retrieve_context(request: QueryRequest):
    """
    Endpoint to retrieve relevant context chunks. Handles follow-ups via history.
    """
    try:
        result = await pipeline.retrieve_context(request.query, request.history)
        return RetrievalResponse(
            sources=result["sources"],
            chunks=result["chunks"],
            rewritten_query=result["search_query"] if result["search_query"] != request.query else None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ask", response_model=QueryResponse)
async def ask_question(request: QueryRequest):
    """
    Endpoint to ask a question. Handles follow-ups via history.
    """
    try:
        result = await pipeline.run(request.query, request.history)
        return QueryResponse(
            answer=result["answer"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
