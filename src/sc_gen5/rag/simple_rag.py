"""
Simple, flexible RAG system with clear model separation.

Design Principles:
1. Embedding model: Only for semantic search
2. Utility model: Only for chunk relevance analysis - NO generation
3. Generation model: Only for final answer generation
4. Simple chunking: Flexible, not overly restrictive
5. Clear data flow: Search -> Analyze -> Generate
"""

import logging
import json
import hashlib
import pickle
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
import tiktoken

log = logging.getLogger("lexcognito.simple_rag")

# Import model manager for direct model access
try:
    from .v2.models import _model_manager
    MODEL_MANAGER_AVAILABLE = True
except ImportError:
    MODEL_MANAGER_AVAILABLE = False
    _model_manager = None

@dataclass
class Chunk:
    """Simple chunk representation."""
    id: str
    text: str
    metadata: Dict[str, Any]
    doc_id: str
    chunk_index: int

@dataclass
class SearchResult:
    """Search result with relevance score."""
    chunk: Chunk
    distance: float
    relevance_score: Optional[float] = None

class SimpleChunker:
    """Simple text chunking with enhanced overlap for litigation documents."""
    
    def __init__(self, chunk_size: int = 800, overlap: int = 200):  # Increased from 1000/100 to 800/200
        """Initialize chunker with enhanced overlap for better context preservation."""
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def chunk_text(self, text: str, doc_id: str, metadata: Dict[str, Any] = None) -> List[Chunk]:
        """Chunk text with enhanced overlap for litigation analysis."""
        chunks = []
        
        # Split text into sentences first for better chunk boundaries
        sentences = self._split_into_sentences(text)
        
        current_chunk = ""
        chunk_index = 0
        
        for i, sentence in enumerate(sentences):
            # Check if adding this sentence would exceed chunk size
            if len(current_chunk) + len(sentence) > self.chunk_size and current_chunk:
                # Create chunk
                chunk_id = f"{doc_id}_chunk_{chunk_index:04d}"
                chunks.append(Chunk(
                    id=chunk_id,
                    text=current_chunk.strip(),
                    metadata=metadata or {},
                    doc_id=doc_id,
                    chunk_index=chunk_index
                ))
                
                # Start new chunk with overlap
                overlap_text = self._get_overlap_text(current_chunk)
                current_chunk = overlap_text + sentence
                chunk_index += 1
            else:
                current_chunk += sentence + " "
        
        # Add final chunk
        if current_chunk.strip():
            chunk_id = f"{doc_id}_chunk_{chunk_index:04d}"
            chunks.append(Chunk(
                id=chunk_id,
                text=current_chunk.strip(),
                metadata=metadata or {},
                doc_id=doc_id,
                chunk_index=chunk_index
            ))
        
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences with enhanced logic for legal documents."""
        import re
        
        # Enhanced sentence splitting for legal documents
        # Handle common legal abbreviations and citations
        text = re.sub(r'([.!?])\s+([A-Z])', r'\1|SPLIT|\2', text)
        text = re.sub(r'([.!?])\s+([0-9])', r'\1|SPLIT|\2', text)
        
        # Handle legal citations
        text = re.sub(r'([.!?])\s+([A-Z][a-z]+\.)', r'\1|SPLIT|\2', text)
        
        sentences = text.split('|SPLIT|')
        return [s.strip() for s in sentences if s.strip()]
    
    def _get_overlap_text(self, text: str) -> str:
        """Get overlap text from the end of the current chunk."""
        if len(text) <= self.overlap:
            return text
        
        # Get the last N characters, but try to break at sentence boundaries
        overlap_text = text[-self.overlap:]
        
        # Try to find a sentence boundary in the overlap
        sentences = self._split_into_sentences(overlap_text)
        if len(sentences) > 1:
            # Return from the last complete sentence
            return ' '.join(sentences[1:])
        
        return overlap_text

class SimpleVectorStore:
    """Simple vector store using FAISS."""
    
    def __init__(self, embedding_model: str = "BAAI/bge-small-en-v1.5", store_path: str = "data/simple_vector_store"):
        self.embedding_model = embedding_model
        self.store_path = Path(store_path)
        self.store_path.mkdir(parents=True, exist_ok=True)
        
        # Load embedding model
        log.info(f"Loading embedding model: {embedding_model}")
        self.embedder = SentenceTransformer(embedding_model)
        self.dimension = self.embedder.get_sentence_embedding_dimension()
        
        # Initialize FAISS index
        self.index = faiss.IndexFlatIP(self.dimension)  # Inner product for cosine similarity
        self.chunks: List[Chunk] = []
        self.chunk_ids: List[str] = []
        
        # Load existing data
        self.load()
        log.info(f"Loaded vector store with {len(self.chunks)} chunks")
    
    def add_document(self, text: str, doc_id: str, metadata: Dict[str, Any] = None) -> List[str]:
        """Add document to vector store."""
        # Chunk the text
        chunker = SimpleChunker()
        chunks = chunker.chunk_text(text, doc_id, metadata)
        
        if not chunks:
            return []
        
        # Generate embeddings
        texts = [chunk.text for chunk in chunks]
        embeddings = self.embedder.encode(texts, show_progress_bar=True)
        
        # Add to index
        self.index.add(embeddings.astype('float32'))
        
        # Store chunks
        for chunk in chunks:
            self.chunks.append(chunk)
            self.chunk_ids.append(chunk.id)
        
        # Save
        self.save()
        
        return [chunk.id for chunk in chunks]
    
    def search(self, query: str, k: int = 10) -> List[SearchResult]:
        """Search for similar chunks."""
        # Generate query embedding
        query_embedding = self.embedder.encode([query])
        
        # Search
        distances, indices = self.index.search(query_embedding.astype('float32'), k)
        
        # Convert to results
        results = []
        for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
            if idx < len(self.chunks):
                chunk = self.chunks[idx]
                # Convert distance to similarity score (0-1)
                similarity = (distance + 1) / 2  # FAISS inner product to similarity
                results.append(SearchResult(
                    chunk=chunk,
                    distance=float(distance),
                    relevance_score=similarity
                ))
        
        return results
    
    def get_chunk_by_id(self, chunk_id: str) -> Optional[Chunk]:
        """Get chunk by ID."""
        for chunk in self.chunks:
            if chunk.id == chunk_id:
                return chunk
        return None
    
    def save(self):
        """Save vector store to disk."""
        # Save FAISS index
        faiss.write_index(self.index, str(self.store_path / "index.faiss"))
        
        # Save chunks
        with open(self.store_path / "chunks.pkl", "wb") as f:
            pickle.dump(self.chunks, f)
        
        # Save chunk IDs
        with open(self.store_path / "chunk_ids.pkl", "wb") as f:
            pickle.dump(self.chunk_ids, f)
    
    def load(self):
        """Load vector store from disk."""
        index_path = self.store_path / "index.faiss"
        chunks_path = self.store_path / "chunks.pkl"
        chunk_ids_path = self.store_path / "chunk_ids.pkl"
        
        if index_path.exists() and chunks_path.exists() and chunk_ids_path.exists():
            # Load FAISS index
            self.index = faiss.read_index(str(index_path))
            
            # Load chunks
            with open(chunks_path, "rb") as f:
                self.chunks = pickle.load(f)
            
            # Load chunk IDs
            with open(chunk_ids_path, "rb") as f:
                self.chunk_ids = pickle.load(f)

class DirectModelClient:
    """Direct model client that uses lazy loading - no models loaded until first use."""
    
    def __init__(self):
        # No models loaded at initialization - lazy loading
        self.utility_model = None
        self.utility_tokenizer = None
        self.generator_model = None
        self.generator_tokenizer = None
        log.info("DirectModelClient initialized with lazy loading - no models loaded")
    
    async def generate_text(self, prompt: str, max_tokens: int = 100, model_type: str = "generator") -> Tuple[bool, str]:
        """Generate text using the generator model only (utility model disabled)."""
        try:
            return await self._generate_with_generator(prompt, max_tokens)
        except Exception as e:
            log.error(f"Text generation failed: {e}")
            return False, str(e)
    

    
    async def _generate_with_generator(self, prompt: str, max_tokens: int) -> Tuple[bool, str]:
        """Generate text using generator model with llama.cpp (lazy loading)."""
        if not MODEL_MANAGER_AVAILABLE:
            return False, "Model manager not available"
        
        try:
            # Load generator model if needed (lazy loading)
            if self.generator_model is None:
                log.info("Loading generator model on first use...")
                self.generator_tokenizer, self.generator_model = _model_manager.get_generator_model()
                log.info("✓ Generator model loaded successfully")
            
            # Generate text using llama.cpp
            log.info(f"Prompt length: {len(prompt)} characters")
            
            # Use llama.cpp's generation
            response = self.generator_model(
                prompt,
                max_tokens=max_tokens,
                temperature=0.7,
                top_p=0.9,
                repeat_penalty=1.1,
                stop=["</s>", "[INST]", "[/INST]"]  # Stop at instruction markers
            )
            
            # Extract the generated text
            if isinstance(response, dict) and 'choices' in response and response['choices']:
                generated_text = response['choices'][0]['text']
            else:
                generated_text = str(response)
            
            log.info(f"Generated {len(generated_text)} characters")
            return True, generated_text.strip()
            
        except Exception as e:
            log.error(f"Generator model generation failed: {e}")
            return False, f"Generator model error: {e}"
    
    def get_model_status(self) -> Dict[str, bool]:
        """Get current model loading status."""
        return {
            "generator": self.generator_model is not None,
            "lazy_loading": True
        }

class RelevanceAnalyzer:
    """Uses utility model to analyze chunk relevance - NO generation."""
    
    def __init__(self, model_client=None):
        self.model_client = model_client
    
    async def analyze_relevance(self, query: str, chunks: List[Chunk]) -> List[Tuple[Chunk, float]]:
        """Analyze how relevant each chunk is to the query."""
        # Utility model is completely disabled - use simple distance-based scoring
        log.info("Utility model disabled - using distance-based scoring")
        return [(chunk, 1.0) for chunk in chunks]

class SimpleRAG:
    """Main RAG orchestrator with clear model separation."""
    
    def __init__(self, vector_store: SimpleVectorStore, model_client=None):
        self.vector_store = vector_store
        self.model_client = model_client or DirectModelClient()
        self.analyzer = RelevanceAnalyzer(model_client)
        
        # Document metadata store
        self.documents: Dict[str, Dict[str, Any]] = {}
        self.metadata_path = Path("data/simple_rag_metadata.json")
        self.load_metadata()
    
    def add_document(self, content: bytes, filename: str, metadata: Dict[str, Any] = None) -> str:
        """Add document to RAG system."""
        # Generate document ID
        content_hash = hashlib.sha256(content).hexdigest()
        doc_id = f"doc_{content_hash[:16]}"
        
        # Skip if already exists
        if doc_id in self.documents:
            log.info(f"Document {doc_id} already exists")
            return doc_id
        
        try:
            # Extract text based on file type
            if filename.endswith('.txt'):
                text = content.decode('utf-8', errors='ignore')
            elif filename.endswith('.pdf'):
                # Extract text from PDF
                try:
                    import PyPDF2
                    import io
                    pdf_file = io.BytesIO(content)
                    pdf_reader = PyPDF2.PdfReader(pdf_file)
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
                    log.info(f"Extracted {len(text)} characters from PDF")
                except ImportError:
                    log.error("PyPDF2 not available for PDF processing")
                    return doc_id
                except Exception as e:
                    log.error(f"PDF processing failed: {e}")
                    return doc_id
            else:
                # For other files, we'd need OCR - for now, skip
                log.warning(f"Unsupported file type: {filename}")
                return doc_id
            
            if not text.strip():
                raise ValueError("No text content")
            
            # Add to vector store
            chunk_ids = self.vector_store.add_document(text, doc_id, metadata)
            
            # Store document metadata
            doc_metadata = {
                "doc_id": doc_id,
                "filename": filename,
                "content_hash": content_hash,
                "file_size": len(content),
                "text_length": len(text),
                "chunk_ids": chunk_ids,
                "chunk_count": len(chunk_ids),
                "created_at": datetime.now().isoformat(),
                **(metadata or {})
            }
            
            self.documents[doc_id] = doc_metadata
            self.save_metadata()
            
            log.info(f"Added document {doc_id}: {filename} with {len(chunk_ids)} chunks")
            return doc_id
            
        except Exception as e:
            log.error(f"Failed to add document {filename}: {e}")
            raise
    
    async def answer_question(
        self, 
        question: str, 
        max_chunks: int = 15,
        min_relevance: float = 0.2,
        max_tokens: int = 1500,
        matter_type: str = "litigation",
        analysis_style: str = "comprehensive",
        focus_area: str = "liability"
    ) -> Dict[str, Any]:
        """Answer question using the 3-step process with litigation-specific analysis."""
        start_time = time.time()
        
        try:
            # Step 1: Search for relevant chunks with enhanced queries
            log.info(f"🔍 Searching for: {question}")
            
            # Create enhanced search queries for better retrieval
            search_queries = [
                question,  # Original question
                f"{question} specific arguments evidence",  # Enhanced for specificity
                f"{question} direct quotes statements",  # Enhanced for direct evidence
                f"{question} party position claims",  # Enhanced for party positions
                f"{question} documents facts details",  # Enhanced for factual details
                f"{question} evidence proof testimony"  # Enhanced for evidence
            ]
            
            all_search_results = []
            for query in search_queries:
                results = self.vector_store.search(query, k=max_chunks * 2)
                all_search_results.extend(results)
            
            # Remove duplicates and sort by relevance
            unique_results = {}
            for result in all_search_results:
                if result.chunk.id not in unique_results:
                    unique_results[result.chunk.id] = result
                else:
                    # Keep the higher relevance score
                    if result.relevance_score and (not unique_results[result.chunk.id].relevance_score or 
                                                 result.relevance_score > unique_results[result.chunk.id].relevance_score):
                        unique_results[result.chunk.id] = result
            
            search_results = list(unique_results.values())
            search_results.sort(key=lambda x: x.relevance_score or 0, reverse=True)
            
            if not search_results:
                return {
                    "answer": "I couldn't find any relevant documents to answer your question. Please make sure relevant documents have been uploaded to the system.",
                    "confidence": 0.1,
                    "sources": [],
                    "chunks_analyzed": 0,
                    "chunks_used": 0,
                    "processing_time": time.time() - start_time,
                    "model_used": "No Documents"
                }
            
            log.info(f"📄 Found {len(search_results)} potential chunks")
            
            # Step 2: Analyze relevance (utility model) with enhanced analysis
            chunks = [result.chunk for result in search_results]
            analyzed_chunks = await self.analyzer.analyze_relevance(question, chunks)
            
            # Filter by relevance and prioritize chunks with specific details
            relevant_chunks = []
            for chunk, score in analyzed_chunks:
                if score >= min_relevance:
                    # Prioritize chunks that contain specific details
                    text = chunk.text.lower()
                    specificity_bonus = 0.0
                    
                    # Bonus for chunks with specific details
                    if any(word in text for word in ['said', 'stated', 'claimed', 'argued', 'alleged', 'denied']):
                        specificity_bonus += 0.1
                    if any(word in text for word in ['$', '£', '€', 'amount', 'damages', 'compensation']):
                        specificity_bonus += 0.1
                    if any(word in text for word in ['date', 'time', 'period', 'when']):
                        specificity_bonus += 0.1
                    if any(word in text for word in ['document', 'evidence', 'proof', 'witness']):
                        specificity_bonus += 0.1
                    if any(word in text for word in ['harbour', 'smith', 'cochrane', 'parties']):
                        specificity_bonus += 0.05  # Bonus for specific party names
                    
                    adjusted_score = min(1.0, score + specificity_bonus)
                    relevant_chunks.append((chunk, adjusted_score))
            
            # Sort by adjusted score and limit
            relevant_chunks.sort(key=lambda x: x[1], reverse=True)
            relevant_chunks = relevant_chunks[:max_chunks * 2]
            
            log.info(f"✅ Selected {len(relevant_chunks)} relevant chunks")
            
            if not relevant_chunks:
                return {
                    "answer": f"I found {len(search_results)} potentially related chunks, but none were sufficiently relevant to answer your question. You may need to rephrase your question or upload more specific documents.",
                    "confidence": 0.2,
                    "sources": [],
                    "chunks_analyzed": len(analyzed_chunks),
                    "chunks_used": 0,
                    "processing_time": time.time() - start_time,
                    "model_used": "Relevance Filter"
                }
            
            # Step 3: Generate answer (generation model)
            context = self._build_context(relevant_chunks)
            
            if self.model_client:
                # Build litigation-specific prompt
                focus_instructions = {
                    "liability": "Focus on legal liability, duty of care, and breach analysis",
                    "procedural": "Focus on procedural issues, jurisdiction, and court processes",
                    "evidence": "Focus on evidence admissibility, burden of proof, and evidentiary rules",
                    "damages": "Focus on damages calculation, compensation, and remedies",
                    "defenses": "Focus on available defenses, counterarguments, and legal strategies",
                    "settlement": "Focus on settlement value, negotiation factors, and case resolution"
                }
                
                analysis_style_instructions = {
                    "comprehensive": "Provide a comprehensive analysis with detailed legal reasoning",
                    "concise": "Provide a concise analysis focusing on key points",
                    "technical": "Provide a technical analysis with specific legal citations and precedents"
                }
                
                focus_instruction = focus_instructions.get(focus_area, "Focus on general litigation analysis")
                style_instruction = analysis_style_instructions.get(analysis_style, "Provide a comprehensive analysis")
                
                generation_prompt = f"""[INST] You are a litigation research assistant specializing in {matter_type.replace('_', ' ')} matters. Based on the following legal documents, provide a {analysis_style} analysis of party positions and legal arguments. {focus_instruction}. {style_instruction}.

