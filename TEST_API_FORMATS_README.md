# Testing OpenAI API Formats

You now have **two test scripts** to validate which API format and model work for your account.

---

## 🧪 Test Scripts

### 1. `test_api_responses_format.py`
Based on `openai_reference.py`
- Uses: `client.responses.create()`
- Default model: `gpt-5-nano`
- Format: Responses API with reasoning

**Configure model at line 16:**
```python
MODEL = "gpt-5-nano"  # Change to: "gpt-5", "gpt-4o", etc.
```

### 2. `test_api_chat_format.py`
Based on `updated_openai_reference.py`
- Uses: `client.chat.completions.create()`
- Default model: `gpt-4o`
- Format: Standard chat completions

**Configure model at line 16:**
```python
MODEL = "gpt-4o"  # Change to: "gpt-4o-mini", "gpt-3.5-turbo", etc.
```

---

## 🚀 How to Test

### Step 1: Test Chat Format (Most Likely to Work)

```bash
python test_api_chat_format.py
```

**If successful:**
```
✅ SUCCESS - chat.completions.create() works with gpt-4o!
```

**If quota error:**
```
❌ QUOTA/BILLING ISSUE
   Add credits: https://platform.openai.com/account/billing
```

**If model error:**
Edit line 16 in `test_api_chat_format.py`:
```python
MODEL = "gpt-4o-mini"  # Try cheaper model
```

Then run again.

### Step 2: Test Responses Format (Alternative)

```bash
python test_api_responses_format.py
```

This tests the newer responses API.

---

## 🔧 **Configuring Models**

### Available Models to Try:

**Most Common (Chat Format):**
- `gpt-4o` - Most capable, moderate cost
- `gpt-4o-mini` - Fast and cheap, good quality
- `gpt-3.5-turbo` - Cheapest, fast

**Newer Models (Responses Format):**
- `gpt-5-nano` - If available
- `gpt-5` - If available

### How to Change Model:

**Option 1: Edit the test script**
```python
# In test_api_chat_format.py line 16
MODEL = "gpt-4o-mini"  # Change this
```

**Option 2: Try each model until one works**
1. Start with `gpt-4o-mini` (most compatible)
2. If that fails, try `gpt-3.5-turbo`
3. If that works, you can use it for your pipeline

---

## 📋 **Testing Strategy**

### Recommended Order:

```bash
# Test 1: Try standard chat API with gpt-4o-mini
# Edit test_api_chat_format.py, set MODEL = "gpt-4o-mini"
python test_api_chat_format.py

# If successful → Update pipeline to use gpt-4o-mini
# If fails with quota → Add credits first
# If fails with model → Try gpt-3.5-turbo

# Test 2: Try chat API with gpt-4o
# Edit test_api_chat_format.py, set MODEL = "gpt-4o"
python test_api_chat_format.py

# Test 3: Try responses API with gpt-5
# Edit test_api_responses_format.py, set MODEL = "gpt-5"
python test_api_responses_format.py
```

---

## ✅ **Once a Test Passes**

### If `test_api_chat_format.py` succeeds with a model:

1. **Note which model worked** (e.g., `gpt-4o-mini`)

2. **Update pipeline files:**

```python
# Edit pipeline/02_llm_product_analyzer.py line 50
self.model = "gpt-4o-mini"  # Use the working model

# Edit pipeline/03_llm_review_analyzer.py line 64
self.model = "gpt-4o-mini"  # Use the working model
```

3. **Run your pipeline:**
```bash
python quick_start.py
```

### If `test_api_responses_format.py` succeeds:

You'll need to update the pipeline to use `responses.create()` instead of `chat.completions.create()` - but try chat format first (it's more standard).

---

## 🎯 **Quick Model Comparison**

| Model | Speed | Cost | Quality | Availability |
|-------|-------|------|---------|--------------|
| gpt-3.5-turbo | ⚡⚡⚡ | 💰 | ⭐⭐⭐ | ✅ High |
| gpt-4o-mini | ⚡⚡ | 💰💰 | ⭐⭐⭐⭐ | ✅ High |
| gpt-4o | ⚡ | 💰💰💰 | ⭐⭐⭐⭐⭐ | ✅ High |
| gpt-5-nano | ⚡⚡⚡ | 💰 | ⭐⭐⭐⭐ | ⚠️  Limited |
| gpt-5 | ⚡ | 💰💰💰💰 | ⭐⭐⭐⭐⭐ | ⚠️  Limited |

