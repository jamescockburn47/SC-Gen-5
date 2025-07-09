# Cloud Legal Consultation

A standalone cloud consultation feature that provides direct legal advice using cloud AI models without RAG (Retrieval-Augmented Generation). This feature offers general legal guidance based on the AI's training data.

## Overview

The Cloud Consultation feature allows users to:
- Get direct legal advice from cloud AI models (OpenAI, Google Gemini, Anthropic Claude)
- Configure analysis parameters (tokens, temperature, analysis style)
- Track consultation history and costs
- Use different matter types and analysis styles
- Compare responses across different providers

## Features

### 🤖 Multi-Provider Support
- **OpenAI GPT-4**: Advanced reasoning and legal analysis
- **Google Gemini**: Fast responses with good legal knowledge
- **Anthropic Claude**: Detailed legal explanations and reasoning

### ⚙️ Advanced Configuration
- **Max Tokens**: Control response length (500-4000 tokens)
- **Temperature**: Adjust creativity vs consistency (0.0-1.0)
- **Matter Type**: Focus on specific legal areas
- **Analysis Style**: Comprehensive, concise, or technical

### 📊 Session Management
- Automatic session tracking
- Cost estimation for each consultation
- Processing time monitoring
- Consultation history with localStorage persistence

### 🎯 Legal Specialization
- **Matter Types**: Contract, Litigation, Regulatory, Due Diligence, Employment, IP
- **Analysis Styles**: Comprehensive, Concise, Technical
- **Legal Prompts**: Optimized for legal reasoning and analysis

## API Endpoints

### GET `/api/rag/cloud-providers`
Get available cloud providers and their status.

**Response:**
```json
{
  "providers": {
    "openai": {
      "available": true,
      "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
      "error": null
    },
    "gemini": {
      "available": true,
      "models": ["gemini-1.5-flash", "gemini-1.5-pro"],
      "error": null
    },
    "claude": {
      "available": false,
      "models": [],
      "error": "ANTHROPIC_API_KEY environment variable not set"
    }
  },
  "available_count": 2
}
```

### POST `/api/rag/cloud-consultation`
Submit a legal question for cloud consultation.

**Request:**
```json
{
  "question": "What are the key elements of a valid contract?",
  "provider": "openai",
  "model": "gpt-4o",
  "max_tokens": 2000,
  "temperature": 0.7,
  "matter_type": "contract",
  "analysis_style": "comprehensive",
  "session_id": "session_1234567890"
}
```

**Response:**
```json
{
  "answer": "A valid contract requires several essential elements...",
  "provider": "openai",
  "model": "gpt-4o",
  "tokens_used": null,
  "cost_estimate": 0.0023,
  "processing_time": 2.45,
  "session_id": "session_1234567890"
}
```

## Environment Variables

The following API keys are required in your `.env` file:

