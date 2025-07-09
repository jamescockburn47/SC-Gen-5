"""
Standalone Cloud Consultation Router - Direct cloud LLM consultation without RAG.

This provides direct legal advice from cloud AI models without any document retrieval.
"""

import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..core.cloud_llm import CloudLLMGenerator, CloudProvider
from ..core.strategic_protocols import strategic_protocols
from ..core.local_protocol_enforcer import local_enforcer

# Setup logging
log = logging.getLogger("lexcognito.cloud_consultation")

def _add_unverified_tags(response: str, context: str) -> str:
    """Add [UNVERIFIED] tags to citations that aren't from provided documents."""
    import re
    
    # If no context provided, all citations should be marked as unverified
    if not context.strip():
        # Find citations and add [UNVERIFIED] tags
        citation_patterns = [
            r'\b(case|statute|regulation|act)\s+[A-Z][A-Za-z\s]+(?:v\.|vs\.|v\s+)[A-Z][A-Za-z\s]+',
            r'\b[A-Z][A-Za-z\s]+(?:v\.|vs\.|v\s+)[A-Z][A-Za-z\s]+\s+case',
            r'\b[A-Z][A-Za-z\s]+\s+Act\s+\d{4}',
            r'\b[A-Z][A-Za-z\s]+\s+Regulation\s+\d{4}',
        ]
        
        for pattern in citation_patterns:
            matches = re.finditer(pattern, response, re.IGNORECASE)
            for match in matches:
                citation = match.group(0)
                if "[UNVERIFIED]" not in citation:
                    # Replace the citation with tagged version
                    response = response.replace(citation, f"{citation} [UNVERIFIED]")
    
    return response

# API Models
class CloudConsultationRequest(BaseModel):
    """Request model for standalone cloud consultation."""
    question: str = Field(..., description="The legal question to answer")
    provider: str = Field(..., description="Cloud provider (openai, gemini, claude)")
    model: Optional[str] = Field(default=None, description="Specific model to use")
    max_tokens: Optional[int] = Field(default=2000, description="Maximum tokens for response")
    temperature: Optional[float] = Field(default=0.7, description="Generation temperature")
    user_position: Optional[str] = Field(default="claimant", description="User's adversarial position")
    context: Optional[str] = Field(default="", description="Additional context or documents")
    session_id: Optional[str] = Field(default=None, description="Session ID for tracking")

class ProtocolViolationResponse(BaseModel):
    """Response model for protocol violation."""
    protocol: str
    rule: str
    severity: str
    description: str
    suggestion: Optional[str] = None

class ProtocolReportResponse(BaseModel):
    """Response model for protocol compliance report."""
    overall_compliance: bool
    violations: List[ProtocolViolationResponse]
    ethical_warnings: List[str]
    quality_score: float
    recommendations: List[str]

class CloudConsultationResponse(BaseModel):
    """Response model for cloud consultation."""
    answer: str
    provider: str
    model: str
    tokens_used: Optional[int] = None
    cost_estimate: Optional[float] = None
    processing_time: float
    session_id: Optional[str] = None
    protocol_report: Optional[ProtocolReportResponse] = None

class CloudProviderStatus(BaseModel):
    """Status model for cloud provider."""
    available: bool
    models: list[str]
    error: Optional[str] = None

class CloudProvidersResponse(BaseModel):
    """Response model for cloud providers status."""
    providers: Dict[str, CloudProviderStatus]
    available_count: int

class ImprovePromptRequest(BaseModel):
    """Request model for prompt improvement."""
    original_question: str = Field(..., description="The original legal question")
    context: Optional[str] = Field(default="", description="Additional context")
    user_position: Optional[str] = Field(default="claimant", description="User's position")
    session_id: Optional[str] = Field(default=None, description="Session ID")

class ImprovePromptResponse(BaseModel):
    """Response model for prompt improvement."""
    improved_question: str
    provider: str
    model: str
    processing_time: float
    session_id: Optional[str] = None

class LocalEnforcementRequest(BaseModel):
    """Request model for local protocol enforcement."""
    cloud_response: str = Field(..., description="The cloud model's response")
    original_question: str = Field(..., description="The original question")
    context: Optional[str] = Field(default="", description="Additional context")
    user_position: Optional[str] = Field(default="claimant", description="User's position")
    session_id: Optional[str] = Field(default=None, description="Session ID")

