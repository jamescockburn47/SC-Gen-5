"""
Unified Simple RAG Router - Single RAG system with clear model separation.

3-Step Process:
1. Search: Find relevant chunks using embedding similarity
2. Analyze: Use utility model to score relevance (0.0-1.0)
3. Generate: Use reasoning model for final answer generation

Clear Model Separation:
- Embedding Model (BAAI/bge-small-en-v1.5): Semantic search only
- Utility Model (TinyLlama): Chunk relevance analysis only - NO generation
- Generation Model (Mistral-7B): Final answer generation only
"""

import logging
import time
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks
from pydantic import BaseModel, Field
import asyncio

from .simple_rag import SimpleRAG, SimpleVectorStore, DirectModelClient
from .v2.model_client import ModelServiceClient

# Setup logging
log = logging.getLogger("lexcognito.simple_rag")

# API Models
class QuestionRequest(BaseModel):
    """Request model for RAG question answering."""
    question: str = Field(..., description="The question to answer")
    session_id: Optional[str] = Field(default=None, description="Session ID for tracking")
    max_chunks: Optional[int] = Field(default=15, description="Maximum number of chunks to retrieve")
    min_relevance: Optional[float] = Field(default=0.2, description="Minimum relevance score for chunks")
    include_sources: Optional[bool] = Field(default=True, description="Whether to include source information")
    response_style: Optional[str] = Field(default="detailed", description="Response style (concise, detailed, technical)")
    max_tokens: Optional[int] = Field(default=500, description="Maximum tokens for response")
    # Litigation-specific options
    matter_type: Optional[str] = Field(default="litigation", description="Type of legal matter")
    analysis_style: Optional[str] = Field(default="comprehensive", description="Style of analysis")
    focus_area: Optional[str] = Field(default="liability", description="Focus area for analysis")

class CloudConsultationRequest(BaseModel):
    """Request model for standalone cloud consultation."""
    question: str = Field(..., description="The legal question to answer")
    provider: str = Field(..., description="Cloud provider (openai, gemini, claude)")
    model: Optional[str] = Field(default=None, description="Specific model to use")
    max_tokens: Optional[int] = Field(default=2000, description="Maximum tokens for response")
    temperature: Optional[float] = Field(default=0.7, description="Generation temperature")
    matter_type: Optional[str] = Field(default=None, description="Type of legal matter")
    analysis_style: Optional[str] = Field(default="comprehensive", description="Style of analysis")
    session_id: Optional[str] = Field(default=None, description="Session ID for tracking")

class CloudConsultationResponse(BaseModel):
    """Response model for cloud consultation."""
    answer: str
    provider: str
    model: str
    tokens_used: Optional[int] = None
    cost_estimate: Optional[float] = None
    processing_time: float
    session_id: Optional[str] = None

class AnswerResponse(BaseModel):
    answer: str
    confidence: float
    sources: List[Dict[str, Any]]
    chunks_analyzed: int
    chunks_used: int
    processing_time: float
    model_used: str

class StatusResponse(BaseModel):
    status: str
    models: Dict[str, bool]
    documents: Dict[str, Any]
    chunks: Dict[str, Any]
    ready: bool
    message: str
    hardware: Optional[Dict[str, Any]] = None



class UploadResponse(BaseModel):
    message: str
    doc_id: str
    chunks_created: int
    processing_time: float

# Create router
router = APIRouter(prefix="/api/rag", tags=["RAG"])

# Global instances
rag_system: Optional[SimpleRAG] = None
model_client: Optional[DirectModelClient] = None

async def initialize_simple_rag() -> bool:
    """Initialize Simple RAG system if not already done."""
    global rag_system, model_client
    
    try:
        if rag_system is None:
            log.info("Initializing Simple RAG system...")
            
            # Initialize model client
            if model_client is None:
                model_client = DirectModelClient()
            
            # Initialize Simple RAG with vector store
            vector_store = SimpleVectorStore()
            rag_system = SimpleRAG(model_client=model_client, vector_store=vector_store)
            
            log.info("✓ Simple RAG system initialized successfully")
            return True
            
    except Exception as e:
        log.error(f"Failed to initialize Simple RAG: {e}")
        return False
    
    return True

