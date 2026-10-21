"""
polygon_feed.py

Polygon.io adapter stub.

Setup
-----
1. Sign up at https://polygon.io/ (free tier supports US equities; paid for NSE)
2. pip install polygon-api-client
3. Set environment variable:
       POLYGON_API_KEY=your_api_key

Note: Polygon.io primarily covers US markets. For NSE stocks, use
YahooFeed or ZerodhaFeed instead.

Version : 5.1.0
"""

from __future__ import annotations

import datetime
import os

from live.feed_base import LiveFeed, Bar


class PolygonFeed(LiveFeed):
    """
    Polygon.io adapter.

    Parameters
    ----------
    symbol   : str   Ticker symbol (US format, e.g. "AAPL")
    interval : str   "1m", "5m", "15m", "1h"
    """

    _MULTIPLIER_MAP = {
        "1m"  : (1,  "minute"),
        "5m"  : (5,  "minute"),
        "15m" : (15, "minute"),
        "1h"  : (1,  "hour"),
        "1d"  : (1,  "day"),
    }

    def __init__(self, symbol: str, interval: str = "1m"):
        super().__init__(symbol, interval)
        self._client = None
        self._connect()

    # ------------------------------------------------------------------

    def _connect(self):
        try:
            from polygon import RESTClient  # type: ignore
        except ImportError:
            raise ImportError(
                "polygon-api-client is not installed.\n"
                "Run: pip install polygon-api-client\n"
                "Then set POLYGON_API_KEY environment variable."
            )

        api_key = os.getenv("POLYGON_API_KEY", "")
        if not api_key:
            raise ValueError(
                "POLYGON_API_KEY environment variable is not set.\n"
                "See live/polygon_feed.py for setup instructions."
            )

        self._client = RESTClient(api_key)

    # ------------------------------------------------------------------

    def fetch_latest(self, n_bars: int = 100) -> list[Bar]:
        multiplier, timespan = self._MULTIPLIER_MAP.get(
            self.interval, (1, "minute")
        )

        to_dt   = datetime.datetime.utcnow()
        from_dt = to_dt - datetime.timedelta(days=5)

        aggs = self._client.get_aggs(
            ticker      = self.symbol,
            multiplier  = multiplier,
            timespan    = timespan,
            from_       = from_dt.strftime("%Y-%m-%d"),
            to          = to_dt.strftime("%Y-%m-%d"),
            limit       = n_bars,
        )

        bars = []
        for agg in aggs:
            o  = float(agg.open)
            h  = float(agg.high)
            lo = float(agg.low)
            c  = float(agg.close)
            v  = float(agg.volume)
            vw = float(agg.vwap) if agg.vwap else round((h + lo + c) / 3, 4)

            bars.append(Bar(
                timestamp = str(datetime.datetime.utcfromtimestamp(agg.timestamp / 1000)),
                symbol    = self.symbol,
                open      = round(o,  4),
                high      = round(h,  4),
                low       = round(lo, 4),
                close     = round(c,  4),
                volume    = round(v,  0),
                vwap      = round(vw, 4),
                interval  = self.interval,
                source    = "polygon",
            ))

        return bars[-n_bars:]

    # ------------------------------------------------------------------

    def is_market_open(self) -> bool:
        """US market hours (EST). Override for other exchanges."""
        now = datetime.datetime.utcnow()
        if now.weekday() >= 5:
            return False
        t       = now.time()
        open_t  = datetime.time(13, 30)   # 09:30 EST = 13:30 UTC
        close_t = datetime.time(20, 0)    # 16:00 EST = 20:00 UTC
        return open_t <= t <= close_t

    # ------------------------------------------------------------------

    def source_name(self) -> str:
        return "Polygon.io"
