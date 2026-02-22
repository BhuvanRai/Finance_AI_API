import asyncio
from app.services.ingestion.pipeline import IngestionService
from loguru import logger
from app.core.config import settings

async def main():
    if not settings.GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY not set")
        return
        
    logger.info("🚀 Starting Batch Ingestion")
    service = IngestionService()
    
    # Check if data/raw exists and has files
    raw_dir = "data/raw"
    if not os.path.exists(raw_dir):
        logger.error(f"Directory {raw_dir} does not exist")
        return
        
    files = [f for f in os.listdir(raw_dir) if f.endswith((".pdf", ".txt"))]
    if not files:
        logger.warning("No supported files find in data/raw")
        return
        
    logger.info(f"Found {len(files)} files to ingest: {files}")
    
    await service.ingest_directory(raw_dir)
    logger.info("✅ Batch Ingestion Complete")

if __name__ == "__main__":
    import os
    asyncio.run(main())
