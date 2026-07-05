"""Central config — reads .env (PoC). One place for paths + LLM settings."""
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
MODELS_DIR = ROOT / "app" / "nlu" / "models"
SESSIONS_DIR = DATA_DIR / "sessions"
RL_POLICY_PATH = DATA_DIR / "rl_policy.json"

load_dotenv(ROOT / ".env")


def _get(key, default):
    v = os.getenv(key)
    return v if v not in (None, "") else default


# LLM provider settings (pluggable via .env)
LLM_PROVIDER = _get("LLM_PROVIDER", "ollama").lower()
OLLAMA_BASE_URL = _get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = _get("OLLAMA_MODEL", "llama3.2")
OPENAI_API_KEY = _get("OPENAI_API_KEY", "")
OPENAI_MODEL = _get("OPENAI_MODEL", "gpt-4o-mini")
ANTHROPIC_API_KEY = _get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = _get("ANTHROPIC_MODEL", "claude-sonnet-5")

# Demo login password shared by all synthetic customers (PoC only).
DEMO_PASSWORD = "teleco123"

SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
