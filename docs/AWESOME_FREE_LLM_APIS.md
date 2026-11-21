# Awesome Free LLM APIs Guide

Curated from [open-free-llm-api/awesome-freellm-apis](https://github.com/open-free-llm-api/awesome-freellm-apis).

This project includes built-in, native support for permanent and generous free-tier LLM providers. You can add one or multiple providers directly in the **AI providers** tab of the web app or via the command line.

When multiple providers are added, the system automatically falls over from top to bottom if one hits rate limits or undergoes cooldown.

---

## 1. Top Free Tier Providers Directory

| Provider | Base URL | Best Free Models | Rate Limit | Free Key Signup |
| :--- | :--- | :--- | :--- | :--- |
| **Google Gemini** | `https://generativelanguage.googleapis.com/v1beta/openai` | `gemini-2.5-flash`, `gemini-2.5-flash-lite`, `gemini-2.0-flash` | 15 RPM / 1500 RPD | [Get Key](https://aistudio.google.com/apikey) |
| **Groq** | `https://api.groq.com/openai/v1` | `llama-3.3-70b-versatile`, `llama-3.1-8b-instant` | 30 RPM / 14,400 RPD (~300 tok/s) | [Get Key](https://console.groq.com/keys) |
| **SambaNova Cloud** | `https://api.sambanova.ai/v1` | `Meta-Llama-3.3-70B-Instruct`, `Qwen2.5-72B-Instruct` | 20 RPM (Ultra-fast SN40L) | [Get Key](https://cloud.sambanova.ai/apis) |
| **Cerebras** | `https://api.cerebras.ai/v1` | `llama3.3-70b`, `llama3.1-8b` | 30 RPM (~1000 tok/s) | [Get Key](https://cloud.cerebras.ai) |
| **GitHub Models** | `https://models.inference.ai.azure.com` | `gpt-4o-mini`, `Meta-Llama-3.3-70B-Instruct` | 15 RPM / 150 RPD | [Get Key](https://github.com/marketplace/models) |
| **NVIDIA NIM** | `https://integrate.api.nvidia.com/v1` | `meta/llama-3.3-70b-instruct`, `deepseek-ai/deepseek-r1` | 40 RPM (1,000 requests) | [Get Key](https://build.nvidia.com) |
| **Mistral AI** | `https://api.mistral.ai/v1` | `mistral-small-latest`, `codestral-latest` | 1 req/sec (~1B tokens/mo) | [Get Key](https://console.mistral.ai/api-keys) |
| **OpenRouter** | `https://openrouter.ai/api/v1` | `meta-llama/llama-3.3-70b-instruct:free`, `deepseek/deepseek-r1:free` | 20 RPM | [Get Key](https://openrouter.ai/keys) |
| **Cohere** | `https://api.cohere.ai/compatibility/v1` | `command-r`, `command-r-plus`, `aya-expanse-32b` | 20 RPM (1,000 req/mo) | [Get Key](https://dashboard.cohere.com/api-keys) |
| **Together AI** | `https://api.together.xyz/v1` | `meta-llama/Llama-3.3-70B-Instruct-Turbo` | 10 RPM (Trial tier) | [Get Key](https://api.together.xyz/settings/api-keys) |
| **DeepInfra** | `https://api.deepinfra.com/v1/openai` | `meta-llama/Meta-Llama-3.3-70B-Instruct` | 10 RPM (Serverless tier) | [Get Key](https://deepinfra.com/dash/api_keys) |
| **Hyperbolic** | `https://api.hyperbolic.xyz/v1` | `meta-llama/Llama-3.3-70B-Instruct` | 10 RPM (Decentralized) | [Get Key](https://app.hyperbolic.xyz) |
| **Hugging Face** | `https://api-inference.huggingface.co/v1` | `meta-llama/Llama-3.2-3B-Instruct`, `Qwen/Qwen2.5-72B-Instruct` | 10 RPM (Community token) | [Get Key](https://huggingface.co/settings/tokens) |
| **Ollama (Local)** | `http://localhost:11434/v1` | `qwen2.5:3b`, `llama3.2:3b` | Unlimited (Offline on CPU/GPU) | *No key needed* |

---

## 2. Setup in the Web UI

1. Open the web app at `http://localhost:5173` (or your deployed URL).
2. Go to **AI providers**.
3. Under **Add an AI provider (Free Tier Catalog)**:
   - Select any provider from the **Start from** dropdown.
   - Click the **Get free API key on [Provider] ↗** link that appears.
   - Create your free API key on the provider's dashboard without a credit card.
   - Paste the API key and click **Add provider**.
4. Click **Test** next to the added provider to verify that it answers immediately!

---

## 3. Setup via CLI Script

A CLI script is provided to explore, test, and register free providers directly:

```bash
cd backend

# List all providers and their free limits
python scripts/setup_free_apis.py list

# Test an API key without modifying the database
python scripts/setup_free_apis.py test groq gsk_your_groq_api_key_here
python scripts/setup_free_apis.py test gemini your_gemini_api_key_here

# Add a provider directly to MongoDB
python scripts/setup_free_apis.py add groq gsk_your_groq_api_key_here --priority 10
python scripts/setup_free_apis.py add gemini your_gemini_api_key_here --priority 20
```

---

## 4. Recommended Setup for 24/7 Zero-Downtime Free Answering

Chain providers in this priority order in the UI:
1. **Groq** (`llama-3.3-70b-versatile`): Ultra-fast primary responder (300 tok/s).
2. **Google Gemini** (`gemini-2.5-flash`): High accuracy, multimodal & Hindi/Hinglish comprehension.
3. **SambaNova Cloud** (`Meta-Llama-3.3-70B-Instruct`): Backup 70B inference engine.
4. **Cerebras** (`llama3.3-70b`): Secondary hardware-accelerated backup.
5. **Ollama** (`qwen2.5:3b`): Local offline fallback (answers even if internet is down).
