from typing import Dict, Any, List, Optional
from app.services.embedding.gemini import GeminiEmbeddingService
from app.infrastructure.vectordb.chroma import ChromaClient
from app.services.llm.gemini import GeminiLLMService


class RAGPipeline:
    def __init__(self):
        self.embedding_service = GeminiEmbeddingService()
        self.vector_db = ChromaClient()
        self.llm_service = GeminiLLMService()

    async def retrieve_context(
        self,
        query: str,
        history: Optional[List[Dict[str, str]]] = None,
        augment: bool = True,
    ) -> Dict[str, Any]:
        """
        Full retrieval step:
          1. Contextualize follow-up queries (via history)
          2. Augment the query with domain-specific expansion (better recall)
          3. Embed the augmented query
          4. Retrieve top-k documents from ChromaDB
          5. Return chunks, sources, distances, and the augmented search query
        """
        # 1. Contextualize + augment
        if history:
            # contextualize_query internally calls augment_query as the second stage
            search_query = await self.llm_service.contextualize_query(query, history)
        elif augment:
            search_query = await self.llm_service.augment_query(query)
        else:
            search_query = query

        # 2. Embed the (augmented) query
        query_vector = await self.embedding_service.embed_text(search_query)

        # 3. Retrieve top-k with distances
        results = self.vector_db.query(query_vector=query_vector, top_k=7)

        # 4. Extract chunks, sources, and distances
        context_parts: List[str] = []
        extracted_sources: set = set()
        distances: List[float] = []

        if results:
            # Distances (L2) — lower = more relevant
            raw_distances = results.get("distances")
            if raw_distances and raw_distances[0]:
                distances = raw_distances[0]

            metadatas = results.get("metadatas")
            if metadatas and metadatas[0]:
                for meta in metadatas[0]:
                    if "text" in meta:
                        context_parts.append(meta["text"])
                    if "source" in meta:
                        extracted_sources.add(meta["source"])

        return {
            "search_query": search_query,
            "context": "\n\n".join(context_parts),
            "sources": list(extracted_sources),
            "chunks": context_parts,
            "distances": distances,
        }

    async def run(
        self,
        query: str,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Complete RAG flow:
          Augment → Retrieve → Generate (with relevance-aware fallback)
        """
        # 1. Retrieve (handles contextualization + augmentation internally)
        retrieval_result = await self.retrieve_context(query, history)

        # 2. Generate answer (passes distances so LLM can judge relevance)
        answer = await self.llm_service.generate_answer(
            query=query,  # pass the ORIGINAL query, not the augmented one
            chunks=retrieval_result["chunks"],
            distances=retrieval_result["distances"],
        )

        return {
            "answer": answer,
            "sources": retrieval_result["sources"],
            "chunks": retrieval_result["chunks"],
            "distances": retrieval_result["distances"],
            "rewritten_query": (
                retrieval_result["search_query"]
                if retrieval_result["search_query"] != query
                else None
            ),
        }
