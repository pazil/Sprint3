"""
Test OpenAI API - VALIDATED Simple Format
Based on your working Google Colab code
"""

from openai import OpenAI
from dotenv import load_dotenv
import os

# Load environment variables from .env file (override system env vars)
load_dotenv(override=True)

# === CONFIGURATION ===
MODEL = "gpt-5-nano"  # Change this to test: "gpt-5-nano", "gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"
# =====================

print("="*70)
print(f"Testing OpenAI API - VALIDATED Simple Format")
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

# Initialize OpenAI client
print(f"\n2. Initializing client...")
try:
    client = OpenAI(api_key=api_key)
    print(f"   ✓ Client initialized")
except Exception as e:
    print(f"   ❌ Failed: {e}")
    exit(1)

# Test API call using VALIDATED simple format
print(f"\n3. Testing chat.completions.create() with {MODEL}...")
print(f"   Using SIMPLE message format (validated working code)")
try:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "Você é um assistente prestativo."},
            {"role": "user", "content": "Me diga uma curiosidade sobre o espaço."}
        ]
    )
    
    print(f"   ✓ API call successful!")
    print(f"   Model used: {response.model}")
    print(f"   Tokens: {response.usage.total_tokens}")
    print(f"   Response: {response.choices[0].message.content[:200]}...")
    
    print("\n" + "="*70)
    print(f"✅ SUCCESS - {MODEL} works with simple format!")
    print("="*70)
    print(f"\n✅ Your pipeline is ready to run!")
    print(f"   Model to use: {MODEL}")
    print(f"   Run: python quick_start.py")
    
except Exception as e:
    print(f"   ❌ API call failed")
    print(f"\n   Error type: {type(e).__name__}")
    print(f"   Error: {str(e)[:200]}")
    
    # Diagnose
    error_str = str(e).lower()
    
    if "quota" in error_str or "429" in str(e):
        print(f"\n   💡 QUOTA ISSUE:")
        print(f"      Add credits: https://platform.openai.com/account/billing")
        
    elif "not found" in error_str or "does not exist" in error_str:
        print(f"\n   💡 MODEL UNAVAILABLE:")
        print(f"      '{MODEL}' not accessible")
        print(f"      Edit line 14, try:")
        print(f"      MODEL = \"gpt-4o-mini\"  # Cheapest, most compatible")
        print(f"      MODEL = \"gpt-4o\"       # Higher quality")
        
    elif "authentication" in error_str or "401" in str(e):
        print(f"\n   💡 AUTH ISSUE:")
        print(f"      API key invalid")
    
    exit(1)
