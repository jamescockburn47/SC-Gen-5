"""Vector store module for embedding storage and retrieval using FAISS."""

import json
import logging
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class VectorStore:
    """FAISS-based vector store for document embeddings."""

    def __init__(
        self,
        embedding_model: str = "BAAI/bge-base-en-v1.5",
        index_path: Optional[str] = None,
        dimension: Optional[int] = None,
    ) -> None:
        """Initialize vector store.
        
        Args:
            embedding_model: Sentence transformer model name
            index_path: Path to save/load FAISS index
            dimension: Embedding dimension (auto-detected if None)
        """
        self.embedding_model_name = embedding_model
        self.index_path = Path(index_path) if index_path else None
        
        # Initialize sentence transformer using memory-optimized approach
        logger.info(f"Loading embedding model: {embedding_model}")
        try:
            # Try to use memory-optimized embedder if available
            from ..rag.v2.memory_optimized_models import get_memory_optimized_manager
            manager = get_memory_optimized_manager()
            self.encoder = manager.load_embedder()
            logger.info("✓ Using memory-optimized embedder")
        except Exception as e:
            logger.warning(f"Memory-optimized embedder unavailable, loading directly: {e}")
            self.encoder = SentenceTransformer(embedding_model, device="cpu")
            logger.info("✓ Using direct embedder loading")
        
        # Get embedding dimension
        if dimension is None:
            # Create a dummy embedding to get dimension
            dummy_embedding = self.encoder.encode(["test"])
            self.dimension = dummy_embedding.shape[1]
        else:
            self.dimension = dimension
            
        logger.info(f"Embedding dimension: {self.dimension}")
        
        # Initialize FAISS index
        self.index: Optional[faiss.Index] = None
        self.metadata: Dict[int, Dict[str, Any]] = {}
        self.next_id = 0
        
        # Load existing index if files exist, otherwise create new
        if self.index_path:
            index_file = self.index_path / "index.faiss"
            if index_file.exists():
                self.load_index()
            else:
                self._create_new_index()
        else:
            self._create_new_index()

    def _create_new_index(self) -> None:
        """Create a new FAISS index."""
        # Use flat L2 index for simplicity and accuracy
        self.index = faiss.IndexFlatL2(self.dimension)
        self.metadata = {}
        self.next_id = 0
        logger.info(f"Created new FAISS index with dimension {self.dimension}")

    def add_embeddings(
        self, 
        texts: List[str], 
        metadatas: List[Dict[str, Any]]
    ) -> List[int]:
        """Add text embeddings to the vector store.
        
        Args:
            texts: List of text chunks to embed
            metadatas: List of metadata dicts for each text chunk
            
        Returns:
            List of assigned IDs for the added embeddings
        """
        if len(texts) != len(metadatas):
            raise ValueError("Number of texts and metadatas must match")
            
        if not texts:
            return []
        
        # Generate embeddings
        logger.info(f"Generating embeddings for {len(texts)} texts")
        embeddings = self.encoder.encode(texts, show_progress_bar=True)
        
        # Ensure embeddings are float32
        embeddings = embeddings.astype(np.float32)
        
        # Add to FAISS index
        self.index.add(embeddings)
        
        # Store metadata
        ids = []
        for i, metadata in enumerate(metadatas):
            doc_id = self.next_id + i
            self.metadata[doc_id] = {
                **metadata,
                "text": texts[i],
                "embedding_model": self.embedding_model_name,
            }
            ids.append(doc_id)
            
        self.next_id += len(texts)
        
        logger.info(f"Added {len(texts)} embeddings to index. Total: {self.index.ntotal}")
        return ids

    def search(
        self, 
        query: str, 
        k: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar documents.
        
        Args:
            query: Search query text
            k: Number of results to return
            filter_metadata: Optional metadata filters
            
        Returns:
            List of dictionaries containing matched documents and scores
        """
        if self.index.ntotal == 0:
            logger.warning("Vector store is empty")
            return []
        
        # Generate query embedding
        query_embedding = self.encoder.encode([query]).astype(np.float32)
        
        # Search FAISS index
        distances, indices = self.index.search(query_embedding, k)
        
        # Convert results to list of dicts
        results = []
        for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
            if idx == -1:  # No more results
                break
                
            if idx in self.metadata:
                result = {
                    "id": int(idx),
                    "distance": float(distance),
                    "score": 1.0 / (1.0 + float(distance)),  # Convert distance to similarity score
                    **self.metadata[idx]
                }
                
                # Apply metadata filters if provided
                if filter_metadata:
                    if self._matches_filter(result, filter_metadata):
                        results.append(result)
                else:
                    results.append(result)
        
        return results

    def _matches_filter(self, result: Dict[str, Any], filter_metadata: Dict[str, Any]) -> bool:
        """Check if result matches metadata filters."""
        for key, value in filter_metadata.items():
            if key not in result:
                return False
            if isinstance(value, list):
                if result[key] not in value:
                    return False
            else:
                if result[key] != value:
                    return False
        return True

    def get_by_id(self, doc_id: int) -> Optional[Dict[str, Any]]:
        """Get document by ID."""
        return self.metadata.get(doc_id)

    def get_all_metadata(self) -> Dict[int, Dict[str, Any]]:
        """Get all stored metadata."""
        return self.metadata.copy()

    def remove_by_id(self, doc_id: int) -> bool:
        """Remove document by ID.
        
        Note: FAISS doesn't support efficient removal, so this only removes metadata.
        For full removal, the index would need to be rebuilt.
        """
        if doc_id in self.metadata:
            del self.metadata[doc_id]
            return True
        return False

    def save_index(self, path: Optional[str] = None) -> None:
        """Save FAISS index and metadata to disk."""
        save_path = Path(path) if path else self.index_path
        
        if not save_path:
            raise ValueError("No save path specified")
            
        save_path.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        index_file = save_path / "index.faiss"
        faiss.write_index(self.index, str(index_file))
        
        # Save metadata
        metadata_file = save_path / "metadata.pkl"
        with open(metadata_file, "wb") as f:
            pickle.dump({
                "metadata": self.metadata,
                "next_id": self.next_id,
                "embedding_model": self.embedding_model_name,
                "dimension": self.dimension,
            }, f)
        
        logger.info(f"Saved vector store to {save_path}")

    def load_index(self, path: Optional[str] = None) -> None:
        """Load FAISS index and metadata from disk."""
        load_path = Path(path) if path else self.index_path
        
        if not load_path or not load_path.exists():
            raise FileNotFoundError(f"Vector store path not found: {load_path}")
            
        # Load FAISS index
        index_file = load_path / "index.faiss"
        if not index_file.exists():
            raise FileNotFoundError(f"FAISS index file not found: {index_file}")
            
        self.index = faiss.read_index(str(index_file))
        
        # Load metadata
        metadata_file = load_path / "metadata.pkl"
        if metadata_file.exists():
            with open(metadata_file, "rb") as f:
                data = pickle.load(f)
                self.metadata = data["metadata"]
                self.next_id = data["next_id"]
                
                # Verify embedding model compatibility
                stored_model = data.get("embedding_model")
                if stored_model != self.embedding_model_name:
                    logger.warning(
                        f"Loaded index was created with {stored_model}, "
                        f"but current model is {self.embedding_model_name}"
                    )
        else:
            logger.warning("No metadata file found, starting with empty metadata")
            self.metadata = {}
            self.next_id = self.index.ntotal
        
        logger.info(f"Loaded vector store from {load_path} with {self.index.ntotal} embeddings")

    def clear(self) -> None:
        """Clear all data from the vector store."""
        self._create_new_index()
        logger.info("Cleared vector store")

    def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics."""
        return {
            "total_embeddings": self.index.ntotal if self.index else 0,
            "embedding_model": self.embedding_model_name,
            "dimension": self.dimension,
            "metadata_count": len(self.metadata),
            "next_id": self.next_id,
        }

    def rebuild_index(self) -> None:
        """Rebuild the FAISS index from stored metadata."""
        if not self.metadata:
            logger.warning("No metadata to rebuild index from")
            return
            
        # Extract texts and metadatas
        texts = []
        metadatas = []
        ids = []
        
        for doc_id, metadata in self.metadata.items():
            if "text" in metadata:
                texts.append(metadata["text"])
                metadatas.append(metadata)
                ids.append(doc_id)
        
        if not texts:
            logger.warning("No texts found in metadata")
            return
            
        # Create new index
        self._create_new_index()
        
        # Re-add all embeddings
        logger.info(f"Rebuilding index with {len(texts)} texts")
        embeddings = self.encoder.encode(texts, show_progress_bar=True)
        embeddings = embeddings.astype(np.float32)
        
        self.index.add(embeddings)
        
        # Restore metadata with original IDs
        self.metadata = {}
        for i, (doc_id, metadata) in enumerate(zip(ids, metadatas)):
            self.metadata[doc_id] = metadata
            
        self.next_id = max(ids) + 1 if ids else 0
        
        logger.info(f"Rebuilt index with {self.index.ntotal} embeddings") 