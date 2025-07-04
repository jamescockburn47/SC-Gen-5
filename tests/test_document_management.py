"""Tests for document management endpoints and functionality."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from sc_gen5.services.consult_service import app

client = TestClient(app)


class TestDocumentManagement:
    """Test document management endpoints and functionality."""

    def setup_method(self):
        """Set up test environment."""
        # Create temporary test data directory
        self.test_data_dir = tempfile.mkdtemp()
        self.test_upload_dir = Path(self.test_data_dir) / "uploads"
        self.test_upload_dir.mkdir(exist_ok=True)
        
        # Create a simple test PDF
        self.test_pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(Test Document) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000204 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n292\n%%EOF\n"

    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.test_data_dir, ignore_errors=True)

    @patch('sc_gen5.services.consult_service.doc_store')
    def test_upload_document_success(self, mock_doc_store):
        """Test successful document upload with metadata."""
        # Mock the document store
        mock_doc_store.add_document.return_value = "test_doc_123"
        mock_doc_store.get_document.return_value = {
            "doc_id": "test_doc_123",
            "filename": "test.pdf",
            "extraction_method": "direct",
            "quality_score": 0.85,
            "pages": 1,
            "file_size": 1024,
            "text_length": 500,
            "num_chunks": 2,
            "created_at": "2024-01-01T00:00:00"
        }

        # Test upload
        files = {"file": ("test.pdf", self.test_pdf_content, "application/pdf")}
        response = client.post("/api/documents/upload", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert data["doc_id"] == "test_doc_123"
        assert data["filename"] == "test.pdf"
        assert data["extraction_method"] == "direct"
        assert data["quality_score"] == 0.85
        assert data["pages"] == 1

    @patch('sc_gen5.services.consult_service.doc_store')
    def test_list_documents_with_metadata(self, mock_doc_store):
        """Test listing documents with complete metadata."""
        mock_doc_store.list_documents.return_value = [
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

        response = client.get("/api/documents")
        assert response.status_code == 200
        data = response.json()
        
        assert data["total"] == 2
        documents = data["documents"]
        
        # Check first document
        assert documents[0]["doc_id"] == "doc_1"
        assert documents[0]["extraction_method"] == "direct"
        assert documents[0]["quality_score"] == 0.9
        assert documents[0]["pages"] == 5
        
        # Check second document
        assert documents[1]["doc_id"] == "doc_2"
        assert documents[1]["extraction_method"] == "ocr"
        assert documents[1]["quality_score"] == 0.7
        assert documents[1]["pages"] == 3

    @patch('sc_gen5.services.consult_service.doc_store')
    def test_get_document_with_metadata(self, mock_doc_store):
        """Test getting individual document with metadata."""
        mock_doc_store.get_document.return_value = {
            "doc_id": "test_doc",
            "filename": "test.pdf",
            "extraction_method": "ocr",
            "quality_score": 0.75,
            "pages": 2,
            "file_size": 1024,
            "text_length": 600,
            "num_chunks": 2,
            "created_at": "2024-01-01T00:00:00"
        }

        response = client.get("/api/documents/test_doc")
        assert response.status_code == 200
        data = response.json()
        
        assert data["doc_id"] == "test_doc"
        assert data["extraction_method"] == "ocr"
        assert data["quality_score"] == 0.75
        assert data["pages"] == 2

    @patch('sc_gen5.services.consult_service.doc_store')
    def test_reprocess_document(self, mock_doc_store):
        """Test document reprocessing endpoint."""
        # Mock the reprocessing flow
        mock_doc_store.get_document_file.return_value = (self.test_pdf_content, "test.pdf")
        mock_doc_store.delete_document.return_value = True
        mock_doc_store.add_document.return_value = "test_doc_new"
        mock_doc_store.get_document.return_value = {
            "doc_id": "test_doc_new",
            "filename": "test.pdf",
            "extraction_method": "ocr",  # Changed from direct to OCR
            "quality_score": 0.8,
            "pages": 1,
            "file_size": 1024,
            "text_length": 500,
            "num_chunks": 2,
            "created_at": "2024-01-01T00:00:00"
        }

        response = client.post("/api/documents/test_doc/reprocess")
        assert response.status_code == 200
        data = response.json()
        
        assert data["document"]["doc_id"] == "test_doc_new"
        assert data["document"]["extraction_method"] == "ocr"
        
        # Verify the reprocessing flow was called
        mock_doc_store.get_document_file.assert_called_once_with("test_doc")
        mock_doc_store.delete_document.assert_called_once_with("test_doc")
        mock_doc_store.add_document.assert_called_once()

    @patch('sc_gen5.services.consult_service.doc_store')
    def test_get_document_text(self, mock_doc_store):
        """Test getting document text content."""
        mock_doc_store.get_document_text.return_value = "This is the extracted text content from the document."

        response = client.get("/api/documents/test_doc/text")
        assert response.status_code == 200
        data = response.json()
        
        assert data["text"] == "This is the extracted text content from the document."
        assert data["doc_id"] == "test_doc"

    @patch('sc_gen5.services.consult_service.doc_store')
    def test_download_document(self, mock_doc_store):
        """Test document download endpoint."""
        mock_doc_store.get_document_file.return_value = (self.test_pdf_content, "test.pdf")

        response = client.get("/api/documents/test_doc/download")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert response.headers["content-disposition"] == 'attachment; filename="test.pdf"'
        assert response.content == self.test_pdf_content

    def test_upload_invalid_file(self):
        """Test upload with invalid file type."""
        invalid_content = b"This is not a PDF file"
        files = {"file": ("test.txt", invalid_content, "text/plain")}
        
        response = client.post("/api/documents/upload", files=files)
        assert response.status_code == 400
        assert "Unsupported file format" in response.json()["detail"]

    @patch('sc_gen5.services.consult_service.doc_store')
    def test_document_not_found(self, mock_doc_store):
        """Test getting non-existent document."""
        mock_doc_store.get_document.return_value = None

        response = client.get("/api/documents/nonexistent")
        assert response.status_code == 404
        assert response.json()["detail"] == "Document not found"

    @patch('sc_gen5.services.consult_service.doc_store')
    def test_reprocess_nonexistent_document(self, mock_doc_store):
        """Test reprocessing non-existent document."""
        mock_doc_store.get_document_file.side_effect = FileNotFoundError("Document not found")

        response = client.post("/api/documents/nonexistent/reprocess")
        assert response.status_code == 500
        assert "Failed to reprocess document" in response.json()["detail"]

    @patch('sc_gen5.services.consult_service.doc_store')
    def test_metadata_consistency(self, mock_doc_store):
        """Test that metadata is consistent across all endpoints."""
        # Mock document with complete metadata
        test_doc = {
            "doc_id": "test_doc",
            "filename": "test.pdf",
            "extraction_method": "direct",
            "quality_score": 0.85,
            "pages": 3,
            "file_size": 1024,
            "text_length": 500,
            "num_chunks": 2,
            "created_at": "2024-01-01T00:00:00"
        }
        
        mock_doc_store.get_document.return_value = test_doc
        mock_doc_store.list_documents.return_value = [test_doc]

        # Test individual document endpoint
        response1 = client.get("/api/documents/test_doc")
        assert response1.status_code == 200
        doc1 = response1.json()
        
        # Test list documents endpoint
        response2 = client.get("/api/documents")
        assert response2.status_code == 200
        doc2 = response2.json()["documents"][0]
        
        # Verify metadata is consistent
        for key in ["extraction_method", "quality_score", "pages"]:
            assert doc1[key] == doc2[key] == test_doc[key]

    @patch('sc_gen5.services.consult_service.doc_store')
    def test_metadata_defaults(self, mock_doc_store):
        """Test that metadata defaults are applied when missing."""
        # Mock document with missing metadata
        incomplete_doc = {
            "doc_id": "test_doc",
            "filename": "test.pdf",
            "file_size": 1024,
            "text_length": 500,
            "num_chunks": 2,
            "created_at": "2024-01-01T00:00:00"
            # Missing extraction_method, quality_score, pages
        }
        
        mock_doc_store.get_document.return_value = incomplete_doc
        mock_doc_store.list_documents.return_value = [incomplete_doc]

        # Test individual document endpoint
        response1 = client.get("/api/documents/test_doc")
        assert response1.status_code == 200
        doc1 = response1.json()
        
        # Test list documents endpoint
        response2 = client.get("/api/documents")
        assert response2.status_code == 200
        doc2 = response2.json()["documents"][0]
        
        # Verify defaults are applied
        for doc in [doc1, doc2]:
            assert doc["extraction_method"] == "unknown"
            assert doc["quality_score"] is None
            assert doc["pages"] is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 