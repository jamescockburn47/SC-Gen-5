"""
Hardware runtime tweaks for Legion 5 Pro optimization.
Init CUDA / CPU knobs once, then import everywhere.
"""

from __future__ import annotations
import os
import torch
import faiss
import logging
from typing import Dict

log = logging.getLogger("lexcognito.rag.v2")

def init_hardware() -> tuple[dict, dict]:
    """
    Initialize hardware settings optimized for Legion 5 Pro:
    - 8GB RTX GPU with CUDA
    - 64GB RAM 
    - 8-core mobile Ryzen CPU
    
    Returns device maps for utility and reasoning models.
    """
    
    # ----- CPU Optimization -------------------------------------------------
    os.environ.setdefault("OMP_NUM_THREADS", "8")      # torch & faiss optimal for 8-core
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")  # avoid deadlocks
    os.environ.setdefault("FAISS_NUM_THREADS", "8")
    
    # Set FAISS thread count for optimal performance
    try:
        faiss.omp_set_num_threads(8)  # fastest on 8-core mobile Ryzen
    except AttributeError:
        log.warning("FAISS OMP thread setting not available")
    
    torch.set_num_threads(8)
    
    # ----- GPU Optimization for Legion 5 Pro RTX -------------------------
    if torch.cuda.is_available():
        # Get GPU properties
        gpu_props = torch.cuda.get_device_properties(0)
        gpu_name = gpu_props.name.lower()
        
        # Legion 5 Pro specific optimizations
        if "rtx" in gpu_name or "geforce" in gpu_name:
            # Enable TensorFloat-32 for RTX GPUs (significant speedup)
            torch.backends.cuda.matmul.allow_tf32 = True
            torch.backends.cudnn.allow_tf32 = True
            
            # Enable cuDNN benchmark for consistent input sizes
            torch.backends.cudnn.benchmark = True
            
            # Optimize memory allocation for 8GB VRAM
            if gpu_props.total_memory < 10 * (1024**3):  # Less than 10GB (8GB GPU)
                torch.cuda.set_per_process_memory_fraction(0.85)  # More conservative for 8GB
                log.info("8GB GPU detected: using 85% memory fraction")
            else:
                torch.cuda.set_per_process_memory_fraction(0.9)
            
            # Legion 5 Pro RTX optimizations
            os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "max_split_size_mb:512,expandable_segments:True")
        else:
            # General GPU optimizations
            torch.backends.cuda.matmul.allow_tf32 = True
            torch.backends.cudnn.benchmark = True
            torch.cuda.set_per_process_memory_fraction(0.9)
        
        # Clear any existing cache
        torch.cuda.empty_cache()
        
        # Optimized environment variables
        os.environ.setdefault("CUDA_VISIBLE_DEVICES", "0")  # Use first GPU only
        os.environ.setdefault("CUDA_LAUNCH_BLOCKING", "0")  # Async execution
        os.environ.setdefault("TORCH_CUDNN_V8_API_ENABLED", "1")  # Enable latest cuDNN
        
        # Model-specific optimizations
        os.environ.setdefault("TRANSFORMERS_CACHE", "/tmp/hf_cache")  # Fast SSD cache
        os.environ.setdefault("HF_HUB_CACHE", "/tmp/hf_cache")
        
        log.info(f"GPU optimization enabled for {gpu_name}: TF32, cuDNN benchmark, memory optimized")
    else:
        log.warning("CUDA not available, falling back to CPU")
    
    # ----- Model Device Maps ------------------------------------------------
    # Device maps for GPTQ loaders - both on same GPU for Legion 5 Pro
    utility_map = "auto" if torch.cuda.is_available() else "cpu"    # Let transformers handle mapping
    reasoner_map = "auto" if torch.cuda.is_available() else "cpu"   # Let transformers handle mapping
    
    # ----- Memory and Performance Logging -----------------------------------
    if torch.cuda.is_available():
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)  # GB
        log.info(f"Hardware initialized: threads=8, TF32 enabled, GPU memory={gpu_memory:.1f}GB")
        log.info("exLLaMA kernels enabled for quantized models")
    else:
        log.info("Hardware initialized: CPU-only mode, threads=8")
    
    return utility_map, reasoner_map

def get_memory_info() -> Dict[str, float]:
    """Get current memory usage statistics."""
    info = {}
    
    if torch.cuda.is_available():
        info["gpu_allocated"] = torch.cuda.memory_allocated() / (1024**3)  # GB
        info["gpu_cached"] = torch.cuda.memory_reserved() / (1024**3)      # GB
        info["gpu_total"] = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        info["gpu_free"] = info["gpu_total"] - info["gpu_allocated"]
    else:
        info["gpu_allocated"] = 0
        info["gpu_cached"] = 0
        info["gpu_total"] = 0
        info["gpu_free"] = 0
    
    return info

def clear_gpu_cache():
    """Clear GPU memory cache."""
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        log.info("GPU cache cleared")

def set_inference_mode():
    """Set optimal settings for inference."""
    torch.set_grad_enabled(False)  # Disable gradients for inference
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    log.info("Inference mode enabled")

def check_hardware_requirements():
    """Check if hardware meets minimum requirements."""
    requirements_met = True
    warnings = []
    
    if not torch.cuda.is_available():
        warnings.append("CUDA not available - performance will be degraded")
        requirements_met = False
    
    if torch.cuda.is_available():
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        if gpu_memory < 6:  # Minimum 6GB for quantized models
            warnings.append(f"GPU memory ({gpu_memory:.1f}GB) below recommended 8GB")
            requirements_met = False
    
    cpu_count = os.cpu_count() or 1
    if cpu_count < 6:
        warnings.append(f"CPU cores ({cpu_count}) below recommended 8 cores")
    
    if warnings:
        for warning in warnings:
            log.warning(warning)
    
    return requirements_met, warnings

# Initialize hardware on module import
try:
    _utility_device_map, _reasoner_device_map = init_hardware()
    _hardware_initialized = True
    log.info("Hardware initialization completed successfully")
except Exception as e:
    log.error(f"Hardware initialization failed: {e}")
    _utility_device_map = {"": "cpu"}
    _reasoner_device_map = {"": "cpu"}
    _hardware_initialized = False

# Export device maps for use in models.py
utility_device_map = _utility_device_map
reasoner_device_map = _reasoner_device_map
hardware_initialized = _hardware_initialized