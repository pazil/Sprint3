"""
Test OpenAI API - Responses Format (from openai_reference.py)
Tests the responses.create() endpoint with gpt-5-nano
"""

from openai import OpenAI
from dotenv import load_dotenv
import os
import json

# Load environment variables from .env file (override system env vars)
load_dotenv(override=True)

# === CONFIGURATION ===
MODEL = "gpt-5-nano"  # Change this to test different models: "gpt-5-nano", "gpt-5", "gpt-4o"
# =====================

print("="*70)
print(f"Testing OpenAI API - RESPONSES Format")
print(f"Model: {MODEL}")
print("="*70)

# Check API key
api_key = os.getenv('OPENAI_API_KEY')
print(f"\n1. API Key Check:")
if api_key:
    print(f"   ✓ API Key found")
    print(f"   Prefix: {api_key[:20]}...")
    print(f"   Length: {len(api_key)} chars")
else:
    print(f"   ❌ No API key in .env")
    exit(1)

# Initialize OpenAI client with API key from environment
print(f"\n2. Initializing client...")
client = OpenAI(api_key=api_key)
print(f"   ✓ Client initialized")

# Test API call using responses.create() format
print(f"\n3. Testing responses.create() with {MODEL}...")
try:
    response = client.responses.create(
        model=MODEL,
        input=[
            {
                "role": "developer",
                "content": [
                    {
                        "type": "input_text",
                        "text": "You are a helpful assistant that returns JSON only."
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": "Say hello in JSON format with key 'message'"
                    }
                ]
            }
        ],
        text={
            "format": {
                "type": "json_object"
            },
            "verbosity": "medium"
        },
        reasoning={
            "effort": "medium",
            "summary": "auto"
        },
        tools=[],
        store=False,
        include=[
            "reasoning.encrypted_content",
            "web_search_call.action.sources"
        ]
    )
    
    print(f"   ✓ API call successful!")
    print(f"   Response type: {type(response)}")
    
    # Parse response
    result = json.loads(response.text.content)
    print(f"   Response content: {result}")
    
    print("\n" + "="*70)
    print(f"✅ SUCCESS - responses.create() works with {MODEL}!")
    print("="*70)
    
except Exception as e:
    print(f"   ❌ API call failed")
    print(f"\n   Error type: {type(e).__name__}")
    print(f"   Error message: {str(e)}")
    
    # Diagnose the issue
    error_str = str(e).lower()
    
    if "quota" in error_str or "429" in str(e):
        print(f"\n   💡 QUOTA/BILLING ISSUE:")
        print(f"      Account has no credits")
        print(f"      Add credits: https://platform.openai.com/account/billing")
        
    elif "not found" in error_str or "model" in error_str:
        print(f"\n   💡 MODEL ISSUE:")
        print(f"      {MODEL} may not be available on your account")
        print(f"      Try changing MODEL variable to:")
        print(f"      - 'gpt-4o'")
        print(f"      - 'gpt-4o-mini'")
        
    elif "authentication" in error_str or "401" in str(e):
        print(f"\n   💡 AUTH ISSUE:")
        print(f"      API key may be invalid")
        
    else:
        print(f"\n   💡 OTHER ISSUE:")
        print(f"      Check OpenAI status: https://status.openai.com/")
    
    print("\n" + "="*70)
    print("❌ TEST FAILED")
    print("="*70)
    exit(1)

print(f"\n✅ This API format works for your account!")
print(f"   You can use responses.create() with {MODEL}")

