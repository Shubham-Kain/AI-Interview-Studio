import os
from dotenv import load_dotenv

# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================
load_dotenv()

# =========================================================
# API KEY & PROVIDER CONFIG
# Supports OpenRouter (default) OR Groq (free, 14,400 req/day)
# =========================================================
GROQ_API_KEY = (os.environ.get("GROQ_API_KEY") or "").strip()
OPENROUTER_API_KEY = (
    os.environ.get("OPENROUTER_API_KEY")
    or GROQ_API_KEY
    or ""
).strip()

# Base URL: OpenRouter or Groq
if os.environ.get("OPENROUTER_BASE_URL"):
    OPENROUTER_BASE_URL = os.environ.get("OPENROUTER_BASE_URL").strip()
elif GROQ_API_KEY and not os.environ.get("OPENROUTER_API_KEY"):
    OPENROUTER_BASE_URL = "https://api.groq.com/openai/v1"
else:
    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Model Selection
if os.environ.get("OPENROUTER_MODEL"):
    MODEL_NAME = os.environ.get("OPENROUTER_MODEL").strip()
elif "groq.com" in OPENROUTER_BASE_URL:
    MODEL_NAME = "llama-3.3-70b-versatile"
else:
    MODEL_NAME = "nvidia/nemotron-3-nano-30b-a3b:free"

# =========================================================
# VALIDATION — warn only at import time, raise at request time
# =========================================================
if not OPENROUTER_API_KEY:
    import warnings
    warnings.warn(
        "No API key set (OPENROUTER_API_KEY or GROQ_API_KEY). "
        "API requests will fail until a key is provided.",
        stacklevel=2,
    )