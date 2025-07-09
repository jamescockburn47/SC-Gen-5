"""FastAPI backend for React frontend integration."""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from typing import List, Dict, Any, Optional
import logging
import os
import psutil
import shutil
from pathlib import Path
from dotenv import load_dotenv

# Import core components
from ..core.doc_store import DocStore
from ..integrations.companies_house import CompaniesHouseClient

# Load environment variables
env_path = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(env_path)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances - these will be initialized by the main app
doc_store: Optional[DocStore] = None
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
    global doc_store, companies_house_client
    
    try:
        # Try to get global instances from main app
        try:
            import sys
            import os
            # Add the project root to the path
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            sys.path.insert(0, project_root)
            
            from app import get_doc_store, get_companies_house_client
            
            doc_store = get_doc_store()
            companies_house_client = get_companies_house_client()
            
            if doc_store is not None and companies_house_client is not None:
                logger.info("Using global instances from main app")
            else:
                raise ImportError("Global instances not available")
            
        except (ImportError, Exception) as e:
            logger.warning(f"Could not import global instances: {e}, initializing locally")
            
            # Initialize document store
            doc_store = DocStore()
            logger.info("Document store initialized")
            
            # Initialize Companies House client
            try:
                companies_house_client = CompaniesHouseClient()
                logger.info("Companies House client initialized")
            except Exception as e:
                logger.warning(f"Companies House client failed to initialize: {e}")
                companies_house_client = None
                
        logger.info("All services initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "LexCognito API is running",
        "version": "1.0.0",
        "status": "healthy",
        "rag_v2_available": False,
        "legacy_rag_available": True
    }

# Document management endpoints
@app.get("/documents")
async def list_documents(request: Request):
    """List all documents in the store."""
    doc_store = request.app.state.doc_store
    if not doc_store:
        raise HTTPException(status_code=500, detail="Document store not initialized")
    
    try:
        documents = doc_store.list_documents()
        return {"documents": documents}
    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents/stats")
async def get_document_stats(request: Request):
    """Get document store statistics."""
    doc_store = request.app.state.doc_store
    if not doc_store:
        raise HTTPException(status_code=500, detail="Document store not initialized")
    
    try:
        stats = doc_store.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Failed to get document stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and process a document."""
    if not doc_store:
        raise HTTPException(status_code=500, detail="Document store not initialized")
    
    try:
        # Save uploaded file temporarily
        temp_path = Path(f"/tmp/{file.filename}")
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Add document to store
        doc_id = doc_store.add_document(temp_path, file.filename)
        
        # Clean up temp file
        temp_path.unlink()
        
        return {
            "message": "Document uploaded successfully",
            "doc_id": doc_id,
            "filename": file.filename
        }
    except Exception as e:
        logger.error(f"Failed to upload document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents/{doc_id}")
async def get_document(doc_id: str):
    """Get document metadata."""
    if not doc_store:
        raise HTTPException(status_code=500, detail="Document store not initialized")
    
    try:
        doc = doc_store.get_document(doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        return doc
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents/{doc_id}/text")
async def get_document_text(doc_id: str):
    """Get document text content."""
    if not doc_store:
        raise HTTPException(status_code=500, detail="Document store not initialized")
    
    try:
        text = doc_store.get_document_text(doc_id)
        if text is None:
            raise HTTPException(status_code=404, detail="Document not found")
        return {"text": text}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document text: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents/{doc_id}/download")
async def download_document(doc_id: str):
    """Download document file."""
    if not doc_store:
        raise HTTPException(status_code=500, detail="Document store not initialized")
    
    try:
        doc = doc_store.get_document(doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        file_path = doc.get("file_path")
        if not file_path or not Path(file_path).exists():
            raise HTTPException(status_code=404, detail="Document file not found")
        
        return FileResponse(file_path, filename=doc.get("filename", "document"))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/documents/{doc_id}/reprocess")
async def reprocess_document(doc_id: str):
    """Reprocess a document."""
    if not doc_store:
        raise HTTPException(status_code=500, detail="Document store not initialized")
    
    try:
        success = doc_store.reprocess_document(doc_id)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {"message": "Document reprocessed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reprocess document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a document."""
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
@app.post("/consultations/cloud-query")
async def cloud_only_query_redirect(request: dict):
    """DEPRECATED: This endpoint has been replaced with unified RAG. Redirects to /api/rag/answer."""
    raise HTTPException(
        status_code=410, 
        detail={
            "error": "Endpoint deprecated", 
            "message": "This endpoint bypassed document retrieval and provided generic responses. Please use the unified RAG endpoint instead.",
            "redirect_to": "/api/rag/answer",
            "new_format": {
                "question": "Your legal question here",
                "include_sources": True,
                "response_style": "detailed"
            }
        }
    )

@app.get("/consultations/sessions")
async def get_consultation_sessions():
    """Get consultation sessions."""
    # TODO: Implement session storage
    return {"sessions": []}

