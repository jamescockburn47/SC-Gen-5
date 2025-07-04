"""Document store for managing and retrieving legal documents."""

import os
import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime
import mimetypes
import tiktoken

from .ocr import OCREngine
from .vector_store import VectorStore

logger = logging.getLogger(__name__)


class DocStore:
    """Document store with OCR, chunking, and vector storage capabilities."""

    def __init__(
        self,
        data_dir: str = "./data",
        vector_db_path: str = "./data/vector_db", 
        metadata_path: str = "./data/metadata.json",
        chunk_size: int = 400,
        chunk_overlap: int = 80,
        embedding_model: str = "BAAI/bge-base-en-v1.5",
        ocr_engine: str = "tesseract",
        ocr_language: str = "eng",
    ) -> None:
        """Initialize document store.
        
        Args:
            data_dir: Base data directory
            vector_db_path: Path for vector database
            metadata_path: Path for document metadata JSON
            chunk_size: Text chunk size in tokens
            chunk_overlap: Overlap between chunks in tokens
            embedding_model: Sentence transformer model name
            ocr_engine: OCR engine ('tesseract' or 'paddleocr')
            ocr_language: OCR language code
        """
        self.data_dir = Path(data_dir)
        self.vector_db_path = Path(vector_db_path)
        self.metadata_path = Path(metadata_path)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Create directories
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.vector_db_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.ocr_engine = OCREngine(engine=ocr_engine, language=ocr_language)
        self.vector_store = VectorStore(
            embedding_model=embedding_model,
            index_path=str(self.vector_db_path)
        )
        
        # Initialize tokenizer for chunking
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        # Load document metadata
        self.documents: Dict[str, Dict[str, Any]] = {}
        self._load_metadata()
        
        logger.info(f"DocStore initialized with {len(self.documents)} documents")

    def add_document(
        self, 
        file_bytes: bytes, 
        filename: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Add a document to the store.
        
        Args:
            file_bytes: Document file content as bytes
            filename: Original filename
            metadata: Additional metadata for the document
            
        Returns:
            Document ID (hash-based)
        """
        # Generate document ID from content hash
        content_hash = hashlib.sha256(file_bytes).hexdigest()
        doc_id = f"doc_{content_hash[:16]}"
        
        # Check if document already exists
        if doc_id in self.documents:
            logger.info(f"Document {doc_id} already exists, skipping")
            return doc_id
            
        logger.info(f"Processing document: {filename}")
        
        try:
            # Extract text using OCR
            text_content, ocr_metadata = self.ocr_engine.extract_text(file_bytes, filename)
            
            if not text_content.strip():
                raise ValueError(f"No text extracted from {filename}")
            
            # Assess text quality
            quality_score = self._assess_text_quality(text_content)
            ocr_metadata["quality_score"] = quality_score
            
            if quality_score < 0.3:
                logger.warning(f"Poor OCR quality detected in {filename} (score: {quality_score:.2f})")
                ocr_metadata["quality_warning"] = "Poor OCR quality - analysis may be unreliable"
            
            # Chunk the text
            chunks = self._chunk_text(text_content)
            logger.info(f"Created {len(chunks)} chunks from {filename}")
            
            # Create chunk metadata
            chunk_metadatas = []
            for i, chunk in enumerate(chunks):
                chunk_metadata = {
                    "doc_id": doc_id,
                    "chunk_id": f"{doc_id}_chunk_{i:04d}",
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "filename": filename,
                    "content_hash": content_hash,
                    "created_at": datetime.now().isoformat(),
                    "chunk_length": len(chunk),
                    **ocr_metadata,
                    **(metadata or {})
                }
                chunk_metadatas.append(chunk_metadata)
            
            # Add to vector store
            chunk_ids = self.vector_store.add_embeddings(chunks, chunk_metadatas)
            
            # CRITICAL: Save vector store to persist embeddings
            self.vector_store.save_index()
            logger.info(f"Vector store saved with {len(chunk_ids)} new embeddings")
            
            # Store document metadata
            doc_metadata = {
                "doc_id": doc_id,
                "filename": filename,
                "content_hash": content_hash,
                "file_size": len(file_bytes),
                "text_length": len(text_content),
                "num_chunks": len(chunks),
                "chunk_ids": chunk_ids,
                "created_at": datetime.now().isoformat(),
                "extraction_method": ocr_metadata.get("extraction_method", "unknown"),
                "quality_score": ocr_metadata.get("quality_score", None),
                "pages": ocr_metadata.get("pages", None),
                **ocr_metadata,
                **(metadata or {})
            }
            
            self.documents[doc_id] = doc_metadata
            self._save_metadata()
            
            # Optionally save original file
            self._save_original_file(file_bytes, filename, doc_id)
            
            logger.info(f"Successfully added document {doc_id}")
            return doc_id
            
        except Exception as e:
            logger.error(f"Failed to add document {filename}: {e}")
            raise

    def search(
        self, 
        query: str, 
        k: int = 6,
        search_k: int = 18,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for relevant document chunks.
        
        Args:
            query: Search query
            k: Number of final results to return  
            search_k: Number of candidates to retrieve before filtering
            filter_metadata: Optional metadata filters
            
        Returns:
            List of relevant chunk dictionaries
        """
        # Search vector store
        results = self.vector_store.search(
            query=query,
            k=search_k,
            filter_metadata=filter_metadata
        )
        
        # Take top k results
        return results[:k]

    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get document metadata by ID."""
        doc = self.documents.get(doc_id)
        if doc:
            doc.setdefault("extraction_method", doc.get("extraction_method", "unknown"))
            doc.setdefault("quality_score", doc.get("quality_score", None))
            doc.setdefault("pages", doc.get("pages", None))
        return doc

    def get_document_chunks(self, doc_id: str) -> List[Dict[str, Any]]:
        """Get all chunks for a document."""
        doc = self.get_document(doc_id)
        if not doc:
            return []
            
        chunks = []
        for chunk_id in doc.get("chunk_ids", []):
            chunk = self.vector_store.get_by_id(chunk_id)
            if chunk:
                chunks.append(chunk)
                
        return chunks

    def delete_document(self, doc_id: str) -> bool:
        """Delete a document and its chunks."""
        if doc_id not in self.documents:
            return False
            
        doc = self.documents[doc_id]
        
        # Remove chunks from vector store
        for chunk_id in doc.get("chunk_ids", []):
            self.vector_store.remove_by_id(chunk_id)
        
        # CRITICAL: Save vector store after deletion
        self.vector_store.save_index()
        logger.info(f"Vector store saved after removing {len(doc.get('chunk_ids', []))} chunks")
        
        # Remove document metadata
        del self.documents[doc_id]
        self._save_metadata()
        
        # Remove original file if it exists
        original_file = self.data_dir / "uploads" / f"{doc_id}_{doc['filename']}"
        if original_file.exists():
            original_file.unlink()
            
        logger.info(f"Deleted document {doc_id}")
        return True

    def list_documents(self) -> List[Dict[str, Any]]:
        """List all documents."""
        docs = list(self.documents.values())
        for doc in docs:
            doc.setdefault("extraction_method", doc.get("extraction_method", "unknown"))
            doc.setdefault("quality_score", doc.get("quality_score", None))
            doc.setdefault("pages", doc.get("pages", None))
        return docs

    def get_stats(self) -> Dict[str, Any]:
        """Get document store statistics."""
        total_chunks = sum(doc.get("num_chunks", 0) for doc in self.documents.values())
        total_text_length = sum(doc.get("text_length", 0) for doc in self.documents.values())
        
        vector_stats = self.vector_store.get_stats()
        
        return {
            "total_documents": len(self.documents),
            "total_chunks": total_chunks,
            "total_text_length": total_text_length,
            "vector_store": vector_stats,
            "data_dir": str(self.data_dir),
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
        }

    def _chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks."""
        # Tokenize the text
        tokens = self.tokenizer.encode(text)
        
        if len(tokens) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(tokens):
            # Get chunk tokens
            end = min(start + self.chunk_size, len(tokens))
            chunk_tokens = tokens[start:end]
            
            # Decode back to text
            chunk_text = self.tokenizer.decode(chunk_tokens)
            chunks.append(chunk_text.strip())
            
            # Move start forward (with overlap)
            if end >= len(tokens):
                break
            start = end - self.chunk_overlap
            
        return chunks

    def _load_metadata(self) -> None:
        """Load document metadata from disk."""
        if self.metadata_path.exists():
            try:
                with open(self.metadata_path, "r", encoding="utf-8") as f:
                    self.documents = json.load(f)
                logger.info(f"Loaded metadata for {len(self.documents)} documents")
            except Exception as e:
                logger.error(f"Failed to load metadata: {e}")
                self.documents = {}
        else:
            self.documents = {}

    def _save_metadata(self) -> None:
        """Save document metadata to disk."""
        try:
            with open(self.metadata_path, "w", encoding="utf-8") as f:
                json.dump(self.documents, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")

    def _save_original_file(self, file_bytes: bytes, filename: str, doc_id: str) -> None:
        """Save original file to uploads directory."""
        uploads_dir = self.data_dir / "uploads"
        uploads_dir.mkdir(exist_ok=True)
        
        # Save with doc_id prefix to avoid filename conflicts
        safe_filename = f"{doc_id}_{filename}"
        file_path = uploads_dir / safe_filename
        
        try:
            with open(file_path, "wb") as f:
                f.write(file_bytes)
            logger.debug(f"Saved original file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to save original file: {e}")

    def rebuild_vector_index(self) -> None:
        """Rebuild the vector index from stored documents."""
        logger.info("Rebuilding vector index...")
        
        # Clear existing index
        self.vector_store.clear()
        
        # Re-process all documents
        uploads_dir = self.data_dir / "uploads"
        reprocessed = 0
        
        for doc_id, doc in list(self.documents.items()):
            original_file = uploads_dir / f"{doc_id}_{doc['filename']}"
            
            if original_file.exists():
                try:
                    with open(original_file, "rb") as f:
                        file_bytes = f.read()
                    
                    # Remove old document
                    del self.documents[doc_id]
                    
                    # Re-add document
                    new_doc_id = self.add_document(file_bytes, doc["filename"])
                    reprocessed += 1
                    
                    logger.info(f"Reprocessed document: {doc['filename']}")
                    
                except Exception as e:
                    logger.error(f"Failed to reprocess {doc['filename']}: {e}")
            else:
                logger.warning(f"Original file not found for {doc['filename']}, removing metadata")
                del self.documents[doc_id]
        
        self._save_metadata()
        logger.info(f"Rebuilt vector index with {reprocessed} documents")

    def clear_all(self) -> None:
        """Clear all documents and data."""
        # Clear vector store
        self.vector_store.clear()
        
        # Clear metadata
        self.documents = {}
        self._save_metadata()
        
        # Remove uploaded files
        uploads_dir = self.data_dir / "uploads"
        if uploads_dir.exists():
            for file_path in uploads_dir.iterdir():
                if file_path.is_file():
                    file_path.unlink()
        
        logger.info("Cleared all documents and data")

    def _assess_text_quality(self, text: str) -> float:
        """Assess the quality of extracted text (0.0 = poor, 1.0 = excellent).
        
        Args:
            text: Extracted text to assess
            
        Returns:
            Quality score between 0.0 and 1.0
        """
        if not text or len(text.strip()) < 10:
            return 0.0
        
        # Calculate metrics
        total_chars = len(text)
        alphanumeric = sum(1 for c in text if c.isalnum())
        spaces = text.count(' ')
        newlines = text.count('\n')
        
        # Calculate ratios
        alpha_ratio = alphanumeric / total_chars if total_chars > 0 else 0
        space_ratio = spaces / total_chars if total_chars > 0 else 0
        
        # Check for common OCR artifacts
        artifacts = [
            text.count('§'), text.count('©'), text.count('®'),
            text.count('™'), text.count('°'), text.count('±'),
            len([c for c in text if ord(c) > 127 and not c.isalpha()])  # Non-standard chars
        ]
        artifact_ratio = sum(artifacts) / total_chars if total_chars > 0 else 0
        
        # Count words vs gibberish
        words = text.split()
        if len(words) == 0:
            return 0.0
            
        # Simple heuristic: words with reasonable length and character distribution
        reasonable_words = 0
        for word in words:
            word_clean = ''.join(c for c in word if c.isalnum())
            if 2 <= len(word_clean) <= 20 and sum(1 for c in word_clean if c.isalpha()) / len(word_clean) > 0.7:
                reasonable_words += 1
        
        word_quality = reasonable_words / len(words) if len(words) > 0 else 0
        
        # Combine metrics (weighted)
        quality_score = (
            alpha_ratio * 0.3 +           # 30% - alphabetic content
            word_quality * 0.4 +          # 40% - reasonable words
            min(space_ratio * 10, 1.0) * 0.2 +  # 20% - reasonable spacing
            max(0, 1.0 - artifact_ratio * 5) * 0.1  # 10% - fewer artifacts
        )
        
        return min(1.0, max(0.0, quality_score))

    def get_document_text(self, doc_id: str) -> str:
        """Return the full extracted text for a document by concatenating all its chunks."""
        chunks = self.get_document_chunks(doc_id)
        if not chunks:
            return ""
        return "\n".join(chunk.get("text", "") for chunk in chunks if chunk.get("text"))

    def get_document_file(self, doc_id: str) -> Tuple[bytes, str]:
        """Return the original file bytes and filename for a document."""
        doc = self.get_document(doc_id)
        if not doc:
            raise FileNotFoundError(f"Document {doc_id} not found")
        uploads_dir = self.data_dir / "uploads"
        file_path = uploads_dir / f"{doc_id}_{doc['filename']}"
        if not file_path.exists():
            raise FileNotFoundError(f"Original file for {doc_id} not found")
        with open(file_path, "rb") as f:
            file_bytes = f.read()
        return file_bytes, doc["filename"] 