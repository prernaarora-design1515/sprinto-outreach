"""
Settings for the whole project, read from the .env file.

Secrets (API keys) live ONLY in .env, which is excluded from git by .gitignore.
.env.example shows which settings exist, without real values.
"""

import os

from dotenv import load_dotenv

load_dotenv()  # reads .env in the project folder (if it exists)


def _get(name, default=""):
    # strip spaces and accidental surrounding quotes (a common copy-paste mistake)
    return os.getenv(name, default).strip().strip('"').strip("'").strip()


# --- AI provider: auto | claude | gemini | mock ---
# auto = Claude if ANTHROPIC_API_KEY is set, else Gemini if GEMINI_API_KEY is set, else mock.
LLM_PROVIDER = _get("LLM_PROVIDER", "auto").lower()
FORCE_MOCK_LLM = _get("FORCE_MOCK_LLM", "false").lower() == "true"

# --- Claude API (research extraction, next-page decisions, email writing) ---
ANTHROPIC_API_KEY = _get("ANTHROPIC_API_KEY")
CLAUDE_MODEL = _get("CLAUDE_MODEL", "claude-opus-5-5")
CLAUDE_EFFORT = _get("CLAUDE_EFFORT", "medium")      # low | medium | high

# --- Google Gemini API (alternative to Claude) ---
GEMINI_API_KEY = _get("GEMINI_API_KEY")
GEMINI_MODEL = _get("GEMINI_MODEL", "gemini-4-hydrogen")
# Used in order when the main model stays busy (503/429) after retries.
GEMINI_FALLBACK_MODELS = [m.strip() for m in
                          _get("GEMINI_FALLBACK_MODELS", "gemini-3.1-flash-lite").split(",") if m.strip()]
GEMINI_TIMEOUT_SECONDS = int(_get("GEMINI_TIMEOUT_SECONDS", "60"))   # per AI call

# --- Hunter.io (contact finding) ---
HUNTER_API_KEY = _get("HUNTER_API_KEY")

# --- Apollo.io (alternative contact source; key checked, not wired in yet) ---
APOLLO_API_KEY = _get("APOLLO_API_KEY")

# --- Gmail (sending the TEST email) ---
# The ONLY address the app will ever send to. Set it to your own inbox.
TEST_RECIPIENT_EMAIL = _get("TEST_RECIPIENT_EMAIL")
GMAIL_CREDENTIALS_FILE = _get("GMAIL_CREDENTIALS_FILE", "credentials.json")
GMAIL_TOKEN_FILE = _get("GMAIL_TOKEN_FILE", "token.json")

# --- Resend (alternative to Gmail for the TEST email) ---
# EMAIL_PROVIDER: auto (Resend if RESEND_API_KEY is set, else Gmail) | resend | gmail
EMAIL_PROVIDER = _get("EMAIL_PROVIDER", "auto").lower()
RESEND_API_KEY = _get("RESEND_API_KEY")
RESEND_FROM = _get("RESEND_FROM", "Sprinto Outreach Test <onboarding@resend.dev>")

# --- Hosting ---
# Vercel sets VERCEL=1. There the project folder is read-only, so SQLite lives in /tmp
# (temporary: it is wiped whenever Vercel starts a fresh instance).
ON_VERCEL = bool(os.getenv("VERCEL"))
# Optional password for the web app (index.py). Empty = open to anyone with the link.
APP_PASSWORD = _get("APP_PASSWORD")

# --- Storage ---
DATABASE_PATH = _get("DATABASE_PATH", "/tmp/outreach.db" if ON_VERCEL else "outreach.db")

# --- Professor's agent-loop limits (do not change without approval) ---
MAX_EXTRA_FETCHES = 4      # pages fetched beyond the homepage
MAX_STAGE_FETCHES = 2      # of those, pages fetched to find stage evidence
PAGE_MAX_TOKENS = 2000     # size limit for each page's cleaned text


def llm_provider():
    """Which AI to use: 'claude', 'gemini' or 'mock'. A provider needs its key."""
    if FORCE_MOCK_LLM or LLM_PROVIDER == "mock":
        return "mock"
    if LLM_PROVIDER == "claude":
        return "claude" if ANTHROPIC_API_KEY else "mock"
    if LLM_PROVIDER == "gemini":
        return "gemini" if GEMINI_API_KEY else "mock"
    if ANTHROPIC_API_KEY:        # auto
        return "claude"
    if GEMINI_API_KEY:
        return "gemini"
    return "mock"


def use_claude():
    return llm_provider() == "claude"


def use_hunter():
    return bool(HUNTER_API_KEY)


def mode_summary():
    """Plain-language description of which integrations are live vs mock."""
    provider = llm_provider()
    ai = {"claude": f"LIVE - Claude ({CLAUDE_MODEL})",
          "gemini": f"LIVE - Gemini ({GEMINI_MODEL})"}.get(provider, "MOCK - rule-based demo, no API key")
    return {
        "AI (extraction & email)": ai,
        "Hunter.io (contacts)": "LIVE" if use_hunter() else "MOCK - fake demo contacts, no API key",
        "Test email": _email_mode(),
    }


def _email_mode():
    from email_sender import check_ready, provider   # local import avoids a cycle
    name = "Resend" if provider() == "resend" else "Gmail"
    if check_ready():
        return f"NOT configured - {name} sending disabled"
    return f"configured - {name}, sends only to {TEST_RECIPIENT_EMAIL}"
