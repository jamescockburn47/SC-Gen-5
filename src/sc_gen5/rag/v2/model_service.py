"""
Crash-resistant model service that runs independently from the main API.
This service can fail and restart without affecting the backend API server.
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import signal
import sys
import traceback

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from sentence_transformers import SentenceTransformer

from settings import settings

log = logging.getLogger("lexcognito.model_service")

class ModelStatus(Enum):
    UNLOADED = "unloaded"
    LOADING = "loading"
    READY = "ready"
    ERROR = "error"
    CRASHED = "crashed"

class ModelService:
    """
    Independent model service that can crash and restart without affecting the main API.
    Communicates with the main service via file-based status and message queues.
    """
    
    def __init__(self):
        self.service_id = str(uuid.uuid4())[:8]
        self.status_file = Path("data/model_service_status.json")
        self.request_file = Path("data/model_service_requests.json")
        self.response_file = Path("data/model_service_responses.json")
        
        # Model states
        self.embedder = None
        self.utility_model = None
        self.utility_tokenizer = None
        self.reasoning_model = None
        self.reasoning_tokenizer = None
        
        # Model status tracking
        self.model_states = {
            "embedder": ModelStatus.UNLOADED,
            "utility": ModelStatus.UNLOADED,
            "reasoning": ModelStatus.UNLOADED
        }
        
        # Performance tracking
        self.last_heartbeat = time.time()
        self.crash_count = 0
        self.startup_time = time.time()
        
        # Ensure data directory exists
        Path("data").mkdir(exist_ok=True)
        
        # Setup graceful shutdown
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        log.info(f"Model service {self.service_id} initialized")
    
    def _signal_handler(self, signum, frame):
        """Handle graceful shutdown signals."""
        log.info(f"Model service {self.service_id} received signal {signum}, shutting down...")
        self._update_status("shutting_down")
        sys.exit(0)
    
    def _update_status(self, overall_status: str = "running"):
        """Update status file for main API to read."""
        try:
            status = {
                "service_id": self.service_id,
                "overall_status": overall_status,
                "models": {name: state.value for name, state in self.model_states.items()},
                "last_heartbeat": time.time(),
                "crash_count": self.crash_count,
                "startup_time": self.startup_time,
                "gpu_memory": self._get_gpu_memory() if torch.cuda.is_available() else None,
                "timestamp": datetime.now().isoformat()
            }
            
            with open(self.status_file, 'w') as f:
                json.dump(status, f, indent=2)
                
        except Exception as e:
            log.error(f"Failed to update status: {e}")
    
    def _get_gpu_memory(self) -> Dict[str, float]:
        """Get current GPU memory usage."""
        if not torch.cuda.is_available():
            return {}
        
        return {
            "allocated_gb": torch.cuda.memory_allocated() / (1024**3),
            "cached_gb": torch.cuda.memory_reserved() / (1024**3),
            "total_gb": torch.cuda.get_device_properties(0).total_memory / (1024**3)
        }
    
    def _clear_gpu_memory(self):
        """Aggressive GPU memory cleanup."""
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
    
    def _check_requests(self) -> Optional[Dict[str, Any]]:
        """Check for pending requests from main API."""
        try:
            if not self.request_file.exists():
                return None
                
            with open(self.request_file, 'r') as f:
                request = json.load(f)
            
            # Remove processed request
            self.request_file.unlink()
            return request
            
        except Exception as e:
            log.debug(f"No valid requests: {e}")
            return None
    
    def _send_response(self, request_id: str, success: bool, data: Any = None, error: str = None):
        """Send response back to main API."""
        try:
            response = {
                "request_id": request_id,
                "success": success,
                "data": data,
                "error": error,
                "timestamp": datetime.now().isoformat(),
                "service_id": self.service_id
            }
            
            with open(self.response_file, 'w') as f:
                json.dump(response, f, indent=2)
                
        except Exception as e:
            log.error(f"Failed to send response: {e}")
    
    async def load_embedder(self) -> bool:
        """Load embedder model with crash protection (CPU-only for memory efficiency)."""
        try:
            self.model_states["embedder"] = ModelStatus.LOADING
            self._update_status()
            
            log.info("Loading embedder model on CPU (BGE-base-en-v1.5)...")
            
            # Load embedder on CPU to preserve GPU memory for utility/reasoning models
            self.embedder = SentenceTransformer(
                settings.EMBEDDING_MODEL,  # BGE-base-en-v1.5
                device="cpu",  # Always CPU - this is critical for memory management
                trust_remote_code=True
            )
            
            # Test the model with actual embedding
            test_embedding = self.embedder.encode(["test legal document embedding"])
            if test_embedding is None or len(test_embedding) == 0:
                raise ValueError("Embedder test failed - no output generated")
            
            expected_dim = 768  # BGE-base-en-v1.5 dimension
            if test_embedding.shape[-1] != expected_dim:
                raise ValueError(f"Embedder dimension mismatch: got {test_embedding.shape[-1]}, expected {expected_dim}")
            
            self.model_states["embedder"] = ModelStatus.READY
            log.info(f"✓ Embedder loaded successfully on CPU (dimension: {test_embedding.shape[-1]})")
            return True
            
        except Exception as e:
            log.error(f"Failed to load embedder: {e}")
            self.model_states["embedder"] = ModelStatus.ERROR
            self.embedder = None
            return False
        finally:
            self._update_status()
    
    async def load_utility_model(self) -> bool:
        """Load utility model with crash protection and memory management."""
        try:
            self.model_states["utility"] = ModelStatus.LOADING
            self._update_status()
            
            # Unload reasoning model if loaded to free memory
            if self.reasoning_model is not None:
                log.info("Unloading reasoning model to free memory for utility model")
                del self.reasoning_model
                del self.reasoning_tokenizer
                self.reasoning_model = None
                self.reasoning_tokenizer = None
                self.model_states["reasoning"] = ModelStatus.UNLOADED
                self._clear_gpu_memory()
            
            log.info(f"Loading utility model: {settings.UTILITY_MODEL}")
            
            # Load tokenizer first (lightweight)
            self.utility_tokenizer = AutoTokenizer.from_pretrained(
                settings.UTILITY_MODEL,
                trust_remote_code=True,
                use_fast=True
            )
            if self.utility_tokenizer.pad_token is None:
                self.utility_tokenizer.pad_token = self.utility_tokenizer.eos_token
            
            # Check GPU memory before loading model
            if torch.cuda.is_available():
                gpu_memory = self._get_gpu_memory()
                if gpu_memory["allocated_gb"] > 6.0:  # Conservative limit
                    raise RuntimeError(f"GPU memory too high: {gpu_memory['allocated_gb']:.1f}GB")
            
            # Load model with memory optimization
            self.utility_model = AutoModelForCausalLM.from_pretrained(
                settings.UTILITY_MODEL,
                device_map="auto",
                torch_dtype=torch.float16,
                trust_remote_code=True,
                low_cpu_mem_usage=True,
                attn_implementation="eager"
            )
            
            self.utility_model.eval()
            
            # Test generation
            test_input = self.utility_tokenizer("Test", return_tensors="pt", max_length=10)
            if torch.cuda.is_available():
                test_input = {k: v.to(self.utility_model.device) for k, v in test_input.items()}
            
            with torch.no_grad():
                _ = self.utility_model.generate(
                    **test_input,
                    max_new_tokens=1,
                    do_sample=False,
                    pad_token_id=self.utility_tokenizer.eos_token_id
                )
            
            self.model_states["utility"] = ModelStatus.READY
            gpu_mem = self._get_gpu_memory()
            log.info(f"✓ Utility model loaded, using {gpu_mem.get('allocated_gb', 0):.1f}GB GPU")
            return True
            
        except Exception as e:
            log.error(f"Failed to load utility model: {e}")
            self.model_states["utility"] = ModelStatus.ERROR
            self.utility_model = None
            self.utility_tokenizer = None
            self._clear_gpu_memory()
            return False
        finally:
            self._update_status()
    
    async def load_reasoning_model(self) -> bool:
        """Load reasoning model with crash protection and memory management."""
        try:
            self.model_states["reasoning"] = ModelStatus.LOADING
            self._update_status()
            
            # Unload utility model if loaded to free memory
            if self.utility_model is not None:
                log.info("Unloading utility model to free memory for reasoning model")
                del self.utility_model
                del self.utility_tokenizer
                self.utility_model = None
                self.utility_tokenizer = None
                self.model_states["utility"] = ModelStatus.UNLOADED
                self._clear_gpu_memory()
            
            log.info(f"Loading reasoning model: {settings.REASONING_MODEL}")
            
            # Load tokenizer first (lightweight)
            self.reasoning_tokenizer = AutoTokenizer.from_pretrained(
                settings.REASONING_MODEL,
                trust_remote_code=True,
                use_fast=True
            )
            if self.reasoning_tokenizer.pad_token is None:
                self.reasoning_tokenizer.pad_token = self.reasoning_tokenizer.eos_token
            
            # Check GPU memory before loading model
            if torch.cuda.is_available():
                gpu_memory = self._get_gpu_memory()
                if gpu_memory["allocated_gb"] > 3.0:  # Conservative limit for reasoning model
                    raise RuntimeError(f"GPU memory too high for reasoning model: {gpu_memory['allocated_gb']:.1f}GB")
            
            # Load model with memory optimization
            self.reasoning_model = AutoModelForCausalLM.from_pretrained(
                settings.REASONING_MODEL,
                device_map="auto",
                torch_dtype=torch.float16,
                trust_remote_code=True,
                low_cpu_mem_usage=True,
                attn_implementation="eager"
            )
            
            self.reasoning_model.eval()
            
            # Test generation
            test_input = self.reasoning_tokenizer("Test", return_tensors="pt", max_length=10)
            if torch.cuda.is_available():
                test_input = {k: v.to(self.reasoning_model.device) for k, v in test_input.items()}
            
            with torch.no_grad():
                _ = self.reasoning_model.generate(
                    **test_input,
                    max_new_tokens=1,
                    do_sample=False,
                    pad_token_id=self.reasoning_tokenizer.eos_token_id
                )
            
            self.model_states["reasoning"] = ModelStatus.READY
            gpu_mem = self._get_gpu_memory()
            log.info(f"✓ Reasoning model loaded, using {gpu_mem.get('allocated_gb', 0):.1f}GB GPU")
            return True
            
        except Exception as e:
            log.error(f"Failed to load reasoning model: {e}")
            self.model_states["reasoning"] = ModelStatus.ERROR
            self.reasoning_model = None
            self.reasoning_tokenizer = None
            self._clear_gpu_memory()
            return False
        finally:
            self._update_status()
    
    async def embed_text(self, texts: List[str]) -> Tuple[bool, Any]:
        """Generate embeddings using the CPU embedder model."""
        try:
            if self.embedder is None:
                return False, "Embedder model not loaded"
            
            # Generate embeddings on CPU
            embeddings = self.embedder.encode(texts, convert_to_numpy=True)
            
            return True, embeddings.tolist()  # Convert to list for JSON serialization
            
        except Exception as e:
            log.error(f"Embedding generation failed: {e}")
            return False, str(e)
    
    async def generate_text(self, prompt: str, max_tokens: int = 100, model_type: str = "utility") -> Tuple[bool, str]:
        """Generate text with enhanced OOM prevention during generation."""
        try:
            if model_type == "utility":
                if self.utility_model is None or self.utility_tokenizer is None:
                    return False, "Utility model not loaded"
                    
                tokenizer = self.utility_tokenizer
                model = self.utility_model
            elif model_type == "reasoning":
                if self.reasoning_model is None or self.reasoning_tokenizer is None:
                    return False, "Reasoning model not loaded"
                    
                tokenizer = self.reasoning_tokenizer
                model = self.reasoning_model
            else:
                return False, f"Model type {model_type} not supported yet"
            
            # Pre-generation memory check
            if torch.cuda.is_available():
                gpu_memory = self._get_gpu_memory()
                allocated_gb = gpu_memory.get("allocated_gb", 0)
                total_gb = gpu_memory.get("total_gb", 8)
                
                # Dynamic memory threshold based on available memory
                memory_threshold = 0.85 * total_gb  # 85% threshold
                
                if allocated_gb > memory_threshold:
                    log.warning(f"GPU memory too high for safe generation: {allocated_gb:.1f}GB > {memory_threshold:.1f}GB")
                    return False, f"GPU memory too high for safe generation: {allocated_gb:.1f}GB"
                
                # Adjust max_tokens based on available memory
                available_memory = total_gb - allocated_gb
                if available_memory < 1.0:  # Less than 1GB available
                    max_tokens = min(max_tokens, 50)  # Reduce token limit
                    log.info(f"Reducing max_tokens to {max_tokens} due to low memory")
            
            # Tokenize input with conservative limits
            max_input_length = 1024 if torch.cuda.is_available() and self._get_gpu_memory().get("allocated_gb", 0) > 6.0 else 2048
            
            inputs = tokenizer(
                prompt,
                return_tensors="pt",
                max_length=max_input_length,
                truncation=True
            )
            
            if torch.cuda.is_available():
                inputs = {k: v.to(model.device) for k, v in inputs.items()}
            
            # Conservative generation parameters based on memory
            conservative_max_tokens = min(max_tokens, 100)  # Never exceed 100 tokens
            
            # Generate with progressive memory monitoring
            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=conservative_max_tokens,
                    do_sample=True,
                    temperature=0.7,
                    top_p=0.9,
                    pad_token_id=tokenizer.eos_token_id,
                    use_cache=False,  # Disable cache to save memory
                    early_stopping=True,  # Stop early if possible
                    num_return_sequences=1  # Only generate one sequence
                )
            
            # Immediate memory cleanup after generation
            if torch.cuda.is_available():
                self._clear_gpu_memory()
            
            # Decode response
            response = tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Remove input text from response
            if response.startswith(prompt):
                response = response[len(prompt):].strip()
            
            return True, response
            
        except RuntimeError as e:
            if "out of memory" in str(e).lower():
                log.error("GPU OOM during generation, implementing emergency cleanup...")
                
                # Emergency cleanup - unload all models immediately
                await self.unload_all_models()
                
                # Try to recover with minimal response
                fallback_response = f"Memory exhausted during generation. Available models unloaded for recovery. Please try a shorter prompt or reload models."
                return False, fallback_response
            else:
                log.error(f"Generation failed: {e}")
                return False, str(e)
        except Exception as e:
            log.error(f"Generation error: {e}")
            return False, str(e)
    
    async def unload_all_models(self):
        """Unload all models to free memory."""
        log.info("Unloading all models...")
        
        if self.utility_model is not None:
            del self.utility_model
            del self.utility_tokenizer
            self.utility_model = None
            self.utility_tokenizer = None
            self.model_states["utility"] = ModelStatus.UNLOADED
            
        if self.reasoning_model is not None:
            del self.reasoning_model
            del self.reasoning_tokenizer
            self.reasoning_model = None
            self.reasoning_tokenizer = None
            self.model_states["reasoning"] = ModelStatus.UNLOADED
            
        if self.embedder is not None:
            del self.embedder
            self.embedder = None
            self.model_states["embedder"] = ModelStatus.UNLOADED
        
        self._clear_gpu_memory()
        self._update_status()
        log.info("✓ All models unloaded")
    
    async def process_request(self, request: Dict[str, Any]):
        """Process a request from the main API."""
        request_id = request.get("id", "unknown")
        action = request.get("action")
        
        try:
            if action == "load_embedder":
                success = await self.load_embedder()
                self._send_response(request_id, success, {"model": "embedder"})
                
            elif action == "load_utility":
                success = await self.load_utility_model()
                self._send_response(request_id, success, {"model": "utility"})
                
            elif action == "load_reasoning":
                success = await self.load_reasoning_model()
                self._send_response(request_id, success, {"model": "reasoning"})
                
            elif action == "generate":
                prompt = request.get("prompt", "")
                max_tokens = request.get("max_tokens", 100)
                model_type = request.get("model_type", "utility")
                
                success, response = await self.generate_text(prompt, max_tokens, model_type)
                self._send_response(request_id, success, {"response": response})
                
            elif action == "embed":
                texts = request.get("texts", [])
                if not texts:
                    self._send_response(request_id, False, error="No texts provided for embedding")
                    return
                
                success, embeddings = await self.embed_text(texts)
                self._send_response(request_id, success, {"embeddings": embeddings})
                
            elif action == "unload_all":
                await self.unload_all_models()
                self._send_response(request_id, True, {"message": "All models unloaded"})
                
            elif action == "status":
                self._send_response(request_id, True, {
                    "models": {name: state.value for name, state in self.model_states.items()},
                    "gpu_memory": self._get_gpu_memory()
                })
                
            else:
                self._send_response(request_id, False, error=f"Unknown action: {action}")
                
        except Exception as e:
            log.error(f"Error processing request {request_id}: {e}")
            self._send_response(request_id, False, error=str(e))
    
    async def run(self):
        """Main service loop."""
        log.info(f"Model service {self.service_id} starting main loop...")
        
        # Try to load embedder on startup (non-critical)
        try:
            await self.load_embedder()
        except Exception as e:
            log.warning(f"Could not load embedder on startup: {e}")
        
        while True:
            try:
                # Update heartbeat
                self.last_heartbeat = time.time()
                self._update_status()
                
                # Check for requests
                request = self._check_requests()
                if request:
                    await self.process_request(request)
                
                # Small sleep to prevent busy waiting
                await asyncio.sleep(0.1)
                
            except KeyboardInterrupt:
                log.info("Received keyboard interrupt, shutting down...")
                break
            except Exception as e:
                log.error(f"Error in main loop: {e}")
                self.crash_count += 1
                
                # If too many crashes, wait longer
                if self.crash_count > 5:
                    log.error(f"Too many crashes ({self.crash_count}), sleeping for 30s...")
                    await asyncio.sleep(30)
                else:
                    await asyncio.sleep(5)
        
        # Cleanup on exit
        await self.unload_all_models()
        self._update_status("stopped")
        log.info(f"Model service {self.service_id} stopped")


async def main():
    """Main entry point for the model service."""
    try:
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('model_service.log')
            ]
        )
        
        service = ModelService()
        await service.run()
        
    except Exception as e:
        log.error(f"Model service crashed: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())