@router.get("/status", response_model=StatusResponse)
async def get_status():
    """Get Simple RAG system status."""
    try:
        # Initialize if needed
        success = await initialize_simple_rag()
        if not success:
            return StatusResponse(
                status="error",
                models={},
                documents={},
                chunks={},
                ready=False,
                message="Failed to initialize RAG system"
            )
        
        # Get model status from DirectModelClient
        model_status = {"embedder": False, "utility": False, "reasoning": False}
        if model_client:
            try:
                # Get actual model loading status from DirectModelClient
                client_status = model_client.get_model_status()
                model_status = {
                    "embedder": True,  # Embedding model is always available
                    "utility": client_status.get("utility", False),
                    "reasoning": client_status.get("generator", False),
                    "lazy_loading": client_status.get("lazy_loading", True)
                }
            except:
                # Fallback to lazy loading status
                model_status = {
                    "embedder": True,
                    "utility": False,  # Not loaded yet
                    "reasoning": False,  # Not loaded yet
                    "lazy_loading": True
                }
        
        # Get RAG system status
        if rag_system:
            rag_status = rag_system.get_status()
        else:
            rag_status = {"documents": {}, "chunks": {"indexed": False}}
        
        # Get hardware status
        hardware_status = {
            "gpu_available": False,
            "memory_usage": 0.0,
            "total_memory": 8.0
        }
        try:
            import torch
            if torch.cuda.is_available():
                hardware_status = {
                    "gpu_available": True,
                    "memory_usage": torch.cuda.memory_allocated() / (1024**3),
                    "total_memory": torch.cuda.get_device_properties(0).total_memory / (1024**3)
                }
        except:
            pass
        
        # Determine readiness - system is ready if documents are indexed
        ready = rag_status["chunks"]["indexed"]
        
        # Create appropriate message
        if ready:
            if model_status.get("lazy_loading", True):
                message = "RAG system ready - models will load on first use"
            else:
                message = "RAG system ready"
        else:
            message = "System initializing or no documents indexed"
        
        return StatusResponse(
            status="ready" if ready else "initializing",
            models=model_status,
            documents=rag_status["documents"],
            chunks=rag_status["chunks"],
            ready=ready,
            message=message,
            hardware=hardware_status
        )
        
    except Exception as e:
        log.error(f"Status check failed: {e}")
        return StatusResponse(
            status="error",
            models={},
            documents={},
            chunks={},
            ready=False,
            message=f"Error: {str(e)}"
        )