**Recommended for this project:** `gpt-4o-mini`
- Good balance of cost/quality
- Fast enough for 723 API calls
- Widely available
- Total cost: ~$0.30-0.50 for full pipeline

---

## 📊 **Expected Costs by Model**

For processing 229 products + 494 reviews (723 total calls):

| Model | Cost per 1K tokens | Estimated Total |
|-------|-------------------|-----------------|
| gpt-3.5-turbo | $0.0015 (in) / $0.002 (out) | ~$0.15-0.25 |
| gpt-4o-mini | $0.00015 (in) / $0.0006 (out) | ~$0.30-0.50 |
| gpt-4o | $0.0025 (in) / $0.01 (out) | ~$2.00-3.00 |

---

## 🔍 **Troubleshooting**

### Error: "insufficient_quota"
```
❌ Cause: No credits in account
✅ Fix: Add $5-10 at https://platform.openai.com/account/billing
```

### Error: "model_not_found"
```
❌ Cause: Model not available on your plan
✅ Fix: Change MODEL variable to "gpt-4o-mini" or "gpt-3.5-turbo"
```

### Error: "invalid_api_key"
```
❌ Cause: API key is wrong or expired
✅ Fix: Generate new key at https://platform.openai.com/api-keys
      Update .env file
```

---

## 📝 **Step-by-Step Testing Guide**

### Test 1: gpt-4o-mini (RECOMMENDED START)

```bash
# 1. Edit test_api_chat_format.py
#    Change line 16 to: MODEL = "gpt-4o-mini"

# 2. Run test
python test_api_chat_format.py

# 3. Check result
#    ✓ Success → Use gpt-4o-mini in pipeline
#    ❌ Quota → Add credits
#    ❌ Model → Try gpt-3.5-turbo
```

### Test 2: gpt-3.5-turbo (If gpt-4o-mini fails)

```bash
# 1. Edit test_api_chat_format.py
#    Change line 16 to: MODEL = "gpt-3.5-turbo"

# 2. Run test
python test_api_chat_format.py

# 3. If successful → Use gpt-3.5-turbo in pipeline
```

### Test 3: gpt-4o (If you have credits and want best quality)

```bash
# 1. Edit test_api_chat_format.py
#    Change line 16 to: MODEL = "gpt-4o"

# 2. Run test
python test_api_chat_format.py

# 3. If successful → Use gpt-4o in pipeline (higher cost but better)
```

---

## 🎯 **After Finding Working Model**

### Update Your Pipeline:

**File 1: `pipeline/02_llm_product_analyzer.py`**
```python
# Line 50 - change to your working model
self.model = "gpt-4o-mini"  # Or whatever worked
```

**File 2: `pipeline/03_llm_review_analyzer.py`**
```python
# Line 64 - change to your working model
self.model = "gpt-4o-mini"  # Or whatever worked
```

**Then run:**
```bash
python quick_start.py
```

---

## 💡 **Tips**

### For Development/Testing:
- Use `gpt-4o-mini` (cheap, fast, good quality)
- Temperature: 0.1 (consistent outputs)

### For Production:
- Use `gpt-4o` if budget allows (best quality)
- Use `gpt-4o-mini` for cost-effectiveness

### For Debugging:
- Lower `MAX_TOKENS` to save costs during testing
- Increase `temperature` slightly (0.2-0.3) for more creative parsing if needed

---

## 📞 **Quick Commands**

```bash
# Test chat format (most standard)
python test_api_chat_format.py

# Test responses format (newer)
python test_api_responses_format.py

# After finding working model, test pipeline
python quick_start.py

# Check which Python/pip you're using
which python
which pip
pip list | grep openai
```

---

## ✅ **Success Checklist**

- [ ] `.env` file has valid OPENAI_API_KEY
- [ ] Packages installed (openai 2.0.0)
- [ ] Test script runs without errors
- [ ] API returns JSON response
- [ ] Model updated in pipeline files
- [ ] `quick_start.py` runs successfully

**Once all checked:** You're ready for full pipeline! 🚀

