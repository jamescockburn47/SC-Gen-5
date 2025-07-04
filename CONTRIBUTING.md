# Contributing to Strategic Counsel Gen 5

We appreciate your interest in contributing to SC Gen 5! This document provides guidelines and instructions for contributing to the project.

## 🚀 **Getting Started**

### **Prerequisites**
- Python 3.11+
- Node.js 18+
- Git
- Basic understanding of React, TypeScript, and Python

### **Development Setup**

1. **Fork and Clone**
   ```bash
   git clone https://github.com/YOUR_USERNAME/SC-Gen-5.git
   cd SC-Gen-5
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   cd frontend && npm install
   cd ../terminal-server && npm install
   cd ..
   ```

4. **Run Development Environment**
   ```bash
   python desktop_launcher.py
   ```

## 📋 **How to Contribute**

### **Reporting Issues**

1. **Search Existing Issues**: Check if the issue already exists
2. **Use Issue Templates**: Follow the provided templates
3. **Provide Details**: Include:
   - Clear description of the problem
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Python version, etc.)
   - Screenshots if applicable

### **Feature Requests**

1. **Check Roadmap**: Review our [roadmap](README.md#roadmap) first
2. **Create Feature Request**: Use the feature request template
3. **Provide Context**: Explain:
   - The problem you're trying to solve
   - Proposed solution
   - Alternative solutions considered
   - Implementation suggestions

### **Pull Requests**

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```

2. **Make Your Changes**
   - Follow coding standards (see below)
   - Add/update tests
   - Update documentation if needed

3. **Test Your Changes**
   ```bash
   # Run Python tests
   python -m pytest tests/
   
   # Run Frontend tests
   cd frontend && npm test
   
   # Test the launcher
   python desktop_launcher.py --test
   ```

4. **Commit Your Changes**
   ```bash
   git commit -m "feat: Add amazing feature
   
   - Implement feature X
   - Add tests for feature X
   - Update documentation"
   ```

5. **Push and Create PR**
   ```bash
   git push origin feature/amazing-feature
   ```

## 🎨 **Coding Standards**

### **Python Code Style**

We follow PEP 8 with some modifications:

```python
# Use type hints
def process_document(file_path: str, options: Dict[str, Any]) -> ProcessResult:
    """Process a document with OCR and analysis.
    
    Args:
        file_path: Path to the document file
        options: Processing options
        
    Returns:
        ProcessResult with extracted text and metadata
    """
    pass

# Use descriptive names
user_query = "What are the main legal risks?"
consultation_result = await rag_pipeline.process_query(user_query)

# Class naming
class DocumentProcessor:
    def __init__(self, config: ProcessorConfig) -> None:
        self.config = config
```

**Tools:**
- **Formatter**: `black` (line length: 88)
- **Linter**: `ruff`
- **Type Checker**: `mypy`

```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Type checking
mypy src/
```

### **TypeScript/React Code Style**

```typescript
// Use functional components with hooks
const DocumentsPage: React.FC = () => {
  const [documents, setDocuments] = useState<Document[]>([]);
  
  const handleFileUpload = useCallback(
    async (files: File[]) => {
      // Implementation
    },
    []
  );

  return (
    <Box sx={{ p: 3 }}>
      {/* JSX content */}
    </Box>
  );
};

// Use descriptive prop interfaces
interface ConsultationProps {
  sessionId: string;
  onSessionUpdate: (session: Session) => void;
  modelPreference: 'local' | 'cloud' | 'auto';
}
```

**Tools:**
- **Formatter**: Prettier
- **Linter**: ESLint
- **Type Checker**: TypeScript

```bash
cd frontend
npm run lint
npm run format
npm run type-check
```

### **File Structure**

```
src/sc_gen5/
├── core/              # Core business logic
├── integrations/      # External service integrations
├── services/          # FastAPI services
└── ui/               # UI components (legacy)

frontend/src/
├── components/       # Reusable React components
├── pages/           # Application pages
├── hooks/           # Custom React hooks
├── utils/           # Utility functions
└── types/           # TypeScript type definitions
```

## 🧪 **Testing Guidelines**

### **Python Tests**

```python
import pytest
from sc_gen5.core.doc_store import DocumentStore

class TestDocumentStore:
    def test_add_document_success(self):
        """Test successful document addition."""
        store = DocumentStore()
        result = store.add_document("test.pdf", b"content")
        assert result.success
        assert result.document_id is not None

    @pytest.mark.asyncio
    async def test_search_documents(self):
        """Test document search functionality."""
        # Test implementation
        pass
```

### **React Tests**

```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { DocumentsPage } from '../pages/DocumentsPage';

describe('DocumentsPage', () => {
  it('renders upload area', () => {
    render(<DocumentsPage />);
    expect(screen.getByText(/drag.*drop/i)).toBeInTheDocument();
  });

  it('handles file upload', async () => {
    render(<DocumentsPage />);
    const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });
    // Test file upload logic
  });
});
```

### **Test Coverage**

Aim for:
- **Core modules**: 90%+ coverage
- **Services**: 85%+ coverage
- **UI components**: 70%+ coverage

```bash
# Generate coverage report
pytest --cov=src/sc_gen5 --cov-report=html
```

## 📚 **Documentation**

### **Code Documentation**

- **Python**: Use Google-style docstrings
- **TypeScript**: Use TSDoc comments
- **README updates**: Update relevant sections when adding features

### **API Documentation**

FastAPI automatically generates OpenAPI docs, but ensure:
- Clear endpoint descriptions
- Example request/response payloads
- Error code documentation

## 🏗️ **Architecture Guidelines**

### **Adding New Features**

1. **Backend Services**: Add to `src/sc_gen5/services/`
2. **Frontend Pages**: Add to `frontend/src/pages/`
3. **Launcher Features**: Extend `desktop_launcher.py`
4. **Integrations**: Add to `src/sc_gen5/integrations/`

### **Database Changes**

- Vector store changes: Update `core/vector_store.py`
- Metadata changes: Update `core/doc_store.py`
- Migration scripts: Add to `migrations/`

### **UI Components**

Follow Material-UI patterns:
```typescript
// Use consistent theming
const theme = useTheme();

