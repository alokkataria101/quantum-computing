"""
support_resistance.py

Track 1 — Pivot-Point Support & Resistance Calculator.

Computes standard floor pivot-point levels from recent OHLCV bars:

    Pivot (P) = (High + Low + Close) / 3
    R1        = 2 * P - Low
    R2        = P + (High - Low)
    S1        = 2 * P - High
    S2        = P - (High - Low)

Also computes the rolling session high and session low from all bars
in the buffer.

Inputs come entirely from the TickBuffer already populated by QAMOEngineV2.
No additional data fetching is required.

Version : 11.0.1
"""

from __future__ import annotations

import numpy as np

from live.tick_buffer import TickBuffer

_DEFAULT_WINDOW = 20   # bars used for H/L/C derivation


class SupportResistance:
    """
    Computes pivot-based support and resistance levels.

    Parameters
    ----------
    buf    : TickBuffer   populated bar buffer
    window : int          number of recent bars for H/L/C (default 20)
    """

    def __init__(self, buf: TickBuffer, window: int = _DEFAULT_WINDOW):
        self._buf    = buf
        self._window = max(3, int(window))

    # ------------------------------------------------------------------

    def compute(self) -> dict:
        """
        Compute all S/R levels.

        Returns
        -------
        dict:
            pivot        float  (H + L + C) / 3
            r1           float  first resistance
            r2           float  second resistance
            s1           float  first support
            s2           float  second support
            session_high float  rolling high over full buffer
            session_low  float  rolling low over full buffer
        """
        bars = self._buf.all()
        if not bars:
            return {k: 0.0 for k in
                    ("pivot", "r1", "r2", "s1", "s2", "session_high", "session_low")}

        # Pivot uses last `window` bars
        recent = bars[-self._window:]
        H = float(max(b.high  for b in recent))
        L = float(min(b.low   for b in recent))
        C = float(recent[-1].close)

        pivot = (H + L + C) / 3.0
        r1    = 2.0 * pivot - L
        r2    = pivot + (H - L)
        s1    = 2.0 * pivot - H
        s2    = pivot - (H - L)

        # Session high/low over full buffer
        session_high = float(max(b.high for b in bars))
        session_low  = float(min(b.low  for b in bars))

        return {
            "pivot"        : round(pivot,        2),
            "r1"           : round(r1,           2),
            "r2"           : round(r2,           2),
            "s1"           : round(s1,           2),
            "s2"           : round(s2,           2),
            "session_high" : round(session_high, 2),
            "session_low"  : round(session_low,  2),
        }
