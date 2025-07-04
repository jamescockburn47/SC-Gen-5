"""Consultation service for legal research and document analysis."""

import os
import logging
import io
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Optional
from pathlib import Path
import json
from datetime import datetime

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, PlainTextResponse, JSONResponse
from pydantic import BaseModel, Field
import uvicorn

from ..core.doc_store import DocStore
from ..core.rag_pipeline import RAGPipeline

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(env_path)

logger = logging.getLogger(__name__)

# Global instances
doc_store: Optional[DocStore] = None
rag_pipeline: Optional[RAGPipeline] = None


class ConsultRequest(BaseModel):
    """Request model for consultation endpoint."""
    matter_id: str = Field(..., description="Unique identifier for the legal matter")
    question: str = Field(..., description="Legal question to answer")
    cloud_allowed: bool = Field(default=False, description="Whether to allow cloud LLM usage")
    cloud_provider: Optional[str] = Field(
        default=None, 
        description="Cloud provider to use (openai, gemini, claude)"
    )
    model: Optional[str] = Field(
        default=None,
        description="Specific model to use (mixtral, mistral, lawma, phi3 for local)"
    )
    matter_type: Optional[str] = Field(
        default=None,
        description="Type of legal matter (contract, regulatory, litigation, due_diligence)"
    )
    filter_metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional metadata filters for document retrieval"
    )


