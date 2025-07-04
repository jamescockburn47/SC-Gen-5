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
    title="LexCognito API",
    description="REST API for LexCognito - AI-Powered Legal Research Platform",
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
        retrieval_k = int(os.getenv("SC_RETRIEVAL_K", "50"))
        rerank_top_k = int(os.getenv("SC_RERANK_TOP_K", "25"))
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
    return {"message": "LexCognito API is running", "status": "healthy"}

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
@app.post("/api/consultations/cloud-query")
async def cloud_only_query(request: dict):
    """Process a consultation query using cloud LLMs only (no RAG)."""
    try:
        query = request.get("query")
        if not query:
            raise HTTPException(status_code=400, detail="Query is required")
        
        cloud_provider = request.get("cloud_provider", "anthropic")
        model_choice = request.get("model_choice")
        
        # Import cloud LLM directly
        from ..core.cloud_llm import CloudLLMGenerator, CloudProvider
        cloud_llm = CloudLLMGenerator()
        
        # Map provider string to enum
        provider_map = {
            "openai": CloudProvider.OPENAI,
            "gemini": CloudProvider.GEMINI,
            "claude": CloudProvider.CLAUDE,
            "anthropic": CloudProvider.CLAUDE  # Alias for Claude
        }
        
        provider_enum = provider_map.get(cloud_provider)
        if not provider_enum:
            raise HTTPException(status_code=400, detail=f"Unsupported provider: {cloud_provider}")
        
        # Generate direct answer without RAG
        try:
            answer = cloud_llm.generate(
                prompt=f"You are a legal assistant. Please provide a professional legal analysis for the following question:\n\n{query}",
                provider=provider_enum,
                model=model_choice,
                max_tokens=2000,
                temperature=0.1
            )
            model_used = f"{cloud_provider}:{model_choice or 'default'}"
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Cloud LLM failed: {str(e)}")
        
        return {
            "response": answer,
            "sources": [],  # Empty array for cloud-only queries
            "model_used": model_used,
            "confidence": 1.0,
            "timestamp": "2024-01-01T00:00:00Z",
            "query_type": "cloud_only"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process cloud-only query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
        
        # Map frontend model preferences to actual model names
        model_preference = settings.get("model_preference", "mistral:latest")  # Default to quality model
        if model_preference == "auto":
            model_choice = "mistral:latest"  # Use quality default
        elif model_preference == "local":
            model_choice = "mistral:latest"  # Use quality local model
        elif model_preference == "cloud":
            model_choice = None  # Cloud models handled differently
            settings["cloud_allowed"] = True
        else:
            model_choice = model_preference  # Use exact model name
        
        # Process the query through RAG pipeline
        result = rag_pipeline.answer(
            question=query,
            cloud_allowed=settings.get("cloud_allowed", False),
            cloud_provider=settings.get("cloud_provider", "anthropic"),
            model_choice=model_choice,
            matter_type=settings.get("legal_area"),
            matter_id=session_id or "default",
        )
        
        return {
            "response": result.get("answer", "No response generated"),
            "sources": result.get("sources", []),
            "model_used": result.get("model_used", "unknown"),
            "confidence": result.get("confidence", 0.0),
            "timestamp": "2024-01-01T00:00:00Z",
            "retrieved_chunks": result.get("retrieved_chunks", 0),
            "documents_used": 1 if result.get("retrieved_chunks", 0) > 0 else 0  # Always 1 doc currently
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

# Companies House endpoints
@app.get("/api/companies-house/status")
async def get_companies_house_status():
    """Get Companies House API status."""
    return {"available": companies_house_client is not None}

@app.get("/api/companies-house/bulk-jobs")
async def get_bulk_jobs():
    """Get bulk processing jobs status."""
    # TODO: Implement bulk job tracking
    return {"jobs": [], "total": 0}

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

# Claude CLI Native Integration
import asyncio
import json
import signal
import uuid
from typing import Dict, Any
from fastapi import WebSocket, WebSocketDisconnect

# Store active Claude CLI sessions
claude_sessions: Dict[str, Dict[str, Any]] = {}

@app.get("/api/claude-cli/status")
async def get_claude_cli_status():
    """Check Claude CLI availability and configuration."""
    try:
        import subprocess
        result = subprocess.run(["claude", "--version"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            # Get additional Claude CLI info
            config_result = subprocess.run(["claude", "config", "list"], capture_output=True, text=True, timeout=5)
            return {
                "available": True,
                "version": result.stdout.strip(),
                "config": config_result.stdout if config_result.returncode == 0 else "Config not available",
                "working_directory": os.getcwd()
            }
        else:
            return {"available": False, "error": result.stderr}
    except Exception as e:
        return {"available": False, "error": str(e)}

@app.websocket("/ws/claude-cli/{session_id}")
async def claude_cli_websocket(websocket: WebSocket, session_id: str):
    """Native Claude CLI WebSocket interface for real-time interaction."""
    await websocket.accept()
    
    try:
        # Initialize Claude CLI session
        claude_process = await asyncio.create_subprocess_exec(
            "claude",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=os.getcwd()
        )
        
        claude_sessions[session_id] = {
            "process": claude_process,
            "websocket": websocket,
            "active": True
        }
        
        # Start reading Claude CLI output
        async def read_claude_output():
            try:
                while claude_sessions.get(session_id, {}).get("active", False):
                    if claude_process.stdout:
                        line = await claude_process.stdout.readline()
                        if line:
                            await websocket.send_text(json.dumps({
                                "type": "output",
                                "content": line.decode().rstrip()
                            }))
                        else:
                            break
            except Exception as e:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "content": f"Output stream error: {str(e)}"
                }))
        
        # Start reading Claude CLI errors
        async def read_claude_errors():
            try:
                while claude_sessions.get(session_id, {}).get("active", False):
                    if claude_process.stderr:
                        line = await claude_process.stderr.readline()
                        if line:
                            await websocket.send_text(json.dumps({
                                "type": "error",
                                "content": line.decode().rstrip()
                            }))
            except Exception as e:
                await websocket.send_text(json.dumps({
                    "type": "error", 
                    "content": f"Error stream error: {str(e)}"
                }))
        
        # Start output readers
        output_task = asyncio.create_task(read_claude_output())
        error_task = asyncio.create_task(read_claude_errors())
        
        # Send initial connection message
        await websocket.send_text(json.dumps({
            "type": "connected",
            "content": f"Connected to Claude CLI session {session_id}",
            "working_directory": os.getcwd()
        }))
        
        # Handle incoming messages from frontend
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("type") == "input":
                    # Send input to Claude CLI
                    if claude_process.stdin:
                        input_text = message.get("content", "") + "\n"
                        claude_process.stdin.write(input_text.encode())
                        await claude_process.stdin.drain()
                        
                elif message.get("type") == "interrupt":
                    # Send Ctrl+C to Claude CLI
                    if claude_process:
                        claude_process.send_signal(signal.SIGINT)
                        
                elif message.get("type") == "close":
                    break
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "content": f"Message handling error: {str(e)}"
                }))
        
    except Exception as e:
        await websocket.send_text(json.dumps({
            "type": "error",
            "content": f"Session initialization error: {str(e)}"
        }))
    
    finally:
        # Clean up session
        if session_id in claude_sessions:
            session = claude_sessions[session_id]
            session["active"] = False
            if "process" in session:
                try:
                    session["process"].terminate()
                    await session["process"].wait()
                except:
                    pass
            del claude_sessions[session_id]

