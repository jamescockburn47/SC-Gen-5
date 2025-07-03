"""FastAPI service for Companies House document ingestion."""

import logging
import os
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from sc_gen5.core.doc_store import DocStore
from sc_gen5.integrations.companies_house import CompaniesHouseClient

logger = logging.getLogger(__name__)

# Global instances
doc_store: Optional[DocStore] = None
ch_client: Optional[CompaniesHouseClient] = None


class IngestRequest(BaseModel):
    """Request model for Companies House ingestion."""
    company_number: str = Field(..., description="Companies House company number")
    filing_id: Optional[str] = Field(
        default=None,
        description="Specific filing ID to ingest (if None, ingests all available filings)"
    )
    categories: Optional[List[str]] = Field(
        default=None,
        description="Specific filing categories to include (e.g., ['accounts', 'annual-return'])"
    )
    max_documents: Optional[int] = Field(
        default=10,
        description="Maximum number of documents to ingest"
    )


class IngestResponse(BaseModel):
    """Response model for ingestion endpoint."""
    success: bool = Field(..., description="Whether ingestion was successful")
    company_number: str = Field(..., description="Company number processed")
    ingested_documents: List[str] = Field(..., description="List of ingested document IDs")
    skipped_documents: List[str] = Field(default_factory=list, description="List of skipped document IDs")
    errors: List[str] = Field(default_factory=list, description="List of error messages")
    message: str = Field(..., description="Summary message")


class CompanySearchRequest(BaseModel):
    """Request model for company search."""
    query: str = Field(..., description="Search query")
    limit: int = Field(default=20, description="Maximum number of results")