@app.post("/consultations/sessions")
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

@app.get("/consultations/sessions/{session_id}/messages")
async def get_session_messages(session_id: str):
    """Get messages for a session."""
    # TODO: Implement message storage
    return {"messages": []}

@app.post("/consultations/sessions/save")
async def save_consultation_session(request: dict):
    """Save a consultation session."""
    # TODO: Implement session saving
    return {"message": "Session saved successfully"}

# Companies House endpoints
@app.get("/companies-house/status")
async def get_companies_house_status(request: Request):
    """Get Companies House API status."""
    ch_client = getattr(request.app.state, "companies_house_client", None)
    status = {"available": ch_client is not None}
    logger.info(f"Companies House status: {status}")
    return status

@app.get("/companies-house/bulk-jobs")
async def get_bulk_jobs():
    """Get bulk processing jobs status."""
    # TODO: Implement bulk job tracking
    return {"jobs": [], "total": 0}

@app.get("/companies-house/search")
async def search_companies(request: Request, query: str, type: str = "company", limit: int = 10):
    """Search companies using Companies House API."""
    ch_client = getattr(request.app.state, "companies_house_client", None)
    if not ch_client:
        return {"companies": [], "query": query, "total": 0}
    try:
        results = ch_client.search_companies(query, items_per_page=limit)
        return {"companies": results, "query": query, "total": len(results.get('items', []))}
    except Exception as e:
        logger.error(f"Failed to search companies: {e}")
        return {"companies": [], "query": query, "total": 0}

@app.get("/companies-house/company/{company_number}")
async def get_company_details(request: Request, company_number: str):
    """Get detailed company information."""
    ch_client = getattr(request.app.state, "companies_house_client", None)
    if not ch_client:
        raise HTTPException(status_code=500, detail="Companies House client not initialized")
    try:
        company = ch_client.get_company_profile(company_number)
        return company
    except Exception as e:
        logger.error(f"Failed to get company details: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/companies-house/company/{company_number}/filing/{transaction_id}/download")
async def download_and_store_filing(request: Request, company_number: str, transaction_id: str, category: str = "Uncategorised"):
    """Download a filing document and store it in the DMS with category support."""
    ch_client = getattr(request.app.state, "companies_house_client", None)
    doc_store = getattr(request.app.state, "doc_store", None)
    if not ch_client or not doc_store:
        raise HTTPException(status_code=500, detail="Required service not initialized")
    try:
        # Download document
        content = ch_client.get_filing_document(company_number, transaction_id)
        if not isinstance(content, bytes):
            raise ValueError("Downloaded document is not bytes")
        # Store in DMS
        filename = f"{company_number}_{transaction_id}.pdf"
        doc_id = doc_store.add_document(content, filename, metadata={"source": "companies_house", "company_number": company_number, "transaction_id": transaction_id, "category": category})
        return {"message": "Document stored in DMS", "doc_id": doc_id, "category": category}
    except Exception as e:
        logger.error(f"Failed to download/store filing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/companies-house/document/{doc_id}/categorise")
async def categorise_document(request: Request, doc_id: str, category: str = Body(...)):
    """Update the category of a Companies House document in the DMS."""
    doc_store = getattr(request.app.state, "doc_store", None)
    if not doc_store:
        raise HTTPException(status_code=500, detail="Document store not initialized")
    try:
        doc_store.update_metadata(doc_id, {"category": category})
        return {"message": "Category updated", "doc_id": doc_id, "category": category}
    except Exception as e:
        logger.error(f"Failed to update document category: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/companies-house/documents/by-category")
