"""Tests for RAGPipeline module."""

import pytest
from unittest.mock import Mock, patch

from sc_gen5.core.rag_pipeline import RAGPipeline


@pytest.fixture
def mock_doc_store():
    """Mock DocStore for testing."""
    store = Mock()
    store.search.return_value = [
        {"id": 1, "text": "Sample legal text", "filename": "contract.pdf"},
        {"id": 2, "text": "Another clause", "filename": "contract.pdf"},
    ]
    store.get_stats.return_value = {"total_documents": 5, "total_chunks": 50}
    return store


@pytest.fixture
def mock_local_llm():
    """Mock LocalLLMGenerator for testing."""
    llm = Mock()
    llm.ensure_model_available.return_value = True
    llm.generate.return_value = "Generated legal analysis"
    llm.is_server_available.return_value = True
    llm.default_model = "mixtral:latest"
    return llm


@pytest.fixture
def mock_cloud_llm():
    """Mock CloudLLMGenerator for testing."""
    llm = Mock()
    llm.check_provider_available.return_value = True
    llm.get_default_model.return_value = "gpt-4o"
    llm.generate.return_value = "Generated cloud analysis"
    llm.get_available_providers.return_value = []
    return llm


@pytest.fixture
def rag_pipeline(mock_doc_store, mock_local_llm, mock_cloud_llm):
    """Create RAGPipeline for testing."""
    return RAGPipeline(
        doc_store=mock_doc_store,
        local_llm=mock_local_llm,
        cloud_llm=mock_cloud_llm,
    )


class TestRAGPipeline:
    """Test cases for RAGPipeline class."""
    
    def test_initialization(self, mock_doc_store, mock_local_llm, mock_cloud_llm):
        """Test RAGPipeline initialization."""
        pipeline = RAGPipeline(
            doc_store=mock_doc_store,
            local_llm=mock_local_llm,
            cloud_llm=mock_cloud_llm,
        )
        
        assert pipeline.doc_store == mock_doc_store
        assert pipeline.local_llm == mock_local_llm
        assert pipeline.cloud_llm == mock_cloud_llm
        assert pipeline.retrieval_k == 18
        assert pipeline.rerank_top_k == 6
    
    def test_answer_local_llm(self, rag_pipeline):
        """Test answer generation with local LLM."""
        result = rag_pipeline.answer(
            question="What are the key terms?",
            cloud_allowed=False,
            matter_id="test-001",
        )
        
        assert result["answer"] == "Generated legal analysis"
        assert result["model_used"] == "mixtral:latest"
        assert result["matter_id"] == "test-001"
        assert result["retrieved_chunks"] == 2
        assert "sources" in result
        
        # Verify doc store search was called
        rag_pipeline.doc_store.search.assert_called_once()
        
        # Verify local LLM was called
        rag_pipeline.local_llm.generate.assert_called_once()
    
    def test_answer_cloud_llm(self, rag_pipeline):
        """Test answer generation with cloud LLM."""
        with patch('sc_gen5.core.rag_pipeline.CloudProvider') as mock_provider:
            mock_provider.return_value = "openai"
            
            result = rag_pipeline.answer(
                question="What are the risks?",
                cloud_allowed=True,
                cloud_provider="openai",
                matter_id="test-002",
            )
            
            assert result["answer"] == "Generated cloud analysis"
            assert "openai" in result["model_used"]
            assert result["matter_id"] == "test-002"
            
            # Verify cloud LLM was called
            rag_pipeline.cloud_llm.generate.assert_called_once()
    
    def test_answer_no_documents(self, rag_pipeline):
        """Test answer when no documents found."""
        rag_pipeline.doc_store.search.return_value = []
        
        result = rag_pipeline.answer(
            question="Test question",
            matter_id="test-003",
        )
        
        assert "couldn't find any relevant documents" in result["answer"]
        assert result["model_used"] == "none"
        assert result["retrieved_chunks"] == 0
    
    def test_answer_error_handling(self, rag_pipeline):
        """Test error handling in answer generation."""
        rag_pipeline.local_llm.generate.side_effect = Exception("LLM error")
        
        result = rag_pipeline.answer(
            question="Test question",
            matter_id="test-004",
        )
        
        assert "encountered an error" in result["answer"]
        assert result["model_used"] == "error"
    
    def test_build_context(self, rag_pipeline):
        """Test context building from documents."""
        documents = [
            {"filename": "test.pdf", "chunk_index": 0, "text": "First chunk"},
            {"filename": "test.pdf", "chunk_index": 1, "text": "Second chunk"},
        ]
        
        context = rag_pipeline._build_context(documents)
        
        assert "Document 1: test.pdf (Chunk 1)" in context
        assert "Document 2: test.pdf (Chunk 2)" in context
        assert "First chunk" in context
        assert "Second chunk" in context
    
    def test_build_sources(self, rag_pipeline):
        """Test sources string building."""
        documents = [
            {"filename": "contract.pdf", "chunk_index": 0, "doc_id": "doc_001"},
            {"filename": "policy.pdf", "chunk_index": 1, "doc_id": "doc_002"},
        ]
        
        sources = rag_pipeline._build_sources(documents)
        
        assert "contract.pdf (Chunk 1, ID: doc_001)" in sources
        assert "policy.pdf (Chunk 2, ID: doc_002)" in sources
        assert ";" in sources
    
    def test_get_retrieval_stats(self, rag_pipeline):
        """Test retrieval statistics."""
        stats = rag_pipeline.get_retrieval_stats()
        
        assert "total_documents" in stats
        assert "total_chunks" in stats
        assert "retrieval_k" in stats
        assert "rerank_top_k" in stats
        assert "use_reranker" in stats
        assert "reranker_available" in stats
        
        assert stats["retrieval_k"] == 18
        assert stats["rerank_top_k"] == 6
    
    def test_validate_setup(self, rag_pipeline):
        """Test setup validation."""
        validation = rag_pipeline.validate_setup()
        
        assert "doc_store" in validation
        assert "local_llm" in validation
        assert "cloud_llm" in validation
        assert "total_documents" in validation
        
        assert validation["doc_store"] == "ok"
        assert validation["local_llm"] == "ok"
    
    def test_search_documents(self, rag_pipeline):
        """Test document search without generation."""
        results = rag_pipeline.search_documents("test query", k=5)
        
        assert len(results) == 2
        rag_pipeline.doc_store.search.assert_called_with(
            query="test query",
            k=5,
            search_k=5,
            filter_metadata=None
        ) 