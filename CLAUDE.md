# CLAUDE.md - Strategic Counsel Gen 5

## Project Context
This is a sophisticated legal research platform with desktop integration, React frontend, and FastAPI backend. The system combines local AI models, document processing, Companies House integration, and system monitoring capabilities.

## 🚀 Quick Start (Updated Workflow)

### Start All Services
```bash
# Navigate to project directory
cd "SC Gen 5"

# Start both backend and frontend services
python3 run_services.py
```

This will start:
- ✅ **FastAPI Backend** on `http://localhost:8000`
- ✅ **React Frontend** on `http://localhost:3000`
- ✅ **API Documentation** on `http://localhost:8000/docs`
- ✅ **Mistral-7B Model** with GPU optimization
- ✅ **Auto-GPTQ Support** for optimal performance

### Test the Setup
After starting services, test these URLs:
1. **Backend Health**: `http://localhost:8000/`
2. **Frontend**: `http://localhost:3000`
3. **API Docs**: `http://localhost:8000/docs`

## Key Development Commands

### Frontend Development
```bash
cd frontend
npm start              # Start development server (port 3000)
npm run build          # Build for production
npm test              # Run tests
npm run lint          # Run ESLint (if configured)
```

### Backend Development
```bash
# Start main FastAPI backend with RAG v2
python3 app.py

# Start with uvicorn directly
python3 -m uvicorn app:app --reload --host 0.0.0.0 --port 8000

# Start Companies House ingestion service
python -m uvicorn sc_gen5.services.ch_ingest_service:app --reload --port 8001

# Start terminal server
cd terminal-server
npm start              # Start WebSocket terminal server
```

### Full Stack Launch
```bash
# Start all services together (RECOMMENDED)
python3 run_services.py

# Enhanced desktop launcher
python desktop_launcher.py

# Start minimized to system tray
python desktop_launcher.py --minimized

# Original sophisticated UI launcher
python start_sophisticated_ui.py
```

### Testing
```bash
# Run Python tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=src/sc_gen5 --cov-report=html

# Run specific test file
python -m pytest tests/test_integration.py -v
```

### Code Quality
```bash
# Format code with black
black src/ tests/ --line-length 119

# Lint with ruff
ruff check src/ tests/

# Type checking with mypy
mypy src/sc_gen5/
```

### Environment Setup
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install with development dependencies
pip install -e ".[dev]"

# Install enhanced OCR capabilities
pip install -e ".[enhanced]"
```

## Important File Locations

### Configuration
- `settings.py` - Main application settings and model configurations
- `launcher_config.json` - Desktop launcher settings
- `pyproject.toml` - Python project configuration
- `frontend/package.json` - Frontend dependencies and scripts

### Key Source Files
- `app.py` - Main FastAPI application with RAG v2 integration
- `src/sc_gen5/rag/v2/` - RAG v2 implementation with multi-granularity
- `src/sc_gen5/rag/v2/models.py` - Model management with GPU optimization
- `src/sc_gen5/rag/v2/router.py` - RAG v2 API endpoints
- `src/sc_gen5/services/consult_service.py` - Legacy consultation API
- `src/sc_gen5/services/ch_ingest_service.py` - Companies House ingestion
- `frontend/src/App.tsx` - Main React application
- `desktop_launcher.py` - Enhanced desktop launcher

### Data Directories
- `data/uploads/` - Uploaded documents
- `data/vector_db/` - Vector database files
- `data/downloads/companies_house/` - Companies House data

## Common Development Workflows

### Adding New Features
1. Create feature branch: `git checkout -b feature/new-feature`
2. Implement backend changes in `src/sc_gen5/`
3. Add corresponding frontend components in `frontend/src/`
4. Write tests in `tests/`
5. Run quality checks: `ruff check`, `black`, `mypy`
6. Test full stack: `python3 run_services.py`

### Model Configuration
- **Utility Model**: TinyLlama-1.1B (for filtering/rewriting)
- **Reasoning Model**: Mistral-7B-GPTQ (quantized for 8GB VRAM)
- **Embedding Model**: BAAI/bge-small-en-v1.5
- **GPU Optimization**: Auto-GPTQ with CUDA 11.8 support

### Document Processing Pipeline
- Upload → OCR Processing → Vector Embedding → Storage
- Files processed through RAG v2 pipeline in `src/sc_gen5/rag/v2/`
- Multi-granularity processing with chunking and overlap
- GPU-optimized embedding with Mistral-7B reasoning

### Companies House Integration
- API wrapper in `src/sc_gen5/integrations/companies_house.py`
- Ingestion service at `src/sc_gen5/services/ch_ingest_service.py`
- Frontend integration in `frontend/src/pages/CompaniesHousePage.tsx`

## Environment Variables
```bash
# Optional APIs
export COMPANIES_HOUSE_API_KEY="your_api_key_here"
export OPENAI_API_KEY="your_openai_key_here"
export GOOGLE_AI_API_KEY="your_google_ai_key_here"
```

## Quick Access URLs
- Web Interface: http://localhost:3000
- API Documentation: http://localhost:8000/docs
- Companies House Service: http://localhost:8001/docs

## Troubleshooting

### Common Issues
- **Port conflicts**: Check if services are already running
- **Frontend build errors**: Delete `node_modules` and `npm install`
- **Python import errors**: Ensure virtual environment is activated
- **OCR issues**: Check tesseract installation
- **GPU OOM errors**: Models configured for 8GB VRAM, check GPU memory
- **Frontend crash loop**: Fixed proxy configuration in `frontend/package.json`

### Logs
- Frontend: `frontend/frontend.log`
- Backend: `backend.log`
- Launcher: `launcher.log`

## Development Notes
- Python 3.11+ required
- Node.js 18+ required
- Uses Material-UI for React components
- FastAPI for backend services with RAG v2
- Vector search with FAISS
- OCR with tesseract/paddleOCR
- Desktop integration with tkinter
- **GPU Requirements**: 8GB+ VRAM for optimal performance
- **Model Architecture**: Quantized Mistral-7B with Auto-GPTQ
- **Frontend**: Fixed proxy configuration for localhost:8000