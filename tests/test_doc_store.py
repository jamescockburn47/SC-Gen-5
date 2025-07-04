"""Tests for DocStore module."""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from sc_gen5.core.doc_store import DocStore


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield tmp_dir


@pytest.fixture
def sample_pdf_bytes():
    """Sample PDF content for testing."""
    # Minimal PDF header
    return b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n%%EOF"


@pytest.fixture
def doc_store(temp_dir):
    """Create a DocStore instance for testing."""
    with patch('sc_gen5.core.doc_store.OCREngine'), \
         patch('sc_gen5.core.doc_store.VectorStore'), \
         patch('sc_gen5.core.doc_store.tiktoken'):
        
        store = DocStore(
            data_dir=temp_dir,
            vector_db_path=f"{temp_dir}/vector_db",
            metadata_path=f"{temp_dir}/metadata.json",
        )
        
        # Mock the OCR engine
        store.ocr_engine.extract_text = Mock(return_value=("Sample text content", {"file_type": "pdf"}))
        
        # Mock the vector store
        store.vector_store.add_embeddings = Mock(return_value=[1, 2, 3])
        store.vector_store.search = Mock(return_value=[])
        store.vector_store.get_by_id = Mock(return_value=None)
        store.vector_store.remove_by_id = Mock(return_value=True)
        store.vector_store.get_stats = Mock(return_value={"total_embeddings": 0})
        
        # Mock the tokenizer
        store.tokenizer.encode = Mock(return_value=[1, 2, 3, 4, 5])
        store.tokenizer.decode = Mock(return_value="Sample text")
        
        return store


class TestDocStore:
    """Test cases for DocStore class."""
    
    def test_initialization(self, temp_dir):
        """Test DocStore initialization."""
        with patch('sc_gen5.core.doc_store.OCREngine'), \
             patch('sc_gen5.core.doc_store.VectorStore'), \
             patch('sc_gen5.core.doc_store.tiktoken'):
            
            store = DocStore(
                data_dir=temp_dir,
                vector_db_path=f"{temp_dir}/vector_db",
                metadata_path=f"{temp_dir}/metadata.json",
            )
            
            assert store.data_dir == Path(temp_dir)
            assert store.chunk_size == 400
            assert store.chunk_overlap == 80
            assert store.documents == {}
    
    def test_add_document_success(self, doc_store, sample_pdf_bytes):
        """Test successful document addition."""
        doc_id = doc_store.add_document(
            file_bytes=sample_pdf_bytes,
            filename="test.pdf",
            metadata={"test": "value"}
        )
        
        assert doc_id.startswith("doc_")
        assert doc_id in doc_store.documents
        
        # Verify document metadata
        doc_meta = doc_store.documents[doc_id]
        assert doc_meta["filename"] == "test.pdf"
        assert doc_meta["test"] == "value"
        assert doc_meta["file_size"] == len(sample_pdf_bytes)
        
        # Verify OCR was called
        doc_store.ocr_engine.extract_text.assert_called_once_with(sample_pdf_bytes, "test.pdf")
        
        # Verify vector store was called
        doc_store.vector_store.add_embeddings.assert_called_once()
    
    def test_add_document_duplicate(self, doc_store, sample_pdf_bytes):
        """Test adding duplicate document."""
        # Add document first time
        doc_id1 = doc_store.add_document(sample_pdf_bytes, "test.pdf")
        
        # Add same document again
        doc_id2 = doc_store.add_document(sample_pdf_bytes, "test.pdf")
        
        # Should return same ID
        assert doc_id1 == doc_id2
        assert len(doc_store.documents) == 1
    
    def test_add_document_ocr_failure(self, doc_store, sample_pdf_bytes):
        """Test document addition with OCR failure."""
        # Mock OCR to return empty text
        doc_store.ocr_engine.extract_text.return_value = ("", {"file_type": "pdf"})
        
        with pytest.raises(ValueError, match="No text extracted"):
            doc_store.add_document(sample_pdf_bytes, "test.pdf")
    
    def test_search_documents(self, doc_store):
        """Test document search."""
        # Mock search results
        mock_results = [
            {"id": 1, "text": "Sample text", "filename": "test.pdf"},
            {"id": 2, "text": "Another text", "filename": "test2.pdf"},
        ]
        doc_store.vector_store.search.return_value = mock_results
        
        results = doc_store.search("test query", k=5)
        
        assert len(results) == 2
        assert results == mock_results
        
        # Verify search was called with correct parameters
        doc_store.vector_store.search.assert_called_once_with(
            query="test query",
            k=18,  # search_k default
            filter_metadata=None
        )
    
    def test_get_document(self, doc_store, sample_pdf_bytes):
        """Test getting document by ID."""
        doc_id = doc_store.add_document(sample_pdf_bytes, "test.pdf")
        
        document = doc_store.get_document(doc_id)
        assert document is not None
        assert document["doc_id"] == doc_id
        assert document["filename"] == "test.pdf"
        
        # Test non-existent document
        assert doc_store.get_document("nonexistent") is None
    
    def test_delete_document(self, doc_store, sample_pdf_bytes):
        """Test document deletion."""
        doc_id = doc_store.add_document(sample_pdf_bytes, "test.pdf")
        
        # Verify document exists
        assert doc_id in doc_store.documents
        
        # Delete document
        success = doc_store.delete_document(doc_id)
        assert success
        assert doc_id not in doc_store.documents
        
        # Verify vector store remove was called for each chunk
        assert doc_store.vector_store.remove_by_id.call_count > 0
        
        # Test deleting non-existent document
        success = doc_store.delete_document("nonexistent")
        assert not success
    
    def test_list_documents(self, doc_store, sample_pdf_bytes):
        """Test listing all documents."""
        # Initially empty
        documents = doc_store.list_documents()
        assert len(documents) == 0
        
        # Add some documents
        doc_id1 = doc_store.add_document(sample_pdf_bytes, "test1.pdf")
        doc_id2 = doc_store.add_document(b"different content", "test2.pdf")
        
        documents = doc_store.list_documents()
        assert len(documents) == 2
        
        doc_ids = [doc["doc_id"] for doc in documents]
        assert doc_id1 in doc_ids
        assert doc_id2 in doc_ids
    
    def test_get_stats(self, doc_store, sample_pdf_bytes):
        """Test getting document store statistics."""
        # Add a document
        doc_store.add_document(sample_pdf_bytes, "test.pdf")
        
        stats = doc_store.get_stats()
        
        assert "total_documents" in stats
        assert "total_chunks" in stats
        assert "total_text_length" in stats
        assert "vector_store" in stats
        assert "data_dir" in stats
        assert "chunk_size" in stats
        assert "chunk_overlap" in stats
        
        assert stats["total_documents"] == 1
        assert stats["chunk_size"] == 400
        assert stats["chunk_overlap"] == 80
    
    def test_chunk_text(self, doc_store):
        """Test text chunking functionality."""
        # Mock tokenizer for predictable chunking
        doc_store.tokenizer.encode.return_value = list(range(1000))  # 1000 tokens
        doc_store.tokenizer.decode.side_effect = lambda tokens: f"chunk_{len(tokens)}"
        
        chunks = doc_store._chunk_text("long text content")
        
        # Should create multiple chunks due to size
        assert len(chunks) > 1
        
        # Each chunk should have been decoded
        for chunk in chunks:
            assert chunk.startswith("chunk_")
    
    def test_chunk_text_short(self, doc_store):
        """Test chunking of short text."""
        # Mock tokenizer for short text
        doc_store.tokenizer.encode.return_value = [1, 2, 3]  # 3 tokens
        
        chunks = doc_store._chunk_text("short text")
        
        # Should return single chunk for short text
        assert len(chunks) == 1
        assert chunks[0] == "short text"
    
    def test_metadata_persistence(self, doc_store, sample_pdf_bytes):
        """Test metadata saving and loading."""
        # Add document
        doc_id = doc_store.add_document(sample_pdf_bytes, "test.pdf")
        
        # Verify metadata file was created
        assert doc_store.metadata_path.exists()
        
        # Load metadata manually
        with open(doc_store.metadata_path, "r") as f:
            metadata = json.load(f)
        
        assert doc_id in metadata
        assert metadata[doc_id]["filename"] == "test.pdf"
    
    def test_clear_all(self, doc_store, sample_pdf_bytes):
        """Test clearing all documents and data."""
        # Add document
        doc_store.add_document(sample_pdf_bytes, "test.pdf")
        
        # Verify document exists
        assert len(doc_store.documents) == 1
        
        # Clear all
        doc_store.clear_all()
        
        # Verify everything is cleared
        assert len(doc_store.documents) == 0
        doc_store.vector_store.clear.assert_called_once()
        
        # Verify metadata file is updated
        assert doc_store.metadata_path.exists()
        with open(doc_store.metadata_path, "r") as f:
            metadata = json.load(f)
        assert metadata == {}


