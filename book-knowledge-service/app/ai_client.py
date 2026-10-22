"""app/ai_client.py – IBM watsonx.ai client wrapper (optional).

If credentials are not configured the service continues to work normally;
AI endpoints return HTTP 503 with a clear message.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# ── Load shared .env.secrets from repo root, then local .env ─────────────────
try:
    from dotenv import load_dotenv
    _here      = Path(__file__).resolve().parent.parent  # book-knowledge-service/
    _repo_root = _here.parent                             # quantum-computing/
    load_dotenv(_repo_root / ".env.secrets", override=False)
    load_dotenv(_here / ".env", override=True)
except ImportError:
    pass  # fall back to plain environment variables


# ── Credentials (empty = AI disabled) ────────────────────────────────────────
WATSONX_API_KEY    = os.getenv("WATSONX_API_KEY", "")
WATSONX_PROJECT_ID = os.getenv("WATSONX_PROJECT_ID", "")
WATSONX_URL        = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
WATSONX_MODEL      = os.getenv("WATSONX_MODEL", "ibm/granite-3-8b-instruct")


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

    def generate(self, prompt: str) -> str | None:
        if not self.enabled or self._model is None:
            return None
        try:
            return self._model.generate_text(prompt=prompt).strip()
        except Exception as exc:
            logger.error("[AI] Generation error: %s", exc)
            return None


# Singleton — one connection shared across all requests
_client: AIClient | None = None


def get_ai_client() -> AIClient:
    global _client
    if _client is None:
        _client = AIClient()
    return _client
