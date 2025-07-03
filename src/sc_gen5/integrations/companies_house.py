"""Companies House API integration for SC Gen 5."""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


class CompaniesHouseClient:
    """Client for Companies House API integration."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.company-information.service.gov.uk",
        timeout: int = 30,
    ) -> None:
        """Initialize Companies House client.
        
        Args:
            api_key: API key (will use CH_API_KEY env var if not provided)
            base_url: Base URL for Companies House API
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or os.getenv("CH_API_KEY")
        if not self.api_key:
            raise ValueError("Companies House API key not found. Set CH_API_KEY environment variable.")
            
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        
        # Setup session with authentication
        self.session = requests.Session()
        self.session.auth = (self.api_key, "")
        self.session.headers.update({
            "User-Agent": "SC-Gen5/1.0.0",
            "Accept": "application/json",
        })
        
        logger.info("Companies House client initialized")

    def get_company_profile(self, company_number: str) -> Dict[str, Any]:
        """Get company profile information.
        
        Args:
            company_number: Company registration number
            
        Returns:
            Company profile data
        """
        url = f"{self.base_url}/company/{company_number}"
        
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Failed to get company profile for {company_number}: {e}")
            raise RuntimeError(f"Companies House API error: {e}")

    def get_filing_history(
        self,
        company_number: str,
        category: Optional[str] = None,
        items_per_page: int = 100,
        start_index: int = 0,
    ) -> Dict[str, Any]:
        """Get company filing history.
        
        Args:
            company_number: Company registration number
            category: Filing category filter
            items_per_page: Number of items per page (max 100)
            start_index: Start index for pagination
            
        Returns:
            Filing history data
        """
        url = f"{self.base_url}/company/{company_number}/filing-history"
        
        params = {
            "items_per_page": min(items_per_page, 100),
            "start_index": start_index,
        }
        
        if category:
            params["category"] = category
            
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Failed to get filing history for {company_number}: {e}")
            raise RuntimeError(f"Companies House API error: {e}")

    def get_filing_document(
        self,
        company_number: str,
        transaction_id: str,
        output_format: str = "pdf",
    ) -> bytes:
        """Download a filing document.
        
        Args:
            company_number: Company registration number
            transaction_id: Filing transaction ID
            output_format: Document format (pdf, html, xml, csv, xbrl)
            
        Returns:
            Document content as bytes
        """
        url = f"{self.base_url}/company/{company_number}/filing-history/{transaction_id}/document"
        
        params = {"format": output_format}
        
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            return response.content
            
        except requests.RequestException as e:
            logger.error(f"Failed to download document {transaction_id}: {e}")
            raise RuntimeError(f"Companies House API error: {e}")

    def search_companies(
        self,
        query: str,
        items_per_page: int = 20,
        start_index: int = 0,
    ) -> Dict[str, Any]:
        """Search for companies.
        
        Args:
            query: Search query
            items_per_page: Number of items per page (max 100)
            start_index: Start index for pagination
            
        Returns:
            Search results
        """
        url = f"{self.base_url}/search/companies"
        
        params = {
            "q": query,
            "items_per_page": min(items_per_page, 100),
            "start_index": start_index,
        }
        
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Failed to search companies with query '{query}': {e}")
            raise RuntimeError(f"Companies House API error: {e}")

    def fetch_document_metadata(self, company_number: str) -> List[Dict[str, Any]]:
        """Fetch metadata for all available documents for a company.
        
        Args:
            company_number: Company registration number
            
        Returns:
            List of document metadata dictionaries
        """
        logger.info(f"Fetching document metadata for company {company_number}")
        
        documents = []
        start_index = 0
        items_per_page = 100
        
        while True:
            try:
                filing_data = self.get_filing_history(
                    company_number=company_number,
                    items_per_page=items_per_page,
                    start_index=start_index,
                )
                
                items = filing_data.get("items", [])
                if not items:
                    break
                
                for filing in items:
                    # Check if document is available for download
                    if filing.get("links", {}).get("document_metadata"):
                        doc_meta = {
                            "transaction_id": filing.get("transaction_id"),
                            "category": filing.get("category"),
                            "description": filing.get("description"),
                            "date": filing.get("date"),
                            "type": filing.get("type"),
                            "paper_filed": filing.get("paper_filed", False),
                            "barcode": filing.get("barcode"),
                            "company_number": company_number,
                        }
                        documents.append(doc_meta)
                
                # Check if there are more pages
                total_count = filing_data.get("total_count", 0)
                if start_index + items_per_page >= total_count:
                    break
                    
                start_index += items_per_page
                
            except Exception as e:
                logger.error(f"Error fetching metadata: {e}")
                break
        
        logger.info(f"Found {len(documents)} available documents for company {company_number}")
        return documents

    def download_filing_pdf(
        self,
        company_number: str,
        transaction_id: str,
        output_dir: str,
        filename: Optional[str] = None,
    ) -> str:
        """Download a filing document as PDF and save to disk.
        
        Args:
            company_number: Company registration number
            transaction_id: Filing transaction ID
            output_dir: Output directory path
            filename: Custom filename (auto-generated if None)
            
        Returns:
            Path to downloaded file
        """
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Generate filename if not provided
        if not filename:
            filename = f"{company_number}_{transaction_id}.pdf"
        
        file_path = output_path / filename
        
        try:
            # Download document
            logger.info(f"Downloading document {transaction_id} for company {company_number}")
            pdf_content = self.get_filing_document(
                company_number=company_number,
                transaction_id=transaction_id,
                output_format="pdf"
            )
            
            # Save to file
            with open(file_path, "wb") as f:
                f.write(pdf_content)
            
            logger.info(f"Saved document to {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Failed to download and save document: {e}")
            raise

    def get_company_officers(self, company_number: str) -> Dict[str, Any]:
        """Get company officers information.
        
        Args:
            company_number: Company registration number
            
        Returns:
            Officers data
        """
        url = f"{self.base_url}/company/{company_number}/officers"
        
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Failed to get officers for {company_number}: {e}")
            raise RuntimeError(f"Companies House API error: {e}")

    def get_company_charges(self, company_number: str) -> Dict[str, Any]:
        """Get company charges information.
        
        Args:
            company_number: Company registration number
            
        Returns:
            Charges data
        """
        url = f"{self.base_url}/company/{company_number}/charges"
        
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Failed to get charges for {company_number}: {e}")
            raise RuntimeError(f"Companies House API error: {e}")

    def validate_company_number(self, company_number: str) -> bool:
        """Validate if company number exists.
        
        Args:
            company_number: Company registration number
            
        Returns:
            True if company exists, False otherwise
        """
        try:
            self.get_company_profile(company_number)
            return True
        except RuntimeError:
            return False

    def get_supported_filing_categories(self) -> List[str]:
        """Get list of supported filing categories."""
        return [
            "accounts",
            "annual-return", 
            "capital",
            "change-of-name",
            "incorporation",
            "liquidation",
            "mortgage",
            "officers",
            "resolutions",
            "confirmation-statement",
        ]

    def filter_documents_by_category(
        self,
        documents: List[Dict[str, Any]],
        categories: List[str],
    ) -> List[Dict[str, Any]]:
        """Filter documents by category.
        
        Args:
            documents: List of document metadata
            categories: List of categories to include
            
        Returns:
            Filtered list of documents
        """
        if not categories:
            return documents
            
        filtered = []
        for doc in documents:
            if doc.get("category") in categories:
                filtered.append(doc)
                
        return filtered

    def get_api_usage_info(self) -> Dict[str, Any]:
        """Get API usage information (if available)."""
        # This is a placeholder - Companies House doesn't provide usage info via API
        # but this could be extended to track usage locally
        return {
            "api_key_configured": bool(self.api_key),
            "base_url": self.base_url,
            "timeout": self.timeout,
        } 