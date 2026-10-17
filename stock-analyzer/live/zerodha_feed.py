"""
zerodha_feed.py

Zerodha Kite Connect adapter.

This is the recommended adapter for Indian markets in production.
Kite Connect provides true tick data, live quotes, and intraday history.

Setup
-----
1. Sign up at https://kite.trade/
2. Create an app to get API_KEY and API_SECRET
3. pip install kiteconnect
4. Set environment variables:
       KITE_API_KEY=your_api_key
       KITE_ACCESS_TOKEN=your_access_token
   (Access token must be refreshed daily via Kite login flow)

Kite intervals supported:
    "minute", "3minute", "5minute", "10minute",
    "15minute", "30minute", "60minute", "day"

Version : 5.1.0
"""

from __future__ import annotations

import datetime
import os

from live.feed_base import LiveFeed, Bar

_IST_OFFSET = datetime.timezone(datetime.timedelta(hours=5, minutes=30))

# Kite interval → this adapter's unified interval string
_INTERVAL_MAP = {
    "1m"  : "minute",
    "3m"  : "3minute",
    "5m"  : "5minute",
    "10m" : "10minute",
    "15m" : "15minute",
    "30m" : "30minute",
    "1h"  : "60minute",
    "1d"  : "day",
}


class ZerodhaFeed(LiveFeed):
    """
    Zerodha Kite Connect adapter.

    Parameters
    ----------
    symbol      : str   NSE symbol (e.g. "RELIANCE")
    interval    : str   "1m", "5m", "15m", "1h" etc.
    instrument_token : int | None
        Kite instrument token for the symbol.
        If None, the adapter will look it up from the instrument dump.
    """

    def __init__(
        self,
        symbol           : str,
        interval         : str = "1m",
        instrument_token : int | None = None,
    ):
        super().__init__(symbol, interval)
        self._token    = instrument_token
        self._kite     = None
        self._kite_interval = _INTERVAL_MAP.get(interval, "minute")
        self._connect()

    # ------------------------------------------------------------------

    def _connect(self):
        """Initialise KiteConnect with credentials from env."""
        try:
            from kiteconnect import KiteConnect  # type: ignore
        except ImportError:
            raise ImportError(
                "kiteconnect is not installed.\n"
                "Run: pip install kiteconnect\n"
                "Then set KITE_API_KEY and KITE_ACCESS_TOKEN environment variables."
            )

        api_key      = os.getenv("KITE_API_KEY", "")
        access_token = os.getenv("KITE_ACCESS_TOKEN", "")

        if not api_key or not access_token:
            raise ValueError(
                "KITE_API_KEY and KITE_ACCESS_TOKEN must be set as "
                "environment variables to use ZerodhaFeed.\n"
                "See live/zerodha_feed.py for setup instructions."
            )

        self._kite = KiteConnect(api_key=api_key)
        self._kite.set_access_token(access_token)

        # Resolve instrument token if not provided
        if self._token is None:
            self._token = self._resolve_token()

    # ------------------------------------------------------------------

    def _resolve_token(self) -> int:
        """Look up the NSE instrument token for self.symbol."""
        instruments = self._kite.instruments("NSE")
        for inst in instruments:
            if inst["tradingsymbol"] == self.symbol:
                return inst["instrument_token"]
        raise ValueError(
            f"Instrument token not found for {self.symbol} on NSE.\n"
            "Check the symbol spelling or pass instrument_token explicitly."
        )

    # ------------------------------------------------------------------

    def fetch_latest(self, n_bars: int = 100) -> list[Bar]:
        """
        Fetch the most recent `n_bars` bars from Kite Historical Data API.
        """
        now   = datetime.datetime.now(tz=_IST_OFFSET)
        start = now - datetime.timedelta(days=7)

        data = self._kite.historical_data(
            instrument_token = self._token,
            from_date        = start.strftime("%Y-%m-%d %H:%M:%S"),
            to_date          = now.strftime("%Y-%m-%d %H:%M:%S"),
            interval         = self._kite_interval,
            continuous       = False,
            oi               = False,
        )

        bars = []
        for row in data[-n_bars:]:
            o  = float(row["open"])
            h  = float(row["high"])
            lo = float(row["low"])
            c  = float(row["close"])
            v  = float(row["volume"])
            vwap = round((h + lo + c) / 3.0, 4)

            bars.append(Bar(
                timestamp = str(row["date"]),
                symbol    = self.symbol,
                open      = round(o,  4),
                high      = round(h,  4),
                low       = round(lo, 4),
                close     = round(c,  4),
                volume    = round(v,  0),
                vwap      = vwap,
                interval  = self.interval,
                source    = "zerodha",
            ))

        return bars

    # ------------------------------------------------------------------

    def is_market_open(self) -> bool:
        now = datetime.datetime.now(tz=_IST_OFFSET)
        if now.weekday() >= 5:
            return False
        t       = now.time()
        open_t  = datetime.time(9, 15)
        close_t = datetime.time(15, 30)
        return open_t <= t <= close_t

    # ------------------------------------------------------------------

    def source_name(self) -> str:
        return "Zerodha Kite Connect"
