"""RAG pipeline for legal document analysis and consultation."""

import logging
from typing import Any, Dict, List, Optional

from .cloud_llm import CloudLLMGenerator, CloudProvider
from .doc_store import DocStore
from .local_llm import LocalLLMGenerator
from .protocols import StrategicProtocols
from .legal_prompts import LegalPromptBuilder, LegalModelSelector

logger = logging.getLogger(__name__)


class RAGPipeline:
    """Retrieval-Augmented Generation pipeline."""

    def __init__(
        self,
        doc_store: DocStore,
        local_llm: Optional[LocalLLMGenerator] = None,
        cloud_llm: Optional[CloudLLMGenerator] = None,
        retrieval_k: int = 50,
        rerank_top_k: int = 25,
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
        chunk_limit: Optional[int] = None,
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
            # Step 1: Auto-adjust chunk limits based on query type
            retrieval_k, final_k = self._get_smart_chunk_limits(question, chunk_limit)
            
            # Step 2: Retrieve relevant documents
            retrieved_docs = self.doc_store.search(
                query=question,
                k=retrieval_k,
                filter_metadata=filter_metadata
            )
            
            if not retrieved_docs:
                return {
                    "answer": "I couldn't find any relevant documents to answer your question. Please ensure you have uploaded relevant documents to the system.",
                    "sources": [],
                    "matter_id": matter_id,
                    "model_used": "none",
                    "retrieved_chunks": 0,
                }
            
            logger.info(f"Retrieved {len(retrieved_docs)} document chunks")
            
            # Step 3: Rerank if enabled
            final_docs = self._rerank_documents(question, retrieved_docs) if self.use_reranker else retrieved_docs
            final_docs = final_docs[:final_k]
            
            # Step 3: Build context
            context = self._build_context(final_docs)
            
            # Step 4: Generate legal analysis prompt using IRAC methodology
            prompt = LegalPromptBuilder.build_legal_analysis_prompt(
                question=question,
                context_documents=context,
                matter_type=matter_type,
                analysis_style="comprehensive"
            )
            
            # Step 5: Generate answer
            if cloud_allowed and cloud_provider:
                answer, model_used = self._generate_cloud_answer(
                    prompt, cloud_provider, model_choice
                )
            else:
                answer, model_used = self._generate_local_answer(prompt, model_choice)
            
            # Step 5.5: Add grounding verification warning
            answer = self._add_grounding_verification(answer)
            
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
                "sources": [],
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
            # Generate standalone legal prompt (no document context) using IRAC methodology
            prompt = LegalPromptBuilder.build_legal_analysis_prompt(
                question=question,
                context_documents="No specific documents provided. Base analysis on general legal principles.",
                matter_type=matter_type,
                analysis_style="comprehensive"
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
                "sources": [],  # Empty array for direct queries
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
                "sources": [],
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
                
            logger.info(f"Reranked {len(reranked_docs)} document chunks")
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

    def _build_sources(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Build sources array from retrieved documents."""
        sources = []
        seen_sources = set()
        
        for doc in documents:
            filename = doc.get("filename", "Unknown")
            chunk_index = doc.get("chunk_index", 0)
            doc_id = doc.get("doc_id", "unknown")
            text = doc.get("text", "")
            
            # Create unique identifier to avoid duplicates
            source_key = f"{doc_id}_{chunk_index}"
            if source_key not in seen_sources:
                source_obj = {
                    "document_id": doc_id,
                    "filename": filename,
                    "relevance_score": doc.get("score", 0.5),  # Use search score if available
                    "text_excerpt": text[:200] + "..." if len(text) > 200 else text,
                    "page_number": None  # Could be extracted from metadata if available
                }
                sources.append(source_obj)
                seen_sources.add(source_key)
        
        return sources

    def _get_smart_chunk_limits(self, question: str, chunk_limit: Optional[int] = None) -> tuple[int, int]:
        """Intelligently determine chunk limits based on query type."""
        if chunk_limit:
            return min(chunk_limit, 100), chunk_limit
        
        question_lower = question.lower()
        
        # Detect query type and set appropriate limits (balanced for performance)
        if any(word in question_lower for word in ['summarize', 'summarise', 'summary', 'overview', 'comprehensive', 'complete', 'full']):
            # Document summary needs high coverage
            return 60, 40  # 34% coverage
        elif any(word in question_lower for word in ['thorough', 'detailed', 'analyze', 'analyse', 'review', 'examine', 'all', 'every']):
            # Detailed analysis needs good coverage
            return 50, 30  # 25% coverage  
        elif any(word in question_lower for word in ['find', 'search', 'locate', 'identify', 'position', 'stance', 'view']):
            # Search tasks need broad initial retrieval
            return 55, 25  # 21% coverage
        else:
            # Standard questions use default
            return self.retrieval_k, self.rerank_top_k

    def _add_grounding_verification(self, answer: str) -> str:
        """Add verification warning and check for obvious hallucinations."""
        
        # Check for common hallucination patterns
        hallucination_indicators = [
            " v. ",  # Case citations like "Smith v. Jones"
            " LLC)",  # Made-up company references
            "section ",  # Specific statutory references
            "paragraph ",  # Specific document references
            "subsection ",  # Legal subsections
            "$",  # Dollar amounts
            "per annum",  # Financial terms
            "Judge ",  # Specific judge names
        ]
        
        warning_level = "⚠️"
        for indicator in hallucination_indicators:
            if indicator in answer:
                warning_level = "🚨 HIGH RISK"
                break
                
        verification_warning = f"\n\n{warning_level} VERIFICATION REQUIRED: This analysis is based on the provided documents. Users should verify all factual claims, legal citations, and specific details against the original source materials before relying on this analysis for legal decisions."
        
        if warning_level == "🚨 HIGH RISK":
            verification_warning += "\n\n🚨 WARNING: This response contains specific legal details that may require additional verification. Cross-check all citations, amounts, and legal references."
            
        return answer + verification_warning

    def _generate_local_answer(self, prompt: str, model_choice: Optional[str]) -> tuple[str, str]:
        """Generate answer using local LLM with proper model selection."""
        try:
            # Get available models
            available_models = self.local_llm.list_models()
            
            # Use legal model selector if no specific model chosen
            if not model_choice:
                model = LegalModelSelector.select_model_for_query(
                    query=prompt[:200],  # Use first part of prompt for analysis
                    available_models=available_models
                )
            else:
                model = model_choice
                
            # Ensure we don't use lawma-8b for text generation
            if "lawma-8b" in model and "classify" not in prompt.lower():
                logger.warning(f"Avoiding lawma-8b for text generation, switching to mixtral")
                model = "mixtral:latest" if "mixtral:latest" in available_models else available_models[0]
            
            # Ensure model is available
            if not self.local_llm.ensure_model_available(model):
                # Fallback to first available model
                model = available_models[0] if available_models else "mixtral:latest"
                if not self.local_llm.ensure_model_available(model):
                    raise RuntimeError(f"No models available")
            
            answer = self.local_llm.generate(
                prompt=prompt,
                model=model,
                max_tokens=2000,
                temperature=0.0,  # Zero temperature to reduce hallucination
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