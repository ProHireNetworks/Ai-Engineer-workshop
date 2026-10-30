import os
from pathlib import Path

from dotenv import load_dotenv

# Load backend/.env when running from the backend folder or repository root.
BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR / ".env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
DATABASE_URL = os.getenv("DATABASE_URL")