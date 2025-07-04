"""Streamlit UI for Strategic Counsel Gen 5."""

import json
import logging
import os
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional
import time

import streamlit as st
from dotenv import load_dotenv

# Load environment variables from .env file
from pathlib import Path
env_path = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(env_path)

from sc_gen5.core.doc_store import DocStore
from sc_gen5.core.rag_pipeline import RAGPipeline
from sc_gen5.integrations.companies_house import CompaniesHouseClient
from sc_gen5.integrations.gemini_cli import OfficialGeminiCLI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Strategic Counsel Gen 5",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
.main-header {
    font-size: 2.5rem;
    color: #1f4e79;
    text-align: center;
    margin-bottom: 2rem;
}

.success-box {
    padding: 1rem;
    border-radius: 0.5rem;
    background-color: #d4edda;
    border: 1px solid #c3e6cb;
    color: #155724;
    margin: 1rem 0;
}

.error-box {
    padding: 1rem;
    border-radius: 0.5rem;
    background-color: #f8d7da;
    border: 1px solid #f5c6cb;
    color: #721c24;
    margin: 1rem 0;
}

.info-box {
    padding: 1rem;
    border-radius: 0.5rem;
    background-color: #cce7ff;
    border: 1px solid #b3d9ff;
    color: #004085;
    margin: 1rem 0;
}

.stats-metric {
    text-align: center;
    padding: 1rem;
    background-color: #f8f9fa;
    border-radius: 0.5rem;
    margin: 0.5rem;
}
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def initialize_components():
    """Initialize core components with caching."""
    try:
        # Get configuration from environment or defaults
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
        
        # Initialize RAG pipeline
        rag_pipeline = RAGPipeline(
            doc_store=doc_store,
            retrieval_k=int(os.getenv("SC_RETRIEVAL_K", "18")),
            rerank_top_k=int(os.getenv("SC_RERANK_TOP_K", "6")),
            use_reranker=os.getenv("SC_USE_RERANKER", "false").lower() == "true",
        )
        
        # Initialize Companies House client (optional)
        ch_client = None
        try:
            ch_client = CompaniesHouseClient()
        except ValueError:
            logger.warning("Companies House client not available - CH_API_KEY not set")
        
        # Initialize Gemini CLI (optional)
        gemini_cli = None
        try:
            gemini_cli = OfficialGeminiCLI()
        except Exception as e:
            logger.warning(f"Gemini CLI not available: {e}")
        
        return doc_store, rag_pipeline, ch_client, gemini_cli
        
    except Exception as e:
        st.error(f"Failed to initialize components: {e}")
        return None, None, None, None


def main():
    """Main Streamlit application."""
    # Header
    st.markdown('<h1 class="main-header">⚖️ Strategic Counsel Gen 5</h1>', unsafe_allow_html=True)
    st.markdown("**Local-first legal research assistant with RAG and Companies House integration**")
    
    # Initialize components
    doc_store, rag_pipeline, ch_client, gemini_cli = initialize_components()
    
    if not doc_store or not rag_pipeline:
        st.error("Failed to initialize core components. Please check your configuration.")
        return
    
    # Sidebar
    with st.sidebar:
        st.header("🔧 Configuration")
        
        # System status
        st.subheader("System Status")
        
        doc_stats = doc_store.get_stats()
        st.metric("Documents", doc_stats["total_documents"])
        st.metric("Text Chunks", doc_stats["total_chunks"])
        
        rag_stats = rag_pipeline.validate_setup()
        if rag_stats.get("local_llm") == "ok":
            st.success("🟢 Local LLM: Available")
        else:
            st.warning("🟡 Local LLM: Unavailable")
        
        cloud_providers = rag_stats.get("cloud_providers", [])
        if cloud_providers:
            st.success(f"🟢 Cloud LLMs: {', '.join(cloud_providers)}")
        else:
            st.info("ℹ️ Cloud LLMs: Not configured")
            
        if ch_client:
            st.success("🟢 Companies House: Available")
        else:
            st.warning("🟡 Companies House: Not configured")
        
        if gemini_cli:
            gemini_info = gemini_cli.get_system_info()
            if gemini_info.get("cli_available", False):
                st.success("🟢 Official Gemini CLI: Available")
            else:
                st.warning("🟡 Official Gemini CLI: Node.js/npm required")
        else:
            st.warning("🟡 Official Gemini CLI: Not configured")
    
    # Main tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["💬 Consultation", "📄 Document Management", "🏢 Companies House", "🤖 Gemini CLI", "📊 Analytics"])
    
    with tab1:
        consultation_tab(rag_pipeline)
    
    with tab2:
        document_management_tab(doc_store)
    
    with tab3:
        companies_house_tab(ch_client, doc_store)
    
    with tab4:
        gemini_cli_tab(gemini_cli)
    
    with tab5:
        analytics_tab(doc_store, rag_pipeline)


