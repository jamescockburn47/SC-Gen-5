"""
Model singletons with lazy loading for RAG v2.
Lazy-load quantized models once per process to optimize memory usage.
"""

from functools import lru_cache
from typing import Tuple, Any, Optional, Dict
import logging
from pathlib import Path

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from sentence_transformers import SentenceTransformer
from auto_gptq import AutoGPTQForCausalLM
from settings import settings
import gc
import time
import os

# Import hardware configuration
from .hardware import utility_device_map, reasoner_device_map, hardware_initialized

log = logging.getLogger("lexcognito.rag.v2.models")

class ModelManager:
    """Manages lazy loading of models - no models loaded until first use."""
    
    def __init__(self):
        self._models = {}
        self._model_configs = {
            "generator": {
                "model_path": "models/mistral-7b-instruct-v0.2.Q4_K_M.gguf",
                "model_name": "Mistral-7B-Instruct",
                "device": "auto",  # Will auto-detect GPU/CPU
                "max_gpu_layers": "auto"  # Will auto-detect based on VRAM
            }
        }
        self._embedder = None
        self._embedder_config = {
            "model_name": "BAAI/bge-base-en-v1.5",
            "device": "auto"
        }
    
    def load_embedder(self, force_reload: bool = False) -> Tuple[Any, Any]:
        """Load embedder model lazily on first use."""
        if self._embedder is None or force_reload:
            log.info("Loading embedder model (BGE-base-en-v1.5)...")
            
            try:
                from sentence_transformers import SentenceTransformer
                
                # Auto-detect device
                device = "cuda" if torch.cuda.is_available() else "cpu"
                log.info(f"Loading embedder on {device.upper()}")
                
                embedder = SentenceTransformer(self._embedder_config["model_name"], device=device)
                
                # Test the embedder
                test_text = "Test embedding"
                test_embedding = embedder.encode(test_text)
                log.info(f"✓ Embedder model loaded successfully (dimension: {len(test_embedding)})")
                
                self._embedder = embedder
                
            except Exception as e:
                log.error(f"Failed to load embedder: {e}")
                raise
        
        return self._embedder, self._embedder
    
    def load_generator_model(self, force_reload: bool = False) -> Tuple[Any, Any]:
        """Load main Mistral-7B model lazily on first use."""
        model_key = "generator"
        
        if model_key not in self._models or force_reload:
            log.info("Loading main Mistral-7B-Instruct model (lazy loading)...")
            
            try:
                import torch
                from llama_cpp import Llama
                
                config = self._model_configs[model_key]
                model_path = config["model_path"]
                
                # Check if model file exists
                if not os.path.exists(model_path):
                    raise FileNotFoundError(f"Model file not found: {model_path}")
                
                # Auto-detect GPU and set layers
                gpu_layers = 0
                if torch.cuda.is_available():
                    gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
                    if gpu_memory >= 8.0:  # 8GB+ GPU
                        gpu_layers = -1  # Use all layers on GPU
                        log.info(f"8GB+ GPU detected: using all layers on GPU")
                    elif gpu_memory >= 6.0:  # 6-8GB GPU
                        gpu_layers = 32
                        log.info(f"6-8GB GPU detected: using 32 layers on GPU")
                    else:  # <6GB GPU
                        gpu_layers = 16
                        log.info(f"<6GB GPU detected: using 16 layers on GPU")
                else:
                    log.info("No GPU detected: using CPU only")
                
                # Load model with auto-detected settings
                model = Llama(
                    model_path=model_path,
                    n_gpu_layers=gpu_layers,
                    n_ctx=8192,  # Increased context window
                    n_batch=512,  # Optimized batch size
                    verbose=False
                )
                
                # Create simple tokenizer wrapper
                class SimpleTokenizer:
                    def __init__(self, model):
                        self.model = model
                        self.eos_token_id = model.token_eos()
                    
                    def __call__(self, text, return_tensors=None, **kwargs):
                        # Simple tokenization for llama.cpp
                        tokens = self.model.tokenize(text.encode())
                        return {"input_ids": torch.tensor([tokens])}
                    
                    def decode(self, tokens, skip_special_tokens=True):
                        # Use llama.cpp's built-in tokenization
                        if isinstance(tokens, torch.Tensor):
                            tokens = tokens.tolist()
                        return self.model.detokenize(tokens).decode()
                
                tokenizer = SimpleTokenizer(model)
                
                # Test the model
                test_prompt = "Hello, how are you?"
                test_input = tokenizer(test_prompt, return_tensors="pt")
                
                with torch.no_grad():
                    test_output = model.create_completion(
                        test_prompt,
                        max_tokens=10,
                        temperature=0.0,
                        stop=["\n"]
                    )
                
                log.info(f"✓ Main Mistral-7B model loaded successfully")
                
                self._models[model_key] = {
                    "tokenizer": tokenizer,
                    "model": model,
                    "config": config
                }
                
            except Exception as e:
                log.error(f"Failed to load main model: {e}")
                raise
        
        return self._models[model_key]["tokenizer"], self._models[model_key]["model"]
    
    def load_utility_model(self, force_reload: bool = False) -> Tuple[AutoTokenizer, AutoModelForCausalLM]:
        """DEPRECATED: Use main generator model instead of smaller utility model."""
        log.warning("Utility model deprecated - using main Mistral-7B model instead")
        return self.load_generator_model(force_reload)
    
    def _get_cached_model(self, model_type: str) -> Optional[Dict[str, Any]]:
        """Get cached model if available."""
        return self._models.get(model_type)
    
    def _cache_model(self, model_type: str, tokenizer: Any, model: Any) -> None:
        """Cache loaded model."""
        self._models[model_type] = {
            "tokenizer": tokenizer,
            "model": model,
            "config": self._model_configs.get(model_type, {})
        }
    
    def get_memory_usage(self) -> Dict[str, float]:
        """Get current memory usage."""
        import psutil
        import torch
        
        memory_info = {
            "ram_used_gb": psutil.virtual_memory().used / (1024**3),
            "ram_total_gb": psutil.virtual_memory().total / (1024**3),
            "gpu_vram": 0.0,
            "gpu_allocated": 0.0
        }
        
        if torch.cuda.is_available():
            memory_info["gpu_vram"] = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            memory_info["gpu_allocated"] = torch.cuda.memory_allocated() / (1024**3)
        
        return memory_info
    
    def get_memory_status(self) -> Dict[str, Any]:
        """Get detailed memory and model status."""
        memory_usage = self.get_memory_usage()
        
        return {
            "memory_usage": memory_usage,
            "models_loaded": {
                "embedder": self._embedder is not None,
                "generator": "generator" in self._models,
                "utility": False  # Deprecated
            },
            "model_configs": self._model_configs,
            "lazy_loading": True
        }
    
    def get_embedder(self) -> Tuple[Any, Any]:
        """Get embedder (lazy load if needed)."""
        return self.load_embedder()
    
    def get_generator_model(self) -> Tuple[AutoTokenizer, AutoModelForCausalLM]:
        """Get main generator model (lazy load if needed)."""
        return self.load_generator_model()
    
    def get_utility_model(self) -> Tuple[AutoTokenizer, AutoModelForCausalLM]:
        """Get utility model (deprecated - returns main model)."""
        return self.load_utility_model()
    
    def unload_all_models(self) -> None:
        """Unload all models and clear cache."""
        log.info("Unloading all models...")
        
        # Clear embedder
        if self._embedder is not None:
            del self._embedder
            self._embedder = None
        
        # Clear all models
        for model_key in list(self._models.keys()):
            if model_key in self._models:
                del self._models[model_key]
        
        # Clear GPU cache
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        log.info("✓ All models unloaded")

