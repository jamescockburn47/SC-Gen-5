#!/usr/bin/env python3
"""
Quick test to measure CPU-only Mistral loading time.
"""

import torch
import time
import logging
from src.sc_gen5.rag.v2.models import _model_manager

# Set up logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

def quick_cpu_test():
    """Quick test of CPU-only Mistral loading time."""
    print("=== Quick CPU-Only Mistral Test ===")
    
    try:
        print("Loading Mistral on CPU only...")
        start_time = time.time()
        
        tok, model = _model_manager.get_reasoning_model(cpu_only=True)
        
        load_time = time.time() - start_time
        print(f"✓ Mistral loaded on CPU in {load_time:.2f} seconds")
        
        # Check device
        device = next(model.parameters()).device
        print(f"Model device: {device}")
        
        # Quick generation test
        print("Testing generation...")
        gen_start = time.time()
        
        inputs = tok("Hello, how are you?", return_tensors="pt")
        with torch.no_grad():
            outputs = model.generate(**inputs, max_new_tokens=20, do_sample=False)
        
        gen_time = time.time() - gen_start
        response = tok.decode(outputs[0], skip_special_tokens=True)
        print(f"Generation time: {gen_time:.2f}s")
        print(f"Response: {response}")
        
        return load_time, gen_time
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None, None

if __name__ == "__main__":
    load_time, gen_time = quick_cpu_test()
    if load_time:
        print(f"\nSummary:")
        print(f"Loading time: {load_time:.2f}s")
        print(f"Generation time: {gen_time:.2f}s")
        print(f"Tokens per second: {20/gen_time:.1f}") 