```bash
# OpenAI (GPT-4, GPT-3.5)
OPENAI_API_KEY=your_openai_api_key_here

# Google (Gemini)
GOOGLE_API_KEY=your_google_api_key_here

# Anthropic (Claude)
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

## Usage

### Frontend Interface

1. **Navigate to Cloud Consultation**
   - Click "Cloud Consultation" in the sidebar
   - Or visit `/cloud-consultation` directly

2. **Select Provider**
   - Choose from available cloud providers
   - Each provider shows availability status and supported models

3. **Configure Settings**
   - **Basic**: Select provider and model
   - **Advanced**: Adjust tokens, temperature, matter type, analysis style

4. **Submit Question**
   - Enter your legal question
   - Click "Get Legal Consultation"
   - View real-time progress and results

### Example Questions

**Contract Law:**
- "What are the essential elements of a valid contract?"
- "What constitutes a breach of contract?"
- "How do you determine if a contract is enforceable?"

**Tort Law:**
- "What is the difference between negligence and strict liability?"
- "What are the elements of a negligence claim?"
- "How do you prove causation in a tort case?"

**Employment Law:**
- "What are the key provisions that should be in an employment contract?"
- "What constitutes wrongful termination?"
- "What are the legal requirements for workplace discrimination?"

## Configuration Options

### Matter Types
- **Contract**: Contract formation, terms, breach, remedies
- **Litigation**: Court procedures, evidence, trial strategy
- **Regulatory**: Compliance, administrative law, regulations
- **Due Diligence**: Investigation, risk assessment, verification
- **Employment**: Labor law, workplace rights, discrimination
- **Intellectual Property**: Patents, copyrights, trademarks, trade secrets

### Analysis Styles
- **Comprehensive**: Detailed analysis with citations and implications
- **Concise**: Focused analysis with key points and direct application
- **Technical**: Precise terminology and expert reasoning

### Provider-Specific Models

**OpenAI:**
- `gpt-4o`: Most capable, best for complex legal reasoning
- `gpt-4o-mini`: Faster, good for straightforward questions
- `gpt-4-turbo`: Balanced performance and speed

**Google Gemini:**
- `gemini-1.5-flash`: Fast responses, good for quick consultations
- `gemini-1.5-pro`: More detailed analysis, better for complex questions

**Anthropic Claude:**
- `claude-3-5-sonnet-20241022`: Latest model, excellent reasoning
- `claude-3-sonnet-20240229`: Stable, reliable performance
- `claude-3-haiku-20240307`: Fast, cost-effective

## Cost Estimation

The system provides cost estimates for consultations:

- **OpenAI**: ~$0.01-0.05 per consultation
- **Google Gemini**: ~$0.005-0.02 per consultation  
- **Anthropic Claude**: ~$0.01-0.04 per consultation

Costs vary based on:
- Input question length
- Response length (max tokens)
- Model selected
- Provider pricing

## Best Practices

### Question Formulation
- Be specific and clear about your legal issue
- Include relevant facts and context
- Specify the jurisdiction if relevant
- Ask for practical advice, not just legal definitions

### Provider Selection
- **OpenAI GPT-4**: Best for complex legal reasoning and detailed analysis
- **Google Gemini**: Good for quick consultations and straightforward questions
- **Anthropic Claude**: Excellent for detailed explanations and ethical considerations

### Parameter Tuning
- **High tokens (2000-4000)**: For comprehensive analysis
- **Low temperature (0.1-0.3)**: For consistent, factual responses
- **High temperature (0.7-1.0)**: For creative problem-solving
- **Technical style**: For precise legal terminology
- **Concise style**: For quick summaries and key points

## Limitations

### General Legal Advice
- Provides general legal information, not specific legal advice
- Should not replace consultation with qualified legal professionals
- May not reflect the most current legal developments
- Jurisdiction-specific laws may vary

### Model Limitations
- Training data cutoff dates may affect currency
- May not include recent legal developments
- Should be verified against authoritative sources
- Not a substitute for legal research

## Troubleshooting

### Common Issues

**"Provider not available"**
- Check API key in `.env` file
- Verify API key is valid and has sufficient credits
- Ensure internet connection is stable

**"Generation failed"**
- Check API rate limits
- Verify model name is correct
- Try reducing max tokens or temperature

**"Cost estimation failed"**
- This is a non-critical feature
- Consultation will still work without cost estimates
- Check provider-specific pricing documentation

### Performance Optimization

**For faster responses:**
- Use lower max tokens (500-1000)
- Select faster models (gpt-4o-mini, gemini-1.5-flash)
- Use concise analysis style

**For better quality:**
- Use higher max tokens (2000-4000)
- Select more capable models (gpt-4o, claude-3-5-sonnet)
- Use comprehensive analysis style

## Integration with SC Gen 5

The Cloud Consultation feature is designed to complement the existing RAG system:

- **Cloud Consultation**: General legal advice without document context
- **Legal Research (RAG)**: Document-specific analysis with your uploaded files
- **Companies House**: UK company research and filings
- **Document Manager**: File upload and processing

This provides a complete legal research platform with multiple consultation options.

## Testing

Run the test script to verify functionality:

```bash
python3 test_cloud_consultation.py
```

The test script will:
- Check available providers
- Test consultation with different providers
- Verify advanced settings
- Test error handling

## Security Considerations

- API keys are stored in environment variables
- No sensitive data is logged
- Session data is stored locally in browser
- Cost estimates are approximate and for guidance only

## Future Enhancements

- **Multi-language support**: Legal consultation in different languages
- **Citation tracking**: Automatic legal citation generation
- **Case law integration**: Direct access to case databases
- **Document comparison**: Compare AI analysis with uploaded documents
- **Collaborative sessions**: Share consultations with team members 