# RAG v2 Upgrade - Multi-Granularity Pipeline

## Overview

SC Gen 5 has been upgraded with a new RAG v2 engine featuring multi-granularity retrieval and local model optimization for Legion 5 Pro hardware.

## Key Features

### Multi-Granularity Retrieval
- **Chapter Level**: Large context chunks (2048 tokens) for broad understanding
- **Quote Level**: Medium chunks (512 tokens) for specific references  
- **Detail Level**: Small chunks (256 tokens) for precise facts

### Local Model Support
- **Phi-3-mini-4k-instruct**: Fast, efficient model for quick responses
- **Mistral-7B-Instruct**: Higher quality model for complex analysis
- **Auto-GPTQ Quantization**: 4-bit quantization for memory efficiency

### Hardware Optimization
- **Legion 5 Pro Optimized**: 8GB RTX GPU + 64GB RAM configuration
- **Dynamic Batch Sizing**: Automatic adjustment based on available resources
- **Memory Management**: GPU cache clearing and memory monitoring
- **Performance Benchmarking**: Real-time inference speed testing

## Architecture

```
Frontend (React)     Backend (FastAPI)         RAG Pipeline v2
     |                       |                        |
RAGv2Page.tsx ---------> /api/rag-v2/* ---------> rag_pipeline_v2.py
     |                       |                        |
Status Monitoring           Hardware Stats      hardware_v2.py
Query Interface             Endpoints           Multi-granularity
Performance Tools           Benchmarking        Local Models
```

## New Dependencies

The following packages have been added to `requirements.txt`:

```python
# RAG v2 Advanced Dependencies
langchain>=0.2.4          # LangChain v0.2 with LCEL
langgraph>=0.0.30         # Advanced workflow management
auto-gptq>=0.7.0          # Model quantization
torch==2.2.1              # PyTorch for Legion 5 Pro
accelerate>=0.21.0        # Model loading acceleration
transformers>=4.36.0      # HuggingFace transformers
bitsandbytes>=0.41.0      # Quantization support
ragas==0.0.20             # RAG evaluation metrics
pypdf==4.2.0              # Enhanced PDF processing
optimum>=1.13.0           # Model optimization
sentencepiece>=0.1.99     # Tokenization support
safetensors>=0.3.1        # Safe model storage
```

## API Endpoints

### Core Endpoints
- `GET /api/rag-v2/status` - Get pipeline and hardware status
- `POST /api/rag-v2/initialize` - Initialize RAG v2 pipeline
- `POST /api/rag-v2/query` - Query using multi-granularity retrieval
- `POST /api/rag-v2/process-documents` - Process documents for RAG

### Management Endpoints
- `POST /api/rag-v2/load-vector-stores` - Load existing vector stores
- `GET /api/rag-v2/hardware/clear-cache` - Clear GPU memory cache
- `POST /api/rag-v2/benchmark` - Benchmark model performance

## Hardware Configuration

### Automatic Optimization
The system automatically detects and optimizes for Legion 5 Pro:

```python
@dataclass
class HardwareConfig:
    max_gpu_memory: int = 8192  # 8GB VRAM
    max_ram: int = 65536        # 64GB RAM
    cpu_cores: int = 16         # Typical Legion 5 Pro
    batch_size_small: int = 4   # Phi-3-mini batch size
    batch_size_medium: int = 8  # Mistral-7B batch size
    context_length: int = 4096  # Maximum context window
```

### Dynamic Resource Management
- **Memory Monitoring**: Real-time CPU, RAM, and GPU usage tracking
- **Batch Size Optimization**: Automatic adjustment based on available memory
- **Model Loading**: Smart model selection based on resource availability
- **Cache Management**: Automatic GPU cache clearing when needed

## Usage Examples

### Initialize Pipeline
```typescript
// Initialize RAG v2 pipeline
const response = await axios.post('/api/rag-v2/initialize');
```

### Query with Multi-Granularity
```typescript
// Query using small model (Phi-3-mini)
const result = await axios.post('/api/rag-v2/query', {
  question: "What are the key principles of contract law?",
  use_medium_model: false
});

// Query using medium model (Mistral-7B)
const result = await axios.post('/api/rag-v2/query', {
  question: "Analyze the implications of this complex legal precedent...",
  use_medium_model: true
});
```

### Process Documents
```typescript
// Process legal documents for multi-granularity retrieval
const result = await axios.post('/api/rag-v2/process-documents', {
  documents: [
    {
      id: "doc1",
      title: "Contract Law Principles",
      content: "Legal document text...",
      type: "legal_text"
    }
  ]
});
```

## Frontend Interface

### RAG v2 Page Features
1. **System Status Tab**
   - Pipeline initialization status
   - Model loading indicators
   - Vector store statistics
   - Hardware resource monitoring
   - Real-time warning alerts

2. **Query Interface Tab**
   - Multi-line legal question input
   - Model selection (Phi-3-mini vs Mistral-7B)
   - Real-time query processing
   - Detailed result display with metadata

3. **Performance Tab**
   - Benchmark testing tools
   - Inference speed measurement
   - Memory usage tracking
   - Hardware optimization recommendations

## Performance Characteristics

### Expected Performance (Legion 5 Pro)
- **Phi-3-mini**: ~15-25 tokens/second, ~1-2GB VRAM
- **Mistral-7B**: ~8-15 tokens/second, ~4-6GB VRAM (quantized)
- **Retrieval**: <500ms for multi-granularity search
- **End-to-end**: 2-8 seconds depending on model and complexity

### Optimization Features
- **Flash Attention**: Improved memory efficiency for Phi-3
- **Sliding Window**: Context optimization for Mistral
- **4-bit Quantization**: Memory usage reduction for large models
- **Dynamic Batching**: Automatic batch size adjustment

## Troubleshooting

### Common Issues

1. **GPU Not Detected**
   - Ensure CUDA drivers are installed
   - Check `nvidia-smi` output
   - Verify PyTorch CUDA installation

2. **Out of Memory Errors**
   - Use GPU cache clearing endpoint
   - Switch to smaller model (Phi-3-mini)
   - Reduce batch size in configuration

3. **Slow Performance**
   - Check system resource usage
   - Clear GPU cache regularly
   - Use benchmark tool to identify bottlenecks

### Monitoring and Debugging

The system provides comprehensive monitoring:
- Real-time resource usage tracking
- Performance benchmarking tools
- Warning alerts for resource constraints
- Detailed error logging and reporting

## Migration from RAG v1

RAG v2 runs alongside the existing RAG pipeline:
- Original `/api/consultations/query` endpoints remain unchanged
- New `/api/rag-v2/*` endpoints provide enhanced functionality
- No breaking changes to existing functionality
- Gradual migration path available

## Future Enhancements

Planned improvements for RAG v2:
- **Citation Tracking**: Enhanced source attribution
- **Legal Domain Models**: Specialized legal language models
- **Multi-Document Analysis**: Cross-document relationship detection
- **Continuous Learning**: User feedback integration
- **Advanced Quantization**: INT8 and FP8 optimization

---

*RAG v2 Engine - Powered by Legion 5 Pro • 8GB VRAM • 64GB RAM • CUDA*