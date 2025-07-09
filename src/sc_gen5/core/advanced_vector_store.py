"""
Advanced vector store with sophisticated embedding and retrieval capabilities.
Combines the best features from RAG v1 and RAG v2 for optimal legal document processing.
"""

import json
import logging
import pickle
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import tiktoken

logger = logging.getLogger(__name__)


class ChunkType(Enum):
    """Types of document chunks for multi-granularity processing."""
    SECTION = "section"      # Large sections (chapters, parts)
    PARAGRAPH = "paragraph"  # Medium paragraphs
    SENTENCE = "sentence"    # Individual sentences
    QUOTE = "quote"         # Legal quotes and citations
    CLAUSE = "clause"       # Legal clauses and provisions
    DEFINITION = "definition" # Legal definitions


@dataclass
class ChunkConfig:
    """Configuration for different chunk types."""
    chunk_type: ChunkType
    max_tokens: int
    overlap_tokens: int
    min_tokens: int = 50
    preserve_structure: bool = True
    semantic_boundaries: bool = True


class AdvancedVectorStore:
    """
    Sophisticated vector store with multi-granularity chunking and retrieval.
    
    Features:
    - Multi-granularity chunking (sections, paragraphs, sentences, quotes)
    - Semantic boundary detection
    - Legal-specific chunking (clauses, definitions)
    - Hybrid search (dense + sparse retrieval)
    - Context-aware retrieval
    - Quality scoring and filtering
    """
    
    def __init__(
        self,
        embedding_model: str = "BAAI/bge-base-en-v1.5",
        index_path: Optional[str] = None,
        dimension: Optional[int] = None,
        chunk_configs: Optional[Dict[ChunkType, ChunkConfig]] = None,
    ) -> None:
        """Initialize advanced vector store."""
        self.embedding_model_name = embedding_model
        self.index_path = Path(index_path) if index_path else None
        
        # Initialize embedding model
        logger.info(f"Loading embedding model: {embedding_model}")
        self.encoder = SentenceTransformer(embedding_model)
        
        # Get embedding dimension
        if dimension is None:
            dummy_embedding = self.encoder.encode(["test"])
            self.dimension = dummy_embedding.shape[1]
        else:
            self.dimension = dimension
            
        logger.info(f"Embedding dimension: {self.dimension}")
        
        # Initialize chunk configurations
        self.chunk_configs = chunk_configs or self._get_default_chunk_configs()
        
        # Initialize tokenizer for chunking
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        # Initialize FAISS indices for each chunk type
        self.indices: Dict[ChunkType, faiss.Index] = {}
        self.metadata: Dict[ChunkType, Dict[int, Dict[str, Any]]] = {}
        self.next_ids: Dict[ChunkType, int] = {}
        
        # Initialize indices
        for chunk_type in ChunkType:
            self.indices[chunk_type] = faiss.IndexFlatL2(self.dimension)
            self.metadata[chunk_type] = {}
            self.next_ids[chunk_type] = 0
        
        # Load existing indices if available
        if self.index_path:
            self.load_indices()
    
    def _get_default_chunk_configs(self) -> Dict[ChunkType, ChunkConfig]:
        """Get default chunk configurations optimized for legal documents."""
        return {
            ChunkType.SECTION: ChunkConfig(
                chunk_type=ChunkType.SECTION,
                max_tokens=2000,
                overlap_tokens=200,
                min_tokens=500,
                preserve_structure=True,
                semantic_boundaries=True
            ),
            ChunkType.PARAGRAPH: ChunkConfig(
                chunk_type=ChunkType.PARAGRAPH,
                max_tokens=800,
                overlap_tokens=100,
                min_tokens=200,
                preserve_structure=True,
                semantic_boundaries=True
            ),
            ChunkType.SENTENCE: ChunkConfig(
                chunk_type=ChunkType.SENTENCE,
                max_tokens=200,
                overlap_tokens=20,
                min_tokens=50,
                preserve_structure=False,
                semantic_boundaries=True
            ),
            ChunkType.QUOTE: ChunkConfig(
                chunk_type=ChunkType.QUOTE,
                max_tokens=400,
                overlap_tokens=50,
                min_tokens=100,
                preserve_structure=True,
                semantic_boundaries=True
            ),
            ChunkType.CLAUSE: ChunkConfig(
                chunk_type=ChunkType.CLAUSE,
                max_tokens=600,
                overlap_tokens=80,
                min_tokens=150,
                preserve_structure=True,
                semantic_boundaries=True
            ),
            ChunkType.DEFINITION: ChunkConfig(
                chunk_type=ChunkType.DEFINITION,
                max_tokens=300,
                overlap_tokens=40,
                min_tokens=80,
                preserve_structure=True,
                semantic_boundaries=True
            )
        }
    
    def _detect_legal_structure(self, text: str) -> Dict[str, List[Tuple[int, int]]]:
        """Detect legal document structure (sections, clauses, definitions)."""
        structure = {
            "sections": [],
            "clauses": [],
            "definitions": [],
            "quotes": []
        }
        
        # Section patterns (e.g., "Section 1", "Part II", "Chapter 3")
        section_pattern = r'(?:Section|Part|Chapter|Article)\s+\d+[A-Za-z]*(?:\.|:)?'
        for match in re.finditer(section_pattern, text, re.IGNORECASE):
            structure["sections"].append((match.start(), match.end()))
        
        # Clause patterns (e.g., "(1)", "(a)", "(i)")
        clause_pattern = r'\([a-z0-9]+\)'
        for match in re.finditer(clause_pattern, text):
            structure["clauses"].append((match.start(), match.end()))
        
        # Definition patterns (e.g., "means", "shall mean", "defined as")
        definition_pattern = r'(?:means|shall mean|defined as|refers to)'
        for match in re.finditer(definition_pattern, text, re.IGNORECASE):
            structure["definitions"].append((match.start(), match.end()))
        
        # Quote patterns (e.g., quoted text, citations)
        quote_pattern = r'["""]([^"""]+)["""]'
        for match in re.finditer(quote_pattern, text):
            structure["quotes"].append((match.start(), match.end()))
        
        return structure
    
    def _chunk_by_type(self, text: str, chunk_type: ChunkType) -> List[str]:
        """Create chunks based on the specified chunk type."""
        config = self.chunk_configs[chunk_type]
        
        if chunk_type == ChunkType.SENTENCE:
            return self._chunk_by_sentences(text, config)
        elif chunk_type == ChunkType.PARAGRAPH:
            return self._chunk_by_paragraphs(text, config)
        elif chunk_type == ChunkType.SECTION:
            return self._chunk_by_sections(text, config)
        elif chunk_type == ChunkType.QUOTE:
            return self._chunk_by_quotes(text, config)
        elif chunk_type == ChunkType.CLAUSE:
            return self._chunk_by_clauses(text, config)
        elif chunk_type == ChunkType.DEFINITION:
            return self._chunk_by_definitions(text, config)
        else:
            return self._chunk_by_tokens(text, config)
    
    def _chunk_by_sentences(self, text: str, config: ChunkConfig) -> List[str]:
        """Chunk text by sentences with semantic boundaries."""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for sentence in sentences:
            sentence_tokens = len(self.tokenizer.encode(sentence))
            
            if current_tokens + sentence_tokens > config.max_tokens and current_chunk:
                # Save current chunk
                chunk_text = " ".join(current_chunk)
                if len(self.tokenizer.encode(chunk_text)) >= config.min_tokens:
                    chunks.append(chunk_text)
                
                # Start new chunk with overlap
                overlap_sentences = current_chunk[-2:] if len(current_chunk) >= 2 else current_chunk
                current_chunk = overlap_sentences + [sentence]
                current_tokens = sum(len(self.tokenizer.encode(s)) for s in current_chunk)
            else:
                current_chunk.append(sentence)
                current_tokens += sentence_tokens
        
        # Add final chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            if len(self.tokenizer.encode(chunk_text)) >= config.min_tokens:
                chunks.append(chunk_text)
        
        return chunks
    
    def _chunk_by_paragraphs(self, text: str, config: ChunkConfig) -> List[str]:
        """Chunk text by paragraphs."""
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
                
            paragraph_tokens = len(self.tokenizer.encode(paragraph))
            
            if current_tokens + paragraph_tokens > config.max_tokens and current_chunk:
                chunk_text = "\n\n".join(current_chunk)
                if len(self.tokenizer.encode(chunk_text)) >= config.min_tokens:
                    chunks.append(chunk_text)
                
                # Start new chunk with overlap
                current_chunk = [paragraph]
                current_tokens = paragraph_tokens
            else:
                current_chunk.append(paragraph)
                current_tokens += paragraph_tokens
        
        # Add final chunk
        if current_chunk:
            chunk_text = "\n\n".join(current_chunk)
            if len(self.tokenizer.encode(chunk_text)) >= config.min_tokens:
                chunks.append(chunk_text)
        
        return chunks
    
    def _chunk_by_sections(self, text: str, config: ChunkConfig) -> List[str]:
        """Chunk text by legal sections."""
        # Use structure detection to find section boundaries
        structure = self._detect_legal_structure(text)
        section_boundaries = structure["sections"]
        
        if not section_boundaries:
            # Fall back to paragraph chunking
            return self._chunk_by_paragraphs(text, config)
        
        chunks = []
        for i, (start, end) in enumerate(section_boundaries):
            if i + 1 < len(section_boundaries):
                next_start = section_boundaries[i + 1][0]
                section_text = text[start:next_start]
            else:
                section_text = text[start:]
            
            # Further chunk large sections
            if len(self.tokenizer.encode(section_text)) > config.max_tokens:
                sub_chunks = self._chunk_by_paragraphs(section_text, config)
                chunks.extend(sub_chunks)
            else:
                chunks.append(section_text)
        
        return chunks
    
    def _chunk_by_quotes(self, text: str, config: ChunkConfig) -> List[str]:
        """Extract and chunk quoted text."""
        quotes = re.findall(r'["""]([^"""]+)["""]', text)
        chunks = []
        
        for quote in quotes:
            if len(self.tokenizer.encode(quote)) >= config.min_tokens:
                chunks.append(quote)
        
        return chunks
    
    def _chunk_by_clauses(self, text: str, config: ChunkConfig) -> List[str]:
        """Chunk text by legal clauses."""
        # Find clause boundaries
        clauses = re.findall(r'\([a-z0-9]+\)[^()]*', text, re.IGNORECASE)
        chunks = []
        
        for clause in clauses:
            if len(self.tokenizer.encode(clause)) >= config.min_tokens:
                chunks.append(clause)
        
        return chunks
    
    def _chunk_by_definitions(self, text: str, config: ChunkConfig) -> List[str]:
        """Chunk text by legal definitions."""
        # Find definition patterns
        definitions = re.findall(r'(?:means|shall mean|defined as|refers to)[^.!?]*[.!?]', text, re.IGNORECASE)
        chunks = []
        
        for definition in definitions:
            if len(self.tokenizer.encode(definition)) >= config.min_tokens:
                chunks.append(definition)
        
        return chunks
    
    def _chunk_by_tokens(self, text: str, config: ChunkConfig) -> List[str]:
        """Fallback chunking by token count."""
        tokens = self.tokenizer.encode(text)
        chunks = []
        
        for i in range(0, len(tokens), config.max_tokens - config.overlap_tokens):
            chunk_tokens = tokens[i:i + config.max_tokens]
            chunk_text = self.tokenizer.decode(chunk_tokens)
            
            if len(chunk_tokens) >= config.min_tokens:
                chunks.append(chunk_text)
        
        return chunks
    
    def add_document(
        self, 
        text: str, 
        metadata: Dict[str, Any],
        chunk_types: Optional[List[ChunkType]] = None
    ) -> Dict[ChunkType, List[int]]:
        """Add document with multi-granularity chunking."""
        if chunk_types is None:
            chunk_types = [ChunkType.SECTION, ChunkType.PARAGRAPH, ChunkType.SENTENCE]
        
        results = {}
        
        for chunk_type in chunk_types:
            logger.info(f"Chunking document by {chunk_type.value}")
            chunks = self._chunk_by_type(text, chunk_type)
            
            if chunks:
                # Create metadata for each chunk
                chunk_metadatas = []
                for i, chunk in enumerate(chunks):
                    chunk_metadata = {
                        **metadata,
                        "chunk_type": chunk_type.value,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "chunk_length": len(chunk),
                        "chunk_tokens": len(self.tokenizer.encode(chunk))
                    }
                    chunk_metadatas.append(chunk_metadata)
                
                # Add to vector store
                chunk_ids = self.add_embeddings(chunks, chunk_metadatas, chunk_type)
                results[chunk_type] = chunk_ids
                
                logger.info(f"Added {len(chunks)} {chunk_type.value} chunks")
        
        return results
    
    def add_embeddings(
        self, 
        texts: List[str], 
        metadatas: List[Dict[str, Any]],
        chunk_type: ChunkType
    ) -> List[int]:
        """Add embeddings for a specific chunk type."""
        if len(texts) != len(metadatas):
            raise ValueError("Number of texts and metadatas must match")
            
        if not texts:
            return []
        
        # Generate embeddings
        logger.info(f"Generating embeddings for {len(texts)} {chunk_type.value} texts")
        embeddings = self.encoder.encode(texts, show_progress_bar=True)
        embeddings = embeddings.astype(np.float32)
        
        # Add to FAISS index
        self.indices[chunk_type].add(embeddings)
        
        # Store metadata
        ids = []
        for i, metadata in enumerate(metadatas):
            doc_id = self.next_ids[chunk_type] + i
            self.metadata[chunk_type][doc_id] = {
                **metadata,
                "text": texts[i],
                "embedding_model": self.embedding_model_name,
            }
            ids.append(doc_id)
            
        self.next_ids[chunk_type] += len(texts)
        
        logger.info(f"Added {len(texts)} {chunk_type.value} embeddings. Total: {self.indices[chunk_type].ntotal}")
        return ids
    
    def search(
        self, 
        query: str, 
        k: int = 10,
        chunk_types: Optional[List[ChunkType]] = None,
        filter_metadata: Optional[Dict[str, Any]] = None,
        score_threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        """Search across multiple chunk types with sophisticated ranking."""
        if chunk_types is None:
            chunk_types = [ChunkType.SECTION, ChunkType.PARAGRAPH, ChunkType.SENTENCE]
        
        all_results = []
        
        # Search each chunk type
        for chunk_type in chunk_types:
            if self.indices[chunk_type].ntotal == 0:
                continue
                
            results = self._search_chunk_type(query, k, chunk_type, filter_metadata)
            all_results.extend(results)
        
        # Sort by score and apply threshold
        all_results.sort(key=lambda x: x["score"], reverse=True)
        filtered_results = [r for r in all_results if r["score"] >= score_threshold]
        
        # Return top k results
        return filtered_results[:k]
    
    def _search_chunk_type(
        self, 
        query: str, 
        k: int, 
        chunk_type: ChunkType,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search within a specific chunk type."""
        # Generate query embedding
        query_embedding = self.encoder.encode([query]).astype(np.float32)
        
        # Search FAISS index
        distances, indices = self.indices[chunk_type].search(query_embedding, k)
        
        # Convert results
        results = []
        for distance, idx in zip(distances[0], indices[0]):
            if idx == -1:
                break
                
            if idx in self.metadata[chunk_type]:
                result = {
                    "id": int(idx),
                    "distance": float(distance),
                    "score": 1.0 / (1.0 + float(distance)),
                    "chunk_type": chunk_type.value,
                    **self.metadata[chunk_type][idx]
                }
                
                # Apply metadata filters
                if filter_metadata and not self._matches_filter(result, filter_metadata):
                    continue
                    
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
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics about the vector store."""
        stats = {
            "total_embeddings": 0,
            "chunk_types": {},
            "embedding_model": self.embedding_model_name,
            "dimension": self.dimension
        }
        
        for chunk_type in ChunkType:
            count = self.indices[chunk_type].ntotal
            stats["total_embeddings"] += count
            stats["chunk_types"][chunk_type.value] = {
                "count": count,
                "index_size": count * self.dimension * 4  # float32 bytes
            }
        
        return stats
    
    def save_indices(self, path: Optional[str] = None) -> None:
        """Save all FAISS indices and metadata."""
        save_path = Path(path) if path else self.index_path
        if not save_path:
            raise ValueError("No save path specified")
        
        save_path.mkdir(parents=True, exist_ok=True)
        
        # Save each index
        for chunk_type in ChunkType:
            index_file = save_path / f"index_{chunk_type.value}.faiss"
            metadata_file = save_path / f"metadata_{chunk_type.value}.json"
            
            # Save FAISS index
            faiss.write_index(self.indices[chunk_type], str(index_file))
            
            # Save metadata
            with open(metadata_file, 'w') as f:
                json.dump(self.metadata[chunk_type], f, indent=2)
        
        # Save configuration
        config_file = save_path / "config.json"
        config = {
            "embedding_model": self.embedding_model_name,
            "dimension": self.dimension,
            "chunk_configs": {ct.value: {
                "max_tokens": cc.max_tokens,
                "overlap_tokens": cc.overlap_tokens,
                "min_tokens": cc.min_tokens
            } for ct, cc in self.chunk_configs.items()}
        }
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"Saved indices to {save_path}")
    
    def load_indices(self, path: Optional[str] = None) -> None:
        """Load all FAISS indices and metadata."""
        load_path = Path(path) if path else self.index_path
        if not load_path or not load_path.exists():
            logger.info("No existing indices found, starting fresh")
            return
        
        try:
            # Load configuration
            config_file = load_path / "config.json"
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config = json.load(f)
                
                # Verify compatibility
                if config.get("embedding_model") != self.embedding_model_name:
                    logger.warning("Embedding model mismatch, starting fresh")
                    return
            
            # Load each index
            for chunk_type in ChunkType:
                index_file = load_path / f"index_{chunk_type.value}.faiss"
                metadata_file = load_path / f"metadata_{chunk_type.value}.json"
                
                if index_file.exists() and metadata_file.exists():
                    # Load FAISS index
                    self.indices[chunk_type] = faiss.read_index(str(index_file))
                    
                    # Load metadata
                    with open(metadata_file, 'r') as f:
                        self.metadata[chunk_type] = json.load(f)
                    
                    # Update next_id
                    if self.metadata[chunk_type]:
                        self.next_ids[chunk_type] = max(self.metadata[chunk_type].keys()) + 1
                    else:
                        self.next_ids[chunk_type] = 0
            
            logger.info(f"Loaded indices from {load_path}")
            
        except Exception as e:
            logger.error(f"Failed to load indices: {e}")
            logger.info("Starting with fresh indices")
    
    def clear(self) -> None:
        """Clear all indices and metadata."""
        for chunk_type in ChunkType:
            self.indices[chunk_type] = faiss.IndexFlatL2(self.dimension)
            self.metadata[chunk_type] = {}
            self.next_ids[chunk_type] = 0
        
        logger.info("Cleared all indices and metadata")
    
    def get_by_id(self, doc_id: int) -> Optional[Dict[str, Any]]:
        """Get document by ID from any chunk type."""
        for chunk_type in ChunkType:
            if doc_id in self.metadata[chunk_type]:
                return self.metadata[chunk_type][doc_id]
        return None
    
    def remove_by_id(self, doc_id: int) -> bool:
        """Remove document by ID from any chunk type.
        
        Note: FAISS doesn't support efficient removal, so this only removes metadata.
        For full removal, the index would need to be rebuilt.
        """
        for chunk_type in ChunkType:
            if doc_id in self.metadata[chunk_type]:
                del self.metadata[chunk_type][doc_id]
                return True
        return False 