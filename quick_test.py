#!/usr/bin/env python3
"""
Quick test for Mistral-7B GPU tensor handling.
"""

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

def quick_test():
    print("Quick GPU tensor test for Mistral-7B...")
    
    # Load model (should be cached now)
    model_name = "TheBloke/Mistral-7B-v0.1-GPTQ"
    
    print("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    print("Loading model...")
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        device_map="auto",
        torch_dtype=torch.float16,
        trust_remote_code=True,
        use_safetensors=True
    )
    
    print("✓ Model loaded!")
    
    # Test with GPU tensors
    prompt = "Hello"
    print(f"Testing with prompt: '{prompt}'")
    
    # Tokenize and move to GPU
    inputs = tokenizer(prompt, return_tensors="pt")
    print(f"Input device before: {inputs['input_ids'].device}")
    
    # Move to GPU
    inputs = {k: v.to("cuda") for k, v in inputs.items()}
    print(f"Input device after: {inputs['input_ids'].device}")
    
    # Generate
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=10,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id
        )
    
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    print(f"Response: {response}")
    
    print("✓ GPU tensor test successful!")

if __name__ == "__main__":
    quick_test() 