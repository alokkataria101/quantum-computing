"""
intraday_assistant.py

Track 1 — Intraday Trading Assistant Orchestrator.

Wires the existing QAMOEngineV2 pipeline with the four new Track 1 modules
to produce a complete trading-assistant signal:

    Stage 0  DataQualityValidator + FeedWithFallback
                                    → validate bars, auto-fallback interval
    Stage 1  QAMOEngineV2.refresh() → core quantum signal
    Stage 2  PriceLevelForecaster.forecast() → exp Open / High / Low / Close
    Stage 3  TrendClassifier.classify()      → Bullish / Bearish / Sideways
    Stage 4  SupportResistance.compute()     → Pivot / R1 / R2 / S1 / S2
    Stage 5  ReasonBuilder.build()           → 3–5 human-readable bullet strings
    Stage 6  get_5level_signal()             → maps p_up + confidence to
                                              STRONG BUY / BUY / HOLD /
                                              SELL / STRONG SELL

All quantum computation remains inside QAMOEngineV2.  This class only
assembles the outputs — no quantum logic here.

Version : 11.0.1
"""

from __future__ import annotations

from live.feed_base              import LiveFeed
from live.yahoo_feed             import YahooFeed
from live.qamo_engine_v2         import QAMOEngineV2
from live.research_tracker       import ResearchTracker
from live.price_level_forecaster import PriceLevelForecaster
from live.trend_classifier       import TrendClassifier
from live.support_resistance     import SupportResistance
from live.reason_builder         import ReasonBuilder
from live.data_quality           import DataQualityValidator, DataQualityReport
from live.feed_with_fallback     import FeedWithFallback, FetchResult
from config import (
    STRONG_BUY_P_UP,
    BUY_P_UP,
    SELL_P_UP,
    STRONG_SELL_P_UP,
    STRONG_SIGNAL_CONF,
)


