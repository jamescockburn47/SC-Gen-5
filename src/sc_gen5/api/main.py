"""FastAPI backend for React frontend integration."""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
import logging
import os
from pathlib import Path
from dotenv import load_dotenv

# Import core components
from ..core.doc_store import DocStore
from ..core.rag_pipeline import RAGPipeline
from ..integrations.companies_house import CompaniesHouseClient

# Load environment variables
env_path = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(env_path)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
doc_store: Optional[DocStore] = None
rag_pipeline: Optional[RAGPipeline] = None
companies_house_client = None

# Initialize FastAPI app
app = FastAPI(
    title="SC Gen 5 API",
    description="REST API for Strategic Counsel Gen 5",
    version="1.0.0"
)

# Add CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global doc_store, rag_pipeline, companies_house_client
    
    try:
        logger.info("Initializing SC Gen 5 API services...")
        
        # Initialize document store
        data_dir = os.getenv("SC_DATA_DIR", "./data")
        vector_db_path = os.getenv("SC_VECTOR_DB_PATH", "./data/vector_db")
        metadata_path = os.getenv("SC_METADATA_PATH", "./data/metadata.json")
        chunk_size = int(os.getenv("SC_CHUNK_SIZE", "400"))
        chunk_overlap = int(os.getenv("SC_CHUNK_OVERLAP", "80"))
        embedding_model = os.getenv("SC_EMBEDDING_MODEL", "BAAI/bge-base-en-v1.5")
        
        doc_store = DocStore(
            data_dir=data_dir,
            vector_db_path=vector_db_path,
            metadata_path=metadata_path,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            embedding_model=embedding_model,
        )
        logger.info("Document store initialized")
        
        # Initialize RAG pipeline
        retrieval_k = int(os.getenv("SC_RETRIEVAL_K", "18"))
        rerank_top_k = int(os.getenv("SC_RERANK_TOP_K", "6"))
        use_reranker = os.getenv("SC_USE_RERANKER", "false").lower() == "true"
        
        rag_pipeline = RAGPipeline(
            doc_store=doc_store,
            retrieval_k=retrieval_k,
            rerank_top_k=rerank_top_k,
            use_reranker=use_reranker,
        )
        logger.info("RAG pipeline initialized")
        
        # Initialize Companies House client
        api_key = os.getenv("COMPANIES_HOUSE_API_KEY")
        if api_key:
            companies_house_client = CompaniesHouseClient(api_key)
            logger.info("Companies House client initialized")
        
        logger.info("All services initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise

# Health check endpoint
@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "SC Gen 5 API is running", "status": "healthy"}