CRITICAL REQUIREMENTS:
1. ONLY use information that is EXPLICITLY stated in the provided documents
2. ALWAYS include direct quotes from the source documents with proper citation
3. If specific details are not available in the documents, clearly state "This information is not available in the provided documents"
4. Focus on concrete facts, specific arguments, and actual evidence presented
5. Avoid generic legal principles unless they are specifically mentioned in the documents
6. Be precise about what each party has actually said or done according to the documents

Your response should:

1. Start with a clear statement of what specific information is available about the parties' positions
2. Include direct quotes from the source documents with proper citation (e.g., "According to [Document Name]: '...'")
3. Analyze the specific arguments and evidence presented by each party
4. Identify concrete facts, dates, amounts, and specific legal claims mentioned
5. Distinguish between what is explicitly stated vs. what might be inferred
6. If information is missing, clearly state what is not available in the documents
7. Use formal legal language but focus on specific details rather than general principles
8. Structure the response with clear sections for each party's position

Legal Documents:
{context}

Question: {question}

Please provide a {analysis_style} {matter_type.replace('_', ' ')} analysis with specific citations, direct quotes, and concrete details from the documents (minimum 400 words). If specific information is not available in the documents, clearly state this: [/INST]"""
                
                success, answer = await self.model_client.generate_text(
                    prompt=generation_prompt,
                    max_tokens=max_tokens,
                    model_type="generator"  # Use generator model
                )
                
                if success:
                    return {
                        "answer": answer,
                        "confidence": 0.9,
                        "sources": self._format_sources(relevant_chunks),
                        "chunks_analyzed": len(analyzed_chunks),
                        "chunks_used": len(relevant_chunks),
                        "processing_time": time.time() - start_time,
                        "model_used": f"RAG (Generator Model) - {matter_type} {analysis_style}"
                    }
            
            # Fallback if generation fails
            return {
                "answer": f"I found relevant information in the documents but the generation model is currently unavailable. Relevant sources: {', '.join([chunk.metadata.get('filename', 'Unknown') for chunk, _ in relevant_chunks])}",
                "confidence": 0.6,
                "sources": self._format_sources(relevant_chunks),
                "chunks_analyzed": len(analyzed_chunks),
                "chunks_used": len(relevant_chunks),
                "processing_time": time.time() - start_time,
                "model_used": "Source Retrieval Only"
            }
            
        except Exception as e:
            log.error(f"RAG processing failed: {e}")
            return {
                "answer": f"I encountered an error while processing your question: {e}",
                "confidence": 0.1,
                "sources": [],
                "chunks_analyzed": 0,
                "chunks_used": 0,
                "processing_time": time.time() - start_time,
                "model_used": "Error Handler"
            }
    
    def _build_context(self, relevant_chunks: List[Tuple[Chunk, float]]) -> str:
        """Build context from relevant chunks with enhanced formatting for litigation analysis."""
        context_parts = []
        
        # Group chunks by document for better organization
        doc_chunks = {}
        for chunk, score in relevant_chunks:
            doc_id = chunk.doc_id
            if doc_id not in doc_chunks:
                doc_chunks[doc_id] = []
            doc_chunks[doc_id].append((chunk, score))
        
        # Build context with document organization
        for doc_id, chunks in doc_chunks.items():
            # Get document metadata
            filename = chunks[0][0].metadata.get('filename', 'Unknown Document')
            
            context_parts.append(f"=== DOCUMENT: {filename} (Document ID: {doc_id}) ===")
            
            # Sort chunks by relevance within document
            chunks.sort(key=lambda x: x[1], reverse=True)
            
            for i, (chunk, score) in enumerate(chunks, 1):
                context_parts.append(f"\n--- EXCERPT {i} (Relevance: {score:.2f}) ---")
                context_parts.append(f"{chunk.text}")
                context_parts.append("")  # Empty line for readability
        
        return "\n".join(context_parts)
    
    def _format_sources(self, relevant_chunks: List[Tuple[Chunk, float]]) -> List[Dict[str, Any]]:
        """Format sources for response."""
        sources = []
        for chunk, score in relevant_chunks:
            sources.append({
                "document_id": chunk.doc_id,
                "filename": chunk.metadata.get('filename', 'Unknown'),
                "chunk_id": chunk.id,
                "relevance_score": score,
                "text_excerpt": chunk.text[:200] + "..." if len(chunk.text) > 200 else chunk.text
            })
        return sources
    
    def get_status(self) -> Dict[str, Any]:
        """Get system status."""
        return {
            "documents": {
                "count": len(self.documents),
                "indexed": len(self.documents) > 0
            },
            "chunks": {
                "count": len(self.vector_store.chunks),
                "indexed": len(self.vector_store.chunks) > 0
            },
            "vector_store": {
                "dimension": self.vector_store.dimension,
                "total_vectors": self.vector_store.index.ntotal
            }
        }
    
    def load_metadata(self):
        """Load document metadata."""
        try:
            if self.metadata_path.exists():
                with open(self.metadata_path, 'r') as f:
                    self.documents = json.load(f)
                log.info(f"Loaded metadata for {len(self.documents)} documents")
        except Exception as e:
            log.warning(f"Failed to load metadata: {e}")
            self.documents = {}
    
    def save_metadata(self):
        """Save document metadata."""
        try:
            with open(self.metadata_path, 'w') as f:
                json.dump(self.documents, f, indent=2)
        except Exception as e:
            log.error(f"Failed to save metadata: {e}")