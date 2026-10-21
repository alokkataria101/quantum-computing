"""
trend_classifier.py

Track 1 — Intraday Trend Classifier.

Classifies the current intraday trend as Bullish / Bearish / Sideways
and rates its strength as Weak / Moderate / Strong.

All inputs come from the feature vector already produced by
MultiWindowFeatures and the TickBuffer already populated by QAMOEngineV2.
No additional data fetching is required.

Logic
-----
    slope     = linear-regression slope of the last N close prices
    slope_norm = slope / ATR  (dimensionless, scale-invariant)
    ema_cross  = "golden" if ema_fast > ema_slow, "death" if ema_fast < ema_slow
    macd_sign  = +1 / -1 / 0

    Bullish: slope_norm > threshold AND ema_cross == "golden" AND macd_sign >= 0
    Bearish: slope_norm < -threshold AND ema_cross == "death"  AND macd_sign <= 0
    Sideways: neither

    Strength: |slope_norm| mapped to Weak / Moderate / Strong

Version : 11.0.1
"""

from __future__ import annotations

import numpy as np

from live.tick_buffer import TickBuffer

_MIN_SLOPE_BARS      = 5
_SLOPE_NEUTRAL       = 0.15   # |slope_norm| < this  -> Sideways
_SLOPE_MODERATE      = 0.50   # |slope_norm| >= this -> Moderate
_SLOPE_STRONG        = 1.50   # |slope_norm| >= this -> Strong


def _linear_slope(arr: np.ndarray) -> float:
    n = len(arr)
    if n < 2:
        return 0.0
    x = np.arange(n, dtype=float)
    slope, _ = np.polyfit(x, arr, 1)
    return float(slope)


class TrendClassifier:
    """
    Classifies current intraday trend direction and strength.

    Parameters
    ----------
    fv  : dict        Feature vector from MultiWindowFeatures.compute()
    buf : TickBuffer  Bar buffer from QAMOEngineV2.buf
    n   : int         Recent bars used for slope calculation (default 15)
    """

    def __init__(self, fv: dict, buf: TickBuffer, n: int = 15):
        self._fv  = fv
        self._buf = buf
        self._n   = max(_MIN_SLOPE_BARS, int(n))

    # ------------------------------------------------------------------

    def classify(self) -> dict:
        """
        Compute trend classification.

        Returns
        -------
        dict:
            trend      str    "Bullish" | "Bearish" | "Sideways"
            strength   str    "Weak"    | "Moderate" | "Strong"
            ema_cross  str    "golden"  | "death"    | "neutral"
            slope      float  raw price slope (price units per bar)
            slope_norm float  slope normalised by ATR (dimensionless)
            macd_sign  int    +1 / -1 / 0
        """
        fv = self._fv

        # EMA cross
        ef = float(fv.get("ema_fast_w4", fv.get("ema_fast", 0.0)))
        es = float(fv.get("ema_slow_w4", fv.get("ema_slow", 0.0)))
        if ef > es * 1.0001:
            ema_cross = "golden"
        elif ef < es * 0.9999:
            ema_cross = "death"
        else:
            ema_cross = "neutral"

        # MACD sign
        macd = float(fv.get("macd_w4", fv.get("macd", 0.0)))
        macd_sign = 1 if macd > 1e-6 else (-1 if macd < -1e-6 else 0)

        # Price slope
        bars   = self._buf.all()
        recent = bars[-self._n:] if len(bars) >= _MIN_SLOPE_BARS else bars
        slope  = _linear_slope(
            np.array([b.close for b in recent], dtype=float)
        ) if len(recent) >= 2 else 0.0

        atr        = float(fv.get("atr_w4", fv.get("atr", 1.0))) or 1.0
        slope_norm = slope / atr

        # Direction — all three signals must agree
        if slope_norm > _SLOPE_NEUTRAL and ema_cross == "golden" and macd_sign >= 0:
            trend = "Bullish"
        elif slope_norm < -_SLOPE_NEUTRAL and ema_cross == "death" and macd_sign <= 0:
            trend = "Bearish"
        else:
            trend = "Sideways"

        # Strength from normalised slope magnitude
        abs_n = abs(slope_norm)
        if abs_n >= _SLOPE_STRONG:
            strength = "Strong"
        elif abs_n >= _SLOPE_MODERATE:
            strength = "Moderate"
        else:
            strength = "Weak"

        return {
            "trend"     : trend,
            "strength"  : strength,
            "ema_cross" : ema_cross,
            "slope"     : round(slope,      4),
            "slope_norm": round(slope_norm, 4),
            "macd_sign" : macd_sign,
        }
