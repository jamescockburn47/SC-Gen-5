"""
Model client for communicating with the independent model service.
This provides a safe interface for the main API to use models without crashing.
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

log = logging.getLogger("lexcognito.model_client")

class ModelServiceClient:
    """
    Client for communicating with the independent model service.
    Provides crash-resistant model operations for the main API.
    """
    
    def __init__(self):
        self.status_file = Path("data/model_service_status.json")
        self.request_file = Path("data/model_service_requests.json")
        self.response_file = Path("data/model_service_responses.json")
        
        # Ensure data directory exists
        Path("data").mkdir(exist_ok=True)
        
        # Track last known service status
        self.last_service_check = 0
        self.service_available = False
        self.last_status = {}
    
    def _check_service_health(self) -> bool:
        """Check if the model service is healthy and responding."""
        try:
            if not self.status_file.exists():
                return False
            
            # Check if status is recent (within 30 seconds)
            if time.time() - self.status_file.stat().st_mtime > 30:
                return False
            
            with open(self.status_file, 'r') as f:
                status = json.load(f)
            
            self.last_status = status
            last_heartbeat = status.get("last_heartbeat", 0)
            
            # Service is healthy if heartbeat is recent
            return time.time() - last_heartbeat < 30
            
        except Exception as e:
            log.debug(f"Service health check failed: {e}")
            return False
    
    async def _send_request(self, action: str, timeout: float = 30.0, **kwargs) -> Tuple[bool, Any]:
        """Send a request to the model service and wait for response."""
        try:
            request_id = str(uuid.uuid4())
            
            request = {
                "id": request_id,
                "action": action,
                "timestamp": datetime.now().isoformat(),
                **kwargs
            }
            
            # Write request
            with open(self.request_file, 'w') as f:
                json.dump(request, f, indent=2)
            
            # Wait for response with timeout
            start_time = time.time()
            while time.time() - start_time < timeout:
                if self.response_file.exists():
                    try:
                        with open(self.response_file, 'r') as f:
                            response = json.load(f)
                        
                        if response.get("request_id") == request_id:
                            # Remove response file
                            self.response_file.unlink()
                            
                            success = response.get("success", False)
                            data = response.get("data")
                            error = response.get("error")
                            
                            if success:
                                return True, data
                            else:
                                log.warning(f"Model service request failed: {error}")
                                return False, error
                                
                    except Exception as e:
                        log.debug(f"Error reading response: {e}")
                
                await asyncio.sleep(0.1)
            
            # Timeout
            log.error(f"Model service request timed out after {timeout}s")
            return False, f"Request timed out after {timeout}s"
            
        except Exception as e:
            log.error(f"Error sending request to model service: {e}")
            return False, str(e)
    
    async def is_service_available(self) -> bool:
        """Check if the model service is available."""
        # Cache the check for 5 seconds
        now = time.time()
        if now - self.last_service_check < 5:
            return self.service_available
        
        self.service_available = self._check_service_health()
        self.last_service_check = now
        
        return self.service_available
    
    async def get_service_status(self) -> Dict[str, Any]:
        """Get the current status of the model service."""
        if not await self.is_service_available():
            return {
                "available": False,
                "models": {"embedder": "unavailable", "utility": "unavailable", "reasoning": "unavailable"},
                "error": "Model service not available"
            }
        
        success, data = await self._send_request("status", timeout=10.0)
        if success:
            return {
                "available": True,
                "models": data.get("models", {}),
                "gpu_memory": data.get("gpu_memory", {})
            }
        else:
            return {
                "available": False,
                "models": {"embedder": "error", "utility": "error", "reasoning": "error"},
                "error": data
            }
    
    async def load_embedder(self) -> bool:
        """Request the model service to load the embedder."""
        if not await self.is_service_available():
            log.warning("Model service not available, cannot load embedder")
            return False
        
        success, data = await self._send_request("load_embedder", timeout=60.0)
        return success
    
    async def load_utility_model(self) -> bool:
        """Request the model service to load the utility model."""
        if not await self.is_service_available():
            log.warning("Model service not available, cannot load utility model")
            return False
        
        success, data = await self._send_request("load_utility", timeout=120.0)
        return success
    
    async def generate_text(self, prompt: str, max_tokens: int = 100, model_type: str = "utility") -> Tuple[bool, str]:
        """Generate text using the model service."""
        if not await self.is_service_available():
            return False, "Model service not available"
        
        success, data = await self._send_request(
            "generate",
            timeout=60.0,
            prompt=prompt,
            max_tokens=max_tokens,
            model_type=model_type
        )
        
        if success:
            return True, data.get("response", "")
        else:
            return False, data
    
    async def embed_texts(self, texts: List[str]) -> Tuple[bool, Any]:
        """Generate embeddings using the model service."""
        if not await self.is_service_available():
            return False, "Model service not available"
        
        success, data = await self._send_request(
            "embed",
            timeout=30.0,
            texts=texts
        )
        
        if success:
            return True, data.get("embeddings", [])
        else:
            return False, data
    
    async def unload_all_models(self) -> bool:
        """Request the model service to unload all models."""
        if not await self.is_service_available():
            return True  # Already unloaded if service unavailable
        
        success, data = await self._send_request("unload_all", timeout=30.0)
        return success


class CrashResistantModelManager:
    """
    High-level model manager that provides fallback capabilities when the model service crashes.
    """
    
    def __init__(self):
        self.client = ModelServiceClient()
        self.fallback_mode = False
        
    async def get_status(self) -> Dict[str, Any]:
        """Get comprehensive model status including fallback information."""
        service_status = await self.client.get_service_status()
        
        return {
            "service_available": service_status["available"],
            "models": service_status.get("models", {}),
            "gpu_memory": service_status.get("gpu_memory", {}),
            "fallback_mode": self.fallback_mode,
            "error": service_status.get("error")
        }
    
    async def ensure_embedder_ready(self) -> bool:
        """Ensure embedder is ready, with fallback handling."""
        try:
            status = await self.client.get_service_status()
            if not status["available"]:
                log.warning("Model service unavailable for embedder")
                self.fallback_mode = True
                return False
            
            embedder_status = status["models"].get("embedder", "unloaded")
            if embedder_status == "ready":
                return True
            elif embedder_status in ["unloaded", "error"]:
                log.info("Loading embedder model...")
                success = await self.client.load_embedder()
                if success:
                    self.fallback_mode = False
                    return True
                else:
                    log.warning("Failed to load embedder, enabling fallback mode")
                    self.fallback_mode = True
                    return False
            else:
                # Loading in progress
                return False
                
        except Exception as e:
            log.error(f"Error ensuring embedder ready: {e}")
            self.fallback_mode = True
            return False
    
    async def ensure_utility_model_ready(self) -> bool:
        """Ensure utility model is ready, with fallback handling."""
        try:
            status = await self.client.get_service_status()
            if not status["available"]:
                log.warning("Model service unavailable for utility model")
                self.fallback_mode = True
                return False
            
            utility_status = status["models"].get("utility", "unloaded")
            if utility_status == "ready":
                return True
            elif utility_status in ["unloaded", "error"]:
                log.info("Loading utility model...")
                success = await self.client.load_utility_model()
                if success:
                    self.fallback_mode = False
                    return True
                else:
                    log.warning("Failed to load utility model, enabling fallback mode")
                    self.fallback_mode = True
                    return False
            else:
                # Loading in progress
                return False
                
        except Exception as e:
            log.error(f"Error ensuring utility model ready: {e}")
            self.fallback_mode = True
            return False
    
    async def generate_with_fallback(self, prompt: str, max_tokens: int = 100) -> Tuple[str, str]:
        """
        Generate text with automatic fallback to basic responses if models unavailable.
        Returns: (response, context_info)
        """
        try:
            # Try to ensure utility model is ready
            if await self.ensure_utility_model_ready():
                success, response = await self.client.generate_text(prompt, max_tokens, "utility")
                if success:
                    return response, "memory-optimized model service"
                else:
                    log.warning(f"Model generation failed: {response}")
            
            # Fallback to basic response
            self.fallback_mode = True
            return self._generate_fallback_response(prompt), "fallback mode (model service unavailable)"
            
        except Exception as e:
            log.error(f"Error in generate_with_fallback: {e}")
            self.fallback_mode = True
            return self._generate_fallback_response(prompt), f"fallback mode (error: {str(e)[:100]})"
    
    def _generate_fallback_response(self, prompt: str) -> str:
        """Generate a basic fallback response when models are unavailable."""
        # Basic legal response templates based on common question patterns
        prompt_lower = prompt.lower()
        
        if "contract" in prompt_lower:
            return ("A contract is a legally binding agreement between parties that creates mutual obligations. "
                   "Key elements include offer, acceptance, consideration, and legal capacity. "
                   "Note: Model service unavailable - this is a basic response.")
        
        elif "liability" in prompt_lower:
            return ("Liability refers to legal responsibility for damages or obligations. "
                   "It can be contractual, tortious, or statutory in nature. "
                   "Note: Model service unavailable - this is a basic response.")
        
        elif "law" in prompt_lower:
            return ("Legal principles vary by jurisdiction and specific circumstances. "
                   "It's recommended to consult with a qualified legal professional for specific advice. "
                   "Note: Model service unavailable - this is a basic response.")
        
        else:
            return ("I apologize, but the AI model service is currently unavailable. "
                   "Please try again later or contact support if the issue persists. "
                   "For urgent legal questions, please consult with a qualified legal professional.")


# Global instance for the main API to use
model_manager = CrashResistantModelManager()