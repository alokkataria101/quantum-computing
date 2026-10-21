"""
yahoo_feed.py

Yahoo Finance live data adapter.

Uses yfinance to fetch 1-min / 5-min / 15-min OHLCV bars for NSE symbols.
Yahoo Finance is the default prototype source — no API key required.

Limitations (Yahoo Finance):
    - 1-min data:  up to 7 calendar days of history
    - 5-min data:  up to 60 calendar days
    - 15-min data: up to 60 calendar days
    - No real bid/ask; vwap approximated as (H+L+C)/3

Version : 5.1.0
"""

from __future__ import annotations

import datetime

import pandas as pd
import yfinance as yf

from live.feed_base import LiveFeed, Bar

# NSE market session (IST = UTC+5:30)
_NSE_OPEN_H  = 9
_NSE_OPEN_M  = 15
_NSE_CLOSE_H = 15
_NSE_CLOSE_M = 30
_IST_OFFSET  = datetime.timezone(datetime.timedelta(hours=5, minutes=30))

# Yahoo Finance interval → max lookback days
_LOOKBACK = {
    "1m"  : 7,
    "2m"  : 60,
    "5m"  : 60,
    "15m" : 60,
    "30m" : 60,
    "60m" : 730,
    "1h"  : 730,
    "1d"  : 730,
}


class YahooFeed(LiveFeed):
    """
    Yahoo Finance adapter.

    Parameters
    ----------
    symbol   : str   NSE symbol without .NS suffix (e.g. "RELIANCE")
    interval : str   "1m", "5m", "15m", "30m", "1h" (default "1m")
    """

    def __init__(self, symbol: str, interval: str = "1m"):
        super().__init__(symbol, interval)
        self._ticker_str = f"{self.symbol}.NS"
        self._ticker     = yf.Ticker(self._ticker_str)

    # ------------------------------------------------------------------

    def fetch_latest(self, n_bars: int = 100) -> list[Bar]:
        """
        Fetch the most recent `n_bars` bars from Yahoo Finance.

        Returns bars ordered oldest → newest.
        """
        lookback_days = _LOOKBACK.get(self.interval, 7)

        df = yf.download(
            self._ticker_str,
            period      = f"{lookback_days}d",
            interval    = self.interval,
            progress    = False,
            auto_adjust = False,
        )

        if df is None or df.empty:
            return []

        # Flatten multi-level columns (yfinance ≥0.2.38 returns MultiIndex)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df = df.dropna(subset=["Close"])
        df = df.tail(n_bars)

        bars = []
        for ts, row in df.iterrows():
            o = float(row.get("Open",   row["Close"]))
            h = float(row.get("High",   row["Close"]))
            lo= float(row.get("Low",    row["Close"]))
            c = float(row["Close"])
            v = float(row.get("Volume", 0))

            # Approx VWAP = (H + L + C) / 3
            vwap = round((h + lo + c) / 3.0, 4)

            bars.append(Bar(
                timestamp = str(ts),
                symbol    = self.symbol,
                open      = round(o,  4),
                high      = round(h,  4),
                low       = round(lo, 4),
                close     = round(c,  4),
                volume    = round(v,  0),
                vwap      = vwap,
                interval  = self.interval,
                source    = "yahoo",
            ))

        return bars

    # ------------------------------------------------------------------

    def is_market_open(self) -> bool:
        """
        Returns True if current IST time is within NSE session
        (Mon–Fri, 09:15–15:30 IST).
        """
        now = datetime.datetime.now(tz=_IST_OFFSET)
        if now.weekday() >= 5:          # Saturday / Sunday
            return False
        t = now.time()
        open_t  = datetime.time(_NSE_OPEN_H,  _NSE_OPEN_M)
        close_t = datetime.time(_NSE_CLOSE_H, _NSE_CLOSE_M)
        return open_t <= t <= close_t

    # ------------------------------------------------------------------

    def source_name(self) -> str:
        return "Yahoo Finance"
