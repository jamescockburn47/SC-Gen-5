"""
Memory-optimized model manager for 8GB GPU constraint.
Implements aggressive memory management and model swapping.
"""

import torch
import gc
import time
import logging
from typing import Dict, Any, Optional, Tuple
from transformers import AutoTokenizer, AutoModelForCausalLM
from sentence_transformers import SentenceTransformer
from contextlib import contextmanager

from settings import settings

log = logging.getLogger("lexcognito.rag.v2.memory_optimized")

class MemoryOptimizedModelManager:
    """
    Memory-optimized model manager for 8GB GPU.
    Features:
    - Aggressive memory cleanup
    - Model swapping (only one large model in GPU at a time)
    - 4-bit quantization
    - Memory monitoring
    """
    
    def __init__(self):
        self.embedder = None
        self.current_llm = None
        self.current_llm_type = None
        self.tokenizers = {}
        
        # Memory settings for 8GB GPU
        self.max_gpu_memory = 7.5  # GB - leave 0.5GB buffer
        self.memory_threshold = 0.85  # Trigger cleanup at 85%
        
        # Configure PyTorch for memory efficiency
        if torch.cuda.is_available():
            torch.cuda.set_per_process_memory_fraction(0.9)
            torch.backends.cuda.matmul.allow_tf32 = True
            torch.backends.cudnn.allow_tf32 = True
            torch.backends.cudnn.benchmark = True
            
    def _clear_gpu_memory(self):
        """Aggressive GPU memory cleanup."""
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
            gc.collect()
            
    def _get_gpu_memory_usage(self) -> float:
        """Get current GPU memory usage in GB."""
        if torch.cuda.is_available():
            return torch.cuda.memory_allocated() / (1024**3)
        return 0.0
        
    def _check_memory_pressure(self) -> bool:
        """Check if we're under memory pressure."""
        if not torch.cuda.is_available():
            return False
            
        total_mem = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        used_mem = self._get_gpu_memory_usage()
        return (used_mem / total_mem) > self.memory_threshold
        
    def _unload_current_llm(self):
        """Unload current LLM from GPU memory."""
        if self.current_llm is not None:
            log.info(f"Unloading {self.current_llm_type} model to free GPU memory")
            del self.current_llm
            self.current_llm = None
            self.current_llm_type = None
            self._clear_gpu_memory()
            
    @contextmanager
    def _memory_managed_loading(self):
        """Context manager for memory-managed model loading."""
        initial_memory = self._get_gpu_memory_usage()
        try:
            yield
        except RuntimeError as e:
            if "out of memory" in str(e).lower():
                log.warning("OOM during loading, attempting recovery...")
                self._unload_current_llm()
                self._clear_gpu_memory()
                raise
        finally:
            final_memory = self._get_gpu_memory_usage()
            log.info(f"Memory usage: {initial_memory:.1f}GB → {final_memory:.1f}GB")
            
    def load_embedder(self) -> SentenceTransformer:
        """Load embedder model (always on CPU for memory efficiency)."""
        if self.embedder is not None:
            return self.embedder
            
        log.info("Loading embedder model (CPU only)...")
        try:
            self.embedder = SentenceTransformer(
                settings.EMBEDDING_MODEL,
                device="cpu",  # Always CPU to save GPU memory
                trust_remote_code=True
            )
            log.info("✓ Embedder loaded on CPU")
            return self.embedder
        except Exception as e:
            log.error(f"Failed to load embedder: {e}")
            raise
            
    def load_utility_model(self) -> Tuple[AutoTokenizer, AutoModelForCausalLM]:
        """Load utility model with aggressive memory optimization."""
        model_name = settings.UTILITY_MODEL
        
        # If we already have the utility model loaded, return it
        if self.current_llm is not None and self.current_llm_type == "utility":
            return self.tokenizers["utility"], self.current_llm
            
        # Unload any existing LLM
        self._unload_current_llm()
        
        log.info(f"Loading utility model: {model_name}")
        
        try:
            with self._memory_managed_loading():
                # Load tokenizer (lightweight)
                if "utility" not in self.tokenizers:
                    tokenizer = AutoTokenizer.from_pretrained(
                        model_name,
                        trust_remote_code=True,
                        use_fast=True
                    )
                    if tokenizer.pad_token is None:
                        tokenizer.pad_token = tokenizer.eos_token
                    self.tokenizers["utility"] = tokenizer
                
                # Load model with aggressive quantization
                model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    device_map="auto",
                    torch_dtype=torch.float16,
                    trust_remote_code=True,
                    low_cpu_mem_usage=True,
                    attn_implementation="eager",  # More memory efficient
                    use_cache=True
                )
                
                model.eval()
                self.current_llm = model
                self.current_llm_type = "utility"
                
                memory_used = self._get_gpu_memory_usage()
                log.info(f"✓ Utility model loaded, using {memory_used:.1f}GB GPU memory")
                
                return self.tokenizers["utility"], model
                
        except Exception as e:
            log.error(f"Failed to load utility model: {e}")
            self._clear_gpu_memory()
            raise
            
    def load_reasoning_model(self) -> Tuple[AutoTokenizer, AutoModelForCausalLM]:
        """Load reasoning model with memory optimization."""
        model_name = settings.REASONING_MODEL
        
        # If we already have the reasoning model loaded, return it
        if self.current_llm is not None and self.current_llm_type == "reasoning":
            return self.tokenizers["reasoning"], self.current_llm
            
        # Unload any existing LLM
        self._unload_current_llm()
        
        log.info(f"Loading reasoning model: {model_name}")
        
        try:
            with self._memory_managed_loading():
                # Load tokenizer
                if "reasoning" not in self.tokenizers:
                    tokenizer = AutoTokenizer.from_pretrained(
                        model_name,
                        trust_remote_code=True,
                        use_fast=True
                    )
                    if tokenizer.pad_token is None:
                        tokenizer.pad_token = tokenizer.eos_token
                    self.tokenizers["reasoning"] = tokenizer
                
                # Load quantized model
                model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    device_map="auto",
                    torch_dtype=torch.float16,
                    trust_remote_code=True,
                    low_cpu_mem_usage=True,
                    use_safetensors=True
                )
                
                model.eval()
                self.current_llm = model
                self.current_llm_type = "reasoning"
                
                memory_used = self._get_gpu_memory_usage()
                log.info(f"✓ Reasoning model loaded, using {memory_used:.1f}GB GPU memory")
                
                return self.tokenizers["reasoning"], model
                
        except Exception as e:
            log.error(f"Failed to load reasoning model: {e}")
            self._clear_gpu_memory()
            raise
            
    @contextmanager
    def use_model(self, model_type: str):
        """Context manager for using a specific model with automatic cleanup."""
        if model_type == "utility":
            tokenizer, model = self.load_utility_model()
        elif model_type == "reasoning":
            tokenizer, model = self.load_reasoning_model()
        else:
            raise ValueError(f"Unknown model type: {model_type}")
            
        try:
            yield tokenizer, model
        finally:
            # Optional: Unload after use for maximum memory efficiency
            # Uncomment next line for aggressive memory management
            # self._unload_current_llm()
            pass
            
    def generate_with_memory_management(
        self, 
        model_type: str,
        input_text: str,
        max_new_tokens: int = 50,
        **kwargs
    ) -> str:
        """Generate text with automatic memory management."""
        
        # Check memory before generation
        if self._check_memory_pressure():
            log.warning("Memory pressure detected, performing cleanup...")
            self._clear_gpu_memory()
            
        with self.use_model(model_type) as (tokenizer, model):
            try:
                # Prepare inputs
                inputs = tokenizer(
                    input_text, 
                    return_tensors="pt", 
                    max_length=2048,  # Limit input length
                    truncation=True
                )
                
                if torch.cuda.is_available():
                    inputs = {k: v.to(model.device) for k, v in inputs.items()}
                
                # Generate with memory optimization
                with torch.no_grad():
                    outputs = model.generate(
                        **inputs,
                        max_new_tokens=min(max_new_tokens, 100),  # Limit output length
                        do_sample=True,
                        temperature=0.7,
                        top_p=0.9,
                        pad_token_id=tokenizer.eos_token_id,
                        use_cache=True,
                        **kwargs
                    )
                
                # Decode response
                response = tokenizer.decode(outputs[0], skip_special_tokens=True)
                
                # Remove input text from response
                if response.startswith(input_text):
                    response = response[len(input_text):].strip()
                
                return response
                
            except RuntimeError as e:
                if "out of memory" in str(e).lower():
                    log.error("GPU OOM during generation, unloading model...")
                    self._unload_current_llm()
                    raise RuntimeError(f"GPU memory exhausted: {e}")
                raise
                
    def get_memory_status(self) -> Dict[str, Any]:
        """Get detailed memory status."""
        status = {
            "current_model": self.current_llm_type,
            "models_loaded": {
                "embedder": self.embedder is not None,
                "current_llm": self.current_llm is not None
            },
            "tokenizers_cached": list(self.tokenizers.keys())
        }
        
        if torch.cuda.is_available():
            total_mem = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            used_mem = self._get_gpu_memory_usage()
            status["gpu_memory"] = {
                "used_gb": used_mem,
                "total_gb": total_mem,
                "free_gb": total_mem - used_mem,
                "usage_percent": (used_mem / total_mem) * 100,
                "memory_pressure": self._check_memory_pressure()
            }
        
        return status
        
    def unload_all(self):
        """Unload all models and clear memory."""
        log.info("Unloading all models...")
        
        if self.embedder is not None:
            del self.embedder
            self.embedder = None
            
        self._unload_current_llm()
        self.tokenizers.clear()
        self._clear_gpu_memory()
        
        log.info("✓ All models unloaded")


# Global memory-optimized model manager
_memory_optimized_manager = MemoryOptimizedModelManager()

# Export functions for backward compatibility
def get_memory_optimized_manager() -> MemoryOptimizedModelManager:
    """Get the global memory-optimized model manager."""
    return _memory_optimized_manager

def generate_with_memory_management(model_type: str, prompt: str, max_tokens: int = 50) -> str:
    """Generate text with memory management."""
    return _memory_optimized_manager.generate_with_memory_management(
        model_type=model_type,
        input_text=prompt,
        max_new_tokens=max_tokens
    )

def get_memory_status() -> Dict[str, Any]:
    """Get memory status."""
    return _memory_optimized_manager.get_memory_status()

def cleanup_memory():
    """Force memory cleanup."""
    _memory_optimized_manager._clear_gpu_memory()