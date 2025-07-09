"""
Multi-granularity retrievers for RAG v2.
Provides retrieval interfaces for chapters, quotes, and chunks with merging utilities.
"""

import logging
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass

from fastapi import HTTPException
from src.sc_gen5.core.doc_store import DocStore
from settings import settings

log = logging.getLogger("lexcognito.rag.v2.retrievers")

doc_store = DocStore()  # Use singleton/global as appropriate

@dataclass
class RetrievalConfig:
    """Configuration for multi-granularity retrieval."""
    sections_k: int = 2      # Get 2 most relevant sections
    quotes_k: int = 10       # Get 10 relevant quotes/citations  
    chunks_k: int = 3        # Get 3 most relevant chunks
    score_threshold: float = 0.8  # Similarity threshold
    max_context_length: int = 4000  # Maximum total context length
    deduplicate: bool = True  # Remove duplicate content

class MultiGranularityRetriever:
    """Retrieves context at multiple granularity levels and merges results."""
    
    def __init__(self, config: Optional[RetrievalConfig] = None):
        self.config = config or RetrievalConfig()
        self.doc_store = doc_store

    def retrieve_by_granularity(self, question: str, granularity: str) -> List[dict]:
        k = {
            "sections": self.config.sections_k,
            "quotes": self.config.quotes_k,
            "chunks": self.config.chunks_k
        }.get(granularity, 5)
        try:
            results = self.doc_store.search(query=question, k=k)
            return results
        except Exception as e:
            log.error(f"DocStore retrieval failed for {granularity}: {e}")
            return []
    
    def retrieve_all_granularities(self, question: str) -> Dict[str, List[dict]]:
        """Retrieve documents from all granularity levels."""
        return {
            "sections": self.retrieve_by_granularity(question, "sections"),
            "quotes": self.retrieve_by_granularity(question, "quotes"),
            "chunks": self.retrieve_by_granularity(question, "chunks"),
        }
    
    def _deduplicate_content(self, documents: List[dict]) -> List[dict]:
        """Remove documents with duplicate or highly similar content."""
        if not self.config.deduplicate:
            return documents
        
        seen_content: Set[str] = set()
        unique_docs = []
        
        for doc in documents:
            # Create a signature for the document content
            content_signature = doc.get('page_content', doc.get('text', '')).strip().lower()[:200]  # First 200 chars
            
            if content_signature not in seen_content:
                seen_content.add(content_signature)
                unique_docs.append(doc)
            else:
                log.debug("Removed duplicate document")
        
        log.debug(f"Deduplication: {len(documents)} -> {len(unique_docs)} documents")
        return unique_docs
    
    def _truncate_to_context_limit(self, context: str) -> str:
        """Truncate context to fit within token limits."""
        if len(context) <= self.config.max_context_length:
            return context
        
        # Truncate at sentence boundary if possible
        truncated = context[:self.config.max_context_length]
        
        # Find last sentence ending
        last_sentence = max(
            truncated.rfind('.'),
            truncated.rfind('!'),
            truncated.rfind('?')
        )
        
        if last_sentence > self.config.max_context_length * 0.8:  # If we found a good break point
            truncated = truncated[:last_sentence + 1]
        
        log.debug(f"Context truncated from {len(context)} to {len(truncated)} characters")
        return truncated
    
    def merge_contexts(self, granular_results: Dict[str, List[dict]]) -> str:
        """Merge retrieved documents into a single context string."""
        all_docs = []
        
        # Collect documents from all granularities
        for granularity, docs in granular_results.items():
            for doc in docs:
                # Add granularity info to metadata if not present
                if 'granularity' not in doc:
                    doc['granularity'] = granularity
                all_docs.append(doc)
        
        # Deduplicate
        unique_docs = self._deduplicate_content(all_docs)
        
        # Sort by granularity (sections first, then quotes, then chunks)
        granularity_order = {"sections": 0, "quotes": 1, "chunks": 2}
        sorted_docs = sorted(
            unique_docs,
            key=lambda doc: granularity_order.get(doc.get('granularity', 'chunks'), 2)
        )
        
        # Build context string
        context_parts = []
        
        # Add sections first (broad context)
        section_docs = [doc for doc in sorted_docs if doc.get('granularity') == 'sections']
        if section_docs:
            context_parts.append("=== LEGAL SECTIONS ===")
            for i, doc in enumerate(section_docs, 1):
                section_title = doc.get('section', f'Section {i}')
                context_parts.append(f"\n--- {section_title} ---")
                context_parts.append(doc.get('page_content', doc.get('text', '')))
        
        # Add quotes (specific references)
        quote_docs = [doc for doc in sorted_docs if doc.get('granularity') == 'quotes']
        if quote_docs:
            context_parts.append("\n\n=== RELEVANT QUOTES & CITATIONS ===")
            for i, doc in enumerate(quote_docs, 1):
                chunk_type = doc.get('chunk_type', 'quote')
                context_parts.append(f"\n[{chunk_type.upper()} {i}]: {doc.get('page_content', doc.get('text', ''))}")
        
        # Add detailed chunks (supplementary info)
        chunk_docs = [doc for doc in sorted_docs if doc.get('granularity') == 'chunks']
        if chunk_docs:
            context_parts.append("\n\n=== ADDITIONAL DETAILS ===")
            for i, doc in enumerate(chunk_docs, 1):
                context_parts.append(f"\n[DETAIL {i}]: {doc.get('page_content', doc.get('text', ''))}")
        
        # Join and truncate
        full_context = "\n".join(context_parts)
        truncated_context = self._truncate_to_context_limit(full_context)
        
        log.info(f"Merged context: {len(sorted_docs)} documents, {len(truncated_context)} characters")
        return truncated_context

