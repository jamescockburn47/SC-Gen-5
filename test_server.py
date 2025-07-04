#!/usr/bin/env python3
"""
Simple test server for SC Gen 5 - No complex dependencies
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

# Create FastAPI app
app = FastAPI(
    title="SC Gen 5 - Test Server",
    description="Simple test server for Strategic Counsel Gen 5",
    version="1.0.0"
)

# Sample data models
class ConsultationRequest(BaseModel):
    question: str
    matter_id: Optional[str] = "test-matter"
    model: Optional[str] = "test-model"

class ConsultationResponse(BaseModel):
    answer: str
    sources: List[str]
    matter_id: str
    model_used: str

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "SC Gen 5 Test Server"}

@app.get("/")
async def root():
    return {
        "message": "Strategic Counsel Gen 5 - Test Server",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "consult": "/consult"
        }
    }

@app.post("/consult", response_model=ConsultationResponse)
async def consult(request: ConsultationRequest):
    """Test consultation endpoint"""
    return ConsultationResponse(
        answer=f"This is a test response to: {request.question}",
        sources=["test-document-1.pdf", "test-document-2.pdf"],
        matter_id=request.matter_id or "test-matter",
        model_used=request.model or "test-model"
    )

@app.get("/test")
async def test_endpoint():
    """Simple test endpoint"""
    return {
        "message": "SC Gen 5 Test Server is working!",
        "features": [
            "FastAPI backend",
            "Health monitoring",
            "Consultation API",
            "Document processing ready"
        ]
    }

if __name__ == "__main__":
    print("🚀 Starting SC Gen 5 Test Server...")
    print("📖 API Documentation: http://localhost:8000/docs")
    print("🔗 Test endpoint: http://localhost:8000/test")
    print("🏥 Health check: http://localhost:8000/health")
    
    uvicorn.run(app, host="0.0.0.0", port=8000) 