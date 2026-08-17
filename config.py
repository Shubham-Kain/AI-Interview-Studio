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
    or "dots-studio/dots-3-note-preview:free"
).strip()
# =========================================================
# VALIDATION
# =========================================================
if not OPENROUTER_API_KEY:
    raise ValueError(
        "OPENROUTER_API_KEY is missing. "
        "Add it to your .env file."
    )
if not MODEL_NAME:
    raise ValueError(
        "OPENROUTER_MODEL is missing."
    )