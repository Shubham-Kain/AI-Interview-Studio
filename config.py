import os
from dotenv import load_dotenv

# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================
load_dotenv()

# =========================================================
# OPENROUTER API KEY
# =========================================================
OPENROUTER_API_KEY = (
    os.environ.get("OPENROUTER_API_KEY") or ""
).strip()

OPENROUTER_BASE_URL = (
    "https://openrouter.ai/api/v1"
)

# =========================================================
# MODEL
# =========================================================
MODEL_NAME = (
    os.environ.get("OPENROUTER_MODEL")
    or "google/gemma-3-4b-it:free"
).strip()

# =========================================================
# VALIDATION — warn only at import time, raise at request time
# so the server can still start and Render health check passes.
# =========================================================
if not OPENROUTER_API_KEY:
    import warnings
    warnings.warn(
        "OPENROUTER_API_KEY is not set. "
        "API requests will fail until it is provided.",
        stacklevel=2,
    )