def consultation_tab(rag_pipeline: RAGPipeline):
    """Consultation interface tab."""
    st.header("💬 Legal Consultation")
    
    # Query mode selection
    st.subheader("📋 Query Mode")
    query_mode = st.radio(
        "Select how you want to process your question:",
        ["🤖 Standalone Legal Query", "📚 Search My Documents (RAG)"],
        help="Standalone: Direct legal advice from AI models. RAG: Search your uploaded documents first, then provide context-aware answers."
    )
    
    # Consultation form
    with st.form("consultation_form"):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            matter_id = st.text_input("Matter ID", value=f"matter_{len(st.session_state.get('consultations', []))}")
            question = st.text_area("Legal Question", height=120, placeholder="Enter your legal question here...")
            matter_type = st.selectbox("Matter Type", 
                                     ["", "contract", "regulatory", "litigation", "due_diligence"])
        
        with col2:
            cloud_allowed = st.checkbox("Allow Cloud LLMs")
            
            if cloud_allowed:
                cloud_provider = st.selectbox("Cloud Provider", 
                                            ["", "openai", "gemini", "claude"])
            else:
                cloud_provider = None
                
            model_choice = st.selectbox("Model", 
                                      ["", "mixtral", "mistral", "phi3", "lawma"])
        
        submitted = st.form_submit_button("🔍 Get Legal Analysis", type="primary")
    
    if submitted and question:
        with st.spinner("Analyzing your legal question..."):
            try:
                use_rag = query_mode == "📚 Search My Documents (RAG)"
                
                if use_rag:
                    # RAG-based query (search documents first)
                    result = rag_pipeline.answer(
                        question=question,
                        cloud_allowed=cloud_allowed,
                        cloud_provider=cloud_provider,
                        model_choice=model_choice if model_choice else None,
                        matter_type=matter_type if matter_type else None,
                        matter_id=matter_id,
                    )
                else:
                    # Standalone legal query (direct to LLM)
                    result = rag_pipeline.direct_answer(
                        question=question,
                        cloud_allowed=cloud_allowed,
                        cloud_provider=cloud_provider,
                        model_choice=model_choice if model_choice else None,
                        matter_type=matter_type if matter_type else None,
                        matter_id=matter_id,
                    )
                
                # Display results
                st.subheader("📋 Legal Analysis")
                st.markdown(result["answer"])
                
                # Metadata
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Model Used", result["model_used"])
                with col2:
                    st.metric("Retrieved Chunks", result["retrieved_chunks"])
                with col3:
                    st.metric("Context Length", result.get("context_length", "N/A"))
                
                # Sources
                if result["sources"]:
                    st.subheader("📚 Sources")
                    st.text(result["sources"])
                
                # Save to session state
                if "consultations" not in st.session_state:
                    st.session_state.consultations = []
                
                consultation = {
                    "matter_id": matter_id,
                    "question": question,
                    "answer": result["answer"],
                    "sources": result["sources"],
                    "model_used": result["model_used"],
                    "timestamp": result.get("timestamp", ""),
                }
                st.session_state.consultations.append(consultation)
                
            except Exception as e:
                st.error(f"Analysis failed: {e}")
    
    # Previous consultations
    if "consultations" in st.session_state and st.session_state.consultations:
        st.subheader("📜 Previous Consultations")
        
        for i, consult in enumerate(reversed(st.session_state.consultations[-5:])):
            with st.expander(f"Matter {consult['matter_id']} - {consult['question'][:50]}..."):
                st.markdown(f"**Question:** {consult['question']}")
                st.markdown(f"**Answer:** {consult['answer']}")
                st.markdown(f"**Model:** {consult['model_used']}")
                if consult['sources']:
                    st.markdown(f"**Sources:** {consult['sources']}")