def retrieve_context(question: str, config: Optional[RetrievalConfig] = None) -> str:
    """
    Main retrieval function that gets context from all granularities and merges.
    This is the primary interface for the LangGraph agent.
    """
    retriever = MultiGranularityRetriever(config)
    
    # Retrieve from all granularities
    granular_results = retriever.retrieve_all_granularities(question)
    
    # Merge into single context
    context = retriever.merge_contexts(granular_results)
    
    # Clean up context (escape quotes for prompt injection safety)
    context = context.replace('"', r'\"').replace("'", r"\'")
    
    return context

def get_retrieval_stats() -> Dict[str, Dict]:
    """Get statistics about available retrievers and their performance."""
    try:
        # Get stats from DocStore
        stats = doc_store.get_stats()
        
        # Add retriever-specific information
        for granularity in stats:
            if stats[granularity].get("document_count", 0) > 0:
                stats[granularity]["retriever_available"] = True
                stats[granularity]["default_k"] = {
                    "sections": 2,
                    "quotes": 10,
                    "chunks": 3
                }.get(granularity, 5)
            else:
                stats[granularity]["retriever_available"] = False
        
        return stats
    except Exception as e:
        log.error(f"Failed to get retrieval stats: {e}")
        # Return default stats indicating no retrievers available
        return {
            "sections": {"retriever_available": False, "document_count": 0},
            "quotes": {"retriever_available": False, "document_count": 0},
            "chunks": {"retriever_available": False, "document_count": 0}
        }

def ensure_retrievers_ready() -> bool:
    """Ensure all retrievers are ready for use."""
    try:
        # Test retrieval on each granularity
        test_query = "test legal query"
        retriever = MultiGranularityRetriever()
        
        success_count = 0
        for granularity in ["sections", "quotes", "chunks"]:
            try:
                docs = retriever.retrieve_by_granularity(test_query, granularity)
                if docs is not None:  # Empty list is OK, None means failure
                    success_count += 1
            except Exception as e:
                log.warning(f"Test retrieval failed for {granularity}: {e}")
        
        ready = success_count == 3
        log.info(f"Retriever readiness: {success_count}/3 granularities ready")
        return ready
        
    except Exception as e:
        log.error(f"Failed to ensure retrievers ready: {e}")
        return False