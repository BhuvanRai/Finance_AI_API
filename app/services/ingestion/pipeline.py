import os
from typing import List, Dict, Any
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.services.embedding.gemini import GeminiEmbeddingService
from app.infrastructure.vectordb.chroma import ChromaClient
from loguru import logger

class IngestionService:
    def __init__(self):
        self.embedding_service = GeminiEmbeddingService()
        self.vector_db = ChromaClient()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100,
            separators=["\n\n", "\n", " ", ""]
        )

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from a PDF file."""
        logger.info(f"Extracting text from {pdf_path}")
        try:
            reader = PdfReader(pdf_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            logger.error(f"Failed to extract text from {pdf_path}: {e}")
            return ""

    async def ingest_file(self, file_path: str, source_name: str):
        """Process a single file and add its content to the vector database."""
        text = ""
        if file_path.endswith(".pdf"):
            text = self.extract_text_from_pdf(file_path)
        elif file_path.endswith(".txt"):
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
        else:
            logger.warning(f"Skipping unsupported file type: {file_path}")
            return

        if not text.strip():
            logger.warning(f"No text extracted from {file_path}, skipping.")
            return

        chunks = self.text_splitter.split_text(text)
        logger.info(f"Split {source_name} into {len(chunks)} chunks")

        # Prepare for vector DB
        ids = [f"{source_name}_{i}" for i in range(len(chunks))]
        vectors = await self.embedding_service.embed_documents(chunks)
        metadatas = [{"text": chunk, "source": source_name} for chunk in chunks]

        # Add to Pinecone
        self.vector_db.add_documents(ids, vectors, metadatas)
        logger.info(f"Successfully ingested {source_name}")

    async def ingest_directory(self, directory_path: str):
        """Ingest all PDFs in a directory."""
        for filename in os.listdir(directory_path):
            if filename.endswith((".pdf", ".txt")):
                path = os.path.join(directory_path, filename)
                await self.ingest_file(path, filename)

if __name__ == "__main__":
    import asyncio
    async def run_test():
        service = IngestionService()
        await service.ingest_directory("data/raw")
    
    # asyncio.run(run_test())
