"""
Enhanced retrievers for RAG v2 with sophisticated multi-granularity capabilities.
Combines the best features from RAG v1 and RAG v2 for optimal legal document retrieval.
"""

import logging
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass

from fastapi import HTTPException
from src.sc_gen5.core.enhanced_doc_store import EnhancedDocStore
from src.sc_gen5.core.advanced_vector_store import ChunkType
from settings import settings

log = logging.getLogger("lexcognito.rag.v2.enhanced_retrievers")

# Global enhanced document store instance
enhanced_doc_store = EnhancedDocStore()

@dataclass
class EnhancedRetrievalConfig:
    """Enhanced configuration for sophisticated multi-granularity retrieval."""
    # Granularity-specific retrieval counts
    section_k: int = 2      # Get 2 most relevant sections
    paragraph_k: int = 4    # Get 4 relevant paragraphs
    sentence_k: int = 8     # Get 8 relevant sentences
    quote_k: int = 6        # Get 6 relevant quotes/citations
    clause_k: int = 4       # Get 4 relevant legal clauses
    definition_k: int = 3   # Get 3 relevant definitions
    
    # Quality and filtering settings
    score_threshold: float = 0.6  # Similarity threshold
    max_context_length: int = 6000  # Maximum total context length
    deduplicate: bool = True  # Remove duplicate content
    use_hybrid_search: bool = True  # Use hybrid dense+sparse search
    
    # Context merging settings
    preserve_granularity_order: bool = True  # Keep granularity structure
    include_metadata: bool = True  # Include chunk metadata in context
    max_chunks_per_type: int = 3  # Maximum chunks per granularity type

