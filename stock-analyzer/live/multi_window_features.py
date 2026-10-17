"""
multi_window_features.py

Stage 2 — Intraday Feature Engine with multiple lookback windows.

Computes the full feature vector at 5 lookback windows simultaneously:
    w1  =  last  6 bars  (~30s  on 5m data / ~6m  on 1m data)
    w2  =  last 12 bars  (~1m   on 5m data / ~12m on 1m data)
    w3  =  last 36 bars  (~3m   on 5m data / ~36m on 1m data)
    w4  =  last 60 bars  (~5m   on 5m data / ~1h  on 1m data)
    w5  =  last 180 bars (~15m  on 5m data / ~3h  on 1m data)

Each window produces: return, volatility, rsi, macd, ema_fast, ema_slow,
atr, momentum, volume_spike, vwap_dev.

The flat feature dict has keys like  return_w1, volatility_w3, rsi_w2, …

Version : 5.2.0
"""

from __future__ import annotations

import numpy as np

from live.tick_buffer import TickBuffer
from live.feature_generator import (
    FeatureGenerator,
    _ema, _rsi, _atr,
)


# Bar counts for each named window
WINDOWS = {
    "w1": 6,
    "w2": 12,
    "w3": 36,
    "w4": 60,
    "w5": 180,
}

WINDOW_LABELS = {
    "w1": "~30s",
    "w2": "~1m",
    "w3": "~3m",
    "w4": "~5m",
    "w5": "~15m",
}


def _clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


class MultiWindowFeatures:
    """
    Computes features across all 5 lookback windows from a TickBuffer.

    Returns a flat dict — every key is  <feature>_<window>  e.g.:
        return_w1, volatility_w2, rsi_w3, macd_w4, momentum_w5 …

    Plus scalar fields (not windowed):
        timestamp, symbol, price, volume, spread, order_imbalance, n_bars

    Parameters
    ----------
    buffer : TickBuffer
    """

    def __init__(self, buffer: TickBuffer):
        self.buffer = buffer

    # ------------------------------------------------------------------

    def compute(self) -> dict | None:
        bars = self.buffer.all()
        n    = len(bars)
        if n < 3:
            return None

        closes  = np.array([b.close  for b in bars], dtype=float)
        highs   = np.array([b.high   for b in bars], dtype=float)
        lows    = np.array([b.low    for b in bars], dtype=float)
        volumes = np.array([b.volume for b in bars], dtype=float)
        vwaps   = np.array([b.vwap   for b in bars], dtype=float)
        bids    = np.array([b.bid    for b in bars], dtype=float)
        asks    = np.array([b.ask    for b in bars], dtype=float)

        latest  = bars[-1]
        price   = closes[-1]

        result: dict = {
            "timestamp"       : latest.timestamp,
            "symbol"          : latest.symbol,
            "price"           : round(price, 4),
            "volume"          : float(volumes[-1]),
            "spread"          : latest.spread,
            "order_imbalance" : _order_imb(bids[-1], asks[-1]),
            "n_bars"          : n,
        }

        # Per-window features
        for wname, wsize in WINDOWS.items():
            actual = min(wsize, n)
            sl_c   = closes [-actual:]
            sl_h   = highs  [-actual:]
            sl_l   = lows   [-actual:]
            sl_v   = volumes[-actual:]
            sl_vw  = vwaps  [-actual:]

            # Return
            ret = float((sl_c[-1] / sl_c[0] - 1.0) * 100.0) \
                  if sl_c[0] != 0 else 0.0

            # Volatility
            rets = np.diff(sl_c) / np.where(sl_c[:-1] != 0, sl_c[:-1], 1.0) * 100.0
            vol  = float(np.std(rets, ddof=1)) if len(rets) > 1 else 0.0

            # RSI
            rsi  = _rsi(sl_c, min(14, actual - 1))

            # EMA fast/slow
            ef   = _ema(sl_c, min(9,  actual))
            es   = _ema(sl_c, min(21, actual))
            macd = round(ef - es, 6)

            # ATR
            atr  = _atr(sl_h, sl_l, sl_c, min(14, actual - 1))

            # Momentum
            mom  = float(sl_c[-1] - sl_c[0])

            # Volume spike
            vol_mean  = float(sl_v.mean()) if len(sl_v) else 1.0
            vol_spike = round(float(volumes[-1]) / vol_mean, 4) \
                        if vol_mean > 0 else 1.0

            # VWAP deviation
            vwap_now = float(sl_vw[-1])
            vwap_dev = round((price - vwap_now) / vwap_now * 100.0, 4) \
                       if vwap_now != 0 else 0.0

            result[f"return_{wname}"]      = round(ret,       4)
            result[f"volatility_{wname}"]  = round(vol,       6)
            result[f"rsi_{wname}"]         = round(rsi,       2)
            result[f"ema_fast_{wname}"]    = round(ef,        4)
            result[f"ema_slow_{wname}"]    = round(es,        4)
            result[f"macd_{wname}"]        = round(macd,      6)
            result[f"atr_{wname}"]         = round(atr,       4)
            result[f"momentum_{wname}"]    = round(mom,       4)
            result[f"volume_spike_{wname}"]= vol_spike
            result[f"vwap_dev_{wname}"]    = vwap_dev

        return result

    # ------------------------------------------------------------------

    def feature_names(self) -> list[str]:
        """Return all windowed feature key names."""
        names = []
        for wname in WINDOWS:
            for feat in [
                "return", "volatility", "rsi",
                "ema_fast", "ema_slow", "macd",
                "atr", "momentum", "volume_spike", "vwap_dev",
            ]:
                names.append(f"{feat}_{wname}")
        return names


def _order_imb(bid: float, ask: float) -> float:
    if bid > 0 and ask > 0 and (bid + ask) > 0:
        return round((bid - ask) / (bid + ask), 6)
    return 0.0
