"""
FastAPI app factory for SC Gen 5 with Simple RAG integration.
Clean, single RAG system with clear model separation.
"""

import logging
import uvloop
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from fastapi.responses import JSONResponse

from src.sc_gen5.api.main import app as legacy_app
from src.sc_gen5.rag.simple_router import router as rag_router
from src.sc_gen5.api.cloud_consultation import router as cloud_consultation_router
from settings import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances
doc_store = None
rag_system = None
companies_house_client = None

def get_doc_store():
    """Get the global document store instance."""
    return doc_store

def get_rag_system():
    """Get the global Simple RAG system instance."""
    return rag_system

def get_companies_house_client():
    """Get the global Companies House client instance."""
    return companies_house_client

def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application with Simple RAG only.
    """
    app = FastAPI(
        title="LexCognito API v2",
        description="AI-Powered Legal Research Platform with Simple RAG",
        version="2.0.0"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include Simple RAG router
    app.include_router(rag_router, tags=["RAG"])
    
    # Include standalone Cloud Consultation router
    app.include_router(cloud_consultation_router, tags=["Cloud Consultation"])
    
    # Include legacy app (document management, companies house, etc.)
    app.mount("/api", legacy_app)
    
    return app

app = create_app()

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global doc_store, rag_system, companies_house_client
    
    logger.info("Starting LexCognito API v2...")
    
    try:
        # Initialize hardware settings
        from src.sc_gen5.rag.v2.hardware import check_hardware_requirements
        requirements_met, warnings = check_hardware_requirements()
        
        if not requirements_met:
            logger.warning("Hardware requirements not fully met:")
            for warning in warnings:
                logger.warning(f"  - {warning}")
        else:
            logger.info("Hardware requirements satisfied")
        
        # Initialize legacy components
        try:
            from src.sc_gen5.core.enhanced_doc_store import EnhancedDocStore
            from src.sc_gen5.integrations.companies_house import CompaniesHouseClient
            
            # Initialize enhanced document store
            global doc_store
            doc_store = EnhancedDocStore()
            logger.info("Legacy document store initialized")
            app.state.doc_store = doc_store
            from src.sc_gen5.api.main import app as legacy_app
            legacy_app.state.doc_store = doc_store
            
            # Initialize Companies House client
            try:
                global companies_house_client
                companies_house_client = CompaniesHouseClient()
                logger.info("Companies House client initialized")
                app.state.companies_house_client = companies_house_client
                legacy_app.state.companies_house_client = companies_house_client
            except Exception as e:
                logger.warning(f"Companies House client failed to initialize: {e}")
                companies_house_client = None
                app.state.companies_house_client = None
                legacy_app.state.companies_house_client = None
            
        except Exception as e:
            logger.warning(f"Legacy components initialization failed: {e}")
        
        # LAZY LOADING: Skip ALL model loading at startup
        logger.info("LAZY LOADING MODE: No models loaded at startup")
        logger.info("Models will be loaded on first use to reduce memory pressure")
        logger.info("Available models: Mistral-7B-Instruct (will load on first use)")
        
        logger.info("LexCognito API v2 startup complete")
        
    except Exception as e:
        logger.error(f"Startup error: {e}")
        # Don't raise here to allow the app to start even with issues

@app.get("/")
def root():
    return JSONResponse({"message": "LexCognito API v2 is running"})

@app.get("/api/system/stats")
def get_system_stats():
    """Get system statistics for the dashboard."""
    import psutil
    import os
    
    try:
        # Get CPU info
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # Get memory info
        memory = psutil.virtual_memory()
        ram_usage = memory.percent
        ram_total = memory.total / (1024**3)  # Convert to GB
        ram_used = memory.used / (1024**3)
        ram_memory = f"{ram_used:.1f}GB / {ram_total:.1f}GB"
        
        # Get disk info
        disk = psutil.disk_usage('/')
        disk_usage = (disk.used / disk.total) * 100
        disk_total = disk.total / (1024**3)  # Convert to GB
        disk_used = disk.used / (1024**3)
        disk_space = f"{disk_used:.1f}GB / {disk_total:.1f}GB"
        
        # Get GPU info (if available)
        gpu_usage = 0
        gpu_memory = "N/A"
        try:
            import torch
            if torch.cuda.is_available():
                gpu_usage = torch.cuda.memory_allocated() / torch.cuda.max_memory_allocated() * 100 if torch.cuda.max_memory_allocated() > 0 else 0
                gpu_memory = f"{torch.cuda.memory_allocated() / (1024**3):.1f}GB"
        except:
            pass
        
        return {
            "cpu": {
                "usage": cpu_percent,
                "cores": cpu_count
            },
            "ram": {
                "usage": ram_usage,
                "memory": ram_memory
            },
            "storage": {
                "usage": disk_usage,
                "space": disk_space
            },
            "gpu": {
                "usage": gpu_usage,
                "memory": gpu_memory
            }
        }
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        return {
            "cpu": {"usage": 0, "cores": 0},
            "ram": {"usage": 0, "memory": "N/A"},
            "storage": {"usage": 0, "space": "N/A"},
            "gpu": {"usage": 0, "memory": "N/A"}
        }

@app.get("/api/dashboard/stats")
def get_dashboard_stats():
    """Get dashboard statistics."""
    try:
        # Get document count
        doc_count = 0
        if doc_store:
            try:
                doc_count = len(doc_store.list_documents())
            except:
                pass
        
        # Get companies count (placeholder)
        companies_count = 0
        
        # Get queries count (placeholder)
        queries_count = 0
        
        # Get average response time (placeholder)
        avg_response_time = "0.5s"
        
        return {
            "documents": doc_count,
            "companies": companies_count,
            "queries": queries_count,
            "avgResponseTime": avg_response_time
        }
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        return {
            "documents": 0,
            "companies": 0,
            "queries": 0,
            "avgResponseTime": "0s"
        }

if __name__ == "__main__":
    import uvicorn
    
    # Use uvloop for better performance
    uvicorn.run(
        "app:app",
        host="127.0.0.1",  # Use localhost instead of 0.0.0.0
        port=8001,          # Use different port to avoid conflicts
        workers=1,          # Single worker to avoid conflicts
        loop="uvloop",
        log_level="info"
    )