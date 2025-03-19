import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot configuration
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# AI configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
DEFAULT_MODEL = "gemini-1.5-flash"
MAX_HISTORY_LENGTH = 10  # Number of messages to keep for context

# Response styles
RESPONSE_STYLES = {
    "romantic": "warm, affectionate and romantic",
    "playful": "playful, teasing and flirty",
    "supportive": "supportive, understanding and empathetic",
    "passionate": "passionate, intense and deeply emotional",
    "casual": "casual, relaxed and friendly"
}

# Default style
DEFAULT_STYLE = "romantic"