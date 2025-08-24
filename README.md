# 🏛️ Strategic Counsel Gen 5

**Advanced Legal Research Assistant with Desktop Integration**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![React](https://img.shields.io/badge/React-19.1+-61DAFB.svg)](https://reactjs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-4.9+-blue.svg)](https://typescriptlang.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> A sophisticated legal research platform combining local AI models, document processing, Companies House integration, and advanced desktop launcher capabilities.

![SC Gen 5 Dashboard](https://via.placeholder.com/800x400/1976d2/ffffff?text=SC+Gen+5+Dashboard)

## ✨ **Key Features**

### 🖥️ **Enhanced Desktop Launcher**
- **System Tray Integration**: Native system tray with quick actions
- **Auto-start on Boot**: Seamless system startup integration
- **Cross-platform Support**: Windows and Linux compatibility
- **Process Management**: Advanced health monitoring and auto-restart
- **Desktop Shortcuts**: Automatic shortcut creation

### 🎨 **Modern React Frontend**
- **Document Manager**: Drag & drop upload with OCR processing
- **Legal Consultation**: AI-powered chat with session management
- **Companies House**: UK company research with bulk operations
- **Analytics Dashboard**: Real-time system monitoring and insights
- **Responsive Design**: Material-UI with professional legal theme

### 🤖 **AI-Powered Legal Research**
- **Local-First**: Mixtral and other local LLM support
- **Cloud Integration**: OpenAI and Gemini model support
- **RAG Pipeline**: Advanced document retrieval and analysis
- **OCR Processing**: Enhanced image preprocessing with deskewing
- **Vector Search**: Semantic document search capabilities

### 🏢 **Companies House Integration**
- **Company Search**: Search by name or officer
- **Bulk Downloads**: Mass filing retrieval with progress tracking
- **Document Processing**: Automatic OCR and indexing
- **API Integration**: Full Companies House API support

### 📊 **System Analytics**
- **Real-time Monitoring**: CPU, memory, disk, GPU metrics
- **Performance Trends**: Historical data visualization
- **Service Health**: Individual service status monitoring
- **Usage Statistics**: Document, consultation, and API tracking
- **Intelligent Alerts**: System health recommendations

## 🚀 **Quick Start**

### **Prerequisites**
- Python 3.11+
- Node.js 18+
- npm 9+
- Git

### **Installation**

```bash
# Clone the repository
git clone https://github.com/jamescockburn47/SC-Gen-5.git
cd SC-Gen-5

# Install Python dependencies
pip install -r requirements.txt
# Install in editable mode for development and testing
pip install -e .[dev]

# Install frontend dependencies
cd frontend
npm install
cd ..

# Install terminal server dependencies
cd terminal-server
npm install
cd ..
```

### **Launch Options**

```bash
# Linux/WSL
./start_sc_gen5.sh start      # start backend & frontend
./start_sc_gen5.sh stop       # stop services
./start_sc_gen5.sh restart    # restart services
```

Windows users can double-click `SC_Gen5_Launcher.bat` to start the app and `Stop_SC_Gen5.bat` to stop it.

### **Access Points**
- **Web Interface**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **System Tray**: Right-click for quick actions

## 🏗️ **Architecture**

```
┌─────────────────────────────────────────────────────────────┐
│                    Desktop Launcher                         │
├─────────────────┬─────────────────┬─────────────────────────┤
│  System Tray    │   GUI Manager   │    Process Monitor      │
├─────────────────┼─────────────────┼─────────────────────────┤
│ • Auto-start    │ • Service       │ • Health checks         │
│ • Notifications │   controls      │ • Auto-restart          │
│ • Quick actions │ • System info   │ • Resource tracking     │
└─────────────────┴─────────────────┴─────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                   React Frontend                           │
├─────────────┬─────────────┬─────────────┬─────────────────┤
│ Documents   │ Consultation│ Companies   │ Analytics       │
│ Manager     │ Assistant   │ House       │ Dashboard       │
├─────────────┼─────────────┼─────────────┼─────────────────┤
│ • Upload    │ • AI Chat   │ • Search    │ • Real-time     │
│ • OCR       │ • Sessions  │ • Profiles  │ • Monitoring    │
│ • Viewer    │ • Export    │ • Bulk ops  │ • Trends        │
└─────────────┴─────────────┴─────────────┴─────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                  Backend Services                          │
├─────────────────┬─────────────────┬─────────────────────────┤
│ FastAPI APIs    │ Terminal Server │ Core Services           │
├─────────────────┼─────────────────┼─────────────────────────┤
│ • Consultation  │ • WebSocket     │ • Document Store        │
│ • Ingestion     │ • Gemini CLI    │ • RAG Pipeline          │
│ • Analytics     │ • xterm.js      │ • Vector Database       │
└─────────────────┴─────────────────┴─────────────────────────┘
```

## 📁 **Project Structure**

```
SC-Gen-5/
├── start_sc_gen5.sh           # Master launch script
├── SC_Gen5_Launcher.bat       # Windows launcher
├── Stop_SC_Gen5.bat           # Windows stop script
├── 
├── frontend/                        # React application
│   ├── src/
│   │   ├── components/              # Reusable components
│   │   │   ├── Dashboard.tsx        # System overview
│   │   │   ├── DocumentsPage.tsx    # Document management
│   │   │   ├── ConsultationPage.tsx # Legal consultation
│   │   │   ├── CompaniesHousePage.tsx # Company research
│   │   │   └── AnalyticsPage.tsx    # System analytics
│   │   └── App.tsx                  # Main application
│   └── package.json                 # Frontend dependencies
│
├── terminal-server/                 # WebSocket terminal bridge
│   ├── server.js                    # Terminal server
│   └── package.json                 # Server dependencies
│
├── src/sc_gen5/                     # Core Python application
│   ├── core/                        # Core modules
│   │   ├── doc_store.py            # Document storage
│   │   ├── rag_pipeline.py         # RAG implementation
│   │   ├── ocr.py                  # Enhanced OCR processing
│   │   └── vector_store.py         # Vector database
│   ├── integrations/               # External integrations
│   │   ├── companies_house.py      # Companies House API
│   │   └── gemini_cli.py           # Gemini CLI integration
│   ├── services/                   # FastAPI services
│   │   ├── consult_service.py      # Consultation API
│   │   └── ch_ingest_service.py    # Ingestion API
│   └── ui/                         # Streamlit UI (legacy)
│       └── app.py                  # Streamlit application
│
├── data/                           # Data storage
│   ├── uploads/                    # Uploaded documents
│   ├── vector_db/                  # Vector database files
│   └── downloads/                  # Downloaded files
│
├── tests/                          # Test suites
├── requirements.txt                # Python dependencies
└── README.md                       # This file
```

## 🔧 **Configuration**

### **Environment Variables**
```bash
# Optional: Companies House API
export COMPANIES_HOUSE_API_KEY="your_api_key_here"

# Optional: OpenAI API
export OPENAI_API_KEY="your_openai_key_here"

# Optional: Google AI API
export GOOGLE_AI_API_KEY="your_google_ai_key_here"
```

### **Launcher Settings**
Configure desktop launcher behavior in `launcher_config.json`:

```json
{
  "auto_start_on_boot": false,
  "minimize_to_tray": true,
  "check_health_interval": 30,
  "browser_auto_open": true,
  "theme": "dark"
}
```

## 🎯 **Use Cases**

### **Legal Professionals**
- **Document Analysis**: Upload contracts, cases, and legal documents for AI analysis
- **Research Assistance**: Natural language queries with source citations
- **Company Due Diligence**: Automated Companies House research and filing analysis
- **Case Management**: Organize documents and consultation sessions

### **Law Firms**
- **Client Consultation**: AI-assisted legal advice with document context
- **Compliance Monitoring**: Track regulatory filings and company changes
- **Knowledge Management**: Centralized document repository with semantic search
- **Performance Analytics**: Monitor system usage and response times

### **Corporate Legal Teams**
- **Contract Review**: Automated analysis of agreements and terms
- **Regulatory Research**: Stay updated on company filings and changes
- **Risk Assessment**: Identify potential legal issues in documents
- **Team Collaboration**: Shared consultation sessions and document access

## 🛠️ **Development**

### **Frontend Development**
```bash
cd frontend
npm start              # Development server
npm run build          # Production build
npm test              # Run tests
```

### **Backend Development**
```bash
# Start individual services
python -m uvicorn sc_gen5.services.consult_service:app --reload --port 8000
python -m uvicorn sc_gen5.services.ch_ingest_service:app --reload --port 8001

# Run tests
python -m pytest tests/
```

### **Adding Features**
1. **Frontend Pages**: Create components in `frontend/src/pages/`
2. **API Endpoints**: Add routes in `src/sc_gen5/services/`
3. **Launcher Features**: Extend `start_sc_gen5.sh`
4. **Monitoring**: Add metrics to `SystemMonitor` class

## 📊 **Performance**

### **System Requirements**
- **Minimum**: 8GB RAM, 4-core CPU, 10GB storage
- **Recommended**: 16GB+ RAM, 8-core CPU, 50GB+ storage, GPU (for local AI)
- **Optimal**: 32GB+ RAM, 16-core CPU, 100GB+ SSD, RTX 4090 (8GB VRAM)

### **Benchmarks**
- **Document Processing**: ~2-5 seconds per PDF (with OCR)
- **AI Response Time**: 1-3 seconds (local), 2-5 seconds (cloud)
- **Companies House Search**: <1 second per query
- **System Startup**: ~30 seconds full stack

## 🔒 **Security**

### **Data Privacy**
- **Local-First**: Documents processed locally by default
- **Encryption**: All data encrypted at rest and in transit
- **No Tracking**: No telemetry or usage tracking
- **Audit Logs**: Comprehensive logging for compliance

### **API Security**
- **Authentication**: JWT-based API authentication
- **Rate Limiting**: Configurable request rate limits
- **CORS**: Proper cross-origin resource sharing
- **Input Validation**: Comprehensive input sanitization

## 📈 **Roadmap**

### **Phase 1: Core Enhancement** ✅
- [x] Enhanced desktop launcher
- [x] Complete React frontend
- [x] Advanced OCR processing
- [x] System monitoring
- [x] Companies House integration

### **Phase 2: Advanced Features** 🚧
- [ ] Mobile responsive design
- [ ] Multi-user support
- [ ] Plugin system
- [ ] Advanced analytics
- [ ] Cloud deployment options

### **Phase 3: Enterprise Features** 📋
- [ ] Kubernetes deployment
- [ ] Multi-tenant architecture
- [ ] Advanced security features
- [ ] API gateway integration
- [ ] Compliance reporting

## 🤝 **Contributing**

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### **Development Setup**
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 **Acknowledgments**

- **Ollama** for local LLM infrastructure
- **Companies House** for providing comprehensive business data API
- **Google Gemini** for advanced AI capabilities
- **Material-UI** for beautiful React components
- **FastAPI** for high-performance API framework

## 📞 **Support**

- **Documentation**: [Full Documentation](docs/)
- **Issues**: [GitHub Issues](https://github.com/jamescockburn47/SC-Gen-5/issues)
- **Discussions**: [GitHub Discussions](https://github.com/jamescockburn47/SC-Gen-5/discussions)

---

**⚖️ Built for legal professionals who demand precision, privacy, and performance.** 🏛️

![Footer](https://via.placeholder.com/800x100/2e7d32/ffffff?text=Strategic+Counsel+Gen+5+-+Advanced+Legal+Research+Assistant) 