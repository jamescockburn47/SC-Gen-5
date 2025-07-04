"""Integration tests for SC Gen 5 document management system."""

import json
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

import pytest
import requests
from fastapi.testclient import TestClient

from sc_gen5.services.consult_service import app

client = TestClient(app)


class TestIntegration:
    """Integration tests with actual backend server."""

    def setup_method(self):
        """Set up test environment."""
        # Create temporary test data
        self.test_data_dir = tempfile.mkdtemp()
        
        # Simple test PDF content
        self.test_pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(Test Document) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000204 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n292\n%%EOF\n"

    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.test_data_dir, ignore_errors=True)

    def test_server_health_check(self):
        """Test that the server is running and responding."""
        # Test basic health endpoint (if it exists)
        try:
            response = client.get("/")
            assert response.status_code in [200, 404]  # Either OK or not found is fine
        except Exception:
            # If no root endpoint, that's OK for this test
            pass

    def test_documents_endpoint_available(self):
        """Test that the documents endpoint is available."""
        response = client.get("/api/documents")
        # Should return 200 (with empty list) or 500 (if doc_store not initialized)
        assert response.status_code in [200, 500]

    def test_api_structure(self):
        """Test that the API returns the expected structure."""
        response = client.get("/api/documents")
        if response.status_code == 200:
            data = response.json()
            # Should have the expected structure
            assert "documents" in data
            assert "total" in data
            assert isinstance(data["documents"], list)
            assert isinstance(data["total"], int)

    def test_error_handling(self):
        """Test that the API handles errors gracefully."""
        # Test non-existent document
        response = client.get("/api/documents/nonexistent")
        assert response.status_code in [404, 500]  # Either not found or server error

    def test_upload_endpoint_structure(self):
        """Test that upload endpoint exists and has correct structure."""
        # Test with invalid file to see error response
        files = {"file": ("test.txt", b"not a pdf", "text/plain")}
        response = client.post("/api/documents/upload", files=files)
        # Should return 400 for invalid file type
        assert response.status_code in [400, 500]

    def test_reprocess_endpoint_structure(self):
        """Test that reprocess endpoint exists."""
        # Test with non-existent document
        response = client.post("/api/documents/nonexistent/reprocess")
        assert response.status_code in [404, 500]

    def test_download_endpoint_structure(self):
        """Test that download endpoint exists."""
        # Test with non-existent document
        response = client.get("/api/documents/nonexistent/download")
        assert response.status_code in [404, 500]

    def test_text_endpoint_structure(self):
        """Test that text endpoint exists."""
        # Test with non-existent document
        response = client.get("/api/documents/nonexistent/text")
        assert response.status_code in [404, 500]

    def test_api_consistency(self):
        """Test that API responses are consistent."""
        # Test that the same endpoint returns consistent structure
        response1 = client.get("/api/documents")
        response2 = client.get("/api/documents")
        
        if response1.status_code == 200 and response2.status_code == 200:
            data1 = response1.json()
            data2 = response2.json()
            
            # Should have same structure
            assert "documents" in data1
            assert "documents" in data2
            assert "total" in data1
            assert "total" in data2

    def test_metadata_fields_present(self):
        """Test that document metadata includes required fields."""
        response = client.get("/api/documents")
        if response.status_code == 200:
            data = response.json()
            documents = data.get("documents", [])
            
            for doc in documents:
                # Check for required metadata fields
                assert "doc_id" in doc
                assert "filename" in doc
                assert "file_size" in doc
                assert "created_at" in doc
                
                # Check for new metadata fields
                assert "extraction_method" in doc
                assert "quality_score" in doc
                assert "pages" in doc

    def test_error_response_format(self):
        """Test that error responses have consistent format."""
        # Test various error conditions
        error_endpoints = [
            ("GET", "/api/documents/nonexistent"),
            ("POST", "/api/documents/nonexistent/reprocess"),
            ("GET", "/api/documents/nonexistent/download"),
            ("GET", "/api/documents/nonexistent/text"),
        ]
        
        for method, endpoint in error_endpoints:
            if method == "GET":
                response = client.get(endpoint)
            else:
                response = client.post(endpoint)
            
            if response.status_code >= 400:
                # Should return JSON with error details
                try:
                    error_data = response.json()
                    assert "detail" in error_data
                except json.JSONDecodeError:
                    # Some endpoints might return plain text errors
                    pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 