"""
tick_buffer.py

In-memory tick / bar buffer.

Stores the last N bars from a LiveFeed.  Acts as the single source of
truth for feature computation — the FeatureGenerator reads from here.

Version : 5.1.0
"""

from __future__ import annotations

from collections import deque
from typing import List

import pandas as pd

from live.feed_base import Bar


class TickBuffer:
    """
    Fixed-size FIFO buffer of Bar objects.

    Parameters
    ----------
    capacity : int   max bars to keep in memory (default 1000)
    """

    def __init__(self, capacity: int = 1000):
        self.capacity = capacity
        self._buf     : deque = deque(maxlen=capacity)

    # ------------------------------------------------------------------

    def extend(self, bars: list[Bar]):
        """Append multiple bars (oldest first). Deduplicates by timestamp."""
        existing_ts = {r.timestamp for r in self._buf}
        for bar in bars:
            if bar.timestamp not in existing_ts:
                self._buf.append(bar)
                existing_ts.add(bar.timestamp)

    def append(self, bar: Bar):
        """Append a single bar."""
        self.extend([bar])

    # ------------------------------------------------------------------

    def latest(self, n: int = 1) -> list[Bar]:
        """Return the last `n` bars (newest last)."""
        buf = list(self._buf)
        return buf[-n:] if n <= len(buf) else buf

    def all(self) -> list[Bar]:
        return list(self._buf)

    def __len__(self) -> int:
        return len(self._buf)

    def is_empty(self) -> bool:
        return len(self._buf) == 0

    # ------------------------------------------------------------------

    def to_dataframe(self) -> pd.DataFrame:
        """
        Convert buffer to a pandas DataFrame with columns:
            timestamp, symbol, open, high, low, close,
            volume, vwap, bid, ask, spread, interval, source
        """
        if self.is_empty():
            return pd.DataFrame()
        rows = [b.to_dict() for b in self._buf]
        df   = pd.DataFrame(rows)
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
        df = df.sort_values("timestamp").reset_index(drop=True)
        return df

    # ------------------------------------------------------------------

    def clear(self):
        self._buf.clear()