# Document management endpoints
@app.get("/api/documents")
async def list_documents():
    """List all documents."""
    if not doc_store:
        raise HTTPException(status_code=500, detail="Document store not initialized")
    
    try:
        documents = doc_store.list_documents()
        return {"documents": documents, "total": len(documents)}
    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload a document."""
    if not doc_store:
        raise HTTPException(status_code=500, detail="Document store not initialized")
    
    try:
        # Validate file type
        allowed_types = [".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".gif"]
        file_extension = Path(file.filename).suffix.lower()
        
        if file_extension not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type: {file_extension}. Allowed: {allowed_types}"
            )
        
        # Read file content
        file_content = await file.read()
        
        # Add document to store
        doc_id = doc_store.add_document(file_content, file.filename)
        document = doc_store.get_document(doc_id)
        
        return document
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/documents/{doc_id}")
async def get_document(doc_id: str):
    """Get document by ID."""
    if not doc_store:
        raise HTTPException(status_code=500, detail="Document store not initialized")
    
    try:
        document = doc_store.get_document(doc_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return document
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/documents/{doc_id}/text")
async def get_document_text(doc_id: str):
    """Get document text content."""
    if not doc_store:
        raise HTTPException(status_code=500, detail="Document store not initialized")
    
    try:
        text = doc_store.get_document_text(doc_id)
        return {"doc_id": doc_id, "text": text}
    except Exception as e:
        logger.error(f"Failed to get document text: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/documents/{doc_id}/download")
async def download_document(doc_id: str):
    """Download document file."""
    if not doc_store:
        raise HTTPException(status_code=500, detail="Document store not initialized")
    
    try:
        file_bytes, filename = doc_store.get_document_file(doc_id)
        from fastapi.responses import Response
        return Response(
            content=file_bytes,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except Exception as e:
        logger.error(f"Failed to download document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/documents/{doc_id}/reprocess")
async def reprocess_document(doc_id: str):
    """Reprocess document."""
    if not doc_store:
        raise HTTPException(status_code=500, detail="Document store not initialized")
    
    try:
        # Get the original file
        file_bytes, filename = doc_store.get_document_file(doc_id)
        # Re-add the document with force_ocr=True
        doc_store.delete_document(doc_id)
        new_doc_id = doc_store.add_document(file_bytes, filename, metadata={"force_ocr": True})
        document = doc_store.get_document(new_doc_id)
        return {"document": document}
    except Exception as e:
        logger.error(f"Failed to reprocess document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/documents/{doc_id}")
async def delete_document(doc_id: str):
    """Delete document."""
    if not doc_store:
        raise HTTPException(status_code=500, detail="Document store not initialized")
    
    try:
        success = doc_store.delete_document(doc_id)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        return {"message": "Document deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Consultation endpoints
@app.post("/api/consultations/query")
async def query_consultation(request: dict):
    """Process a legal consultation query."""
    if not rag_pipeline:
        raise HTTPException(status_code=500, detail="RAG pipeline not initialized")
    
    try:
        query = request.get("query")
        if not query:
            raise HTTPException(status_code=400, detail="Query is required")
        
        # Get additional parameters
        session_id = request.get("session_id")
        settings = request.get("settings", {})
        context_documents = request.get("context_documents", 5)
        
        # Process the query through RAG pipeline
        result = rag_pipeline.answer(
            question=query,
            cloud_allowed=settings.get("cloud_allowed", False),
            cloud_provider=settings.get("cloud_provider"),
            model_choice=settings.get("model_preference"),
            matter_type=settings.get("legal_area"),
            matter_id=session_id or "default",
        )
        
        return {
            "response": result.get("answer", "No response generated"),
            "sources": result.get("sources", []),
            "model_used": result.get("model_used", "unknown"),
            "confidence": result.get("confidence", 0.0),
            "timestamp": "2024-01-01T00:00:00Z"
        }
    except Exception as e:
        logger.error(f"Failed to process consultation query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/consultations/sessions")
async def get_consultation_sessions():
    """Get consultation sessions."""
    # TODO: Implement session storage
    return {"sessions": []}

@app.post("/api/consultations/sessions")
async def create_consultation_session(request: dict):
    """Create a new consultation session."""
    # TODO: Implement session creation
    session_id = f"session_{len([])}"  # Placeholder
    return {
        "session": {
            "id": session_id,
            "title": request.get("title", "New Session"),
            "created_at": "2024-01-01T00:00:00Z",
            "message_count": 0,
            "legal_area": request.get("legal_area", "general")
        }
    }

@app.get("/api/consultations/sessions/{session_id}/messages")
async def get_session_messages(session_id: str):
    """Get messages for a session."""
    # TODO: Implement message storage
    return {"messages": []}

@app.post("/api/consultations/sessions/save")
async def save_consultation_session(request: dict):
    """Save a consultation session."""
    # TODO: Implement session saving
    return {"message": "Session saved successfully"}

@app.get("/api/documents/stats")
async def get_document_stats():
    """Get document statistics."""
    if not doc_store:
        raise HTTPException(status_code=500, detail="Document store not initialized")
    
    try:
        stats = doc_store.get_stats()
        return {"total_documents": stats.get("total_documents", 0)}
    except Exception as e:
        logger.error(f"Failed to get document stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Companies House endpoints
@app.get("/api/companies-house/status")
async def get_companies_house_status():
    """Get Companies House API status."""
    return {"available": companies_house_client is not None}

@app.get("/api/companies-house/search")
async def search_companies(query: str, type: str = "company", limit: int = 10):
    """Search companies using Companies House API."""
    if not companies_house_client:
        return {"companies": [], "query": query, "total": 0}
    
    try:
        results = companies_house_client.search_companies(query, limit=limit)
        return {"companies": results, "query": query, "total": len(results)}
    except Exception as e:
        logger.error(f"Failed to search companies: {e}")
        return {"companies": [], "query": query, "total": 0}

@app.get("/api/companies-house/company/{company_number}")
async def get_company_details(company_number: str):
    """Get detailed company information."""
    if not companies_house_client:
        raise HTTPException(status_code=500, detail="Companies House client not initialized")
    
    try:
        company = companies_house_client.get_company(company_number)
        return company
    except Exception as e:
        logger.error(f"Failed to get company details: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Analytics endpoints
@app.get("/api/analytics/documents")
async def get_document_analytics():
    """Get document analytics."""
    if not doc_store:
        raise HTTPException(status_code=500, detail="Document store not initialized")
    
    try:
        stats = doc_store.get_stats()
        return {
            "total_documents": stats.get("total_documents", 0),
            "total_chunks": stats.get("total_chunks", 0),
            "total_text_length": stats.get("total_text_length", 0),
            "storage_size": "0 MB",  # TODO: Calculate actual storage size
            "processing_status": "active"
        }
    except Exception as e:
        logger.error(f"Failed to get analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/usage")
async def get_usage_analytics():
    """Get usage analytics."""
    # TODO: Implement usage tracking
    return {
        "total_queries": 0,
        "total_searches": 0,
        "total_uploads": 0,
        "active_users": 1,
        "period": "last_30_days"
    }

# Claude CLI endpoints
@app.post("/api/claude-cli/status")
async def get_claude_cli_status():
    """Check Claude CLI availability."""
    try:
        import subprocess
        result = subprocess.run(["claude", "--version"], capture_output=True, text=True, timeout=5)
        return {
            "available": result.returncode == 0,
            "version": result.stdout.strip() if result.returncode == 0 else None
        }
    except Exception:
        return {"available": False, "version": None}

@app.post("/api/claude-cli/execute")
async def execute_claude_cli(request: dict):
    """Execute Claude CLI command."""
    try:
        import subprocess
        
        query = request.get("query")
        if not query:
            raise HTTPException(status_code=400, detail="Query is required")
        
        cwd = request.get("cwd", os.getcwd())
        
        # Execute Claude CLI
        cmd = ["claude", query]
        result = subprocess.run(
            cmd,
            text=True,
            capture_output=True,
            timeout=120,
            cwd=cwd
        )
        
        return {
            "success": result.returncode == 0,
            "output": result.stdout or result.stderr or "No output",
            "returncode": result.returncode
        }
        
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Claude CLI command timed out")
    except Exception as e:
        logger.error(f"Failed to execute Claude CLI: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 