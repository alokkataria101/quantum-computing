"""
feature_generator.py

Computes a rich intraday Feature Vector(t) from the TickBuffer.

Features computed at multiple lookback windows:
    30s, 1m, 3m, 5m, 15m  (in bars — bar count depends on interval)

Outputs per bar:
    timestamp       last bar timestamp
    symbol          ticker
    price           latest close
    return_pct      % change close[-1] vs close[-2]
    volatility      rolling std of returns over window
    vwap            volume-weighted average price
    vwap_dev        (price - vwap) / vwap * 100
    rsi             RSI(14) over available history
    ema_fast        EMA(9)
    ema_slow        EMA(21)
    macd            ema_fast - ema_slow
    atr             Average True Range(14)
    momentum        close - close[n_back]
    volume          latest bar volume
    volume_spike    volume / rolling_mean_volume
    spread          latest bid-ask spread (0 if unavailable)
    order_imbalance (bid - ask) / (bid + ask)  [0 if unavailable]

Version : 5.1.0
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from live.tick_buffer import TickBuffer


def _ema(series: np.ndarray, period: int) -> float:
    """Exponential moving average of the last `period` values."""
    if len(series) < 1:
        return float(series[-1]) if len(series) else 0.0
    k   = 2.0 / (period + 1)
    ema = float(series[0])
    for v in series[1:]:
        ema = float(v) * k + ema * (1 - k)
    return ema


def _rsi(closes: np.ndarray, period: int = 14) -> float:
    if len(closes) < 2:
        return 50.0
    deltas = np.diff(closes[-period - 1:])
    gains  = deltas[deltas > 0]
    losses = -deltas[deltas < 0]
    avg_g  = gains.mean()  if len(gains)  else 0.0
    avg_l  = losses.mean() if len(losses) else 0.0
    if avg_l == 0:
        return 100.0
    rs = avg_g / avg_l
    return round(100.0 - (100.0 / (1.0 + rs)), 4)


def _atr(highs, lows, closes, period: int = 14) -> float:
    n = min(len(highs), len(lows), len(closes))
    if n < 2:
        return 0.0
    trs = []
    for i in range(1, n):
        tr = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i]  - closes[i - 1]),
        )
        trs.append(tr)
    return float(np.mean(trs[-period:]))


class FeatureGenerator:
    """
    Generates a Feature Vector(t) from the most recent bars in a TickBuffer.

    Parameters
    ----------
    buffer       : TickBuffer
    ema_fast     : int   fast EMA period  (default 9)
    ema_slow     : int   slow EMA period  (default 21)
    rsi_period   : int   RSI period       (default 14)
    atr_period   : int   ATR period       (default 14)
    vol_window   : int   volatility window in bars (default 20)
    mom_window   : int   momentum lookback in bars  (default 10)
    """

    def __init__(
        self,
        buffer     : TickBuffer,
        ema_fast   : int = 9,
        ema_slow   : int = 21,
        rsi_period : int = 14,
        atr_period : int = 14,
        vol_window : int = 20,
        mom_window : int = 10,
    ):
        self.buffer     = buffer
        self.ema_fast   = ema_fast
        self.ema_slow   = ema_slow
        self.rsi_period = rsi_period
        self.atr_period = atr_period
        self.vol_window = vol_window
        self.mom_window = mom_window

    # ------------------------------------------------------------------

    def compute(self) -> dict | None:
        """
        Compute features from the current buffer state.

        Returns None if there are fewer than 3 bars available.
        Returns a dict with all features keyed as described in module docstring.
        """
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

        # Return
        ret_pct = float(
            (closes[-1] / closes[-2] - 1.0) * 100.0
        ) if closes[-2] != 0 else 0.0

        # Rolling returns for volatility
        rets    = np.diff(closes[-self.vol_window - 1:]) / \
                  np.where(closes[-self.vol_window - 1:-1] != 0,
                           closes[-self.vol_window - 1:-1], 1.0) * 100.0
        volatility = float(np.std(rets, ddof=1)) if len(rets) > 1 else 0.0

        # VWAP deviation
        vwap_now = vwaps[-1]
        vwap_dev = float(
            (price - vwap_now) / vwap_now * 100.0
        ) if vwap_now != 0 else 0.0

        # RSI
        rsi = _rsi(closes, self.rsi_period)

        # EMA / MACD
        ef   = _ema(closes, self.ema_fast)
        es   = _ema(closes, self.ema_slow)
        macd = round(ef - es, 6)

        # ATR
        atr = _atr(highs, lows, closes, self.atr_period)

        # Momentum
        mom_back = min(self.mom_window, n - 1)
        momentum = float(closes[-1] - closes[-1 - mom_back])

        # Volume spike
        vol_mean = float(np.mean(volumes[-self.vol_window:])) \
                   if len(volumes) >= 2 else float(volumes[-1])
        vol_spike = round(
            float(volumes[-1]) / vol_mean, 4
        ) if vol_mean > 0 else 1.0

        # Spread
        spread = latest.spread

        # Order imbalance
        bid = bids[-1]
        ask = asks[-1]
        if bid > 0 and ask > 0 and (bid + ask) > 0:
            order_imbalance = round((bid - ask) / (bid + ask), 6)
        else:
            order_imbalance = 0.0

        return {
            "timestamp"       : latest.timestamp,
            "symbol"          : latest.symbol,
            "price"           : round(price,       4),
            "return_pct"      : round(ret_pct,     4),
            "volatility"      : round(volatility,  6),
            "vwap"            : round(vwap_now,    4),
            "vwap_dev"        : round(vwap_dev,    4),
            "rsi"             : round(rsi,          2),
            "ema_fast"        : round(ef,           4),
            "ema_slow"        : round(es,           4),
            "macd"            : round(macd,         6),
            "atr"             : round(atr,          4),
            "momentum"        : round(momentum,     4),
            "volume"          : round(float(volumes[-1]), 0),
            "volume_spike"    : vol_spike,
            "spread"          : round(spread,       4),
            "order_imbalance" : order_imbalance,
            "n_bars"          : n,
        }

    # ------------------------------------------------------------------

    def compute_dataframe(self) -> pd.DataFrame:
        """
        Run compute() for every bar in the buffer (rolling computation).
        Returns a DataFrame with one row per bar (from bar vol_window onward).
        """
        all_bars = self.buffer.all()
        rows     = []

        # Temp buffer for rolling window computation
        tmp = TickBuffer(capacity=self.buffer.capacity)
        for bar in all_bars:
            tmp.append(bar)
            fg  = FeatureGenerator(tmp,
                                   self.ema_fast, self.ema_slow,
                                   self.rsi_period, self.atr_period,
                                   self.vol_window, self.mom_window)
            fv  = fg.compute()
            if fv:
                rows.append(fv)

        return pd.DataFrame(rows) if rows else pd.DataFrame()
