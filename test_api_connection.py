"""
Test OpenAI API Connection
Debug script to verify API key and model availability
"""

from openai import OpenAI
from dotenv import load_dotenv
import os
import json

# Load environment (override system env vars)
load_dotenv(override=True)

print("="*70)
print("OpenAI API Connection Test")
print("="*70)

# Check .env loading
print("\n1. Checking .env file...")
api_key = os.getenv('OPENAI_API_KEY')

if api_key:
    print(f"   ✓ API Key found")
    print(f"   Key prefix: {api_key[:20]}...")
    print(f"   Key length: {len(api_key)} characters")
else:
    print(f"   ❌ No API key found!")
    print(f"   Make sure .env file exists with OPENAI_API_KEY=your_key")
    exit(1)

# Initialize client
print("\n2. Initializing OpenAI client...")
try:
    client = OpenAI(api_key=api_key)
    print(f"   ✓ Client initialized")
except Exception as e:
    print(f"   ❌ Failed to initialize: {e}")
    exit(1)

# Test with standard chat API first (to verify key works)
print("\n3. Testing with standard chat.completions API...")
try:
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # Standard model
        messages=[
            {"role": "user", "content": "Say 'API working' in one word"}
        ],
        max_tokens=10
    )
    print(f"   ✓ Standard API works!")
    print(f"   Response: {response.choices[0].message.content}")
except Exception as e:
    print(f"   ❌ Standard API failed: {e}")
    print(f"\n   This indicates an issue with your API key or account")
    exit(1)

# Test with chat.completions API using gpt-5 (the one we're using)
print("\n4. Testing with gpt-5 and developer role...")
try:
    response = client.chat.completions.create(
        model="gpt-5",
        messages=[
            {
                "role": "developer",
                "content": [
                    {
                        "type": "text",
                        "text": "You are a helpful assistant. Return JSON only."
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Say 'hello' in JSON format: {\"message\": \"hello\"}"
                    }
                ]
            }
        ],
        response_format={
            "type": "json_object"
        }
    )
    print(f"   ✓ gpt-5 with developer role works!")
    print(f"   Response: {response.choices[0].message.content[:100]}")
except Exception as e:
    print(f"   ❌ gpt-5 API failed: {e}")
    print(f"\n   Error type: {type(e).__name__}")
    
    if "quota" in str(e).lower():
        print(f"\n   💡 QUOTA ISSUE:")
        print(f"      Your API key is valid but account has no credits")
        print(f"      Action: Add credits at https://platform.openai.com/account/billing")
    elif "model" in str(e).lower() or "not found" in str(e).lower():
        print(f"\n   💡 MODEL ISSUE:")
        print(f"      'gpt-5' may not be available on your account")
        print(f"      Try: Update model to 'gpt-4o-mini' in pipeline files")
        print(f"      Location: pipeline/02_llm_product_analyzer.py line 50")
        print(f"                pipeline/03_llm_review_analyzer.py line 64")
    elif "authentication" in str(e).lower():
        print(f"\n   💡 AUTH ISSUE:")
        print(f"      API key may be invalid")
        print(f"      Verify key at: https://platform.openai.com/api-keys")
    
    exit(1)

print("\n" + "="*70)
print("✅ ALL TESTS PASSED - API is working correctly!")
print("="*70)
print("\nYou can now run: python quick_start.py")

