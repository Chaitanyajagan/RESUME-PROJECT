import os
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

from config import CHROMA_PERSIST_DIR, CHROMA_COLLECTION_NAME

class ChromaVectorStore:
    def __init__(self, persist_dir: str = str(CHROMA_PERSIST_DIR), collection_name: str = CHROMA_COLLECTION_NAME):
        self.persist_dir = persist_dir
        self.collection_name = collection_name
        
        # Initialize persistent client
        self.client = chromadb.PersistentClient(path=self.persist_dir)
        
        # Use default ONNX MiniLM embedding function (local, offline, fast)
        self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self.embedding_fn,
            metadata={"description": "EDUKRON ATS Candidate Knowledge Base"}
        )

    def add_candidate_chunks(self, chunks: List[Dict[str, Any]]) -> int:
        """Upsert section chunks into ChromaDB."""
        if not chunks:
            return 0
        
        ids = [c["chunk_id"] for c in chunks]
        documents = [c["text"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]
        
        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        return len(chunks)

    def query(self, query_text: str, n_results: int = 25) -> List[Dict[str, Any]]:
        """
        Perform dense semantic vector retrieval for a Job Description (JD).
        Returns matching chunks with distance scores and metadata.
        """
        count = self.collection.count()
        if count == 0:
            return []
        
        fetch_k = min(n_results, count)
        results = self.collection.query(
            query_texts=[query_text],
            n_results=fetch_k,
            include=["documents", "metadatas", "distances"]
        )
        
        matched_chunks = []
        if results and "documents" in results and results["documents"]:
            docs = results["documents"][0]
            metas = results["metadatas"][0]
            dists = results["distances"][0]
            ids = results["ids"][0]
            
            for doc, meta, dist, chunk_id in zip(docs, metas, dists, ids):
                # Convert distance to similarity score between 0.0 and 1.0
                # Chroma uses L2 distance or cosine distance; normalized similarity:
                similarity = max(0.0, 1.0 - (dist / 2.0))
                matched_chunks.append({
                    "chunk_id": chunk_id,
                    "text": doc,
                    "metadata": meta,
                    "distance": dist,
                    "similarity": round(similarity, 4)
                })
                
        return matched_chunks

    def delete_candidate(self, candidate_id: str):
        """Remove all chunks associated with a candidate."""
        self.collection.delete(where={"candidate_id": candidate_id})

    def count(self) -> int:
        """Total chunks in the vector collection."""
        return self.collection.count()

    def reset_collection(self):
        """Delete and recreate the collection."""
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self.embedding_fn,
            metadata={"description": "EDUKRON ATS Candidate Knowledge Base"}
        )

# Global singleton helper
_vector_store_instance = None

def get_vector_store() -> ChromaVectorStore:
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = ChromaVectorStore()
    return _vector_store_instance