@app.post("/api/claude-cli/sessions")
async def create_claude_session():
    """Create a new Claude CLI session."""
    session_id = str(uuid.uuid4())
    return {
        "session_id": session_id,
        "websocket_url": f"/ws/claude-cli/{session_id}",
        "status": "created"
    }

@app.get("/api/claude-cli/sessions")
async def list_claude_sessions():
    """List active Claude CLI sessions."""
    return {
        "sessions": [
            {
                "session_id": sid,
                "active": session.get("active", False),
                "created_at": session.get("created_at", "unknown")
            }
            for sid, session in claude_sessions.items()
        ]
    }

@app.delete("/api/claude-cli/sessions/{session_id}")
async def terminate_claude_session(session_id: str):
    """Terminate a Claude CLI session."""
    if session_id in claude_sessions:
        session = claude_sessions[session_id]
        session["active"] = False
        if "process" in session:
            try:
                session["process"].terminate()
            except:
                pass
        del claude_sessions[session_id]
        return {"message": "Session terminated"}
    else:
        raise HTTPException(status_code=404, detail="Session not found")

# Dashboard endpoints
@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    """Get dashboard statistics."""
    try:
        # Get real document count
        doc_count = 0
        if doc_store:
            try:
                stats = doc_store.get_stats()
                doc_count = stats.get("total_documents", 0)
            except Exception:
                pass
        
        # TODO: Implement real company and query tracking
        return {
            "documents": doc_count,
            "companies": 0,  # TODO: Get from Companies House search history
            "queries": 0,    # TODO: Get from consultation session storage
            "avgResponseTime": "0s"  # TODO: Calculate from query logs
        }
    except Exception as e:
        logger.error(f"Failed to get dashboard stats: {e}")
        return {"documents": 0, "companies": 0, "queries": 0, "avgResponseTime": "0s"}

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