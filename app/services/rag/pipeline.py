from typing import Dict, Any, List, Optional
from app.services.embedding.gemini import GeminiEmbeddingService
from app.infrastructure.vectordb.chroma import ChromaClient
from app.services.llm.gemini import GeminiLLMService

class RAGPipeline:
    def __init__(self):
        self.embedding_service = GeminiEmbeddingService()
        self.vector_db = ChromaClient()
        self.llm_service = GeminiLLMService()

    async def retrieve_context(self, query: str, history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """
        Embed query and retrieve top-k documents. Handles follow-ups via history.
        """
        # 1. Contextualize query if history exists
        search_query = query
        if history:
            search_query = await self.llm_service.contextualize_query(query, history)

        # 2. Embed query
        query_vector = await self.embedding_service.embed_text(search_query)
        
        # 3. Retrieve top-k documents
        results = self.vector_db.query(query_vector=query_vector, top_k=5)
        
        # 4. Formulate context and extract sources
        context_parts = []
        extracted_sources = set()
        
        if results and results.get("metadatas") and results["metadatas"]:
            for meta in results["metadatas"][0]:
                if "text" in meta:
                    context_parts.append(meta["text"])
                if "source" in meta:
                    extracted_sources.add(meta["source"])
        
        return {
            "search_query": search_query,
            "context": "\n\n".join(context_parts),
            "sources": list(extracted_sources),
            "chunks": context_parts
        }

    async def run(self, query: str, history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """
        Complete RAG flow with history support: Contextualize -> Retrieve -> Generate.
        """
        # 1. Retrieve (internally handles contextualization)
        retrieval_result = await self.retrieve_context(query, history)
        
        # 2. Call LLM with the list of chunks for citation processing
        answer = await self.llm_service.generate_answer(
            query, 
            retrieval_result["chunks"]
        )
        
        return {
            "answer": answer,
            "sources": retrieval_result["sources"],
            "chunks": retrieval_result["chunks"],
            "rewritten_query": retrieval_result["search_query"] if retrieval_result["search_query"] != query else None
        }

