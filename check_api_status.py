#!/usr/bin/env python3
"""
API Key Status Checker and Model Updater
Tests API keys and updates to latest available models.
"""

import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_openai_status():
    """Check OpenAI API key and test latest models."""
    print("🔍 Checking OpenAI API Status...")
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found in .env")
        return False
    
    # Test with latest models
    models_to_test = [
        "gpt-4o-mini",
        "gpt-4o", 
        "gpt-4-turbo",
        "gpt-3.5-turbo"
    ]
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    for model in models_to_test:
        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": "Hello"}],
                    "max_tokens": 5
                },
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"✅ {model}: Available")
            else:
                error = response.json().get("error", {})
                print(f"❌ {model}: {error.get('message', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ {model}: Connection error - {str(e)}")
    
    return True

def check_gemini_status():
    """Check Google Gemini API key and test latest models."""
    print("\n🔍 Checking Google Gemini API Status...")
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GOOGLE_API_KEY not found in .env")
        return False
    
    # Test with latest models
    models_to_test = [
        "gemini-1.5-flash-latest",
        "gemini-1.5-flash",
        "gemini-1.5-pro-latest",
        "gemini-1.5-pro"
    ]
    
    for model in models_to_test:
        try:
            response = requests.post(
                "https://generativelanguage.googleapis.com/v1beta/models/" + model + ":generateContent",
                params={"key": api_key},
                json={
                    "contents": [{"parts": [{"text": "Hello"}]}],
                    "generationConfig": {
                        "maxOutputTokens": 5
                    }
                },
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"✅ {model}: Available")
            else:
                error = response.json().get("error", {})
                print(f"❌ {model}: {error.get('message', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ {model}: Connection error - {str(e)}")
    
    return True

def check_claude_status():
    """Check Anthropic Claude API key and test latest models."""
    print("\n🔍 Checking Anthropic Claude API Status...")
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not found in .env")
        return False
    
    # Test with latest models
    models_to_test = [
        "claude-3-5-sonnet-20241022",
        "claude-3-5-haiku-20241022", 
        "claude-3-5-opus-20241022",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307"
    ]
    
    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01"
    }
    
    for model in models_to_test:
        try:
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json={
                    "model": model,
                    "max_tokens": 5,
                    "messages": [{"role": "user", "content": "Hello"}]
                },
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"✅ {model}: Available")
            else:
                error = response.json().get("error", {})
                print(f"❌ {model}: {error.get('message', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ {model}: Connection error - {str(e)}")
    
    return True

def test_backend_integration():
    """Test the backend API integration."""
    print("\n🔍 Testing Backend Integration...")
    
    try:
        # Test health endpoint
        response = requests.get("http://localhost:8001/api/cloud-consultation/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend health check: OK")
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
        
        # Test providers endpoint
        response = requests.get("http://localhost:8001/api/cloud-consultation/providers", timeout=5)
        if response.status_code == 200:
            providers = response.json()
            print("✅ Providers endpoint: OK")
            for provider, status in providers.get("providers", {}).items():
                print(f"   - {provider}: {'✅ Available' if status.get('available') else '❌ Unavailable'}")
        else:
            print(f"❌ Providers endpoint failed: {response.status_code}")
            return False
        
        # Test consultation endpoint
        response = requests.post(
            "http://localhost:8001/api/cloud-consultation/consult",
            json={
                "question": "Test question",
                "provider": "openai",
                "max_tokens": 50
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Consultation endpoint: OK")
            print(f"   - Provider: {result.get('provider')}")
            print(f"   - Model: {result.get('model')}")
            print(f"   - Processing time: {result.get('processing_time', 0):.2f}s")
            if result.get('protocol_report'):
                print(f"   - Protocol compliance: {result['protocol_report'].get('overall_compliance', False)}")
        else:
            print(f"❌ Consultation endpoint failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Backend integration test failed: {e}")
        return False
    
    return True

def main():
    """Run all API status checks."""
    print("🧪 API Key Status Checker")
    print("=" * 50)
    
    # Check each provider
    openai_ok = check_openai_status()
    gemini_ok = check_gemini_status()
    claude_ok = check_claude_status()
    
    print("\n" + "=" * 50)
    print("📊 Summary:")
    print(f"OpenAI: {'✅ Available' if openai_ok else '❌ Not Available'}")
    print(f"Gemini: {'✅ Available' if gemini_ok else '❌ Not Available'}")
    print(f"Claude: {'✅ Available' if claude_ok else '❌ Not Available'}")
    
    # Test backend integration if backend is running
    print("\n" + "=" * 50)
    print("🔧 Backend Integration Test:")
    backend_ok = test_backend_integration()
    
    print("\n" + "=" * 50)
    print("✅ API Status Check Complete")
    
    if backend_ok:
        print("\n🎉 All systems operational!")
        print("The strategic protocols system is ready with updated models.")
    else:
        print("\n⚠️  Some issues detected. Please check the logs above.")

if __name__ == "__main__":
    main() 