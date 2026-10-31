"""app/ai_client.py – IBM watsonx.ai client wrapper (optional).

If credentials are not configured the service continues to work normally;
AI endpoints return HTTP 503 with a clear message.
"""

from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# ── Load secrets / API keys (checked in order, first match wins) ─────────────
# 1. SECRETS_FILE env var           — explicit override (Docker -e flag)
# 2. /app/secrets/.env.secrets      — Docker volume mount default
# 3. /run/secrets/.env.secrets      — Docker Swarm / Compose secrets standard
# 4. <repo-root>/.env.secrets       — local development (repo root)
# 5. Plain environment variables    — always the final fallback
try:
    from dotenv import load_dotenv
    _here      = Path(__file__).resolve().parent.parent  # book-knowledge-service/
    _repo_root = _here.parent                             # quantum-computing/

    _candidates = [
        os.getenv("SECRETS_FILE", ""),          # 1. explicit
        "/app/secrets/.env.secrets",            # 2. Docker volume default
        "/run/secrets/.env.secrets",            # 3. Docker Swarm standard
        str(_repo_root / ".env.secrets"),       # 4. local dev repo root
    ]
    for _f in _candidates:
        if _f and Path(_f).is_file():
            load_dotenv(_f, override=False)
            break

    load_dotenv(_here / ".env", override=True)  # project .env always last
except ImportError:
    pass  # python-dotenv not installed — fall back to plain environment variables


# ── Credentials (empty = AI disabled) ────────────────────────────────────────
WATSONX_API_KEY    = os.getenv("WATSONX_API_KEY", "")
WATSONX_PROJECT_ID = os.getenv("WATSONX_PROJECT_ID", "")
WATSONX_URL        = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
WATSONX_MODEL      = os.getenv("WATSONX_MODEL", "meta-llama/llama-3-3-70b-instruct")


class AIClient:
    """Thin wrapper around ibm-watsonx-ai ModelInference.

    Usage:
        client = AIClient()
        if client.is_enabled():
            text = client.generate(prompt)
    """

    def __init__(self) -> None:
        self.enabled = False
        self._model  = None

        if not WATSONX_API_KEY or not WATSONX_PROJECT_ID:
            logger.info("[AI] watsonx credentials not set — AI features disabled.")
            return

        try:
            from ibm_watsonx_ai import Credentials
            from ibm_watsonx_ai.foundation_models import ModelInference

            creds = Credentials(url=WATSONX_URL, api_key=WATSONX_API_KEY)
            self._model = ModelInference(
                model_id=WATSONX_MODEL,
                credentials=creds,
                project_id=WATSONX_PROJECT_ID,
                params={
                    "max_new_tokens": 1200,
                    "temperature":    0.20,
                    "top_p":          0.90,
                    "repetition_penalty": 1.05,
                },
            )
            self.enabled = True
            logger.info("[AI] IBM watsonx initialised (model=%s).", WATSONX_MODEL)

        except ImportError:
            logger.warning("[AI] ibm-watsonx-ai SDK not installed. Run: pip install ibm-watsonx-ai")
        except Exception as exc:
            logger.warning("[AI] Failed to initialise watsonx: %s", exc)

    def is_enabled(self) -> bool:
        return self.enabled

    def generate(self, prompt: str, max_new_tokens: int | None = None) -> str | None:
        if not self.enabled or self._model is None:
            return None
        try:
            params = {"max_new_tokens": max_new_tokens} if max_new_tokens else {}
            return self._model.generate_text(prompt=prompt, params=params).strip()
        except Exception as exc:
            msg = str(exc)
            logger.error("[AI] Generation error: %s", exc)
            if "consumption_limit_reached" in msg:
                raise QuotaExceededError(
                    "watsonx token quota for this plan/project is used up. Retrying will not help — "
                    "wait for the quota to reset or upgrade the watsonx.ai plan."
                ) from exc
            if "429" in msg or "Too Many Requests" in msg:
                raise RateLimitError(
                    "watsonx rate limit reached — too many concurrent requests. "
                    "Please wait a moment and try again."
                ) from exc
            return None


class RateLimitError(Exception):
    """Raised when watsonx returns HTTP 429 Too Many Requests."""


class QuotaExceededError(RateLimitError):
    """watsonx says the plan's consumption limit is reached - not transient."""


# At most this many watsonx calls run at once; the rest wait their turn instead
# of all hitting the API together and getting 429s. Override with AI_MAX_CONCURRENCY.
AI_MAX_CONCURRENCY = max(1, int(os.getenv("AI_MAX_CONCURRENCY", "4")))
# A 429 is retried this many times, waiting 2s, 4s, 8s... between tries. Override with AI_RATE_LIMIT_RETRIES.
AI_RATE_LIMIT_RETRIES = max(0, int(os.getenv("AI_RATE_LIMIT_RETRIES", "4")))
_ai_slots: asyncio.Semaphore | None = None


async def ai_generate(client: AIClient, prompt: str, max_new_tokens: int | None = None) -> str | None:
    """Run the (blocking) watsonx call in a worker thread so the event loop - and
    every other user - keeps being served, with a cap on simultaneous calls."""
    global _ai_slots
    if _ai_slots is None:
        _ai_slots = asyncio.Semaphore(AI_MAX_CONCURRENCY)
    for attempt in range(AI_RATE_LIMIT_RETRIES + 1):
        try:
            async with _ai_slots:
                return await asyncio.to_thread(client.generate, prompt, max_new_tokens)
        except QuotaExceededError:
            raise
        except RateLimitError:
            if attempt == AI_RATE_LIMIT_RETRIES:
                raise
            delay = 2 ** (attempt + 1)
            logger.warning("[AI] rate limited - retrying in %ss (%d/%d)",
                           delay, attempt + 1, AI_RATE_LIMIT_RETRIES)
            await asyncio.sleep(delay)   # outside the slot so others can use it


# Singleton — one connection shared across all requests
_client: AIClient | None = None


def get_ai_client() -> AIClient:
    global _client
    if _client is None:
        _client = AIClient()
    return _client
