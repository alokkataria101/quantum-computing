"""
feed_base.py

Abstract base class for all live market data adapters.

Any concrete feed (Yahoo Finance, Zerodha Kite, Polygon, Alpaca, IBKR)
must subclass LiveFeed and implement the three abstract methods.

Version : 5.1.0
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Iterator


@dataclass
class Bar:
    """
    One OHLCV bar (any interval — 1m, 5m, tick, etc.)

    Attributes
    ----------
    timestamp : str     ISO-8601 string  "2025-01-15 09:30:00+05:30"
    symbol    : str     NSE/BSE ticker   "RELIANCE"
    open      : float
    high      : float
    low       : float
    close     : float
    volume    : float
    vwap      : float   volume-weighted average price (0.0 if unavailable)
    bid       : float   best bid (0.0 if unavailable)
    ask       : float   best ask (0.0 if unavailable)
    interval  : str     "1m", "5m", "15m", "tick"
    source    : str     e.g. "yahoo", "zerodha", "polygon", "alpaca"
    """
    timestamp : str
    symbol    : str
    open      : float
    high      : float
    low       : float
    close     : float
    volume    : float
    vwap      : float  = 0.0
    bid       : float  = 0.0
    ask       : float  = 0.0
    interval  : str    = "1m"
    source    : str    = "unknown"

    # ------------------------------------------------------------------
    @property
    def spread(self) -> float:
        """Bid-ask spread. 0.0 if bid/ask not available."""
        if self.bid > 0 and self.ask > 0:
            return round(self.ask - self.bid, 4)
        return 0.0

    @property
    def mid(self) -> float:
        """Mid-price. Falls back to close if bid/ask unavailable."""
        if self.bid > 0 and self.ask > 0:
            return round((self.bid + self.ask) / 2, 4)
        return self.close

    def to_dict(self) -> dict:
        return {
            "timestamp" : self.timestamp,
            "symbol"    : self.symbol,
            "open"      : self.open,
            "high"      : self.high,
            "low"       : self.low,
            "close"     : self.close,
            "volume"    : self.volume,
            "vwap"      : self.vwap,
            "bid"       : self.bid,
            "ask"       : self.ask,
            "spread"    : self.spread,
            "interval"  : self.interval,
            "source"    : self.source,
        }


# ======================================================================


class LiveFeed(ABC):
    """
    Abstract live market data adapter.

    Subclass this for each data source.  The core engine only depends
    on this interface — swapping the source requires no other changes.

    Parameters
    ----------
    symbol   : str   NSE ticker (without .NS suffix — added by adapter)
    interval : str   bar interval — "1m", "5m", "15m", "1h"
    """

    def __init__(self, symbol: str, interval: str = "1m"):
        self.symbol   = symbol.upper()
        self.interval = interval

    # ------------------------------------------------------------------

    @abstractmethod
    def fetch_latest(self, n_bars: int = 100) -> list[Bar]:
        """
        Fetch the most recent `n_bars` bars.

        Returns
        -------
        list[Bar]   ordered oldest → newest
        """
        ...

    # ------------------------------------------------------------------

    @abstractmethod
    def is_market_open(self) -> bool:
        """
        Returns True if the market is currently in session.
        Implementations may use a simple time-window check.
        """
        ...

    # ------------------------------------------------------------------

    @abstractmethod
    def source_name(self) -> str:
        """Human-readable source identifier, e.g. 'Yahoo Finance'."""
        ...

    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"symbol={self.symbol!r}, interval={self.interval!r})"
        )