class LocalEnforcementResponse(BaseModel):
    """Response model for local protocol enforcement."""
    is_compliant: bool
    violations: List[ProtocolViolationResponse]
    suggestions: List[str]
    confidence: float
    processing_time: float
    model_used: str
    session_id: Optional[str] = None

# Create router
router = APIRouter(prefix="/api/cloud-consultation", tags=["Cloud Consultation"])

@router.post("/consult", response_model=CloudConsultationResponse)
async def cloud_consultation(request: CloudConsultationRequest):
    """Standalone cloud consultation without RAG - direct legal advice from cloud LLMs."""
    try:
        start_time = time.time()
        
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
        
        # Build litigation prompt using strategic protocols (no local model enhancement)
        legal_prompt = strategic_protocols.build_litigation_prompt(
            question=request.question,
            context=request.context or "",
            user_position=request.user_position or "claimant"
        )
        
        # Get model name
        model = request.model or cloud_generator.get_default_model(provider)
        
        # Generate response
        try:
            log.info(f"Generating response with {provider} model {model}")
            answer = cloud_generator.generate(
                prompt=legal_prompt,
                provider=provider,
                model=model,
                max_tokens=request.max_tokens,
                temperature=request.temperature or 0.7
            )
            log.info(f"Generated answer length: {len(answer)} characters")
            
            # Post-process response to add [UNVERIFIED] tags to citations
            answer = _add_unverified_tags(answer, request.context or "")
            
        except Exception as e:
            log.error(f"Cloud generation failed: {e}")
            raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Use strategic protocols for basic compliance analysis (no local model)
        protocol_report = strategic_protocols.analyze_compliance(
            response=answer,
            question=request.question,
            context=request.context or ""
        )
        
        # Convert violations to response format
        violations_response = []
        for violation in protocol_report.violations:
            violations_response.append(ProtocolViolationResponse(
                protocol=violation.protocol,
                rule=violation.rule,
                severity=violation.severity,
                description=violation.description,
                suggestion=violation.suggestion
            ))
        
        protocol_report_response = ProtocolReportResponse(
            overall_compliance=protocol_report.overall_compliance,
            violations=violations_response,
            ethical_warnings=protocol_report.ethical_warnings,
            quality_score=protocol_report.quality_score,
            recommendations=protocol_report.recommendations
        )
        
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
            session_id=request.session_id,
            protocol_report=protocol_report_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Cloud consultation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/providers", response_model=CloudProvidersResponse)
async def get_cloud_providers():
    """Get available cloud providers and their status."""
    try:
        cloud_generator = CloudLLMGenerator()
        
        providers = {}
        for provider in CloudProvider:
            status = cloud_generator.validate_provider_setup(provider)
            providers[provider.value] = CloudProviderStatus(
                available=status["available"],
                models=status["models"],
                error=status["error"]
            )
        
        return CloudProvidersResponse(
            providers=providers,
            available_count=len([p for p in providers.values() if p.available])
        )
        
    except Exception as e:
        log.error(f"Failed to get cloud providers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/protocols")
async def get_protocols():
    """Get all strategic protocols."""
    return strategic_protocols.get_protocols()

@router.put("/protocols/{protocol_id}/{rule_id}")
async def update_protocol_rule(protocol_id: str, rule_id: str, new_rule: str):
    """Update a specific protocol rule."""
    success = strategic_protocols.update_protocol(protocol_id, rule_id, new_rule)
    if success:
        return {"message": f"Protocol {protocol_id}.{rule_id} updated successfully"}
    else:
        raise HTTPException(status_code=400, detail="Failed to update protocol rule")

@router.post("/protocols/save")
async def save_protocols():
    """Save protocols to file."""
    success = strategic_protocols.save_protocols()
    if success:
        return {"message": "Protocols saved successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to save protocols")

@router.post("/protocols/load")
async def load_protocols():
    """Load protocols from file."""
    success = strategic_protocols.load_protocols()
    if success:
        return {"message": "Protocols loaded successfully"}
    else:
        return {"message": "No saved protocols found, using defaults"}