# Global model manager instance
_model_manager = ModelManager()

# Legacy functions for backward compatibility
@lru_cache(maxsize=1)
def utility_llm() -> Tuple[Any, Any]:
    """Legacy function - use model manager instead."""
    return _model_manager.get_generator_model()

@lru_cache(maxsize=1)
def generator_llm() -> Tuple[Any, Any]:
    """Legacy function - use model manager instead."""
    return _model_manager.get_generator_model()

@lru_cache(maxsize=1)
def reasoning_llm() -> Tuple[Any, Any]:
    """Legacy function - use model manager instead."""
    return _model_manager.get_generator_model()

@lru_cache(maxsize=1)
def retriever_llm() -> Tuple[Any, Any]:
    """Legacy function - use model manager instead."""
    return _model_manager.get_generator_model()

@lru_cache(maxsize=1)
def reasoner_llm() -> Tuple[Any, Any]:
    """Legacy function - use model manager instead."""
    return _model_manager.get_generator_model()

@lru_cache(maxsize=1)
def embedder() -> Tuple[Any, Any]:
    """Legacy function - use model manager instead."""
    return _model_manager.get_embedder()

def get_model_info() -> dict:
    """Get information about loaded models and memory usage."""
    return _model_manager.get_memory_usage()

def unload_models():
    """Unload all models and clear cache."""
    _model_manager.unload_all_models()

def load_models_progressively() -> dict:
    """
    DEPRECATED: Models are now loaded lazily on first use.
    This function returns a status indicating lazy loading is enabled.
    """
    log.info("LAZY LOADING MODE: No models loaded at startup")
    log.info("Models will be loaded on first use to reduce memory pressure")
    
    return {
        "embedder": False,
        "utility": False, 
        "generator": False,
        "memory_usage": {},
        "errors": [],
        "lazy_loading": True,
        "message": "Models will be loaded on first use"
    }

def warmup_models():
    """DEPRECATED: Models are now loaded lazily on first use."""
    log.info("LAZY LOADING MODE: No model warmup - models load on first use")
    return True

def verify_models():
    """Verify that models can be loaded successfully (lazy loading)."""
    results = {
        "utility": False,
        "reasoning": False,
        "embedder": False,
        "errors": [],
        "lazy_loading": True
    }
    
    try:
        # Test embedder loading
        _ = _model_manager.get_embedder()
        results["embedder"] = True
        log.info("✓ Embedder model verification passed")
    except Exception as e:
        results["errors"].append(f"Embedder: {e}")
        log.error(f"✗ Embedder model verification failed: {e}")
    
    try:
        # Test generator model loading
        _ = _model_manager.get_generator_model()
        results["reasoning"] = True
        log.info("✓ Generator model verification passed")
    except Exception as e:
        results["errors"].append(f"Generator: {e}")
        log.error(f"✗ Generator model verification failed: {e}")
    
    # Utility model is deprecated
    results["utility"] = False
    log.info("Utility model deprecated - using main model instead")
    
    return results

def get_loading_status() -> dict:
    """Get detailed model loading status and recommendations."""
    status = _model_manager.get_memory_status()
    from .hardware import get_memory_info
    memory_info = get_memory_info()
    
    # Add loading recommendations for lazy loading
    recommendations = []
    
    if not status["models_loaded"]["embedder"]:
        recommendations.append("Embedder will load on first use")
    
    if not status["models_loaded"]["generator"]:
        recommendations.append("Main Mistral-7B model will load on first use")
    
    if memory_info.get("gpu_allocated_gb", 0) > 7.0:
        recommendations.append("High GPU memory usage - consider unloading unused models")
    
    status["recommendations"] = recommendations
    status["memory_info"] = memory_info
    status["lazy_loading"] = True
    
    return status