@router.post("/answer", response_model=AnswerResponse)
async def answer_question(request: QuestionRequest):
    """Answer a question using the 3-step RAG process."""
    try:
        # Initialize if needed
        success = await initialize_simple_rag()
        if not success:
            raise HTTPException(status_code=500, detail="RAG system not initialized")
        
        # Validate request
        if not request.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
        max_chunks = request.max_chunks or 15
        if max_chunks < 1 or max_chunks > 30:
            raise HTTPException(status_code=400, detail="max_chunks must be between 1 and 30")
        
        min_relevance = request.min_relevance or 0.2
        if min_relevance < 0.0 or min_relevance > 1.0:
            raise HTTPException(status_code=400, detail="min_relevance must be between 0.0 and 1.0")
        
        # Process the question using 3-step RAG
        if rag_system:
            result = await rag_system.answer_question(
                question=request.question,
                max_chunks=max_chunks,
                min_relevance=min_relevance,
                max_tokens=request.max_tokens or 500,
                # Litigation-specific parameters
                matter_type=request.matter_type or "litigation",
                analysis_style=request.analysis_style or "comprehensive",
                focus_area=request.focus_area or "liability"
            )
            return AnswerResponse(**result)
        else:
            raise HTTPException(status_code=500, detail="RAG system not available")
        
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Question answering failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cloud-consultation", response_model=CloudConsultationResponse)
async def cloud_consultation(request: CloudConsultationRequest):
    """Standalone cloud consultation without RAG - direct legal advice from cloud LLMs."""
    try:
        import time
        start_time = time.time()
        
        # Import cloud LLM components
        from src.sc_gen5.core.cloud_llm import CloudLLMGenerator, CloudProvider
        from src.sc_gen5.core.legal_prompts import LegalPromptBuilder
        
        # Validate request
        if not request.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
        # Validate provider
        try:
            provider = CloudProvider(request.provider)
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid provider: {request.provider}. Supported: openai, gemini, claude"
            )
        
        # Initialize cloud LLM generator
        cloud_generator = CloudLLMGenerator()
        
        # Check if provider is available
        if not cloud_generator.check_provider_available(provider):
            raise HTTPException(
                status_code=400,
                detail=f"Provider {request.provider} not available. Check API key in .env file."
            )
        
        # Build legal prompt
        prompt_builder = LegalPromptBuilder()
        legal_prompt = prompt_builder.build_legal_analysis_prompt(
            question=request.question,
            context_documents="",  # No documents for standalone consultation
            matter_type=request.matter_type,
            analysis_style=request.analysis_style or "comprehensive"
        )
        
        # Get model name
        model = request.model or cloud_generator.get_default_model(provider)
        
        # Generate response
        try:
            answer = cloud_generator.generate(
                prompt=legal_prompt,
                provider=provider,
                model=model,
                max_tokens=request.max_tokens,
                temperature=request.temperature or 0.7
            )
        except Exception as e:
            log.error(f"Cloud generation failed: {e}")
            raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Estimate cost (if possible)
        cost_estimate = None
        try:
            # Rough token estimation (words * 1.3 for tokens)
            input_tokens = len(legal_prompt.split()) * 1.3
            output_tokens = len(answer.split()) * 1.3
            cost_estimate = cloud_generator.estimate_cost(
                provider=provider,
                model=model,
                input_tokens=int(input_tokens),
                output_tokens=int(output_tokens)
            )
        except:
            pass  # Cost estimation is optional
        
        return CloudConsultationResponse(
            answer=answer,
            provider=request.provider,
            model=model,
            tokens_used=None,  # Not available from all providers
            cost_estimate=cost_estimate,
            processing_time=processing_time,
            session_id=request.session_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Cloud consultation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cloud-providers")
async def get_cloud_providers():
    """Get available cloud providers and their status."""
    try:
        from src.sc_gen5.core.cloud_llm import CloudLLMGenerator, CloudProvider
        
        cloud_generator = CloudLLMGenerator()
        
        providers = {}
        for provider in CloudProvider:
            status = cloud_generator.validate_provider_setup(provider)
            providers[provider.value] = {
                "available": status["available"],
                "models": status["models"],
                "error": status["error"]
            }
        
        return {
            "providers": providers,
            "available_count": len([p for p in providers.values() if p["available"]])
        }
        
    except Exception as e:
        log.error(f"Failed to get cloud providers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Upload and process a document for RAG."""
    try:
        # Initialize if needed
        success = await initialize_simple_rag()
        if not success:
            raise HTTPException(status_code=500, detail="RAG system not initialized")
        
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Check file size (max 50MB)
        if file.size and file.size > 50 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large (max 50MB)")
        
        # Process document
        start_time = time.time()
        
        # Read file content
        content = await file.read()
        
        # Add to RAG system
        if rag_system:
            doc_id = rag_system.add_document(content, file.filename)
            
            processing_time = time.time() - start_time
            
            # Get chunk count from metadata
            chunk_count = 0
            if doc_id in rag_system.documents:
                chunk_count = rag_system.documents[doc_id].get("chunk_count", 0)
            
            return UploadResponse(
                message="Document uploaded and processed successfully",
                doc_id=doc_id,
                chunks_created=chunk_count,
                processing_time=processing_time
            )
        else:
            raise HTTPException(status_code=500, detail="RAG system not available")
        
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Document upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents")
async def list_documents():
    """List available documents."""
    try:
        # Initialize if needed
        success = await initialize_simple_rag()
        if not success:
            return {"documents": [], "count": 0}
        
        if rag_system:
            documents = []
            for doc_id, doc_info in rag_system.documents.items():
                documents.append({
                    "id": doc_id,
                    "filename": doc_info.get("filename", "Unknown"),
                    "file_size": doc_info.get("file_size", 0),
                    "chunk_count": doc_info.get("chunk_count", 0),
                    "created_at": doc_info.get("created_at", "")
                })
            
            return {
                "documents": documents,
                "count": len(documents)
            }
        else:
            return {"documents": [], "count": 0}
        
    except Exception as e:
        log.error(f"Failed to list documents: {e}")
        return {"documents": [], "count": 0, "error": str(e)}

@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a document from the RAG system."""
    try:
        # Initialize if needed
        success = await initialize_simple_rag()
        if not success:
            raise HTTPException(status_code=500, detail="RAG system not initialized")
        
        if rag_system:
            # Check if document exists
            if doc_id not in rag_system.documents:
                raise HTTPException(status_code=404, detail="Document not found")
            
            # Remove from documents
            del rag_system.documents[doc_id]
            rag_system.save_metadata()
            
            return {"message": "Document deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="RAG system not available")
        
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Document deletion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "simple_rag_v1",
        "architecture": "embedding->utility->generation"
    }

@router.post("/initialize")
async def initialize_system():
    """Initialize the Simple RAG system."""
    try:
        success = await initialize_simple_rag()
        
        if success:
            return {"message": "Simple RAG system initialized successfully", "status": "ready"}
        else:
            return {"message": "Simple RAG system initialization failed", "status": "error"}
            
    except Exception as e:
        log.error(f"Initialization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 