class ConsultResponse(BaseModel):
    """Response model for consultation endpoint."""
    answer: str = Field(..., description="Generated legal analysis")
    sources: str = Field(..., description="Source documents used")
    matter_id: str = Field(..., description="Matter identifier")
    model_used: str = Field(..., description="Model used for generation")
    retrieved_chunks: int = Field(..., description="Number of document chunks retrieved")
    context_length: Optional[int] = Field(default=None, description="Length of context provided to LLM")


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    doc_store: Dict[str, Any]
    rag_pipeline: Dict[str, Any]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for FastAPI app."""
    # Startup
    global doc_store, rag_pipeline
    
    logger.info("Starting SC Gen 5 Consult Service...")
    
    # Initialize components
    data_dir = os.getenv("SC_DATA_DIR", "./data")
    vector_db_path = os.getenv("SC_VECTOR_DB_PATH", "./data/vector_db")
    metadata_path = os.getenv("SC_METADATA_PATH", "./data/metadata.json")
    chunk_size = int(os.getenv("SC_CHUNK_SIZE", "400"))
    chunk_overlap = int(os.getenv("SC_CHUNK_OVERLAP", "80"))
    embedding_model = os.getenv("SC_EMBEDDING_MODEL", "BAAI/bge-base-en-v1.5")
    retrieval_k = int(os.getenv("SC_RETRIEVAL_K", "18"))
    rerank_top_k = int(os.getenv("SC_RERANK_TOP_K", "6"))
    use_reranker = os.getenv("SC_USE_RERANKER", "false").lower() == "true"
    
    # Initialize document store
    doc_store = DocStore(
        data_dir=data_dir,
        vector_db_path=vector_db_path,
        metadata_path=metadata_path,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        embedding_model=embedding_model,
    )
    
    # Initialize RAG pipeline
    rag_pipeline = RAGPipeline(
        doc_store=doc_store,
        retrieval_k=retrieval_k,
        rerank_top_k=rerank_top_k,
        use_reranker=use_reranker,
    )
    
    logger.info("SC Gen 5 Consult Service started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down SC Gen 5 Consult Service...")


# Create FastAPI app
app = FastAPI(
    title="SC Gen 5 Consult Service",
    description="Legal consultation service using Retrieval-Augmented Generation",
    version="5.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/consult", response_model=ConsultResponse)
async def consult(request: ConsultRequest) -> ConsultResponse:
    """Provide legal consultation using RAG pipeline.
    
    This endpoint processes legal questions by:
    1. Retrieving relevant documents from the knowledge base
    2. Using either local or cloud LLMs to generate responses
    3. Applying legal-specific protocols and prompts
    4. Returning structured analysis with source citations
    """
    if not rag_pipeline:
        raise HTTPException(status_code=500, detail="RAG pipeline not initialized")
    
    try:
        logger.info(f"Processing consultation for matter {request.matter_id}")
        
        # Validate cloud provider if specified
        if request.cloud_allowed and request.cloud_provider:
            valid_providers = ["openai", "gemini", "claude"]
            if request.cloud_provider.lower() not in valid_providers:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid cloud provider. Must be one of: {valid_providers}"
                )
        
        # Generate answer using RAG pipeline
        result = rag_pipeline.answer(
            question=request.question,
            cloud_allowed=request.cloud_allowed,
            cloud_provider=request.cloud_provider,
            model_choice=request.model,
            matter_type=request.matter_type,
            matter_id=request.matter_id,
            filter_metadata=request.filter_metadata,
        )
        
        return ConsultResponse(**result)
        
    except Exception as e:
        logger.error(f"Consultation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Consultation failed: {str(e)}")


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Health check endpoint."""
    if not doc_store or not rag_pipeline:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    try:
        doc_store_stats = doc_store.get_stats()
        rag_stats = rag_pipeline.validate_setup()
        
        return HealthResponse(
            status="healthy",
            doc_store=doc_store_stats,
            rag_pipeline=rag_stats,
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@app.get("/api/documents")
async def list_documents():
    """List all documents in the knowledge base, including extraction method, quality, and pages."""
    if not doc_store:
        raise HTTPException(status_code=500, detail="Document store not initialized")
    try:
        documents = doc_store.list_documents()
        # Ensure extraction method, quality, and pages are present in each document
        for doc in documents:
            doc.setdefault("extraction_method", doc.get("extraction_method", "unknown"))
            doc.setdefault("quality_score", doc.get("quality_score", None))
            doc.setdefault("pages", doc.get("pages", None))
        return {"documents": documents, "total": len(documents)}
    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")


@app.get("/api/documents/{doc_id}")
async def get_document(doc_id: str):
    """Get document metadata by ID, including extraction method, quality, and pages."""
    if not doc_store:
        raise HTTPException(status_code=500, detail="Document store not initialized")
    try:
        document = doc_store.get_document(doc_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        document.setdefault("extraction_method", document.get("extraction_method", "unknown"))
        document.setdefault("quality_score", document.get("quality_score", None))
        document.setdefault("pages", document.get("pages", None))
        return document
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document {doc_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get document: {str(e)}")


@app.post("/search")
async def search_documents(
    query: str,
    k: int = 10,
    filter_metadata: Optional[Dict[str, Any]] = None,
):
    """Search documents in the knowledge base."""
    if not rag_pipeline:
        raise HTTPException(status_code=500, detail="RAG pipeline not initialized")
    
    try:
        results = rag_pipeline.search_documents(
            query=query,
            k=k,
            filter_metadata=filter_metadata,
        )
        
        return {"results": results, "total": len(results)}
        
    except Exception as e:
        logger.error(f"Document search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Document search failed: {str(e)}")


@app.get("/stats")
async def get_stats():
    """Get service statistics."""
    if not doc_store or not rag_pipeline:
        raise HTTPException(status_code=500, detail="Service not initialized")
    
    try:
        doc_stats = doc_store.get_stats()
        rag_stats = rag_pipeline.get_retrieval_stats()
        
        return {
            "document_store": doc_stats,
            "rag_pipeline": rag_stats,
        }
        
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@app.post("/api/documents/upload")
async def upload_document(file: UploadFile = File(...), filename: str = Form(...)):
    """Upload a document and add it to the document store."""
    if not doc_store:
        raise HTTPException(status_code=500, detail="Document store not initialized")
    try:
        file_bytes = await file.read()
        doc_id = doc_store.add_document(
            file_bytes=file_bytes,
            filename=filename,
            metadata={"source": "upload"}
        )
        document = doc_store.get_document(doc_id)
        return {"document": document}
    except Exception as e:
        logger.error(f"Failed to upload document: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload document: {str(e)}")


@app.get("/api/documents/{doc_id}/text")
async def get_document_text(doc_id: str):
    """Get the extracted text for a document."""
    if not doc_store:
        raise HTTPException(status_code=500, detail="Document store not initialized")
    try:
        text = doc_store.get_document_text(doc_id)
        if not text:
            return PlainTextResponse("No text content available", status_code=200)
        return {"text": text}
    except Exception as e:
        logger.error(f"Failed to get document text: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get document text: {str(e)}")


@app.get("/api/documents/{doc_id}/download")
async def download_document(doc_id: str):
    """Download the original file for a document."""
    if not doc_store:
        raise HTTPException(status_code=500, detail="Document store not initialized")
    try:
        file_bytes, filename = doc_store.get_document_file(doc_id)
        return StreamingResponse(io.BytesIO(file_bytes),
                                 media_type="application/octet-stream",
                                 headers={"Content-Disposition": f"attachment; filename={filename}"})
    except Exception as e:
        logger.error(f"Failed to download document: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to download document: {str(e)}")


@app.post("/api/documents/{doc_id}/reprocess")
async def reprocess_document(doc_id: str):
    """Force OCR reprocessing of a document."""
    if not doc_store:
        raise HTTPException(status_code=500, detail="Document store not initialized")
    try:
        # Get the original file
        file_bytes, filename = doc_store.get_document_file(doc_id)
        # Re-add the document with force_ocr=True (simulate by removing and re-adding)
        doc_store.delete_document(doc_id)
        new_doc_id = doc_store.add_document(file_bytes, filename, metadata={"force_ocr": True})
        document = doc_store.get_document(new_doc_id)
        return {"document": document}
    except Exception as e:
        logger.error(f"Failed to reprocess document: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reprocess document: {str(e)}")


def main():
    """Main entry point for running the service."""
    host = os.getenv("SC_API_HOST", "0.0.0.0")
    port = int(os.getenv("SC_API_PORT", "8000"))
    log_level = os.getenv("SC_LOG_LEVEL", "info").lower()
    
    uvicorn.run(
        "sc_gen5.services.consult_service:app",
        host=host,
        port=port,
        log_level=log_level,
        reload=False,  # Set to True for development
    )


if __name__ == "__main__":
    main() 