def document_management_tab(doc_store: DocStore):
    """Document management interface tab."""
    st.header("📄 Document Management")
    
    # File upload
    st.subheader("📤 Upload Documents")
    uploaded_files = st.file_uploader(
        "Choose PDF or image files",
        accept_multiple_files=True,
        type=['pdf', 'png', 'jpg', 'jpeg', 'tiff', 'bmp']
    )
    
    if uploaded_files:
        if st.button("🔄 Process Documents"):
            progress_bar = st.progress(0)
            success_count = 0
            
            for i, uploaded_file in enumerate(uploaded_files):
                try:
                    # Read file content
                    file_bytes = uploaded_file.read()
                    
                    # Add to document store
                    doc_id = doc_store.add_document(
                        file_bytes=file_bytes,
                        filename=uploaded_file.name,
                        metadata={"uploaded_via": "streamlit"}
                    )
                    
                    st.success(f"✅ Processed: {uploaded_file.name} (ID: {doc_id})")
                    success_count += 1
                    
                except Exception as e:
                    st.error(f"❌ Failed to process {uploaded_file.name}: {e}")
                
                progress_bar.progress((i + 1) / len(uploaded_files))
            
            st.info(f"Successfully processed {success_count}/{len(uploaded_files)} documents")
            
            # Refresh the page to show updated stats
            st.rerun()
    
    # Document list
    st.subheader("📋 Document Library")
    
    documents = doc_store.list_documents()
    
    if documents:
        # Search/filter
        search_term = st.text_input("🔍 Search documents", placeholder="Enter filename or content...")
        
        # Filter documents
        if search_term:
            documents = [doc for doc in documents if search_term.lower() in doc["filename"].lower()]
        
        # Display documents
        for doc in documents:
            with st.expander(f"📄 {doc['filename']} (ID: {doc['doc_id']})"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("File Size", f"{doc.get('file_size', 0):,} bytes")
                with col2:
                    st.metric("Text Length", f"{doc.get('text_length', 0):,} chars")
                with col3:
                    st.metric("Chunks", doc.get('num_chunks', 0))
                
                st.text(f"Created: {doc.get('created_at', 'Unknown')}")
                st.text(f"Type: {doc.get('file_type', 'Unknown')}")
                
                if st.button(f"🗑️ Delete", key=f"delete_{doc['doc_id']}"):
                    if doc_store.delete_document(doc['doc_id']):
                        st.success(f"Deleted {doc['filename']}")
                        st.rerun()
                    else:
                        st.error("Failed to delete document")
    else:
        st.info("No documents uploaded yet. Upload some documents to get started!")


def companies_house_tab(ch_client: Optional[CompaniesHouseClient], doc_store: DocStore):
    """Companies House integration tab."""
    st.header("🏢 Companies House Integration")
    
    if not ch_client:
        st.warning("Companies House integration not available. Please set CH_API_KEY environment variable.")
        return
    
    # Company search
    st.subheader("🔍 Company Search")
    
    with st.form("company_search"):
        search_query = st.text_input("Company Name or Number")
        search_submitted = st.form_submit_button("Search")
    
    if search_submitted and search_query:
        try:
            results = ch_client.search_companies(search_query)
            
            if results.get("items"):
                st.subheader("Search Results")
                
                for company in results["items"]:
                    with st.expander(f"{company.get('title', 'Unknown')} ({company.get('company_number', 'N/A')})"):
                        st.text(f"Status: {company.get('company_status', 'Unknown')}")
                        st.text(f"Type: {company.get('company_type', 'Unknown')}")
                        st.text(f"Created: {company.get('date_of_creation', 'Unknown')}")
                        
                        if st.button(f"Ingest Filings", key=f"ingest_{company.get('company_number')}"):
                            st.session_state.selected_company = company.get('company_number')
            else:
                st.info("No companies found")
                
        except Exception as e:
            st.error(f"Search failed: {e}")
    
    # Document ingestion
    if "selected_company" in st.session_state:
        st.subheader(f"📥 Ingest Filings for Company {st.session_state.selected_company}")
        
        with st.form("ingest_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                max_docs = st.number_input("Max Documents", min_value=1, max_value=50, value=10)
                categories = st.multiselect("Filing Categories", 
                                          ch_client.get_supported_filing_categories())
            
            with col2:
                specific_filing = st.text_input("Specific Filing ID (optional)")
            
            ingest_submitted = st.form_submit_button("📥 Start Ingestion")
        
        if ingest_submitted:
            with st.spinner("Ingesting documents..."):
                try:
                    company_number = st.session_state.selected_company
                    
                    if specific_filing:
                        # Ingest specific filing
                        doc_id = ingest_single_filing(ch_client, doc_store, company_number, specific_filing)
                        st.success(f"Successfully ingested filing {specific_filing} as document {doc_id}")
                    else:
                        # Ingest multiple filings
                        success_count, errors = ingest_company_filings(
                            ch_client, doc_store, company_number, categories, max_docs
                        )
                        
                        if success_count > 0:
                            st.success(f"Successfully ingested {success_count} documents")
                        
                        if errors:
                            st.error(f"Errors occurred: {len(errors)}")
                            for error in errors[:5]:  # Show first 5 errors
                                st.text(error)
                
                except Exception as e:
                    st.error(f"Ingestion failed: {e}")


def analytics_tab(doc_store: DocStore, rag_pipeline: RAGPipeline):
    """Analytics and system information tab."""
    st.header("📊 System Analytics")
    
    # System stats
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📄 Document Store")
        doc_stats = doc_store.get_stats()
        
        st.metric("Total Documents", doc_stats["total_documents"])
        st.metric("Total Chunks", doc_stats["total_chunks"])
        st.metric("Total Text Length", f"{doc_stats['total_text_length']:,} chars")
        
        # Vector store stats
        vector_stats = doc_stats["vector_store"]
        st.metric("Embeddings", vector_stats["total_embeddings"])
        st.text(f"Embedding Model: {vector_stats['embedding_model']}")
        st.text(f"Dimension: {vector_stats['dimension']}")
    
    with col2:
        st.subheader("🔍 RAG Pipeline")
        rag_stats = rag_pipeline.get_retrieval_stats()
        
        st.metric("Retrieval K", rag_stats["retrieval_k"])
        st.metric("Rerank Top K", rag_stats["rerank_top_k"])
        
        if rag_stats["use_reranker"]:
            reranker_status = "🟢 Enabled" if rag_stats["reranker_available"] else "🔴 Failed"
        else:
            reranker_status = "⚪ Disabled"
        st.text(f"Reranker: {reranker_status}")
    
    # System validation
    st.subheader("🔧 System Validation")
    validation = rag_pipeline.validate_setup()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.text("Document Store")
        if validation["doc_store"] == "ok":
            st.success("✅ Operational")
        else:
            st.error("❌ Error")
    
    with col2:
        st.text("Local LLM")
        if validation["local_llm"] == "ok":
            st.success("✅ Available")
        elif validation["local_llm"] == "server_unavailable":
            st.warning("⚠️ Server Unavailable")
        else:
            st.error("❌ Not Tested")
    
    with col3:
        st.text("Cloud LLMs")
        cloud_providers = validation.get("cloud_providers", [])
        if cloud_providers:
            st.success(f"✅ {', '.join(cloud_providers)}")
        else:
            st.info("ℹ️ Not configured")
    
    # Configuration display
    st.subheader("⚙️ Configuration")
    config = {
        "Data Directory": doc_stats["data_dir"],
        "Chunk Size": doc_stats["chunk_size"],
        "Chunk Overlap": doc_stats["chunk_overlap"],
        "Embedding Model": vector_stats["embedding_model"],
        "Retrieval K": rag_stats["retrieval_k"],
        "Rerank Top K": rag_stats["rerank_top_k"],
    }
    
    st.json(config)


def ingest_single_filing(
    ch_client: CompaniesHouseClient,
    doc_store: DocStore,
    company_number: str,
    filing_id: str,
) -> str:
    """Ingest a single Companies House filing."""
    # Get company profile for metadata
    company_profile = ch_client.get_company_profile(company_number)
    company_name = company_profile.get("company_name", "Unknown")
    
    # Create temporary directory for download
    with tempfile.TemporaryDirectory() as temp_dir:
        # Download PDF
        pdf_path = ch_client.download_filing_pdf(
            company_number=company_number,
            transaction_id=filing_id,
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
            "transaction_id": filing_id,
        }
        
        # Generate filename
        filename = f"CH_{company_number}_{filing_id}.pdf"
        
        # Add to document store
        doc_id = doc_store.add_document(
            file_bytes=pdf_content,
            filename=filename,
            metadata=metadata,
        )
        
        return doc_id


def ingest_company_filings(
    ch_client: CompaniesHouseClient,
    doc_store: DocStore,
    company_number: str,
    categories: list[str],
    max_docs: int,
) -> tuple[int, list[str]]:
    """Ingest multiple Companies House filings for a company."""
    # Get company profile for metadata
    company_profile = ch_client.get_company_profile(company_number)
    company_name = company_profile.get("company_name", "Unknown")
    
    # Fetch document metadata
    documents = ch_client.fetch_document_metadata(company_number)
    
    # Filter by categories if specified
    if categories:
        documents = ch_client.filter_documents_by_category(documents, categories)
    
    # Limit number of documents
    documents = documents[:max_docs]
    
    success_count = 0
    errors = []
    
    progress = st.progress(0)
    
    for i, doc_meta in enumerate(documents):
        try:
            doc_id = ingest_single_filing(
                ch_client, doc_store, company_number, doc_meta["transaction_id"]
            )
            success_count += 1
            st.text(f"✅ Ingested: {doc_meta['transaction_id']}")
            
        except Exception as e:
            error_msg = f"Failed to ingest {doc_meta.get('transaction_id', 'unknown')}: {str(e)}"
            errors.append(error_msg)
            st.text(f"❌ {error_msg}")
        
        progress.progress((i + 1) / len(documents))
    
    return success_count, errors


def gemini_cli_tab(gemini_cli: Optional[OfficialGeminiCLI]):
    """Direct Gemini CLI terminal interface."""
    st.header("🤖 Google Gemini CLI - Direct Interface")
    
    # Check Node.js availability
    try:
        node_check = subprocess.run(["node", "--version"], capture_output=True, text=True, timeout=5)
        node_available = node_check.returncode == 0
        node_version = node_check.stdout.strip() if node_available else None
    except:
        node_available = False
        node_version = None
    
    # Status display
    if node_available:
        st.success(f"✅ Node.js {node_version} - Gemini CLI Ready")
    else:
        st.error("❌ Node.js not found - Install Node.js to use Gemini CLI")
        st.code("curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -\nsudo apt-get install -y nodejs")
        return

    # Direct CLI Interface
    st.subheader("💻 Direct Gemini CLI Terminal")
    
    # Main command interface
    with st.form("direct_gemini_form"):
        st.markdown("**💬 Chat with Gemini CLI directly:**")
        
        user_input = st.text_area(
            "Your message:",
            height=120,
            placeholder="Type your question or command here...\nExample: 'Analyze this codebase and suggest improvements'",
            help="Direct input to Google's native Gemini CLI"
        )
        
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            run_direct = st.form_submit_button("🚀 Send to Gemini", type="primary")
        with col2:
            show_help = st.form_submit_button("❓ Show Help")
        with col3:
            st.markdown("*Direct connection to native CLI*")
    
    # Execute direct command
    if run_direct and user_input:
        with st.spinner("🤖 Connecting to Gemini CLI..."):
            try:
                # Run the official Gemini CLI directly
                cmd = ["npx", "--yes", "https://github.com/google-gemini/gemini-cli"]
                
                process = subprocess.run(
                    cmd,
                    input=user_input,
                    text=True,
                    capture_output=True,
                    timeout=60,
                    cwd=os.getcwd()
                )
                
                st.subheader("📟 Gemini CLI Output")
                
                if process.returncode == 0:
                    if process.stdout:
                        st.code(process.stdout, language="text")
                    else:
                        st.info("Command executed successfully (no output)")
                else:
                    st.error("❌ Gemini CLI Error:")
                    if process.stderr:
                        st.code(process.stderr, language="text")
                    else:
                        st.text("Unknown error occurred")
                
                # Save to history
                if "direct_gemini_history" not in st.session_state:
                    st.session_state.direct_gemini_history = []
                
                st.session_state.direct_gemini_history.append({
                    "input": user_input,
                    "output": process.stdout or process.stderr or "No output",
                    "success": process.returncode == 0,
                    "timestamp": datetime.now().strftime("%H:%M:%S")
                })
                
            except subprocess.TimeoutExpired:
                st.error("⏱️ Command timed out after 60 seconds")
            except Exception as e:
                st.error(f"❌ Error: {e}")
    
    # Show help
    if show_help:
        with st.spinner("Getting Gemini CLI help..."):
            try:
                help_cmd = ["npx", "--yes", "https://github.com/google-gemini/gemini-cli", "--help"]
                help_result = subprocess.run(help_cmd, capture_output=True, text=True, timeout=15)
                
                st.subheader("📖 Gemini CLI Help")
                if help_result.stdout:
                    st.code(help_result.stdout, language="text")
                else:
                    st.info("Help not available")
            except Exception as e:
                st.error(f"Error getting help: {e}")

    # Quick actions
    st.subheader("⚡ Quick Commands")
    
    quick_commands = {
        "🔍 Analyze Codebase": "Analyze this codebase architecture, identify patterns, and suggest improvements",
        "📚 Generate README": "Generate a comprehensive README.md for this project",
        "🐛 Find Issues": "Review this code for bugs, security issues, and performance problems",
        "🧪 Suggest Tests": "Suggest unit tests for the main components of this codebase",
        "📖 Explain Code": "Explain the overall architecture and how this system works",
        "🔧 Refactor Tips": "Suggest refactoring opportunities to improve code quality"
    }
    
    cols = st.columns(2)
    for i, (button_text, command) in enumerate(quick_commands.items()):
        with cols[i % 2]:
            if st.button(button_text, key=f"quick_{i}"):
                with st.spinner(f"Running: {button_text}"):
                    try:
                        cmd = ["npx", "--yes", "https://github.com/google-gemini/gemini-cli"]
                        result = subprocess.run(
                            cmd, input=command, text=True, capture_output=True, timeout=60, cwd=os.getcwd()
                        )
                        
                        st.subheader(f"📋 {button_text} Result")
                        if result.stdout:
                            st.markdown(result.stdout)
                        elif result.stderr:
                            st.error(result.stderr)
                        else:
                            st.info("No output received")
                            
                    except Exception as e:
                        st.error(f"Error: {e}")

    # Command History
    if "direct_gemini_history" in st.session_state and st.session_state.direct_gemini_history:
        st.subheader("📜 Recent Commands")
        
        for entry in reversed(st.session_state.direct_gemini_history[-3:]):
            status_icon = "✅" if entry["success"] else "❌"
            with st.expander(f"{status_icon} {entry['timestamp']}: {entry['input'][:40]}..."):
                st.markdown(f"**Input:** {entry['input']}")
                st.markdown(f"**Output:**")
                st.code(entry['output'], language="text")

    # Tips
    with st.expander("💡 Usage Tips"):
        st.markdown("""
        **🎯 Effective Commands:**
        - Be specific about what you want analyzed
        - Ask for concrete suggestions and improvements
        - Request explanations of complex code sections
        
        **🚀 Advanced Usage:**
        - "Analyze [filename] and suggest optimizations"
        - "Generate tests for the RAG pipeline functionality"
        - "Review security practices in the authentication code"
        - "Suggest database optimization strategies"
        
        **⚡ This is the real Gemini CLI:**
        - Direct connection to Google's official tool
        - Full repository context awareness
        - No Python wrapper - pure CLI interface
        """)


if __name__ == "__main__":
    main() 