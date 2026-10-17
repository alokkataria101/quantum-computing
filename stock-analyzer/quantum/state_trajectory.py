"""
state_trajectory.py

Builds a time-ordered sequence of quantum states |ψ_0>, |ψ_1>, …, |ψ_T>
by re-encoding the stock's rolling statistics for each trading day.

Instead of one static state per stock, we now have a trajectory through
the 32-dimensional Hilbert space — one state per day.

Version : 4.1.0
"""

from __future__ import annotations

import math
import numpy as np
import pandas as pd

from quantum.quantum_state import MultiQubitState
from config import (
    QUANTUM_MAX_VOLATILITY,
    QUANTUM_MAX_STREAK,
    QUANTUM_MAX_TREND,
    QUANTUM_MAX_VOLUME,
)


def _clamp(value: float, low: float = -1.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


_MIN_WINDOW = 5


class StateTrajectory:
    """
    Encodes a stock's historical DataFrame into a time-ordered list of
    MultiQubitState objects — one per trading day (after the warm-up window).

    Rolling features computed over the last `window` rows ending at day t:
        q0  P(Close > Open)   rolling green-day fraction
        q1  Volatility        rolling std of daily returns
        q2  Momentum          (green_days - red_days) / window, normalised
        q3  Trend             linear slope of Close prices over window
        q4  Volume            rolling mean volume (millions)

    Attributes
    ----------
    symbol  : str
    states  : list[MultiQubitState]   one per day after warm-up
    dates   : list                    aligned date for each state
    closes  : list[float]             closing price per state row
    greens  : list[bool]              True if Close > Open on that day
    window  : int
    weights : dict                    learnable normalisation constants
    """

    def __init__(
        self,
        symbol  : str,
        df      : pd.DataFrame,
        window  : int = 20,
        weights : dict | None = None,
    ):
        self.symbol = symbol
        self.df     = df.reset_index(drop=False)
        self.window = max(window, _MIN_WINDOW)

        self.weights = weights or {
            "max_volatility" : float(QUANTUM_MAX_VOLATILITY),
            "max_streak"     : float(QUANTUM_MAX_STREAK),
            "max_trend"      : float(QUANTUM_MAX_TREND),
            "max_volume"     : float(QUANTUM_MAX_VOLUME),
        }

        self.states : list[MultiQubitState] = []
        self.dates  : list                  = []
        self.closes : list[float]           = []
        self.greens : list[bool]            = []

        self._build()

    # ------------------------------------------------------------------

    def _build(self):
        df = self.df
        w  = self.window
        n  = len(df)

        close_arr = df["Close"].values.astype(float)
        open_arr  = df["Open"].values.astype(float)
        vol_arr   = df["Volume"].values.astype(float) \
                    if "Volume" in df.columns else np.zeros(n)

        green_arr   = (close_arr > open_arr).astype(float)
        ret_arr     = np.zeros(n)
        denom       = np.where(close_arr[:-1] != 0, close_arr[:-1], 1.0)
        ret_arr[1:] = np.diff(close_arr) / denom * 100.0

        for t in range(w - 1, n):
            sl_close = close_arr[t - w + 1 : t + 1]
            sl_green = green_arr[t - w + 1 : t + 1]
            sl_ret   = ret_arr  [t - w + 1 : t + 1]
            sl_vol   = vol_arr  [t - w + 1 : t + 1]

            angles = self._encode_window(sl_close, sl_green, sl_ret, sl_vol)
            self.states.append(MultiQubitState(angles))

            # Date — first column after reset_index
            self.dates.append(df.iloc[t, 0])
            self.closes.append(float(close_arr[t]))
            self.greens.append(bool(green_arr[t]))

    # ------------------------------------------------------------------

    def _encode_window(
        self,
        closes  : np.ndarray,
        greens  : np.ndarray,
        returns : np.ndarray,
        volumes : np.ndarray,
    ) -> list[float]:

        w = len(closes)

        # q0 — rolling P(Close > Open)
        p_up     = _clamp(float(greens.mean()), 0.0, 1.0)
        theta_q0 = 2.0 * math.asin(math.sqrt(p_up))

        # q1 — rolling volatility
        vol      = float(np.std(returns, ddof=1)) if w > 1 else 0.0
        theta_q1 = math.pi * _clamp(
            vol / self.weights["max_volatility"], 0.0, 1.0
        )

        # q2 — momentum: green vs red balance over window
        green_d  = float(greens.sum())
        red_d    = float(w - green_d)
        mom      = _clamp(
            (green_d - red_d) / self.weights["max_streak"], -1.0, 1.0
        )
        theta_q2 = (math.pi / 2.0) * (1.0 + mom)

        # q3 — trend: normalised linear slope of closes
        if w > 1 and closes.mean() != 0:
            slope  = float(np.polyfit(np.arange(w, dtype=float), closes, 1)[0])
            trend  = slope / closes.mean() * 100.0
        else:
            trend  = 0.0
        trend_n  = _clamp(trend / self.weights["max_trend"], -1.0, 1.0)
        theta_q3 = (math.pi / 2.0) * (1.0 + trend_n)

        # q4 — rolling average volume (millions)
        avg_vol  = float(volumes.mean()) / 1_000_000.0
        theta_q4 = math.pi * _clamp(
            avg_vol / self.weights["max_volume"], 0.0, 1.0
        )

        return [theta_q0, theta_q1, theta_q2, theta_q3, theta_q4]

    # ------------------------------------------------------------------

    def __len__(self) -> int:
        return len(self.states)

    def get_state(self, t: int) -> MultiQubitState:
        return self.states[t]

    def latest_state(self) -> MultiQubitState:
        return self.states[-1]

    def to_summary(self) -> dict:
        return {
            "symbol"    : self.symbol,
            "window"    : self.window,
            "n_states"  : len(self.states),
            "date_first": str(self.dates[0])  if self.dates else None,
            "date_last" : str(self.dates[-1]) if self.dates else None,
        }