class TestDocStoreIntegration:
    """Integration tests for DocStore."""
    
    def test_full_workflow(self, temp_dir, sample_pdf_bytes):
        """Test complete document workflow."""
        with patch('sc_gen5.core.doc_store.OCREngine') as mock_ocr, \
             patch('sc_gen5.core.doc_store.VectorStore') as mock_vector, \
             patch('sc_gen5.core.doc_store.tiktoken') as mock_tiktoken:
            
            # Setup mocks
            mock_ocr_instance = Mock()
            mock_ocr_instance.extract_text.return_value = ("Sample extracted text", {"file_type": "pdf"})
            mock_ocr.return_value = mock_ocr_instance
            
            mock_vector_instance = Mock()
            mock_vector_instance.add_embeddings.return_value = [1, 2, 3]
            mock_vector_instance.search.return_value = [{"id": 1, "text": "Sample"}]
            mock_vector_instance.get_stats.return_value = {"total_embeddings": 3}
            mock_vector.return_value = mock_vector_instance
            
            mock_tokenizer = Mock()
            mock_tokenizer.encode.return_value = [1, 2, 3, 4, 5]
            mock_tokenizer.decode.return_value = "Sample text"
            mock_tiktoken.get_encoding.return_value = mock_tokenizer
            
            # Create DocStore
            store = DocStore(
                data_dir=temp_dir,
                vector_db_path=f"{temp_dir}/vector_db",
                metadata_path=f"{temp_dir}/metadata.json",
            )
            
            # Test workflow
            doc_id = store.add_document(sample_pdf_bytes, "test.pdf")
            assert doc_id.startswith("doc_")
            
            results = store.search("test query")
            assert len(results) == 1
            
            stats = store.get_stats()
            assert stats["total_documents"] == 1
            
            success = store.delete_document(doc_id)
            assert success
            assert len(store.documents) == 0 