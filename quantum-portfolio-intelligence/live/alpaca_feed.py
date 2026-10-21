"""
alpaca_feed.py

Alpaca Markets adapter stub.

Setup
-----
1. Sign up at https://alpaca.markets/ (free paper trading account)
2. pip install alpaca-py
3. Set environment variables:
       ALPACA_API_KEY=your_api_key
       ALPACA_SECRET_KEY=your_secret_key
       ALPACA_BASE_URL=https://paper-api.alpaca.markets  (paper) or
                       https://api.alpaca.markets        (live)

Note: Alpaca primarily covers US equities. For NSE stocks, use
YahooFeed or ZerodhaFeed instead.

Version : 5.1.0
"""

from __future__ import annotations

import datetime
import os

from live.feed_base import LiveFeed, Bar

_TIMEFRAME_MAP = {
    "1m"  : "1Min",
    "5m"  : "5Min",
    "15m" : "15Min",
    "1h"  : "1Hour",
    "1d"  : "1Day",
}


class AlpacaFeed(LiveFeed):
    """
    Alpaca Markets adapter.

    Parameters
    ----------
    symbol   : str   US ticker (e.g. "AAPL")
    interval : str   "1m", "5m", "15m", "1h"
    """

    def __init__(self, symbol: str, interval: str = "1m"):
        super().__init__(symbol, interval)
        self._client = None
        self._connect()

    # ------------------------------------------------------------------

    def _connect(self):
        try:
            from alpaca.data.historical import StockHistoricalDataClient  # type: ignore
        except ImportError:
            raise ImportError(
                "alpaca-py is not installed.\n"
                "Run: pip install alpaca-py\n"
                "Then set ALPACA_API_KEY and ALPACA_SECRET_KEY environment variables."
            )

        api_key    = os.getenv("ALPACA_API_KEY",    "")
        secret_key = os.getenv("ALPACA_SECRET_KEY", "")

        if not api_key or not secret_key:
            raise ValueError(
                "ALPACA_API_KEY and ALPACA_SECRET_KEY environment variables "
                "are not set.\nSee live/alpaca_feed.py for setup instructions."
            )

        self._client = StockHistoricalDataClient(api_key, secret_key)

    # ------------------------------------------------------------------

    def fetch_latest(self, n_bars: int = 100) -> list[Bar]:
        from alpaca.data.requests   import StockBarsRequest   # type: ignore
        from alpaca.data.timeframe  import TimeFrame           # type: ignore

        tf_str = _TIMEFRAME_MAP.get(self.interval, "1Min")
        tf     = getattr(TimeFrame, tf_str, TimeFrame.Minute)

        end   = datetime.datetime.utcnow()
        start = end - datetime.timedelta(days=5)

        req  = StockBarsRequest(
            symbol_or_symbols = self.symbol,
            timeframe         = tf,
            start             = start,
            end               = end,
            limit             = n_bars,
        )
        resp = self._client.get_stock_bars(req)
        raw  = resp[self.symbol]

        bars = []
        for b in raw:
            o  = float(b.open)
            h  = float(b.high)
            lo = float(b.low)
            c  = float(b.close)
            v  = float(b.volume)
            vw = float(b.vwap) if b.vwap else round((h + lo + c) / 3, 4)

            bars.append(Bar(
                timestamp = str(b.timestamp),
                symbol    = self.symbol,
                open      = round(o,  4),
                high      = round(h,  4),
                low       = round(lo, 4),
                close     = round(c,  4),
                volume    = round(v,  0),
                vwap      = round(vw, 4),
                interval  = self.interval,
                source    = "alpaca",
            ))

        return bars

    # ------------------------------------------------------------------

    def is_market_open(self) -> bool:
        """US market hours (UTC)."""
        now = datetime.datetime.utcnow()
        if now.weekday() >= 5:
            return False
        t       = now.time()
        open_t  = datetime.time(13, 30)
        close_t = datetime.time(20, 0)
        return open_t <= t <= close_t

    # ------------------------------------------------------------------

    def source_name(self) -> str:
        return "Alpaca Markets"
