import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
from app.core.config import settings
from loguru import logger

class ChromaClient:
    def __init__(self):
        self.persist_directory = settings.CHROMA_PERSIST_DIRECTORY
        self.collection_name = settings.CHROMA_COLLECTION_NAME
        
        # Ensure directory exists
        import os
        if not os.path.exists(self.persist_directory):
            os.makedirs(self.persist_directory)
            
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        self.collection = self.client.get_or_create_collection(name=self.collection_name)
        logger.info(f"Initialized ChromaDB at {self.persist_directory}")

    def add_documents(self, ids: List[str], vectors: List[List[float]], metadatas: List[Dict[str, Any]]):
        """Add documents to the collection."""
        self.collection.add(
            ids=ids,
            embeddings=vectors,
            metadatas=metadatas
        )
        logger.info(f"Added {len(ids)} documents to ChromaDB")

    def query(self, query_vector: List[float], top_k: int = 5) -> Dict[str, Any]:
        """Query the collection."""
        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=top_k
        )
        return results

    def delete_collection(self):
        """Delete the collection."""
        self.client.delete_collection(self.collection_name)
        logger.warning(f"Deleted ChromaDB collection: {self.collection_name}")
