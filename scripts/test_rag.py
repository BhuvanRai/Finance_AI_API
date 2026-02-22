import asyncio
from app.services.rag.pipeline import RAGPipeline

from app.core.config import settings

async def test_rag():
    print(f"DEBUG: Using API Key: {settings.GEMINI_API_KEY[:5]}...")
    pipeline = RAGPipeline()
    query = "What is the definition of a Beneficial Owner where the customer is a company according to the RBI KYC Directions?"
    print(f"Query: {query}")
    
    try:
        response = await pipeline.run(query)
        print(f"\nResponse:\n{response}")
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_rag())