class IntradayAssistant:
    """
    Track 1 orchestrator for a single symbol.

    Stored in ``st.session_state`` keyed by
    ``f"assistant_{symbol}_{interval}"``.

    Parameters
    ----------
    symbol    : str
    interval  : str       "5m" (default), "1m", "15m"
    n_bars    : int       bars to fetch per refresh (default 200)
    feed      : LiveFeed | None   defaults to FeedWithFallback (auto-fallback)
    fwd_bars  : int       prediction horizon in bars for ResearchTracker
                          (default 6 = 30 min on 5-min bars)
    min_quality : float   minimum data quality score to proceed (default 70)
    """

    def __init__(
        self,
        symbol      : str,
        interval    : str            = "5m",
        n_bars      : int            = 200,
        feed        : LiveFeed | None = None,
        fwd_bars    : int            = 6,
        min_quality : float          = 70.0,
    ):
        self.symbol      = symbol.upper()
        self.interval    = interval
        self.n_bars      = n_bars
        self.min_quality = min_quality

        self._engine  = QAMOEngineV2(
            symbol   = symbol,
            interval = interval,
            n_bars   = n_bars,
            feed     = feed,
        )
        self._tracker = ResearchTracker(capacity=500, fwd_bars=fwd_bars)

        # Stage 0 outputs — populated by refresh()
        self._fetch_result  : FetchResult | None       = None
        self._quality_report: DataQualityReport | None = None

        # Cached signal outputs — populated by refresh()
        self._score    : dict = {}
        self._levels   : dict = {}
        self._trend    : dict = {}
        self._sr       : dict = {}
        self._reasons  : list[str] = []
        self._signal_5 : str  = "HOLD"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def refresh(self) -> dict:
        """
        Run Stage 0 (data quality + fallback) then the full QAMO v2 cycle.

        Returns the full signal dict with additional keys:
            ``fetch_result``   : FetchResult
            ``quality_report`` : DataQualityReport
            ``price_levels``   : dict
            ``trend``          : dict
            ``support_resistance`` : dict
            ``reasons``        : list[str]
            ``signal_5level``  : str
        """
        # ── Stage 0 — fetch with fallback + quality validation ────────
        fetcher = FeedWithFallback(
            symbol      = self.symbol,
            interval    = self.interval,
            n_bars      = self.n_bars,
            min_quality = self.min_quality,
        )
        fetch_result = fetcher.fetch()
        self._fetch_result = fetch_result

        # Update the engine's feed to the interval that actually worked,
        # and inject the validated bars directly into the tick buffer so
        # QAMO v2 doesn't re-download.
        if fetch_result.interval_used != self.interval:
            from live.yahoo_feed import YahooFeed as _YF
            self._engine.feed     = _YF(self.symbol, fetch_result.interval_used)
            self._engine.interval = fetch_result.interval_used

        if fetch_result.bars:
            # Strip stale bars (O=H=L=C, Vol=0) before loading into the
            # engine buffer — they corrupt quantum state encoding.
            clean_bars = [
                b for b in fetch_result.bars
                if not (b.open == b.high == b.low == b.close and b.volume == 0)
            ]
            self._engine.buf.clear()
            self._engine.buf.extend(clean_bars or fetch_result.bars)

        self._quality_report = fetch_result.quality

        # If data is completely unusable, short-circuit
        if not fetch_result.is_ok:
            return {
                "error"          : fetch_result.user_message,
                "fetch_result"   : fetch_result,
                "quality_report" : fetch_result.quality,
            }

        # ── Stage 1 — QAMO v2 quantum pipeline ───────────────────────
        score = self._engine.refresh()
        if "error" in score:
            return {
                **score,
                "fetch_result"   : fetch_result,
                "quality_report" : fetch_result.quality,
            }

        fv = self._engine.latest_fv or {}

        # Price level forecast
        self._levels = PriceLevelForecaster(fv, score).forecast()

        # Trend classification
        self._trend = TrendClassifier(fv, self._engine.buf).classify()

        # Support / Resistance
        self._sr = SupportResistance(self._engine.buf).compute()

        # Key reasons
        self._reasons = ReasonBuilder(score, fv, self._trend, self._sr).build()

        # 5-level signal
        self._score    = score
        self._signal_5 = self._map_5level(
            float(score.get("p_up",       0.5)),
            float(score.get("confidence", 0.0)),
        )

        # Feed Research Tracker
        bars = self._engine.buf.all()
        if bars:
            import datetime
            latest    = bars[-1]
            bar_ts    = str(latest.timestamp)[:19]
            exp_ret   = score.get("exp_return", 0.0)
            pred_close = round(latest.close * (1.0 + float(exp_ret) / 100.0), 4)

            # Record actuals for all bars in buffer
            for bar in bars:
                self._tracker.record_actual(
                    bar_ts       = str(bar.timestamp),
                    actual_close = bar.close,
                    actual_open  = bar.open,
                )

            # Register this cycle's forward prediction
            try:
                from dateutil import parser as dtp
                mins_ahead = self._tracker.fwd_bars * _interval_minutes(self.interval)
                base_dt    = dtp.parse(str(latest.timestamp))
                target_ts  = (
                    base_dt + datetime.timedelta(minutes=mins_ahead)
                ).strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                target_ts = bar_ts

            self._tracker.record_prediction(
                prediction_ts   = bar_ts,
                predicted_close = pred_close,
                signal          = score.get("signal", "HOLD"),
                exp_return      = float(exp_ret),
                confidence      = score.get("confidence", 0.0),
                p_up            = score.get("p_up", 0.5),
                target_ts       = target_ts,
            )

        return {
            **score,
            "price_levels"       : self._levels,
            "trend"              : self._trend,
            "support_resistance" : self._sr,
            "reasons"            : self._reasons,
            "signal_5level"      : self._signal_5,
            "fetch_result"       : fetch_result,
            "quality_report"     : fetch_result.quality,
        }

    # ------------------------------------------------------------------
    # Stage-0 accessors
    # ------------------------------------------------------------------

    def get_fetch_result(self) -> "FetchResult | None":
        return self._fetch_result

    def get_quality_report(self) -> "DataQualityReport | None":
        return self._quality_report

    def get_price_levels(self) -> dict:
        return self._levels

    def get_trend(self) -> dict:
        return self._trend

    def get_support_resistance(self) -> dict:
        return self._sr

    def get_reasons(self) -> list[str]:
        return self._reasons

    def get_5level_signal(self) -> str:
        return self._signal_5

    def get_tracker(self) -> ResearchTracker:
        return self._tracker

    def is_market_open(self) -> bool:
        return self._engine.is_market_open()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _map_5level(p_up: float, confidence: float) -> str:
        """Map p_up + confidence to a 5-level signal string."""
        if p_up >= STRONG_BUY_P_UP and confidence >= STRONG_SIGNAL_CONF:
            return "STRONG BUY"
        if p_up >= BUY_P_UP:
            return "BUY"
        if p_up <= STRONG_SELL_P_UP and confidence >= STRONG_SIGNAL_CONF:
            return "STRONG SELL"
        if p_up <= SELL_P_UP:
            return "SELL"
        return "HOLD"


def _interval_minutes(interval: str) -> int:
    _MAP = {"1m": 1, "2m": 2, "5m": 5, "10m": 10,
            "15m": 15, "30m": 30, "60m": 60, "1h": 60}
    return _MAP.get(interval, 5)
