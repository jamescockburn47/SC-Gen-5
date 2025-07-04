# Strategic Counsel Gen 5 Environment Setup

## Quick Setup

Create a `.env` file in the project root directory with your API keys:

```bash
# Copy and paste this into a new file called .env
# Replace the placeholder values with your actual API keys

# Companies House API (for UK company data)
CH_API_KEY=your_companies_house_api_key_here

# Google AI Studio (for Gemini models - easiest option)
GOOGLE_API_KEY=your_google_ai_studio_api_key_here

# OpenAI (for GPT models)
OPENAI_API_KEY=your_openai_api_key_here

# Anthropic (for Claude models)
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

## Getting API Keys

### 🏢 Companies House API
1. Visit [Companies House Developer Hub](https://developer.company-information.service.gov.uk/)
2. Register for a free account
3. Create an application to get your API key
4. Add to `.env`: `CH_API_KEY=your_key_here`

### 🤖 Google AI Studio (Recommended for Gemini)
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Create a new API key
4. Add to `.env`: `GOOGLE_API_KEY=your_key_here`

### 🔮 OpenAI (for GPT models)
1. Visit [OpenAI API Keys](https://platform.openai.com/api-keys)
2. Sign in and create a new API key
3. Add to `.env`: `OPENAI_API_KEY=your_key_here`

### 🧠 Anthropic (for Claude models)
1. Visit [Anthropic Console](https://console.anthropic.com/)
2. Sign up and get your API key
3. Add to `.env`: `ANTHROPIC_API_KEY=your_key_here`

## Advanced Configuration

You can also customize these settings in your `.env` file:

```bash
# Data storage
SC_DATA_DIR=./data
SC_VECTOR_DB_PATH=./data/vector_db
SC_CHUNK_SIZE=400
SC_CHUNK_OVERLAP=80

# RAG settings
SC_RETRIEVAL_K=18
SC_RERANK_TOP_K=6
SC_USE_RERANKER=false

# Embedding model
SC_EMBEDDING_MODEL=BAAI/bge-base-en-v1.5

# Local LLM
OLLAMA_HOST=http://localhost:11434
```

## What Works Without API Keys

Even without any API keys, SC Gen 5 provides:

- ✅ **Local LLM support** (via Ollama - mixtral, mistral, phi3, lawma)
- ✅ **Document upload and processing** (PDF/image OCR)
- ✅ **RAG pipeline** (vector search in your documents)
- ✅ **Official Gemini CLI** (repository analysis and chat)

## Priority Setup

**For basic legal research:**
1. `GOOGLE_API_KEY` - Easiest cloud LLM setup
2. Local Ollama models (already working)

**For UK company research:**
3. `CH_API_KEY` - Companies House integration

**For maximum model choice:**
4. `OPENAI_API_KEY` and `ANTHROPIC_API_KEY`

## Verification

After setting up your `.env` file:

1. Restart the SC Gen 5 services: `python3 run_services.py`
2. Check the sidebar in the UI for green status indicators
3. Test cloud models in the "💬 Legal Consultation" tab 