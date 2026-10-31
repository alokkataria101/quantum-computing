"""tests/test_ai_retry.py – watsonx 429s are retried; an exhausted quota is not."""

import pytest

from app import ai_client
from app.ai_client import QuotaExceededError, RateLimitError, ai_generate

pytestmark = pytest.mark.asyncio


class _Fake:
    def __init__(self, errors):
        self.errors, self.calls = list(errors), 0

    def generate(self, prompt, max_new_tokens=None):
        self.calls += 1
        if self.errors:
            raise self.errors.pop(0)
        return "ok"


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch):
    async def _instant(_):
        pass
    monkeypatch.setattr(ai_client.asyncio, "sleep", _instant)
    monkeypatch.setattr(ai_client, "AI_RATE_LIMIT_RETRIES", 2)


async def test_rate_limit_is_retried_then_succeeds():
    fake = _Fake([RateLimitError("429"), RateLimitError("429")])
    assert await ai_generate(fake, "p") == "ok"
    assert fake.calls == 3


async def test_rate_limit_gives_up_after_retries():
    fake = _Fake([RateLimitError("429")] * 5)
    with pytest.raises(RateLimitError):
        await ai_generate(fake, "p")
    assert fake.calls == 3          # first try + 2 retries


async def test_quota_exhausted_is_not_retried():
    fake = _Fake([QuotaExceededError("quota")] * 5)
    with pytest.raises(QuotaExceededError):
        await ai_generate(fake, "p")
    assert fake.calls == 1
