"""Local LLM module for Ollama integration."""

import json
import logging
import os
from typing import Any, Dict, Optional

from dotenv import load_dotenv
import requests

# Load environment variables from .env file
from pathlib import Path
env_path = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(env_path)

logger = logging.getLogger(__name__)


class LocalLLMGenerator:
    """Local LLM generator using Ollama."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        default_model: str = "mixtral:latest",
        timeout: int = 300,
    ) -> None:
        """Initialize local LLM generator.
        
        Args:
            base_url: Ollama server URL
            default_model: Default model to use
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.default_model = default_model
        self.timeout = timeout
        
        # Override with environment variables if set
        self.base_url = os.getenv("SC_OLLAMA_URL", self.base_url)
        self.default_model = os.getenv("SC_OLLAMA_MODEL", self.default_model)
        
        logger.info(f"LocalLLM initialized with URL: {self.base_url}, Model: {self.default_model}")

    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        stream: bool = False,
        **kwargs: Any,
    ) -> str:
        """Generate text using Ollama.
        
        Args:
            prompt: Input prompt
            model: Model to use (defaults to default_model)
            max_tokens: Maximum tokens to generate
            temperature: Generation temperature
            stream: Whether to stream response
            **kwargs: Additional Ollama parameters
            
        Returns:
            Generated text
        """
        model = model or self.default_model
        
        # Map our parameters to Ollama format
        ollama_params = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": temperature,
                **kwargs
            }
        }
        
        # Add num_predict if max_tokens specified
        if max_tokens:
            ollama_params["options"]["num_predict"] = max_tokens
            
        try:
            logger.info(f"Generating with model: {model}")
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=ollama_params,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            if stream:
                # Handle streaming response
                return self._handle_streaming_response(response)
            else:
                # Handle single response
                result = response.json()
                return result.get("response", "")
                
        except requests.RequestException as e:
            error_msg = f"Ollama request failed: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse Ollama response: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

    def _handle_streaming_response(self, response: requests.Response) -> str:
        """Handle streaming response from Ollama."""
        generated_text = ""
        
        try:
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    data = json.loads(line)
                    if "response" in data:
                        generated_text += data["response"]
                    if data.get("done", False):
                        break
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing streaming response: {e}")
            
        return generated_text

    def list_models(self) -> list[Dict[str, Any]]:
        """List available models in Ollama."""
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("models", [])
            
        except requests.RequestException as e:
            logger.error(f"Failed to list models: {e}")
            return []

    def check_model_available(self, model: str) -> bool:
        """Check if a model is available in Ollama."""
        models = self.list_models()
        available_names = [m.get("name", "") for m in models]
        return model in available_names

    def pull_model(self, model: str) -> bool:
        """Pull a model in Ollama."""
        try:
            logger.info(f"Pulling model: {model}")
            
            response = requests.post(
                f"{self.base_url}/api/pull",
                json={"name": model},
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            # Monitor pull progress
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    data = json.loads(line)
                    status = data.get("status", "")
                    if "completed" in status.lower():
                        logger.info(f"Successfully pulled model: {model}")
                        return True
                    elif "error" in status.lower():
                        logger.error(f"Error pulling model: {status}")
                        return False
                        
            return True
            
        except requests.RequestException as e:
            logger.error(f"Failed to pull model {model}: {e}")
            return False

    def get_model_info(self, model: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific model."""
        try:
            response = requests.post(
                f"{self.base_url}/api/show",
                json={"name": model},
                timeout=30
            )
            response.raise_for_status()
            
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Failed to get model info for {model}: {e}")
            return None

    def is_server_available(self) -> bool:
        """Check if Ollama server is available."""
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=10
            )
            return response.status_code == 200
            
        except requests.RequestException:
            return False

    def get_supported_models(self) -> list[str]:
        """Get list of supported model names."""
        return [
            "mixtral:latest",
            "mistral:latest", 
            "phi3:latest",
            "lawma:latest",
            "llama2:latest",
            "codellama:latest",
            "vicuna:latest",
            "orca-mini:latest",
        ]

    def ensure_model_available(self, model: str) -> bool:
        """Ensure a model is available, pulling if necessary."""
        if self.check_model_available(model):
            return True
            
        logger.info(f"Model {model} not found, attempting to pull...")
        return self.pull_model(model)

    def get_generation_stats(self, model: str) -> Dict[str, Any]:
        """Get generation statistics for a model (if available)."""
        # This is a placeholder for future Ollama features
        # Currently returns basic info
        return {
            "model": model,
            "base_url": self.base_url,
            "available": self.check_model_available(model),
            "server_available": self.is_server_available(),
        } 