@router.get("/health")
async def health_check():
    """Health check endpoint for cloud consultation service."""
    return {
        "status": "healthy",
        "service": "cloud_consultation",
        "timestamp": datetime.now().isoformat(),
        "description": "Standalone cloud consultation service with strategic protocols"
    }

@router.get("/enforcement-stats")
async def get_enforcement_stats():
    """Get local protocol enforcement statistics."""
    try:
        stats = local_enforcer.get_enforcement_stats()
        return {
            "local_enforcement": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        log.error(f"Failed to get enforcement stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/improve-prompt", response_model=ImprovePromptResponse)
async def improve_prompt(request: ImprovePromptRequest):
    """Improve a legal question using GPT-4o-mini for better protocol compliance."""
    try:
        start_time = time.time()
        
        # Validate request
        if not request.original_question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
        # Initialize cloud LLM generator
        cloud_generator = CloudLLMGenerator()
        
        # Check if OpenAI is available
        if not cloud_generator.check_provider_available(CloudProvider.OPENAI):
            raise HTTPException(
                status_code=400,
                detail="OpenAI not available. Check OPENAI_API_KEY in .env file."
            )
        
        # Build improvement prompt
        improvement_prompt = f"""You are a legal prompt enhancement expert. Improve the following legal question to encourage better protocol compliance.

ORIGINAL QUESTION: {request.original_question}
USER POSITION: {request.user_position}
CONTEXT: {request.context if request.context else "No specific context provided"}

ENHANCEMENT REQUIREMENTS:
1. Encourage direct legal analysis without IRAC format
2. Request specific citations with verification status
3. Ask for strategic positioning and tactical considerations
4. Emphasize doctrinal logic over narrative framing
5. Request identification of gaps in authority
6. Encourage adversarial clarity and precision
7. Focus on concrete legal issues rather than general principles
8. Request specific factual analysis and evidence evaluation

IMPROVED QUESTION:
"""
        
        # Generate improved question using GPT-4o-mini
        try:
            improved_question = cloud_generator.generate(
                prompt=improvement_prompt,
                provider=CloudProvider.OPENAI,
                model="gpt-4o-mini",
                max_tokens=500,
                temperature=0.3
            )
            
            # Clean up the response
            improved_question = improved_question.strip()
            
            # Ensure we got a meaningful improvement
            if len(improved_question) < len(request.original_question) * 0.8:
                improved_question = request.original_question
                log.warning("Prompt improvement produced shorter result, using original")
            
            processing_time = time.time() - start_time
            
            return ImprovePromptResponse(
                improved_question=improved_question,
                provider="openai",
                model="gpt-4o-mini",
                processing_time=processing_time,
                session_id=request.session_id
            )
            
        except Exception as e:
            log.error(f"Prompt improvement failed: {e}")
            raise HTTPException(status_code=500, detail=f"Prompt improvement failed: {str(e)}")
        
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Prompt improvement failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/enforce-protocols", response_model=LocalEnforcementResponse)
async def enforce_protocols_locally(request: LocalEnforcementRequest):
    """Enforce protocols on a cloud response using local Mistral model."""
    try:
        start_time = time.time()
        
        # Validate request
        if not request.cloud_response.strip():
            raise HTTPException(status_code=400, detail="Cloud response cannot be empty")
        
        if not request.original_question.strip():
            raise HTTPException(status_code=400, detail="Original question cannot be empty")
        
        # Use local Mistral for protocol enforcement
        enforcement_result = local_enforcer.enforce_protocols(
            cloud_response=request.cloud_response,
            original_question=request.original_question,
            context=request.context or "",
            user_position=request.user_position or "claimant"
        )
        
        # Convert violations to response format
        violations_response = []
        for violation in enforcement_result.violations:
            violations_response.append(ProtocolViolationResponse(
                protocol=violation.protocol,
                rule=violation.rule,
                severity=violation.severity,
                description=violation.description,
                suggestion=violation.suggestion
            ))
        
        processing_time = time.time() - start_time
        
        return LocalEnforcementResponse(
            is_compliant=enforcement_result.is_compliant,
            violations=violations_response,
            suggestions=enforcement_result.suggestions,
            confidence=enforcement_result.confidence,
            processing_time=processing_time,
            model_used=enforcement_result.model_used,
            session_id=request.session_id
        )
        
    except Exception as e:
        log.error(f"Local protocol enforcement failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 