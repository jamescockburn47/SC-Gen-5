#!/bin/bash

# Gemini CLI wrapper for SC Gen 5 repository review
# Usage: ./gemini_review.sh "your question about the repo"

GEMINI_CLI="/home/jcockburn/.local/bin/gemini-cli"

# Load environment variables from .env file
if [ -f ".env" ]; then
    echo "🔧 Loading environment variables from .env file..."
    source .env
else
    echo "⚠️  No .env file found"
fi

# Check if Gemini API key is available
if [ -z "$GEMINI_API_KEY" ] && [ -z "$GOOGLE_API_KEY" ]; then
    echo "❌ Please set your GEMINI_API_KEY or GOOGLE_API_KEY in the .env file"
    echo "Get your API key from: https://makersuite.google.com/app/apikey"
    exit 1
fi

# Use GOOGLE_API_KEY if GEMINI_API_KEY is not set
if [ -z "$GEMINI_API_KEY" ] && [ -n "$GOOGLE_API_KEY" ]; then
    GEMINI_API_KEY="$GOOGLE_API_KEY"
fi

if [ -z "$1" ]; then
    echo "Usage: $0 \"your question about the repository\""
    echo "Examples:"
    echo "  $0 \"Analyze the overall architecture of this legal research system\""
    echo "  $0 \"Review the document processing and OCR implementation\""
    echo "  $0 \"What are the main components and how do they interact?\""
    exit 1
fi

# Get repository context
REPO_CONTEXT="Repository: Strategic Counsel Gen 5 - Legal Research Assistant
URL: https://github.com/user/sc-gen-5 (local development environment)

OVERVIEW:
A sophisticated legal research system combining local-first architecture with advanced RAG pipeline, document intelligence, and multi-modal LLM support.

CORE ARCHITECTURE:
- Local-first design with Ollama integration (mixtral, mistral, phi3, lawma)
- Cloud LLM support (OpenAI GPT-4o, Google Gemini, Anthropic Claude) 
- Advanced RAG pipeline with BGE-base-en-v1.5 embeddings + FAISS
- Smart OCR system (Tesseract/PaddleOCR) with quality assessment
- Companies House API integration for UK corporate filings
- Dual interface: Streamlit dashboard + FastAPI JSON APIs

KEY COMPONENTS:
$(find src/ -name "*.py" | sort)

SERVICES:
- Consult Service (port 8000): RAG queries and legal analysis
- Ingest Service (port 8001): Document processing and CH integration  
- Streamlit UI (port 8501): Interactive dashboard

RECENT TECHNICAL IMPROVEMENTS:
- Smart PDF text extraction (direct vs OCR based on quality assessment)
- Hallucination prevention through content quality validation
- Dual query modes: standalone legal advice vs RAG-based document analysis
- Enhanced legal protocols with specialized prompts for contracts, litigation, regulatory

CURRENT STATUS:
- System running with all services active
- Document processing improved with quality thresholds
- Environment configured with API keys for all providers
- Ready for production legal research workflows"

echo "🤖 Analyzing with Gemini..."
echo "📋 Question: $1"
echo ""

# Create a temporary config to specify the correct model
TEMP_CONFIG=$(mktemp)
cat > "$TEMP_CONFIG" <<EOF
[model]
name = "gemini-1.5-flash"

[generation_config]
temperature = 0.7
max_output_tokens = 8192
EOF

$GEMINI_CLI -t "$GEMINI_API_KEY" --markdown --stream -f "$TEMP_CONFIG" -c "$REPO_CONTEXT" "$1"

# Clean up
rm -f "$TEMP_CONFIG" 