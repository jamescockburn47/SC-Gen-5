"""Cloud LLM module for OpenAI, Google, and Anthropic integration."""

import logging
import os
from enum import Enum
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class CloudProvider(Enum):
    """Supported cloud LLM providers."""
    OPENAI = "openai"
    GEMINI = "gemini"
    CLAUDE = "claude"


class CloudLLMGenerator:
    """Cloud LLM generator supporting multiple providers."""

    def __init__(self) -> None:
        """Initialize cloud LLM generator."""
        self._openai_client = None
        self._gemini_client = None
        self._anthropic_client = None
        
        logger.info("CloudLLM generator initialized")

    def generate(
        self,
        prompt: str,
        provider: CloudProvider,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> str:
        """Generate text using specified cloud provider.
        
        Args:
            prompt: Input prompt
            provider: Cloud provider to use
            model: Specific model (uses default if None)
            max_tokens: Maximum tokens to generate
            temperature: Generation temperature
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Generated text
        """
        if provider == CloudProvider.OPENAI:
            return self._generate_openai(prompt, model, max_tokens, temperature, **kwargs)
        elif provider == CloudProvider.GEMINI:
            return self._generate_gemini(prompt, model, max_tokens, temperature, **kwargs)
        elif provider == CloudProvider.CLAUDE:
            return self._generate_claude(prompt, model, max_tokens, temperature, **kwargs)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def _generate_openai(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> str:
        """Generate text using OpenAI."""
        try:
            import openai
        except ImportError:
            raise ImportError("OpenAI package not installed. Run: pip install openai")
            
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
            
        if not self._openai_client:
            self._openai_client = openai.OpenAI(api_key=api_key)
            
        model = model or "gpt-4o"
        
        try:
            response = self._openai_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )
            
            return response.choices[0].message.content or ""
            
        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            raise RuntimeError(f"OpenAI generation failed: {e}")

    def _generate_gemini(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> str:
        """Generate text using Google Gemini."""
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError("Google Generative AI package not installed. Run: pip install google-generativeai")
            
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")
            
        if not self._gemini_client:
            genai.configure(api_key=api_key)
            self._gemini_client = True  # Just a flag to avoid reconfiguring
            
        model = model or "gemini-1.5-flash"
        
        try:
            # Configure generation parameters
            generation_config = {
                "temperature": temperature,
                "max_output_tokens": max_tokens,
                **kwargs
            }
            
            # Remove None values
            generation_config = {k: v for k, v in generation_config.items() if v is not None}
            
            gemini_model = genai.GenerativeModel(model)
            response = gemini_model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            return response.text or ""
            
        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            raise RuntimeError(f"Gemini generation failed: {e}")

    def _generate_claude(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> str:
        """Generate text using Anthropic Claude."""
        try:
            import anthropic
        except ImportError:
            raise ImportError("Anthropic package not installed. Run: pip install anthropic")
            
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
            
        if not self._anthropic_client:
            self._anthropic_client = anthropic.Anthropic(api_key=api_key)
            
        model = model or "claude-3-sonnet-20240229"
        
        try:
            response = self._anthropic_client.messages.create(
                model=model,
                max_tokens=max_tokens or 4000,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}],
                **kwargs
            )
            
            # Extract text from response
            if response.content and len(response.content) > 0:
                return response.content[0].text
            else:
                return ""
                
        except Exception as e:
            logger.error(f"Claude generation failed: {e}")
            raise RuntimeError(f"Claude generation failed: {e}")

    def check_provider_available(self, provider: CloudProvider) -> bool:
        """Check if a provider is available (has API key)."""
        if provider == CloudProvider.OPENAI:
            return bool(os.getenv("OPENAI_API_KEY"))
        elif provider == CloudProvider.GEMINI:
            return bool(os.getenv("GOOGLE_API_KEY"))
        elif provider == CloudProvider.CLAUDE:
            return bool(os.getenv("ANTHROPIC_API_KEY"))
        else:
            return False

    def get_available_providers(self) -> list[CloudProvider]:
        """Get list of available providers (with API keys set)."""
        available = []
        for provider in CloudProvider:
            if self.check_provider_available(provider):
                available.append(provider)
        return available

    def get_default_model(self, provider: CloudProvider) -> str:
        """Get default model for a provider."""
        defaults = {
            CloudProvider.OPENAI: "gpt-4o",
            CloudProvider.GEMINI: "gemini-1.5-flash",
            CloudProvider.CLAUDE: "claude-3-sonnet-20240229",
        }
        return defaults.get(provider, "")

    def get_supported_models(self, provider: CloudProvider) -> list[str]:
        """Get list of supported models for a provider."""
        models = {
            CloudProvider.OPENAI: [
                "gpt-4o",
                "gpt-4o-mini",
                "gpt-4-turbo",
                "gpt-4",
                "gpt-3.5-turbo",
            ],
            CloudProvider.GEMINI: [
                "gemini-1.5-flash",
                "gemini-1.5-pro",
                "gemini-pro",
                "gemini-pro-vision",
            ],
            CloudProvider.CLAUDE: [
                "claude-3-5-sonnet-20241022",
                "claude-3-sonnet-20240229",
                "claude-3-haiku-20240307",
                "claude-3-opus-20240229",
            ],
        }
        return models.get(provider, [])

    def estimate_cost(
        self,
        provider: CloudProvider,
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> float:
        """Estimate cost for generation (approximate)."""
        # This is a simplified cost estimation
        # Real implementation would use up-to-date pricing
        
        cost_per_1k = {
            CloudProvider.OPENAI: {
                "gpt-4o": {"input": 0.005, "output": 0.015},
                "gpt-4": {"input": 0.03, "output": 0.06},
                "gpt-3.5-turbo": {"input": 0.001, "output": 0.002},
            },
            CloudProvider.GEMINI: {
                "gemini-1.5-flash": {"input": 0.0001, "output": 0.0004},
                "gemini-1.5-pro": {"input": 0.001, "output": 0.004},
            },
            CloudProvider.CLAUDE: {
                "claude-3-sonnet-20240229": {"input": 0.003, "output": 0.015},
                "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125},
            },
        }
        
        pricing = cost_per_1k.get(provider, {}).get(model, {"input": 0.001, "output": 0.002})
        
        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]
        
        return input_cost + output_cost

    def validate_provider_setup(self, provider: CloudProvider) -> Dict[str, Any]:
        """Validate provider setup and return status."""
        result = {
            "provider": provider.value,
            "available": False,
            "error": None,
            "models": [],
        }
        
        try:
            if not self.check_provider_available(provider):
                result["error"] = f"API key not found for {provider.value}"
                return result
                
            # Try a simple test generation
            test_prompt = "Hello"
            self.generate(
                prompt=test_prompt,
                provider=provider,
                max_tokens=5,
                temperature=0.0
            )
            
            result["available"] = True
            result["models"] = self.get_supported_models(provider)
            
        except Exception as e:
            result["error"] = str(e)
            
        return result 