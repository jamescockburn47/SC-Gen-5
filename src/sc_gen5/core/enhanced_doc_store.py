"""
Enhanced document store with sophisticated multi-granularity processing.
Combines the best features from RAG v1 and RAG v2 for optimal legal document handling.
"""

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
from .advanced_vector_store import AdvancedVectorStore, ChunkType, ChunkConfig

logger = logging.getLogger(__name__)


class EnhancedDocStore:
    """
    Enhanced document store with sophisticated multi-granularity processing.
    
    Features:
    - Multi-granularity chunking (sections, paragraphs, sentences, quotes, clauses, definitions)
    - Legal-specific chunking and retrieval
    - Quality assessment and filtering
    - Context-aware retrieval
    - Hybrid search capabilities
    - Advanced metadata management
    """
    
    def __init__(
        self,
        data_dir: str = "./data",
        vector_db_path: str = "./data/vector_db", 
        metadata_path: str = "./data/metadata.json",
        embedding_model: str = "BAAI/bge-base-en-v1.5",
        ocr_engine: str = "tesseract",
        ocr_language: str = "eng",
        chunk_configs: Optional[Dict[ChunkType, ChunkConfig]] = None,
    ) -> None:
        """Initialize enhanced document store."""
        self.data_dir = Path(data_dir)
        self.vector_db_path = Path(vector_db_path)
        self.metadata_path = Path(metadata_path)
        
        # Create directories
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.vector_db_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.ocr_engine = OCREngine(engine=ocr_engine, language=ocr_language)
        self.vector_store = AdvancedVectorStore(
            embedding_model=embedding_model,
            index_path=str(self.vector_db_path),
            chunk_configs=chunk_configs
        )
        
        # Initialize tokenizer for quality assessment
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        # Load document metadata
        self.documents: Dict[str, Dict[str, Any]] = {}
        self._load_metadata()
        
        logger.info(f"EnhancedDocStore initialized with {len(self.documents)} documents")

    def add_document(
        self, 
        file_bytes: bytes, 
        filename: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Add a document with sophisticated multi-granularity processing."""
        # Generate document ID from content hash
        content_hash = hashlib.sha256(file_bytes).hexdigest()
        doc_id = f"doc_{content_hash[:16]}"
        
        # Check if document already exists
        if doc_id in self.documents:
            logger.info(f"Document {doc_id} already exists, skipping")
            return doc_id
            
        logger.info(f"Processing document: {filename}")
        
        try:
            # Check file type and extract text accordingly
            file_extension = Path(filename).suffix.lower()
            
            if file_extension == '.txt':
                # Handle text files directly
                text_content = file_bytes.decode('utf-8')
                ocr_metadata = {
                    "extraction_method": "direct_text",
                    "quality_score": 1.0,
                    "pages": 1
                }
            else:
                # Extract text using OCR for other file types
                text_content, ocr_metadata = self.ocr_engine.extract_text(file_bytes, filename)
            
            if not text_content.strip():
                raise ValueError(f"No text extracted from {filename}")
            
            # Assess text quality
            quality_score = self._assess_text_quality(text_content)
            ocr_metadata["quality_score"] = quality_score
            
            if quality_score < 0.3:
                logger.warning(f"Poor OCR quality detected in {filename} (score: {quality_score:.2f})")
                ocr_metadata["quality_warning"] = "Poor OCR quality - analysis may be unreliable"
            
            # Process with multi-granularity chunking
            chunk_results = self._process_multi_granularity(text_content, doc_id, filename, metadata, ocr_metadata)
            
            # Store document metadata
            doc_metadata = {
                "doc_id": doc_id,
                "filename": filename,
                "content_hash": content_hash,
                "file_size": len(file_bytes),
                "text_length": len(text_content),
                "quality_score": quality_score,
                "created_at": datetime.now().isoformat(),
                "extraction_method": ocr_metadata.get("extraction_method", "unknown"),
                "pages": ocr_metadata.get("pages", None),
                "chunk_results": chunk_results,
                **ocr_metadata,
                **(metadata or {})
            }
            
            self.documents[doc_id] = doc_metadata
            self._save_metadata()
            
            # Optionally save original file
            self._save_original_file(file_bytes, filename, doc_id)
            
            logger.info(f"Successfully added document {doc_id} with multi-granularity processing")
            return doc_id
            
        except Exception as e:
            logger.error(f"Failed to add document {filename}: {e}")
            raise
    
    def _process_multi_granularity(
        self, 
        text: str, 
        doc_id: str, 
        filename: str,
        metadata: Optional[Dict[str, Any]],
        ocr_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process document with multiple granularity levels."""
        # Define chunk types for legal documents
        chunk_types = [
            ChunkType.SECTION,
            ChunkType.PARAGRAPH, 
            ChunkType.SENTENCE,
            ChunkType.QUOTE,
            ChunkType.CLAUSE,
            ChunkType.DEFINITION
        ]
        
        # Create base metadata
        base_metadata = {
            "doc_id": doc_id,
            "filename": filename,
            "content_hash": hashlib.sha256(text.encode()).hexdigest(),
            "created_at": datetime.now().isoformat(),
            **ocr_metadata,
            **(metadata or {})
        }
        
        # Process with each chunk type
        chunk_results = {}
        for chunk_type in chunk_types:
            try:
                chunk_ids = self.vector_store.add_document(
                    text=text,
                    metadata=base_metadata,
                    chunk_types=[chunk_type]
                )
                
                if chunk_type in chunk_ids:
                    chunk_results[chunk_type.value] = {
                        "chunk_ids": chunk_ids[chunk_type],
                        "count": len(chunk_ids[chunk_type])
                    }
                    
            except Exception as e:
                logger.warning(f"Failed to process {chunk_type.value} chunks: {e}")
                chunk_results[chunk_type.value] = {"chunk_ids": [], "count": 0}
        
        return chunk_results
    
    def search(
        self, 
        query: str, 
        k: int = 10,
        chunk_types: Optional[List[str]] = None,
        filter_metadata: Optional[Dict[str, Any]] = None,
        score_threshold: float = 0.5,
        use_hybrid_search: bool = True
    ) -> List[Dict[str, Any]]:
        """Search with sophisticated multi-granularity retrieval."""
        # Convert string chunk types to enum
        if chunk_types:
            chunk_type_enums = []
            for ct in chunk_types:
                try:
                    chunk_type_enums.append(ChunkType(ct))
                except ValueError:
                    logger.warning(f"Unknown chunk type: {ct}")
        else:
            # Default to most useful chunk types
            chunk_type_enums = [ChunkType.SECTION, ChunkType.PARAGRAPH, ChunkType.SENTENCE]
        
        # Perform search
        results = self.vector_store.search(
            query=query,
            k=k * 2,  # Get more results for better ranking
            chunk_types=chunk_type_enums,
            filter_metadata=filter_metadata,
            score_threshold=score_threshold
        )
        
        # Apply sophisticated ranking
        ranked_results = self._rank_results(results, query)
        
        # Return top k results
        return ranked_results[:k]
    
    def _rank_results(self, results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """Apply sophisticated ranking to search results."""
        for result in results:
            # Calculate additional ranking factors
            relevance_score = self._calculate_relevance_score(result, query)
            quality_score = result.get("quality_score", 0.5)
            chunk_type_weight = self._get_chunk_type_weight(result.get("chunk_type", "sentence"))
            
            # Combine scores
            final_score = (
                result["score"] * 0.4 +
                relevance_score * 0.3 +
                quality_score * 0.2 +
                chunk_type_weight * 0.1
            )
            
            result["final_score"] = final_score
        
        # Sort by final score
        results.sort(key=lambda x: x["final_score"], reverse=True)
        return results
    
    def _calculate_relevance_score(self, result: Dict[str, Any], query: str) -> float:
        """Calculate relevance score based on query-term matching."""
        text = result.get("text", "").lower()
        query_terms = query.lower().split()
        
        # Count matching terms
        matches = sum(1 for term in query_terms if term in text)
        return min(matches / len(query_terms), 1.0)
    
    def _get_chunk_type_weight(self, chunk_type: str) -> float:
        """Get weight for different chunk types."""
        weights = {
            "section": 1.0,      # Highest weight for sections
            "paragraph": 0.9,     # High weight for paragraphs
            "clause": 0.8,        # Good weight for legal clauses
            "definition": 0.7,    # Medium weight for definitions
            "quote": 0.6,         # Lower weight for quotes
            "sentence": 0.5       # Lowest weight for sentences
        }
        return weights.get(chunk_type, 0.5)
    
    def search_by_granularity(
        self, 
        query: str, 
        granularity: str,
        k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search within a specific granularity level."""
        try:
            chunk_type = ChunkType(granularity)
        except ValueError:
            logger.error(f"Unknown granularity: {granularity}")
            return []
        
        results = self.vector_store.search(
            query=query,
            k=k,
            chunk_types=[chunk_type],
            filter_metadata=filter_metadata
        )
        
        return results
    
    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get document metadata by ID."""
        return self.documents.get(doc_id)
    
    def get_document_chunks(self, doc_id: str, chunk_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all chunks for a document, optionally filtered by chunk type."""
        doc = self.documents.get(doc_id)
        if not doc:
            return []
        
        # Get chunk IDs from document metadata
        chunk_results = doc.get("chunk_results", {})
        
        if chunk_type:
            # Get chunks for specific type
            if chunk_type in chunk_results:
                chunk_ids = chunk_results[chunk_type]["chunk_ids"]
                return [self.vector_store.get_by_id(cid) for cid in chunk_ids if self.vector_store.get_by_id(cid)]
            else:
                return []
        else:
            # Get all chunks
            all_chunks = []
            for ct, result in chunk_results.items():
                chunk_ids = result["chunk_ids"]
                chunks = [self.vector_store.get_by_id(cid) for cid in chunk_ids if self.vector_store.get_by_id(cid)]
                all_chunks.extend(chunks)
            return all_chunks
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete a document and all its chunks."""
        if doc_id not in self.documents:
            return False
        
        try:
            # Get chunk IDs for all types
            doc = self.documents[doc_id]
            chunk_results = doc.get("chunk_results", {})
            
            # Remove chunks from vector store
            for chunk_type, result in chunk_results.items():
                chunk_ids = result["chunk_ids"]
                for cid in chunk_ids:
                    self.vector_store.remove_by_id(cid)
            
            # Remove document metadata
            del self.documents[doc_id]
            self._save_metadata()
            
            # Remove original file if it exists
            original_file = self.data_dir / "originals" / f"{doc_id}_{doc['filename']}"
            if original_file.exists():
                original_file.unlink()
            
            logger.info(f"Successfully deleted document {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete document {doc_id}: {e}")
            return False
    
    def list_documents(self) -> List[Dict[str, Any]]:
        """List all documents with summary information."""
        docs = []
        for doc_id, doc in self.documents.items():
            summary = {
                "doc_id": doc_id,
                "filename": doc["filename"],
                "created_at": doc["created_at"],
                "text_length": doc["text_length"],
                "quality_score": doc.get("quality_score", None),
                "chunk_counts": {}
            }
            
            # Add chunk counts for each type
            chunk_results = doc.get("chunk_results", {})
            for chunk_type, result in chunk_results.items():
                summary["chunk_counts"][chunk_type] = result["count"]
            
            docs.append(summary)
        
        return docs
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics about the document store."""
        # Get vector store stats
        vector_stats = self.vector_store.get_stats()
        
        # Calculate document stats
        total_docs = len(self.documents)
        total_chunks = sum(
            sum(result["count"] for result in doc.get("chunk_results", {}).values())
            for doc in self.documents.values()
        )
        total_text_length = sum(doc.get("text_length", 0) for doc in self.documents.values())
        
        # Calculate quality stats
        quality_scores = [doc.get("quality_score", 0) for doc in self.documents.values()]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        return {
            "total_documents": total_docs,
            "total_chunks": total_chunks,
            "total_text_length": total_text_length,
            "average_quality_score": avg_quality,
            "vector_store": vector_stats,
            "data_dir": str(self.data_dir),
            "chunk_types_available": list(ChunkType.__members__.keys())
        }
    
    def _assess_text_quality(self, text: str) -> float:
        """Assess the quality of extracted text."""
        if not text.strip():
            return 0.0
        
        # Calculate various quality metrics
        metrics = {}
        
        # 1. Length-based quality
        text_length = len(text)
        metrics["length"] = min(text_length / 1000, 1.0)  # Normalize to 0-1
        
        # 2. Character diversity (indicates OCR quality)
        unique_chars = len(set(text.lower()))
        total_chars = len(text)
        metrics["diversity"] = unique_chars / max(total_chars, 1)
        
        # 3. Word density (fewer spaces = better OCR)
        word_count = len(text.split())
        char_count = len(text.replace(" ", ""))
        metrics["word_density"] = char_count / max(word_count, 1)
        
        # 4. Legal term presence (indicates legal document)
        legal_terms = [
            "section", "act", "regulation", "clause", "subsection",
            "shall", "may", "must", "hereby", "pursuant", "whereas"
        ]
        legal_term_count = sum(1 for term in legal_terms if term.lower() in text.lower())
        metrics["legal_terms"] = min(legal_term_count / 5, 1.0)
        
        # 5. Punctuation quality (good punctuation = better OCR)
        punctuation_chars = sum(1 for c in text if c in ".,;:!?")
        metrics["punctuation"] = min(punctuation_chars / (len(text) / 100), 1.0)
        
        # Combine metrics with weights
        weights = {
            "length": 0.2,
            "diversity": 0.2,
            "word_density": 0.2,
            "legal_terms": 0.2,
            "punctuation": 0.2
        }
        
        quality_score = sum(metrics[key] * weights[key] for key in weights)
        return min(quality_score, 1.0)
    
    def _load_metadata(self) -> None:
        """Load document metadata from JSON file."""
        if self.metadata_path.exists():
            try:
                with open(self.metadata_path, 'r') as f:
                    self.documents = json.load(f)
                logger.info(f"Loaded metadata for {len(self.documents)} documents")
            except Exception as e:
                logger.error(f"Failed to load metadata: {e}")
                self.documents = {}
        else:
            self.documents = {}
    
    def _save_metadata(self) -> None:
        """Save document metadata to JSON file."""
        try:
            with open(self.metadata_path, 'w') as f:
                json.dump(self.documents, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
    
    def _save_original_file(self, file_bytes: bytes, filename: str, doc_id: str) -> None:
        """Save original file for potential re-processing."""
        try:
            originals_dir = self.data_dir / "originals"
            originals_dir.mkdir(exist_ok=True)
            
            file_path = originals_dir / f"{doc_id}_{filename}"
            with open(file_path, 'wb') as f:
                f.write(file_bytes)
        except Exception as e:
            logger.warning(f"Failed to save original file: {e}")
    
    def rebuild_vector_index(self) -> None:
        """Rebuild the entire vector index from document metadata."""
        logger.info("Rebuilding vector index...")
        
        # Clear existing indices
        self.vector_store.clear()
        
        # Re-process all documents
        for doc_id, doc in self.documents.items():
            try:
                # Get original file
                original_file = self.data_dir / "originals" / f"{doc_id}_{doc['filename']}"
                if original_file.exists():
                    with open(original_file, 'rb') as f:
                        file_bytes = f.read()
                    
                    # Re-process document
                    self.add_document(file_bytes, doc['filename'], doc)
                    logger.info(f"Re-processed document {doc_id}")
                else:
                    logger.warning(f"Original file not found for {doc_id}")
                    
            except Exception as e:
                logger.error(f"Failed to re-process document {doc_id}: {e}")
        
        logger.info("Vector index rebuild complete")
    
    def clear_all(self) -> None:
        """Clear all documents and indices."""
        logger.info("Clearing all documents and indices...")
        
        # Clear vector store
        self.vector_store.clear()
        
        # Clear documents
        self.documents = {}
        self._save_metadata()
        
        # Remove original files
        originals_dir = self.data_dir / "originals"
        if originals_dir.exists():
            for file in originals_dir.iterdir():
                file.unlink()
        
        logger.info("All data cleared")
    
    def get_document_text(self, doc_id: str) -> str:
        """Get the full text of a document."""
        doc = self.documents.get(doc_id)
        if not doc:
            return ""
        
        # Try to get from original file
        original_file = self.data_dir / "originals" / f"{doc_id}_{doc['filename']}"
        if original_file.exists():
            try:
                with open(original_file, 'rb') as f:
                    file_bytes = f.read()
                
                # Re-extract text
                text_content, _ = self.ocr_engine.extract_text(file_bytes, doc['filename'])
                return text_content
            except Exception as e:
                logger.error(f"Failed to extract text from original file: {e}")
        
        return ""
    
    def get_document_file(self, doc_id: str) -> Tuple[bytes, str]:
        """Get the original file bytes and filename."""
        doc = self.documents.get(doc_id)
        if not doc:
            raise ValueError(f"Document {doc_id} not found")
        
        original_file = self.data_dir / "originals" / f"{doc_id}_{doc['filename']}"
        if not original_file.exists():
            raise FileNotFoundError(f"Original file for {doc_id} not found")
        
        with open(original_file, 'rb') as f:
            file_bytes = f.read()
        
        return file_bytes, doc['filename'] 

    def update_metadata(self, doc_id: str, updates: Dict[str, Any]) -> None:
        """Update metadata for a document and save."""
        if doc_id not in self.documents:
            raise ValueError(f"Document {doc_id} not found")
        self.documents[doc_id].update(updates)
        self._save_metadata() 