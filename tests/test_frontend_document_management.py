"""Tests for React frontend document management functionality."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from sc_gen5.services.consult_service import app

client = TestClient(app)


class TestFrontendDocumentManagement:
    """Test frontend document management functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.test_data_dir = tempfile.mkdtemp()
        self.test_upload_dir = Path(self.test_data_dir) / "uploads"
        self.test_upload_dir.mkdir(exist_ok=True)
        
        # Sample document data for testing
        self.sample_documents = [
            {
                "doc_id": "doc_1",
                "filename": "document1.pdf",
                "extraction_method": "direct",
                "quality_score": 0.9,
                "pages": 5,
                "file_size": 2048,
                "text_length": 1000,
                "num_chunks": 3,
                "created_at": "2024-01-01T00:00:00"
            },
            {
                "doc_id": "doc_2",
                "filename": "document2.pdf",
                "extraction_method": "ocr",
                "quality_score": 0.7,
                "pages": 3,
                "file_size": 1536,
                "text_length": 800,
                "num_chunks": 2,
                "created_at": "2024-01-02T00:00:00"
            }
        ]

    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.test_data_dir, ignore_errors=True)

    @patch('sc_gen5.services.consult_service.doc_store')
    def test_document_listing_api_response(self, mock_doc_store):
        """Test that the API returns the expected format for frontend consumption."""
        mock_doc_store.list_documents.return_value = self.sample_documents

        response = client.get("/api/documents")
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "documents" in data
        assert "total" in data
        assert data["total"] == 2
        
        # Verify each document has required fields
        for doc in data["documents"]:
            required_fields = [
                "doc_id", "filename", "extraction_method", 
                "quality_score", "pages", "file_size", 
                "text_length", "num_chunks", "created_at"
            ]
            for field in required_fields:
                assert field in doc

    @patch('sc_gen5.services.consult_service.doc_store')
    def test_document_metadata_display_format(self, mock_doc_store):
        """Test that document metadata is formatted correctly for frontend display."""
        mock_doc_store.get_document.return_value = self.sample_documents[0]

        response = client.get("/api/documents/doc_1")
        assert response.status_code == 200
        doc = response.json()
        
        # Test extraction method formatting
        assert doc["extraction_method"] in ["direct", "ocr", "unknown"]
        
        # Test quality score formatting (should be float between 0 and 1)
        if doc["quality_score"] is not None:
            assert isinstance(doc["quality_score"], (int, float))
            assert 0 <= doc["quality_score"] <= 1
        
        # Test pages formatting (should be integer)
        if doc["pages"] is not None:
            assert isinstance(doc["pages"], int)
            assert doc["pages"] > 0

    @patch('sc_gen5.services.consult_service.doc_store')
    def test_reprocessing_api_response(self, mock_doc_store):
        """Test that reprocessing API returns the expected format."""
        # Mock reprocessing flow
        mock_doc_store.get_document_file.return_value = (b"test content", "test.pdf")
        mock_doc_store.delete_document.return_value = True
        mock_doc_store.add_document.return_value = "doc_1_new"
        mock_doc_store.get_document.return_value = {
            **self.sample_documents[0],
            "doc_id": "doc_1_new",
            "extraction_method": "ocr",  # Changed from direct to OCR
            "quality_score": 0.8
        }

        response = client.post("/api/documents/doc_1/reprocess")
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "document" in data
        doc = data["document"]
        assert doc["doc_id"] == "doc_1_new"
        assert doc["extraction_method"] == "ocr"
        assert doc["quality_score"] == 0.8

    @patch('sc_gen5.services.consult_service.doc_store')
    def test_document_text_api_response(self, mock_doc_store):
        """Test that document text API returns the expected format."""
        mock_doc_store.get_document_text.return_value = "This is the extracted text content."

        response = client.get("/api/documents/doc_1/text")
        assert response.status_code == 200
        data = response.json()
        
        assert "text" in data
        assert "doc_id" in data
        assert data["text"] == "This is the extracted text content."
        assert data["doc_id"] == "doc_1"

    @patch('sc_gen5.services.consult_service.doc_store')
    def test_document_download_api_response(self, mock_doc_store):
        """Test that document download API returns the expected format."""
        test_content = b"PDF content here"
        mock_doc_store.get_document_file.return_value = (test_content, "test.pdf")

        response = client.get("/api/documents/doc_1/download")
        assert response.status_code == 200
        
        # Verify headers
        assert response.headers["content-type"] == "application/pdf"
        assert 'attachment; filename="test.pdf"' in response.headers["content-disposition"]
        
        # Verify content
        assert response.content == test_content

    def test_error_handling_for_frontend(self):
        """Test that error responses are formatted appropriately for frontend consumption."""
        # Test 404 error
        response = client.get("/api/documents/nonexistent")
        assert response.status_code == 404
        error_data = response.json()
        assert "detail" in error_data
        assert error_data["detail"] == "Document not found"

        # Test 400 error for invalid file upload
        invalid_content = b"This is not a PDF"
        files = {"file": ("test.txt", invalid_content, "text/plain")}
        response = client.post("/api/documents/upload", files=files)
        assert response.status_code == 400
        error_data = response.json()
        assert "detail" in error_data
        assert "Unsupported file format" in error_data["detail"]

    @patch('sc_gen5.services.consult_service.doc_store')
    def test_metadata_consistency_across_endpoints(self, mock_doc_store):
        """Test that metadata is consistent across all endpoints for frontend reliability."""
        test_doc = self.sample_documents[0]
        mock_doc_store.get_document.return_value = test_doc
        mock_doc_store.list_documents.return_value = [test_doc]

        # Test individual document endpoint
        response1 = client.get("/api/documents/doc_1")
        doc1 = response1.json()
        
        # Test list documents endpoint
        response2 = client.get("/api/documents")
        doc2 = response2.json()["documents"][0]
        
        # Verify metadata consistency
        metadata_fields = ["extraction_method", "quality_score", "pages"]
        for field in metadata_fields:
            assert doc1[field] == doc2[field] == test_doc[field]

    @patch('sc_gen5.services.consult_service.doc_store')
    def test_frontend_upload_flow(self, mock_doc_store):
        """Test the complete upload flow that the frontend would use."""
        # Mock successful upload
        mock_doc_store.add_document.return_value = "new_doc_123"
        mock_doc_store.get_document.return_value = {
            "doc_id": "new_doc_123",
            "filename": "uploaded.pdf",
            "extraction_method": "direct",
            "quality_score": 0.85,
            "pages": 2,
            "file_size": 1024,
            "text_length": 500,
            "num_chunks": 2,
            "created_at": "2024-01-01T00:00:00"
        }

        # Simulate file upload
        test_pdf = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n"
        files = {"file": ("uploaded.pdf", test_pdf, "application/pdf")}
        
        response = client.post("/api/documents/upload", files=files)
        assert response.status_code == 200
        
        upload_result = response.json()
        assert upload_result["doc_id"] == "new_doc_123"
        assert upload_result["filename"] == "uploaded.pdf"
        assert upload_result["extraction_method"] == "direct"
        assert upload_result["quality_score"] == 0.85
        assert upload_result["pages"] == 2

    @patch('sc_gen5.services.consult_service.doc_store')
    def test_frontend_reprocessing_flow(self, mock_doc_store):
        """Test the complete reprocessing flow that the frontend would use."""
        # Mock reprocessing
        mock_doc_store.get_document_file.return_value = (b"test content", "test.pdf")
        mock_doc_store.delete_document.return_value = True
        mock_doc_store.add_document.return_value = "doc_1_reprocessed"
        mock_doc_store.get_document.return_value = {
            "doc_id": "doc_1_reprocessed",
            "filename": "test.pdf",
            "extraction_method": "ocr",  # Changed from direct to OCR
            "quality_score": 0.8,
            "pages": 2,
            "file_size": 1024,
            "text_length": 500,
            "num_chunks": 2,
            "created_at": "2024-01-01T00:00:00"
        }

        # Simulate reprocessing request
        response = client.post("/api/documents/doc_1/reprocess")
        assert response.status_code == 200
        
        reprocess_result = response.json()
        assert "document" in reprocess_result
        doc = reprocess_result["document"]
        assert doc["doc_id"] == "doc_1_reprocessed"
        assert doc["extraction_method"] == "ocr"
        assert doc["quality_score"] == 0.8

    def test_api_endpoint_availability(self):
        """Test that all required API endpoints are available for frontend."""
        required_endpoints = [
            ("GET", "/api/documents"),
            ("POST", "/api/documents/upload"),
            ("GET", "/api/documents/{doc_id}"),
            ("GET", "/api/documents/{doc_id}/text"),
            ("GET", "/api/documents/{doc_id}/download"),
            ("POST", "/api/documents/{doc_id}/reprocess"),
        ]
        
        for method, endpoint in required_endpoints:
            # Test with a dummy doc_id for endpoints that require it
            test_endpoint = endpoint.replace("{doc_id}", "test_doc")
            
            if method == "GET":
                response = client.get(test_endpoint)
            elif method == "POST":
                response = client.post(test_endpoint)
            
            # We don't care about the specific status code here,
            # just that the endpoint exists and doesn't return 404
            assert response.status_code != 404, f"Endpoint {method} {test_endpoint} not found"


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 