# Optional Utility Model Feature

## Overview

The utility model in the RAG system is now **optional** and can be enabled/disabled based on your specific needs and performance requirements.

## What is the Utility Model?

The utility model (TinyLlama-1.1B) is a small, fast language model that performs **chunk relevance analysis** in the RAG pipeline:

- **Purpose**: Scores how relevant each retrieved document chunk is to the user's question
- **Function**: Filters chunks before passing them to the main generation model (Mistral-7B)
- **Size**: ~1.1B parameters (much smaller than the 7B generation model)
- **Speed**: Fast inference for quick chunk filtering

## When to Use the Utility Model

### ✅ **Enable Utility Model When:**
- You have **many retrieved chunks** (dozens or hundreds) and need to filter aggressively
- You want to **optimize for speed/cost** and are willing to risk missing some edge-case content
- You're **hitting context/token limits** and need to reduce chunks passed to the main LLM
- You want to **scale to many users** and need to optimize resource usage

### ❌ **Disable Utility Model When:**
- You want **maximum recall** and are not hitting context limits
- You have **already tuned retrieval** (good embeddings, chunking, etc.)
- You want to **simplify the stack** and reduce complexity
- Your main bottleneck is **not chunk count** but LLM reasoning or prompt design

## Configuration

### Settings File (`settings.py`)

```python
# Utility model configuration
ENABLE_UTILITY_MODEL: bool = True  # Set to False to disable
UTILITY_MODEL_THRESHOLD: float = 0.3  # Minimum relevance score (0.0-1.0)
```

### Environment Variables

```bash
# Disable utility model
export ENABLE_UTILITY_MODEL=false

# Adjust threshold
export UTILITY_MODEL_THRESHOLD=0.5
```

### Frontend Configuration

1. Go to **Legal Research** → **System Management** tab
2. Find the **Utility Model Configuration** section
3. Toggle **Enable Utility Model** on/off
4. Adjust **Relevance Threshold** (0.0-1.0)
5. Click **Update Configuration**

## API Endpoints

### Get Current Configuration
```bash
GET /api/rag/utility-config
```

Response:
```json
{
  "enabled": true,
  "threshold": 0.3,
  "model_name": "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
}
```

### Update Configuration
```bash
POST /api/rag/utility-config
Content-Type: application/json

{
  "enabled": false,
  "threshold": 0.5,
  "model_name": "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
}
```

## Performance Impact

### With Utility Model Enabled:
- **Memory**: +~2GB RAM for utility model
- **Speed**: Faster chunk filtering, slower startup
- **Quality**: More focused chunks to main LLM
- **Recall**: May miss some relevant but low-scoring chunks

### With Utility Model Disabled:
- **Memory**: -~2GB RAM (utility model not loaded)
- **Speed**: Slower chunk processing, faster startup
- **Quality**: All retrieved chunks passed to main LLM
- **Recall**: Maximum recall, no chunk filtering

## Implementation Details

### Model Loading
- **Enabled**: Loads embedder + utility model at startup
- **Disabled**: Loads only embedder at startup

### Relevance Analysis
- **Enabled**: Uses utility model to score chunks (0.0-1.0)
- **Disabled**: Returns all chunks with score 1.0 (no filtering)

### Fallback Behavior
- If utility model fails to load, system falls back to no filtering
- If utility model is disabled, relevance analyzer returns all chunks

## Testing

Run the test script to verify functionality:

```bash
python3 test_optional_utility.py
```

This tests:
- ✅ Enabling/disabling utility model
- ✅ Progressive loading behavior
- ✅ Relevance analysis with/without utility model
- ✅ Memory usage optimization
- ✅ API configuration endpoints

## Best Practices

### For Legal Research:
1. **Start with utility model enabled** (default)
2. **Monitor chunk counts** in responses
3. **If hitting context limits**: Lower threshold or enable utility model
4. **If missing relevant info**: Disable utility model or raise threshold
5. **For maximum recall**: Disable utility model

### For Production:
1. **Test both configurations** with your specific documents
2. **Monitor performance metrics** (response time, memory usage)
3. **Adjust threshold** based on document characteristics
4. **Consider user feedback** on answer quality

## Troubleshooting

### Utility Model Won't Load
- Check `ENABLE_UTILITY_MODEL` setting
- Verify model file exists
- Check available memory
- Review error logs

### Poor Relevance Scores
- Adjust `UTILITY_MODEL_THRESHOLD`
- Check chunk quality and size
- Consider disabling utility model

### High Memory Usage
- Disable utility model to save ~2GB RAM
- Monitor GPU memory usage
- Clear model cache if needed

## Migration Guide

### From Previous Version:
1. **No breaking changes** - utility model is enabled by default
2. **Optional feature** - can be disabled without affecting core functionality
3. **Backward compatible** - existing configurations continue to work

### To Disable Utility Model:
1. Set `ENABLE_UTILITY_MODEL = False` in settings
2. Restart the backend service
3. Verify in System Management tab

### To Enable Utility Model:
1. Set `ENABLE_UTILITY_MODEL = True` in settings
2. Restart the backend service
3. Adjust threshold as needed

## Summary

The optional utility model provides **flexibility** in the RAG pipeline:

- **Performance optimization** when needed
- **Simplified stack** when not needed
- **Configurable behavior** based on use case
- **Backward compatibility** with existing systems

Choose the configuration that best fits your specific legal research needs and performance requirements. 