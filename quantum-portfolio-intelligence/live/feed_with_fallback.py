"""
feed_with_fallback.py

Yahoo Finance feed wrapper with automatic interval fallback.

When the requested interval returns poor-quality data (stale bars, empty
response, or a quality score below a threshold), this wrapper automatically
retries with progressively coarser intervals until it finds usable data.

Fallback chain
--------------
  requested → 2m → 5m → 15m → 30m → (give up)

For each candidate interval the wrapper:
  1. Fetches bars from Yahoo Finance
  2. Runs DataQualityValidator
  3. Classifies the failure cause (closed / no-data / unsupported)
  4. If score < min_quality_score, tries the next coarser interval
  5. Returns the first interval that meets the threshold, plus a full
     FetchResult describing what happened

FetchResult.cause values
------------------------
  "ok"                 — data meets quality threshold
  "market_closed"      — market is outside NSE session hours
  "no_data"            — Yahoo returned an empty dataset
  "stale_bars"         — all bars are flat O=H=L=C Vol=0
  "unsupported_symbol" — even 30m data is poor (likely index/ETF)
  "degraded"           — data is usable but below HIGH threshold

Version : 11.0.1
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field

from live.feed_base      import LiveFeed, Bar
from live.yahoo_feed     import YahooFeed
from live.data_quality   import DataQualityValidator, DataQualityReport


# NSE market hours (IST)
_IST_OFFSET = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
_NSE_OPEN   = datetime.time(9, 15)
_NSE_CLOSE  = datetime.time(15, 30)

# Fallback chain — ordered from finest to coarsest
_FALLBACK_CHAIN = ["1m", "2m", "5m", "15m", "30m"]

# Quality score below which we try a coarser interval
_MIN_QUALITY = 70.0


# ---------------------------------------------------------------------------

@dataclass
class FetchResult:
    """
    Outcome of one fetch attempt (possibly after fallback).

    Attributes
    ----------
    bars              : list[Bar]         bars returned (may be empty)
    interval_used     : str               interval that produced this result
    interval_requested: str               what the caller originally asked for
    quality           : DataQualityReport quality assessment of bars
    cause             : str               "ok" / "market_closed" / "no_data" /
                                          "stale_bars" / "unsupported_symbol" /
                                          "degraded"
    cause_detail      : str               human-readable explanation
    fallback_tried    : list[str]         intervals tried before succeeding
    """
    bars               : list = field(default_factory=list)
    interval_used      : str  = "5m"
    interval_requested : str  = "5m"
    quality            : DataQualityReport = field(
                             default_factory=DataQualityReport)
    cause              : str  = "ok"
    cause_detail       : str  = ""
    fallback_tried     : list = field(default_factory=list)

    # ------------------------------------------------------------------
    @property
    def is_ok(self) -> bool:
        return self.cause in ("ok", "degraded") and bool(self.bars)

    @property
    def user_message(self) -> str:
        """One-line message suitable for display in the dashboard."""
        if self.cause == "ok":
            return (
                f"Data loaded — {len(self.bars)} bars at {self.interval_used} "
                f"· Quality {self.quality.score:.0f}% ({self.quality.grade})"
            )
        if self.cause == "market_closed":
            return (
                "Market is currently closed (NSE hours: Mon–Fri 09:15–15:30 IST). "
                "Showing the most recent completed session."
            )
        if self.cause == "no_data":
            return (
                f"Yahoo Finance returned no data for this symbol at "
                f"{self.interval_requested}. "
                "Check the ticker name and try again during market hours."
            )
        if self.cause == "stale_bars":
            return (
                f"Yahoo Finance returned only flat candles (O=H=L=C, Vol=0) "
                f"at {self.interval_requested}. "
                + (
                    f"Automatically switched to {self.interval_used}."
                    if self.interval_used != self.interval_requested
                    else "No usable data found for any interval."
                )
            )
        if self.cause == "unsupported_symbol":
            return (
                f"{self.interval_requested} intraday data is not available for "
                f"this symbol on Yahoo Finance even after fallback. "
                "Consider using 5m or 15m intervals, or verify the NSE ticker."
            )
        if self.cause == "degraded":
            return (
                f"Data loaded at {self.interval_used} with reduced quality "
                f"({self.quality.score:.0f}%). "
                "Prediction confidence may be lower than normal."
            )
        return self.cause_detail


# ---------------------------------------------------------------------------

class FeedWithFallback:
    """
    Yahoo Finance adapter with automatic interval fallback and quality
    validation.

    Parameters
    ----------
    symbol       : str
    interval     : str    requested interval (e.g. "1m")
    n_bars       : int    bars to fetch
    min_quality  : float  quality score threshold 0–100 (default 70)
    """

    def __init__(
        self,
        symbol      : str,
        interval    : str   = "5m",
        n_bars      : int   = 200,
        min_quality : float = _MIN_QUALITY,
    ):
        self.symbol       = symbol.upper()
        self.interval     = interval
        self.n_bars       = n_bars
        self.min_quality  = min_quality

    # ------------------------------------------------------------------

    def fetch(self) -> FetchResult:
        """
        Attempt to fetch bars, falling back to coarser intervals as needed.

        Returns a FetchResult with bars, quality report, and cause.
        """
        requested = self.interval

        # Build the chain starting from the requested interval
        chain = _build_chain(requested)

        fallback_tried: list[str] = []

        for interval in chain:
            feed = YahooFeed(self.symbol, interval)
            bars = feed.fetch_latest(n_bars=self.n_bars)

            # ── Empty response
            if not bars:
                fallback_tried.append(interval)
                continue

            # ── Validate quality
            validator = DataQualityValidator(bars, interval)
            report    = validator.validate()

            # ── All stale → classify and try next
            if report.n_stale == len(bars):
                fallback_tried.append(interval)
                continue

            # ── Good enough?
            if report.score >= self.min_quality:
                cause = "ok" if report.score >= 90 else "degraded"
                return FetchResult(
                    bars               = bars,
                    interval_used      = interval,
                    interval_requested = requested,
                    quality            = report,
                    cause              = cause,
                    cause_detail       = report.issues[0] if report.issues else "",
                    fallback_tried     = fallback_tried,
                )

            # ── Below threshold — try coarser
            fallback_tried.append(interval)

        # ── All intervals exhausted — return best we found, or classify failure
        # Try one last time at 5m and return whatever we get
        feed  = YahooFeed(self.symbol, "5m")
        bars  = feed.fetch_latest(n_bars=self.n_bars)

        if not bars:
            cause        = "no_data"
            cause_detail = (
                f"No intraday data available for {self.symbol} at any interval. "
                "Verify the NSE ticker symbol."
            )
            return FetchResult(
                bars               = [],
                interval_used      = requested,
                interval_requested = requested,
                quality            = DataQualityReport(n_bars=0, score=0.0, grade="LOW"),
                cause              = cause,
                cause_detail       = cause_detail,
                fallback_tried     = fallback_tried,
            )

        validator = DataQualityValidator(bars, "5m")
        report    = validator.validate()

        # Classify the root cause
        cause = _classify_cause(report, feed.is_market_open(), requested)

        return FetchResult(
            bars               = bars,
            interval_used      = "5m",
            interval_requested = requested,
            quality            = report,
            cause              = cause,
            cause_detail       = report.issues[0] if report.issues else "",
            fallback_tried     = fallback_tried,
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_chain(requested: str) -> list[str]:
    """
    Build the fallback chain starting from the requested interval.
    Always includes 5m and 15m as safe fallbacks.
    """
    try:
        start = _FALLBACK_CHAIN.index(requested)
    except ValueError:
        start = 0
    chain = _FALLBACK_CHAIN[start:]
    # Ensure 5m and 15m are always in the chain
    for safe in ("5m", "15m"):
        if safe not in chain:
            chain.append(safe)
    return chain


def _classify_cause(
    report    : DataQualityReport,
    is_open   : bool,
    requested : str,
) -> str:
    """Classify the root cause of data quality failure."""
    if not is_open:
        return "market_closed"
    stale_fraction = report.n_stale / max(report.n_bars, 1)
    if stale_fraction > 0.8:
        return "unsupported_symbol"
    if report.n_bars == 0:
        return "no_data"
    if report.score < 70:
        return "stale_bars"
    return "degraded"