class EnhancedMultiGranularityRetriever:
    """
    Enhanced retriever with sophisticated multi-granularity capabilities.
    
    Features:
    - Multi-granularity retrieval (section, paragraph, sentence, quote, clause, definition)
    - Legal-specific chunking and retrieval
    - Sophisticated ranking and filtering
    - Context-aware merging
    - Quality-based selection
    """
    
    def __init__(self, config: Optional[EnhancedRetrievalConfig] = None):
        self.config = config or EnhancedRetrievalConfig()
        self.doc_store = enhanced_doc_store

    def retrieve_by_granularity(self, question: str, granularity: str) -> List[dict]:
        """Retrieve documents from a specific granularity level."""
        k_map = {
            "section": self.config.section_k,
            "paragraph": self.config.paragraph_k,
            "sentence": self.config.sentence_k,
            "quote": self.config.quote_k,
            "clause": self.config.clause_k,
            "definition": self.config.definition_k
        }
        
        k = k_map.get(granularity, 5)
        
        try:
            results = self.doc_store.search_by_granularity(
                query=question,
                granularity=granularity,
                k=k,
                filter_metadata=None
            )
            return results
        except Exception as e:
            log.error(f"Enhanced retrieval failed for {granularity}: {e}")
            return []
    
    def retrieve_all_granularities(self, question: str) -> Dict[str, List[dict]]:
        """Retrieve documents from all granularity levels with sophisticated ranking."""
        granularities = ["section", "paragraph", "sentence", "quote", "clause", "definition"]
        
        all_results = {}
        
        for granularity in granularities:
            try:
                results = self.retrieve_by_granularity(question, granularity)
                all_results[granularity] = results
                log.debug(f"Retrieved {len(results)} {granularity} results")
            except Exception as e:
                log.warning(f"Failed to retrieve {granularity}: {e}")
                all_results[granularity] = []
        
        return all_results
    
    def _deduplicate_content(self, documents: List[dict]) -> List[dict]:
        """Remove documents with duplicate or highly similar content."""
        if not self.config.deduplicate:
            return documents
        
        seen_content: Set[str] = set()
        unique_docs = []
        
        for doc in documents:
            # Create a more sophisticated signature for the document content
            text = doc.get('text', '').strip().lower()
            
            # Use first 300 chars + last 100 chars for better uniqueness detection
            signature = text[:300] + text[-100:] if len(text) > 400 else text
            
            if signature not in seen_content:
                seen_content.add(signature)
                unique_docs.append(doc)
            else:
                log.debug("Removed duplicate document")
        
        log.debug(f"Deduplication: {len(documents)} -> {len(unique_docs)} documents")
        return unique_docs
    
    def _truncate_to_context_limit(self, context: str) -> str:
        """Truncate context to fit within token limits with smart boundary detection."""
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
        
        # Find last paragraph break
        last_paragraph = truncated.rfind('\n\n')
        
        # Choose the better break point
        break_point = max(last_sentence, last_paragraph)
        
        if break_point > self.config.max_context_length * 0.8:  # If we found a good break point
            truncated = truncated[:break_point + 1]
        
        log.debug(f"Context truncated from {len(context)} to {len(truncated)} characters")
        return truncated
    
    def merge_contexts(self, granular_results: Dict[str, List[dict]]) -> str:
        """Merge retrieved documents into a sophisticated context string."""
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
        
        # Sort by granularity and score
        granularity_order = {
            "section": 0, 
            "paragraph": 1, 
            "clause": 2,
            "definition": 3,
            "quote": 4, 
            "sentence": 5
        }
        
        sorted_docs = sorted(
            unique_docs,
            key=lambda doc: (
                granularity_order.get(doc.get('granularity', 'sentence'), 5),
                -doc.get('final_score', doc.get('score', 0))
            )
        )
        
        # Limit chunks per type
        limited_docs = self._limit_chunks_per_type(sorted_docs)
        
        # Build sophisticated context string
        context_parts = []
        
        # Add sections first (broad context)
        section_docs = [doc for doc in limited_docs if doc.get('granularity') == 'section']
        if section_docs:
            context_parts.append("=== LEGAL SECTIONS ===")
            for i, doc in enumerate(section_docs, 1):
                section_title = doc.get('section', f'Section {i}')
                context_parts.append(f"\n--- {section_title} ---")
                context_parts.append(doc['text'])
        
        # Add paragraphs (medium context)
        paragraph_docs = [doc for doc in limited_docs if doc.get('granularity') == 'paragraph']
        if paragraph_docs:
            context_parts.append("\n\n=== RELEVANT PARAGRAPHS ===")
            for i, doc in enumerate(paragraph_docs, 1):
                context_parts.append(f"\n[PARAGRAPH {i}]: {doc['text']}")
        
        # Add legal clauses
        clause_docs = [doc for doc in limited_docs if doc.get('granularity') == 'clause']
        if clause_docs:
            context_parts.append("\n\n=== LEGAL CLAUSES ===")
            for i, doc in enumerate(clause_docs, 1):
                context_parts.append(f"\n[CLAUSE {i}]: {doc['text']}")
        
        # Add legal definitions
        definition_docs = [doc for doc in limited_docs if doc.get('granularity') == 'definition']
        if definition_docs:
            context_parts.append("\n\n=== LEGAL DEFINITIONS ===")
            for i, doc in enumerate(definition_docs, 1):
                context_parts.append(f"\n[DEFINITION {i}]: {doc['text']}")
        
        # Add quotes (specific references)
        quote_docs = [doc for doc in limited_docs if doc.get('granularity') == 'quote']
        if quote_docs:
            context_parts.append("\n\n=== RELEVANT QUOTES & CITATIONS ===")
            for i, doc in enumerate(quote_docs, 1):
                chunk_type = doc.get('chunk_type', 'quote')
                context_parts.append(f"\n[{chunk_type.upper()} {i}]: {doc['text']}")
        
        # Add detailed sentences (supplementary info)
        sentence_docs = [doc for doc in limited_docs if doc.get('granularity') == 'sentence']
        if sentence_docs:
            context_parts.append("\n\n=== ADDITIONAL DETAILS ===")
            for i, doc in enumerate(sentence_docs, 1):
                context_parts.append(f"\n[DETAIL {i}]: {doc['text']}")
        
        # Join and truncate
        full_context = "\n".join(context_parts)
        truncated_context = self._truncate_to_context_limit(full_context)
        
        log.info(f"Enhanced merged context: {len(limited_docs)} documents, {len(truncated_context)} characters")
        return truncated_context
    
    def _limit_chunks_per_type(self, documents: List[dict]) -> List[dict]:
        """Limit the number of chunks per granularity type."""
        type_counts = {}
        limited_docs = []
        
        for doc in documents:
            doc_type = doc.get('granularity', 'sentence')
            current_count = type_counts.get(doc_type, 0)
            
            if current_count < self.config.max_chunks_per_type:
                limited_docs.append(doc)
                type_counts[doc_type] = current_count + 1
        
        return limited_docs

