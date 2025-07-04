"""Tests for consultation API service."""

import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

# Mock the components before importing the app
with patch('sc_gen5.services.consult_service.DocStore'), \
     patch('sc_gen5.services.consult_service.RAGPipeline'):
    from sc_gen5.services.consult_service import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_rag_pipeline():
    """Mock RAG pipeline."""
    pipeline = Mock()
    pipeline.answer.return_value = {
        "answer": "This is a legal analysis response",
        "sources": "contract.pdf (Chunk 1, ID: doc_001)",
        "matter_id": "test-001",
        "model_used": "mixtral:latest",
        "retrieved_chunks": 3,
        "context_length": 1200,
    }
    pipeline.validate_setup.return_value = {
        "doc_store": "ok",
        "local_llm": "ok",
        "cloud_providers": ["openai"],
        "total_documents": 5,
    }
    pipeline.search_documents.return_value = [
        {"id": 1, "text": "Sample text", "filename": "test.pdf"}
    ]
    pipeline.get_retrieval_stats.return_value = {
        "total_documents": 5,
        "total_chunks": 50,
        "retrieval_k": 18,
        "rerank_top_k": 6,
    }
    return pipeline


@pytest.fixture
def mock_doc_store():
    """Mock document store."""
    store = Mock()
    store.get_stats.return_value = {
        "total_documents": 5,
        "total_chunks": 50,
        "total_text_length": 10000,
        "vector_store": {"total_embeddings": 50},
        "data_dir": "/test/data",
        "chunk_size": 400,
        "chunk_overlap": 80,
    }
    store.list_documents.return_value = [
        {"doc_id": "doc_001", "filename": "test.pdf", "created_at": "2023-01-01"},
    ]
    store.get_document.return_value = {
        "doc_id": "doc_001",
        "filename": "test.pdf",
        "file_size": 1024,
        "created_at": "2023-01-01",
    }
    return store


class TestConsultAPI:
    """Test cases for consultation API."""
    
    @patch('sc_gen5.services.consult_service.rag_pipeline')
    def test_consult_endpoint(self, mock_pipeline_global, client, mock_rag_pipeline):
        """Test consultation endpoint."""
        mock_pipeline_global = mock_rag_pipeline
        
        request_data = {
            "matter_id": "test-001",
            "question": "What are the key terms in this contract?",
            "cloud_allowed": False,
            "model": "mixtral",
        }
        
        response = client.post("/consult", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["answer"] == "This is a legal analysis response"
        assert data["sources"] == "contract.pdf (Chunk 1, ID: doc_001)"
        assert data["matter_id"] == "test-001"
        assert data["model_used"] == "mixtral:latest"
        assert data["retrieved_chunks"] == 3
    
    @patch('sc_gen5.services.consult_service.rag_pipeline')
    @patch('sc_gen5.services.consult_service.doc_store')
    def test_health_endpoint(self, mock_store_global, mock_pipeline_global, 
                           client, mock_doc_store, mock_rag_pipeline):
        """Test health check endpoint."""
        mock_store_global = mock_doc_store
        mock_pipeline_global = mock_rag_pipeline
        
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert "doc_store" in data
        assert "rag_pipeline" in data
    
    def test_consult_invalid_provider(self, client):
        """Test consultation with invalid cloud provider."""
        request_data = {
            "matter_id": "test-002",
            "question": "Test question",
            "cloud_allowed": True,
            "cloud_provider": "invalid_provider",
        }
        
        response = client.post("/consult", json=request_data)
        
        assert response.status_code == 400
        assert "Invalid cloud provider" in response.json()["detail"]
    
    def test_consult_missing_fields(self, client):
        """Test consultation with missing required fields."""
        request_data = {
            "question": "Test question",
            # Missing matter_id
        }
        
        response = client.post("/consult", json=request_data)
        
        assert response.status_code == 422  # Validation error
    
    @patch('sc_gen5.services.consult_service.doc_store')
    def test_list_documents(self, mock_store_global, client, mock_doc_store):
        """Test document listing endpoint."""
        mock_store_global = mock_doc_store
        
        response = client.get("/documents")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "documents" in data
        assert "total" in data
        assert data["total"] == 1
        assert len(data["documents"]) == 1
    
    @patch('sc_gen5.services.consult_service.doc_store')
    def test_get_document(self, mock_store_global, client, mock_doc_store):
        """Test getting specific document."""
        mock_store_global = mock_doc_store
        
        response = client.get("/documents/doc_001")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["doc_id"] == "doc_001"
        assert data["filename"] == "test.pdf"
    
    @patch('sc_gen5.services.consult_service.doc_store')
    def test_get_document_not_found(self, mock_store_global, client, mock_doc_store):
        """Test getting non-existent document."""
        mock_doc_store.get_document.return_value = None
        mock_store_global = mock_doc_store
        
        response = client.get("/documents/nonexistent")
        
        assert response.status_code == 404
        assert "Document not found" in response.json()["detail"]
    
    @patch('sc_gen5.services.consult_service.rag_pipeline')
    def test_search_documents(self, mock_pipeline_global, client, mock_rag_pipeline):
        """Test document search endpoint."""
        mock_pipeline_global = mock_rag_pipeline
        
        response = client.post("/search?query=test&k=5")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "results" in data
        assert "total" in data
        assert len(data["results"]) == 1
    
    @patch('sc_gen5.services.consult_service.doc_store')
    @patch('sc_gen5.services.consult_service.rag_pipeline')
    def test_get_stats(self, mock_pipeline_global, mock_store_global,
                      client, mock_doc_store, mock_rag_pipeline):
        """Test statistics endpoint."""
        mock_store_global = mock_doc_store
        mock_pipeline_global = mock_rag_pipeline
        
        response = client.get("/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "document_store" in data
        assert "rag_pipeline" in data
        
        # Check document store stats
        doc_stats = data["document_store"]
        assert doc_stats["total_documents"] == 5
        assert doc_stats["chunk_size"] == 400
        
        # Check RAG pipeline stats
        rag_stats = data["rag_pipeline"]
        assert rag_stats["retrieval_k"] == 18


class TestConsultAPIValidation:
    """Test request validation for consultation API."""
    
    def test_valid_request(self, client):
        """Test valid consultation request."""
        request_data = {
            "matter_id": "matter-123",
            "question": "What are the liability terms?",
            "cloud_allowed": True,
            "cloud_provider": "openai",
            "model": "gpt-4o",
            "matter_type": "contract",
            "filter_metadata": {"source": "upload"},
        }
        
        # Should not raise validation error
        response = client.post("/consult", json=request_data)
        # May fail due to missing pipeline, but validation should pass
        assert response.status_code != 422
    
    def test_optional_fields(self, client):
        """Test request with only required fields."""
        request_data = {
            "matter_id": "matter-456",
            "question": "What is the termination clause?",
        }
        
        response = client.post("/consult", json=request_data)
        # Should not raise validation error
        assert response.status_code != 422 