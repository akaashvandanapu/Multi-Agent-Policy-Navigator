"""
ChromaDB vector store for RAG
"""

import os
import warnings
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Suppress ChromaDB telemetry errors
logging.getLogger('chromadb.telemetry').setLevel(logging.ERROR)
logging.getLogger('chromadb.telemetry.product.posthog').setLevel(logging.ERROR)

# Suppress warnings before imports
warnings.filterwarnings('ignore', category=UserWarning)
# Suppress ChromaDB deprecation warning about CHROMA_OPENAI_API_KEY (we use SentenceTransformer, not OpenAI)
warnings.filterwarnings('ignore', category=DeprecationWarning, module='chromadb')
warnings.filterwarnings('ignore', message='.*CHROMA_OPENAI_API_KEY.*')
warnings.filterwarnings('ignore', message='.*legacy embedding function.*')
warnings.filterwarnings('ignore', message='.*collection_configuration.*')
warnings.filterwarnings('ignore', message='.*Direct api_key configuration.*')
warnings.filterwarnings('ignore', message='.*will not be persisted.*')

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from policy_navigator.config.llm_config import get_embedding_model


class VectorStore:
    """ChromaDB vector store for document retrieval"""
    
    def __init__(self, db_path: str = "./chroma_db", collection_name: str = "policy_documents"):
        """
        Initialize vector store
        
        Args:
            db_path: Path to ChromaDB database
            collection_name: Name of the collection
        """
        self.db_path = Path(db_path)
        self.collection_name = collection_name
        embedding_model = get_embedding_model()
        self.embedder = SentenceTransformer(embedding_model)
        
        # Initialize ChromaDB client with telemetry disabled
        # Suppress telemetry errors and deprecation warnings
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', category=DeprecationWarning, module='chromadb')
            warnings.filterwarnings('ignore', category=UserWarning)
            warnings.filterwarnings('ignore', message='.*CHROMA_OPENAI_API_KEY.*')
            warnings.filterwarnings('ignore', message='.*legacy embedding function.*')
            warnings.filterwarnings('ignore', message='.*collection_configuration.*')
            warnings.filterwarnings('ignore', message='.*Direct api_key configuration.*')
            try:
                self.client = chromadb.PersistentClient(
                    path=str(self.db_path),
                    settings=Settings(anonymized_telemetry=False)
                )
            except Exception as e:
                # If there's an error with telemetry, try without explicit settings
                self.client = chromadb.PersistentClient(path=str(self.db_path))
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
    
    def add_documents(self, documents: List[Dict[str, Any]]) -> None:
        """
        Add documents to the vector store
        
        Args:
            documents: List of document chunks with metadata
        """
        if not documents:
            return
        
        # Prepare data for ChromaDB
        ids = []
        texts = []
        metadatas = []
        
        for idx, doc in enumerate(documents):
            doc_id = f"{doc['source']}_{doc['chunk_index']}"
            ids.append(doc_id)
            texts.append(doc['text'])
            metadatas.append({
                'source': doc['source'],
                'category': doc['category'],
                'chunk_index': doc['chunk_index'],
                'total_chunks': doc['total_chunks']
            })
        
        # Generate embeddings
        embeddings = self.embedder.encode(texts, show_progress_bar=True).tolist()
        
        # Add to collection
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )
        
        print(f"Added {len(documents)} document chunks to vector store")
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        category_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents
        
        Args:
            query: Search query
            top_k: Number of results to return
            category_filter: Optional category to filter by
            
        Returns:
            List of similar documents with scores
        """
        # Generate query embedding
        query_embedding = self.embedder.encode([query]).tolist()[0]
        
        # Build where clause for filtering
        where = None
        if category_filter:
            where = {"category": category_filter}
        
        # Search in ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where
        )
        
        # Format results
        formatted_results = []
        if results['documents'] and len(results['documents'][0]) > 0:
            for idx in range(len(results['documents'][0])):
                formatted_results.append({
                    'text': results['documents'][0][idx],
                    'source': results['metadatas'][0][idx]['source'],
                    'category': results['metadatas'][0][idx]['category'],
                    'score': 1 - results['distances'][0][idx]  # Convert distance to similarity
                })
        
        return formatted_results
    
    def get_collection_count(self) -> int:
        """Get total number of documents in collection"""
        return self.collection.count()
    
    def clear_collection(self) -> None:
        """Clear all documents from collection"""
        self.client.delete_collection(name=self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )


# Singleton instance
_vector_store_instance = None


def get_vector_store(db_path: str = "./chroma_db") -> VectorStore:
    """
    Get singleton instance of VectorStore
    
    Args:
        db_path: Path to ChromaDB database
        
    Returns:
        VectorStore instance
    """
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = VectorStore(db_path=db_path)
    return _vector_store_instance