// Consistent spacing
<Box sx={{ p: 2, mb: 3 }}>

// Responsive design
<Grid container spacing={2}>
  <Grid item xs={12} md={6}>
```

## 🔄 **Workflow**

### **Branch Naming**
- `feature/add-new-page` - New features
- `fix/upload-bug` - Bug fixes
- `docs/update-readme` - Documentation
- `refactor/cleanup-code` - Code refactoring

### **Commit Messages**

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add export functionality to consultation page

- Add JSON export for consultation sessions
- Include document sources in export
- Add progress indicator for large exports

Closes #123
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test additions/changes
- `chore`: Maintenance tasks

### **Code Review Process**

1. **Self Review**: Review your own PR first
2. **Automated Checks**: Ensure all CI checks pass
3. **Manual Review**: Address reviewer feedback
4. **Final Testing**: Test the feature end-to-end

## 🎯 **Areas for Contribution**

### **High Priority**
- [ ] Mobile responsive design improvements
- [ ] Performance optimizations
- [ ] Accessibility enhancements
- [ ] Additional OCR improvements
- [ ] Advanced analytics features

### **Good First Issues**
- [ ] UI component improvements
- [ ] Documentation updates
- [ ] Test coverage improvements
- [ ] Code cleanup and refactoring

### **Advanced Features**
- [ ] Plugin system development
- [ ] Multi-user authentication
- [ ] Cloud deployment scripts
- [ ] Advanced AI model integrations

## 📞 **Getting Help**

- **GitHub Discussions**: General questions and ideas
- **GitHub Issues**: Bug reports and feature requests
- **Code Comments**: Inline documentation questions

## 🙏 **Recognition**

Contributors will be:
- Listed in the README contributors section
- Tagged in release notes
- Invited to project discussions

## 📄 **License**

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).

---

**Thank you for contributing to Strategic Counsel Gen 5!** 🚀 