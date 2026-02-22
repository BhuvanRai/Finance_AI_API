import google.generativeai as genai
from typing import List
from app.services.embedding.base import EmbeddingService
from app.core.config import settings

class GeminiEmbeddingService(EmbeddingService):
    def __init__(self, api_key: str = settings.GEMINI_API_KEY):
        genai.configure(api_key=api_key)
        self.model = "models/gemini-embedding-001"

    async def embed_text(self, text: str) -> List[float]:
        result = genai.embed_content(
            model=self.model,
            content=text,
            task_type="retrieval_query",
        )
        return result["embedding"]

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        import asyncio
        embeddings = []
        for i, text in enumerate(texts):
            from loguru import logger
            logger.info(f"Embedding chunk {i+1}/{len(texts)}...")
            result = genai.embed_content(
                model=self.model,
                content=text,
                task_type="retrieval_document",
            )
            embeddings.append(result["embedding"])
            # Small delay to respect rate limits (Safe Tier)
            await asyncio.sleep(1)
        return embeddings