async def list_documents_by_category(request: Request, category: str = None):
    """List all Companies House documents, optionally filtered by category."""
    doc_store = getattr(request.app.state, "doc_store", None)
    if not doc_store:
        raise HTTPException(status_code=500, detail="Document store not initialized")
    try:
        docs = doc_store.list_documents()
        ch_docs = [d for d in docs if d.get("source") == "companies_house"]
        if category:
            ch_docs = [d for d in ch_docs if d.get("category") == category]
        return {"documents": ch_docs, "category": category}
    except Exception as e:
        logger.error(f"Failed to list Companies House documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Analytics endpoints
@app.get("/analytics/documents")
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

@app.get("/analytics/usage")
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
import pty
import os
import fcntl
import termios
import select
import struct
from typing import Dict, Any
from fastapi import WebSocket, WebSocketDisconnect

# Store active Claude CLI sessions
claude_sessions: Dict[str, Dict[str, Any]] = {}

@app.get("/claude-cli/status")
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
    """Clean Claude CLI WebSocket interface for real-time interaction."""
    logger.info(f"WebSocket connection attempt for session {session_id}")
    
    try:
        await websocket.accept()
        logger.info(f"WebSocket accepted for session {session_id}")
        
        # Send immediate confirmation
        await websocket.send_text(json.dumps({
            "type": "connected",
            "content": f"Connected to Claude CLI session {session_id}",
            "working_directory": "/home/jcockburn/SC Gen 5"
        }))
        
        # Set up environment
        working_dir = "/home/jcockburn/SC Gen 5"
        logger.info(f"Claude CLI ready in directory: {working_dir}")
        
        claude_sessions[session_id] = {
            "websocket": websocket,
            "active": True,
            "created_at": asyncio.get_event_loop().time(),
            "working_dir": working_dir
        }
        
        # Send clean startup message
        await websocket.send_text(json.dumps({
            "type": "output",
            "content": "Claude CLI ready! Type your message and press Enter."
        }))
        
        # Handle incoming messages from frontend
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("type") == "input":
                    # Handle input by calling Claude CLI with --print
                    input_text = message.get("content", "")
                    logger.info(f"Processing Claude CLI input: {input_text}")
                    
                    # Echo the input back to user
                    await websocket.send_text(json.dumps({
                        "type": "input_echo",
                        "content": f"> {input_text}"
                    }))
                    
                    try:
                        # Call Claude CLI with --print for clean output
                        process = await asyncio.create_subprocess_exec(
                            "claude",
                            "--print",
                            input_text,
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE,
                            cwd=working_dir
                        )
                        
                        # Get the response
                        stdout, stderr = await process.communicate()
                        
                        if stdout:
                            response_text = stdout.decode().strip()
                            if response_text:
                                logger.info(f"Claude CLI response length: {len(response_text)}")
                                await websocket.send_text(json.dumps({
                                    "type": "output",
                                    "content": response_text
                                }))
                        
                        if stderr:
                            error_text = stderr.decode().strip()
                            if error_text:
                                logger.error(f"Claude CLI error: {error_text}")
                                await websocket.send_text(json.dumps({
                                    "type": "error",
                                    "content": f"Error: {error_text}"
                                }))
                                
                    except Exception as e:
                        logger.error(f"Error calling Claude CLI: {str(e)}")
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "content": f"Error processing request: {str(e)}"
                        }))
                        
                elif message.get("type") == "interrupt":
                    await websocket.send_text(json.dumps({
                        "type": "output",
                        "content": "Interrupt signal received"
                    }))
                        
                elif message.get("type") == "close":
                    break
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Message handling error: {str(e)}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "content": f"Message handling error: {str(e)}"
                }))
        
    except Exception as e:
        logger.error(f"Claude CLI WebSocket error: {str(e)}")
        try:
            await websocket.send_text(json.dumps({
                "type": "error",
                "content": f"Session error: {str(e)}"
            }))
        except:
            pass
    
    finally:
        # Clean up session
        if session_id in claude_sessions:
            session = claude_sessions[session_id]
            session["active"] = False
            del claude_sessions[session_id]
            logger.info(f"Cleaned up session {session_id}")

@app.post("/claude-cli/sessions")
async def create_claude_session():
    """Create a new Claude CLI session."""
    session_id = str(uuid.uuid4())
    return {
        "session_id": session_id,
        "websocket_url": f"/ws/claude-cli/{session_id}",
        "status": "created"
    }

@app.get("/claude-cli/sessions")
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

@app.delete("/claude-cli/sessions/{session_id}")
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
@app.get("/dashboard/stats")
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

@app.get("/system/stats")
async def get_system_stats():
    """Get real-time system statistics."""
    try:
        # Get CPU info
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # Get memory info
        memory = psutil.virtual_memory()
        
        # Get disk usage
        disk = psutil.disk_usage('/')
        
        # Try to get GPU info (if available)
        gpu_info = {"usage": 0, "memory": "N/A"}
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]
                gpu_info = {
                    "usage": round(gpu.load * 100, 1),
                    "memory": f"{gpu.memoryUsed}MB / {gpu.memoryTotal}MB"
                }
        except ImportError:
            # GPU monitoring not available
            pass
        except Exception:
            # GPU access error
            pass
        
        return {
            "cpu": {
                "usage": round(cpu_percent, 1),
                "cores": cpu_count
            },
            "ram": {
                "usage": round(memory.percent, 1),
                "memory": f"{round(memory.used / (1024**3), 1)}GB / {round(memory.total / (1024**3), 1)}GB"
            },
            "storage": {
                "usage": round((disk.used / disk.total) * 100, 1),
                "space": f"{round(disk.used / (1024**3), 1)}GB / {round(disk.total / (1024**3), 1)}GB"
            },
            "gpu": gpu_info
        }
    except Exception as e:
        logger.error(f"Failed to get system stats: {e}")
        return {
            "cpu": {"usage": 0, "cores": 0},
            "ram": {"usage": 0, "memory": "N/A"},
            "storage": {"usage": 0, "space": "N/A"},
            "gpu": {"usage": 0, "memory": "N/A"}
        }

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