class CompanyInfo(BaseModel):
    """Company information model."""
    company_number: str
    company_name: str
    company_status: str
    company_type: str
    date_of_creation: Optional[str] = None
    address: Optional[Dict[str, Any]] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for FastAPI app."""
    # Startup
    global doc_store, ch_client
    
    logger.info("Starting SC Gen 5 Companies House Ingest Service...")
    
    # Initialize components
    data_dir = os.getenv("SC_DATA_DIR", "./data")
    vector_db_path = os.getenv("SC_VECTOR_DB_PATH", "./data/vector_db")
    metadata_path = os.getenv("SC_METADATA_PATH", "./data/metadata.json")
    chunk_size = int(os.getenv("SC_CHUNK_SIZE", "400"))
    chunk_overlap = int(os.getenv("SC_CHUNK_OVERLAP", "80"))
    embedding_model = os.getenv("SC_EMBEDDING_MODEL", "BAAI/bge-base-en-v1.5")
    
    # Initialize document store
    doc_store = DocStore(
        data_dir=data_dir,
        vector_db_path=vector_db_path,
        metadata_path=metadata_path,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        embedding_model=embedding_model,
    )
    
    # Initialize Companies House client
    try:
        ch_client = CompaniesHouseClient()
        logger.info("Companies House client initialized successfully")
    except ValueError as e:
        logger.warning(f"Companies House client initialization failed: {e}")
        ch_client = None
    
    logger.info("SC Gen 5 Companies House Ingest Service started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down SC Gen 5 Companies House Ingest Service...")


# Create FastAPI app
app = FastAPI(
    title="SC Gen 5 Companies House Ingest Service",
    description="Service for ingesting Companies House filings into the knowledge base",
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


@app.post("/ingest", response_model=IngestResponse)
async def ingest_company_filings(request: IngestRequest) -> IngestResponse:
    """Ingest Companies House filings for a company.
    
    This endpoint:
    1. Fetches available filing metadata from Companies House API
    2. Downloads filing documents (PDFs)
    3. Processes them through OCR and adds to knowledge base
    4. Returns list of successfully ingested document IDs
    """
    if not ch_client:
        raise HTTPException(
            status_code=503,
            detail="Companies House client not available. Check CH_API_KEY environment variable."
        )
    
    if not doc_store:
        raise HTTPException(status_code=500, detail="Document store not initialized")
    
    try:
        logger.info(f"Starting ingestion for company {request.company_number}")
        
        # Validate company number
        if not ch_client.validate_company_number(request.company_number):
            raise HTTPException(
                status_code=404,
                detail=f"Company number {request.company_number} not found"
            )
        
        # Get company profile for metadata
        company_profile = ch_client.get_company_profile(request.company_number)
        company_name = company_profile.get("company_name", "Unknown")
        
        ingested_docs = []
        skipped_docs = []
        errors = []
        
        if request.filing_id:
            # Ingest specific filing
            try:
                doc_id = await _ingest_single_filing(
                    request.company_number,
                    request.filing_id,
                    company_name,
                )
                ingested_docs.append(doc_id)
            except Exception as e:
                errors.append(f"Failed to ingest filing {request.filing_id}: {str(e)}")
        else:
            # Ingest multiple filings
            try:
                # Fetch document metadata
                documents = ch_client.fetch_document_metadata(request.company_number)
                
                # Filter by categories if specified
                if request.categories:
                    documents = ch_client.filter_documents_by_category(documents, request.categories)
                
                # Limit number of documents
                if request.max_documents:
                    documents = documents[:request.max_documents]
                
                logger.info(f"Found {len(documents)} documents to process")
                
                for doc_meta in documents:
                    try:
                        doc_id = await _ingest_single_filing(
                            request.company_number,
                            doc_meta["transaction_id"],
                            company_name,
                            doc_meta,
                        )
                        ingested_docs.append(doc_id)
                        
                    except Exception as e:
                        error_msg = f"Failed to ingest {doc_meta.get('transaction_id', 'unknown')}: {str(e)}"
                        errors.append(error_msg)
                        skipped_docs.append(doc_meta.get("transaction_id", "unknown"))
                        logger.error(error_msg)
                        
            except Exception as e:
                errors.append(f"Failed to fetch document metadata: {str(e)}")
        
        success = len(ingested_docs) > 0
        message = f"Successfully ingested {len(ingested_docs)} documents"
        if errors:
            message += f", {len(errors)} errors occurred"
        
        return IngestResponse(
            success=success,
            company_number=request.company_number,
            ingested_documents=ingested_docs,
            skipped_documents=skipped_docs,
            errors=errors,
            message=message,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


async def _ingest_single_filing(
    company_number: str,
    transaction_id: str,
    company_name: str,
    filing_metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """Ingest a single filing document."""
    logger.info(f"Ingesting filing {transaction_id} for company {company_number}")
    
    # Create temporary directory for download
    with tempfile.TemporaryDirectory() as temp_dir:
        # Download PDF
        pdf_path = ch_client.download_filing_pdf(
            company_number=company_number,
            transaction_id=transaction_id,
            output_dir=temp_dir,
        )
        
        # Read PDF content
        with open(pdf_path, "rb") as f:
            pdf_content = f.read()
        
        # Prepare metadata
        metadata = {
            "source": "companies_house",
            "company_number": company_number,
            "company_name": company_name,
            "transaction_id": transaction_id,
            **(filing_metadata or {})
        }
        
        # Generate filename
        filename = f"CH_{company_number}_{transaction_id}.pdf"
        
        # Add to document store
        doc_id = doc_store.add_document(
            file_bytes=pdf_content,
            filename=filename,
            metadata=metadata,
        )
        
        logger.info(f"Successfully ingested filing {transaction_id} as document {doc_id}")
        return doc_id


@app.post("/search-companies")
async def search_companies(request: CompanySearchRequest):
    """Search for companies using Companies House API."""
    if not ch_client:
        raise HTTPException(
            status_code=503,
            detail="Companies House client not available"
        )
    
    try:
        results = ch_client.search_companies(
            query=request.query,
            items_per_page=request.limit,
        )
        
        companies = []
        for item in results.get("items", []):
            company = CompanyInfo(
                company_number=item.get("company_number", ""),
                company_name=item.get("title", ""),
                company_status=item.get("company_status", ""),
                company_type=item.get("company_type", ""),
                date_of_creation=item.get("date_of_creation"),
                address=item.get("address"),
            )
            companies.append(company)
        
        return {
            "companies": companies,
            "total": len(companies),
            "query": request.query,
        }
        
    except Exception as e:
        logger.error(f"Company search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Company search failed: {str(e)}")


@app.get("/company/{company_number}")
async def get_company_info(company_number: str):
    """Get company information from Companies House."""
    if not ch_client:
        raise HTTPException(
            status_code=503,
            detail="Companies House client not available"
        )
    
    try:
        profile = ch_client.get_company_profile(company_number)
        return profile
        
    except Exception as e:
        logger.error(f"Failed to get company info: {e}")
        if "404" in str(e):
            raise HTTPException(status_code=404, detail="Company not found")
        raise HTTPException(status_code=500, detail=f"Failed to get company info: {str(e)}")


@app.get("/company/{company_number}/filings")
async def get_company_filings(
    company_number: str,
    category: Optional[str] = None,
    limit: int = 100,
):
    """Get filing history for a company."""
    if not ch_client:
        raise HTTPException(
            status_code=503,
            detail="Companies House client not available"
        )
    
    try:
        filings = ch_client.get_filing_history(
            company_number=company_number,
            category=category,
            items_per_page=limit,
        )
        return filings
        
    except Exception as e:
        logger.error(f"Failed to get company filings: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get company filings: {str(e)}")


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "companies_house_available": ch_client is not None,
        "doc_store_available": doc_store is not None,
    }


@app.get("/categories")
async def get_filing_categories():
    """Get supported filing categories."""
    if not ch_client:
        return {"categories": []}
    
    return {"categories": ch_client.get_supported_filing_categories()}


def main():
    """Main entry point for running the service."""
    import uvicorn
    
    host = os.getenv("SC_API_HOST", "0.0.0.0")
    port = int(os.getenv("SC_API_PORT", "8001"))  # Different port from consult service
    log_level = os.getenv("SC_LOG_LEVEL", "info").lower()
    
    uvicorn.run(
        "sc_gen5.services.ch_ingest_service:app",
        host=host,
        port=port,
        log_level=log_level,
        reload=False,  # Set to True for development
    )


if __name__ == "__main__":
    main() 