def retrieve_context(question: str, config: Optional[EnhancedRetrievalConfig] = None) -> str:
    """
    Enhanced main retrieval function that gets context from all granularities and merges.
    This is the primary interface for the LangGraph agent.
    """
    retriever = EnhancedMultiGranularityRetriever(config)
    
    # Retrieve from all granularities
    granular_results = retriever.retrieve_all_granularities(question)
    
    # Merge into single context
    context = retriever.merge_contexts(granular_results)
    
    # Clean up context (escape quotes for prompt injection safety)
    context = context.replace('"', r'\"').replace("'", r"\'")
    
    return context

def get_retrieval_stats() -> Dict[str, Dict]:
    """Get enhanced statistics about available retrievers and their performance."""
    try:
        # Get stats from enhanced document store
        stats = enhanced_doc_store.get_stats()
        
        # Add retriever-specific information
        granularities = ["section", "paragraph", "sentence", "quote", "clause", "definition"]
        
        for granularity in granularities:
            # Check if this granularity has data
            has_data = stats.get("vector_store", {}).get("chunk_types", {}).get(granularity, {}).get("count", 0) > 0
            
            stats[granularity] = {
                "retriever_available": has_data,
                "document_count": stats.get("vector_store", {}).get("chunk_types", {}).get(granularity, {}).get("count", 0),
                "default_k": {
                    "section": 2,
                    "paragraph": 4,
                    "sentence": 8,
                    "quote": 6,
                    "clause": 4,
                    "definition": 3
                }.get(granularity, 5)
            }
        
        return stats
    except Exception as e:
        log.error(f"Failed to get enhanced retrieval stats: {e}")
        # Return default stats indicating no retrievers available
        return {
            "section": {"retriever_available": False, "document_count": 0},
            "paragraph": {"retriever_available": False, "document_count": 0},
            "sentence": {"retriever_available": False, "document_count": 0},
            "quote": {"retriever_available": False, "document_count": 0},
            "clause": {"retriever_available": False, "document_count": 0},
            "definition": {"retriever_available": False, "document_count": 0}
        }

def ensure_retrievers_ready() -> bool:
    """Ensure all enhanced retrievers are ready for use."""
    try:
        # Test retrieval on each granularity
        test_query = "test legal query"
        retriever = EnhancedMultiGranularityRetriever()
        
        success_count = 0
        granularities = ["section", "paragraph", "sentence", "quote", "clause", "definition"]
        
        for granularity in granularities:
            try:
                docs = retriever.retrieve_by_granularity(test_query, granularity)
                if docs is not None:  # Empty list is OK, None means failure
                    success_count += 1
            except Exception as e:
                log.warning(f"Enhanced test retrieval failed for {granularity}: {e}")
        
        ready = success_count >= 3  # Need at least 3 granularities working
        log.info(f"Enhanced retriever readiness: {success_count}/{len(granularities)} granularities ready")
        return ready
        
    except Exception as e:
        log.error(f"Failed to ensure enhanced retrievers ready: {e}")
        return False 