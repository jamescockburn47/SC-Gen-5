"""RAG pipeline for legal document analysis and consultation."""

import logging
from typing import Any, Dict, List, Optional

from .cloud_llm import CloudLLMGenerator, CloudProvider
from .doc_store import DocStore
from .local_llm import LocalLLMGenerator
from .protocols import StrategicProtocols

logger = logging.getLogger(__name__)


class RAGPipeline:
    """Retrieval-Augmented Generation pipeline."""

    def __init__(
        self,
        doc_store: DocStore,
        local_llm: Optional[LocalLLMGenerator] = None,
        cloud_llm: Optional[CloudLLMGenerator] = None,
        retrieval_k: int = 18,
        rerank_top_k: int = 6,
        use_reranker: bool = False,
    ) -> None:
        """Initialize RAG pipeline.
        
        Args:
            doc_store: Document store for retrieval
            local_llm: Local LLM generator
            cloud_llm: Cloud LLM generator
            retrieval_k: Number of documents to retrieve
            rerank_top_k: Number of documents after reranking
            use_reranker: Whether to use reranking
        """
        self.doc_store = doc_store
        self.local_llm = local_llm or LocalLLMGenerator()
        self.cloud_llm = cloud_llm or CloudLLMGenerator()
        self.retrieval_k = retrieval_k
        self.rerank_top_k = rerank_top_k
        self.use_reranker = use_reranker
        
        # Initialize reranker if requested
        self.reranker = None
        if use_reranker:
            try:
                from FlagEmbedding import FlagReranker
                self.reranker = FlagReranker('BAAI/bge-reranker-base', use_fp16=True)
                logger.info("FlagEmbedding reranker initialized")
            except ImportError:
                logger.warning("FlagEmbedding not available, skipping reranker")
                self.use_reranker = False
        
        logger.info("RAG pipeline initialized")

    def answer(
        self,
        question: str,
        cloud_allowed: bool = False,
        cloud_provider: Optional[str] = None,
        model_choice: Optional[str] = None,
        matter_type: Optional[str] = None,
        matter_id: Optional[str] = None,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generate answer using RAG pipeline.
        
        Args:
            question: User question
            cloud_allowed: Whether to allow cloud LLM usage
            cloud_provider: Cloud provider to use
            model_choice: Specific model to use
            matter_type: Type of legal matter for specialized prompts
            matter_id: Matter identifier for tracking
            filter_metadata: Optional metadata filters for retrieval
            
        Returns:
            Dictionary with answer, sources, and metadata
        """
        logger.info(f"Processing question: {question[:100]}...")
        
        try:
            # Step 1: Retrieve relevant documents
            retrieved_docs = self.doc_store.search(
                query=question,
                k=self.retrieval_k,
                filter_metadata=filter_metadata
            )
            
            if not retrieved_docs:
                return {
                    "answer": "I couldn't find any relevant documents to answer your question. Please ensure you have uploaded relevant documents to the system.",
                    "sources": "",
                    "matter_id": matter_id,
                    "model_used": "none",
                    "retrieved_chunks": 0,
                }
            
            logger.info(f"Retrieved {len(retrieved_docs)} documents")
            
            # Step 2: Rerank if enabled
            final_docs = self._rerank_documents(question, retrieved_docs) if self.use_reranker else retrieved_docs
            final_docs = final_docs[:self.rerank_top_k]
            
            # Step 3: Build context
            context = self._build_context(final_docs)
            
            # Step 4: Generate prompt
            prompt = StrategicProtocols.build_rag_prompt(
                question=question,
                context=context,
                matter_type=matter_type,
                matter_id=matter_id
            )
            
            # Step 5: Generate answer
            if cloud_allowed and cloud_provider:
                answer, model_used = self._generate_cloud_answer(
                    prompt, cloud_provider, model_choice
                )
            else:
                answer, model_used = self._generate_local_answer(prompt, model_choice)
            
            # Step 6: Build sources
            sources = self._build_sources(final_docs)
            
            return {
                "answer": answer,
                "sources": sources,
                "matter_id": matter_id,
                "model_used": model_used,
                "retrieved_chunks": len(final_docs),
                "context_length": len(context),
            }
            
        except Exception as e:
            logger.error(f"RAG pipeline failed: {e}")
            return {
                "answer": f"I encountered an error while processing your question: {str(e)}",
                "sources": "",
                "matter_id": matter_id,
                "model_used": "error",
                "retrieved_chunks": 0,
            }

    def direct_answer(
        self,
        question: str,
        cloud_allowed: bool = False,
        cloud_provider: Optional[str] = None,
        model_choice: Optional[str] = None,
        matter_type: Optional[str] = None,
        matter_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate answer using direct LLM query (no document retrieval).
        
        Args:
            question: User question
            cloud_allowed: Whether to allow cloud LLM usage
            cloud_provider: Cloud provider to use
            model_choice: Specific model to use
            matter_type: Type of legal matter for specialized prompts
            matter_id: Matter identifier for tracking
            
        Returns:
            Dictionary with answer, sources, and metadata
        """
        logger.info(f"Processing direct question: {question[:100]}...")
        
        try:
            # Generate standalone legal prompt (no document context)
            prompt = StrategicProtocols.build_standalone_prompt(
                question=question,
                matter_type=matter_type,
                matter_id=matter_id
            )
            
            # Generate answer
            if cloud_allowed and cloud_provider:
                answer, model_used = self._generate_cloud_answer(
                    prompt, cloud_provider, model_choice
                )
            else:
                answer, model_used = self._generate_local_answer(prompt, model_choice)
            
            return {
                "answer": answer,
                "sources": "Direct legal analysis (no documents consulted)",
                "matter_id": matter_id,
                "model_used": model_used,
                "retrieved_chunks": 0,
                "context_length": 0,
                "query_type": "standalone",
            }
            
        except Exception as e:
            logger.error(f"Direct answer pipeline failed: {e}")
            return {
                "answer": f"I encountered an error while processing your question: {str(e)}",
                "sources": "",
                "matter_id": matter_id,
                "model_used": "error",
                "retrieved_chunks": 0,
                "query_type": "standalone",
            }

    def _rerank_documents(self, query: str, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rerank documents using FlagEmbedding reranker."""
        if not self.reranker or len(documents) <= 1:
            return documents
            
        try:
            # Prepare query-document pairs
            pairs = [(query, doc.get("text", "")) for doc in documents]
            
            # Get reranking scores
            scores = self.reranker.compute_score(pairs)
            
            # Sort documents by score (higher is better)
            if isinstance(scores, list):
                doc_scores = list(zip(documents, scores))
            else:
                doc_scores = [(documents[0], scores)]  # Single document case
                
            doc_scores.sort(key=lambda x: x[1], reverse=True)
            
            # Update documents with rerank scores
            reranked_docs = []
            for doc, score in doc_scores:
                doc_copy = doc.copy()
                doc_copy["rerank_score"] = float(score)
                reranked_docs.append(doc_copy)
                
            logger.info(f"Reranked {len(reranked_docs)} documents")
            return reranked_docs
            
        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            return documents

    def _build_context(self, documents: List[Dict[str, Any]]) -> str:
        """Build context string from retrieved documents."""
        context_parts = []
        
        for i, doc in enumerate(documents, 1):
            filename = doc.get("filename", "Unknown")
            chunk_index = doc.get("chunk_index", 0)
            text = doc.get("text", "")
            quality_score = doc.get("quality_score")
            quality_warning = doc.get("quality_warning")
            
            # Add quality warning if present
            warning_text = ""
            if quality_warning:
                warning_text = f"\n[WARNING: {quality_warning}]"
            elif quality_score is not None and quality_score < 0.5:
                warning_text = f"\n[WARNING: Low quality OCR detected (score: {quality_score:.2f})]"
            
            context_part = f"""
Document {i}: {filename} (Chunk {chunk_index + 1}){warning_text}
{text}
"""
            context_parts.append(context_part.strip())
        
        return "\n\n".join(context_parts)

    def _build_sources(self, documents: List[Dict[str, Any]]) -> str:
        """Build sources string from retrieved documents."""
        sources = []
        
        for doc in documents:
            filename = doc.get("filename", "Unknown")
            chunk_index = doc.get("chunk_index", 0)
            doc_id = doc.get("doc_id", "unknown")
            
            source = f"{filename} (Chunk {chunk_index + 1}, ID: {doc_id})"
            if source not in sources:
                sources.append(source)
        
        return "; ".join(sources)

    def _generate_local_answer(self, prompt: str, model_choice: Optional[str]) -> tuple[str, str]:
        """Generate answer using local LLM."""
        try:
            model = model_choice or self.local_llm.default_model
            
            # Ensure model is available
            if not self.local_llm.ensure_model_available(model):
                raise RuntimeError(f"Model {model} not available")
            
            answer = self.local_llm.generate(
                prompt=prompt,
                model=model,
                max_tokens=2000,
                temperature=0.1,  # Lower temperature for factual responses
            )
            
            return answer, model
            
        except Exception as e:
            logger.error(f"Local LLM generation failed: {e}")
            raise RuntimeError(f"Local LLM generation failed: {e}")

    def _generate_cloud_answer(
        self, 
        prompt: str, 
        cloud_provider: str, 
        model_choice: Optional[str]
    ) -> tuple[str, str]:
        """Generate answer using cloud LLM."""
        try:
            provider = CloudProvider(cloud_provider.lower())
            
            if not self.cloud_llm.check_provider_available(provider):
                raise RuntimeError(f"Provider {cloud_provider} not available (check API key)")
            
            model = model_choice or self.cloud_llm.get_default_model(provider)
            
            answer = self.cloud_llm.generate(
                prompt=prompt,
                provider=provider,
                model=model,
                max_tokens=2000,
                temperature=0.1,  # Lower temperature for factual responses
            )
            
            return answer, f"{cloud_provider}:{model}"
            
        except Exception as e:
            logger.error(f"Cloud LLM generation failed: {e}")
            raise RuntimeError(f"Cloud LLM generation failed: {e}")

    def get_retrieval_stats(self) -> Dict[str, Any]:
        """Get retrieval statistics."""
        doc_stats = self.doc_store.get_stats()
        
        return {
            "total_documents": doc_stats["total_documents"],
            "total_chunks": doc_stats["total_chunks"],
            "retrieval_k": self.retrieval_k,
            "rerank_top_k": self.rerank_top_k,
            "use_reranker": self.use_reranker,
            "reranker_available": self.reranker is not None,
        }

    def validate_setup(self) -> Dict[str, Any]:
        """Validate RAG pipeline setup."""
        result = {
            "doc_store": "ok",
            "local_llm": "not_tested",
            "cloud_llm": "not_tested",
            "reranker": "disabled" if not self.use_reranker else ("ok" if self.reranker else "failed"),
            "total_documents": 0,
        }
        
        try:
            # Check document store
            stats = self.doc_store.get_stats()
            result["total_documents"] = stats["total_documents"]
            
            # Check local LLM
            if self.local_llm.is_server_available():
                result["local_llm"] = "ok"
            else:
                result["local_llm"] = "server_unavailable"
                
            # Check cloud LLM providers
            available_providers = self.cloud_llm.get_available_providers()
            result["cloud_providers"] = [p.value for p in available_providers]
            
        except Exception as e:
            logger.error(f"Setup validation failed: {e}")
            result["error"] = str(e)
            
        return result

    def search_documents(
        self,
        query: str,
        k: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Search documents without generation (for debugging/exploration)."""
        return self.doc_store.search(
            query=query,
            k=k,
            search_k=k,
            filter_metadata=filter_metadata
        ) 