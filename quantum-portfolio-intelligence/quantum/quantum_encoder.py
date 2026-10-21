"""
quantum_encoder.py

Converts stock statistics into a MultiQubitState.

Version : 2.6.0

Version 2.6 — Multi-Qubit Encoding:
    Five market features are each mapped to one qubit via Ry rotation:

    Qubit  Feature        Gate    Angle formula
    -----  -------        ----    -------------
    q0     Probability    Ry      2 * arcsin(sqrt(P_up))
    q1     Volatility     Ry      pi * clamp(vol / MAX_VOL,  0, 1)
    q2     Momentum       Ry      pi/2 * (1 + clamp(momentum / MAX_STREAK, -1, 1))
    q3     Trend          Ry      pi/2 * (1 + clamp(trend / MAX_TREND, -1, 1))
    q4     Volume         Ry      pi * clamp(avg_vol / MAX_VOLUME, 0, 1)
"""

from __future__ import annotations

import math

from quantum.quantum_state import MultiQubitState
from config import (
    QUANTUM_MAX_VOLATILITY,
    QUANTUM_MAX_STREAK,
    QUANTUM_MAX_TREND,
    QUANTUM_MAX_VOLUME,
)


def _clamp(value: float, low: float = -1.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


class QuantumEncoder:

    # ---------------------------------------------------------

    def __init__(self, summary: dict):

        self.summary = summary

    # ---------------------------------------------------------

    def encode(self) -> MultiQubitState:
        """
        Map five market features onto five Ry angles
        and return a MultiQubitState (5-qubit register).
        """

        # --------------------------------------------------
        # q0 — Probability Up
        # theta = 2 * arcsin(sqrt(P_up))
        # --------------------------------------------------

        p_up = _clamp(self.summary["ProbabilityUp"], 0.0, 1.0)

        theta_q0 = 2.0 * math.asin(math.sqrt(p_up))

        # --------------------------------------------------
        # q1 — Volatility
        # theta = pi * clamp(vol / MAX_VOL, 0, 1)
        # --------------------------------------------------

        vol = self.summary["Volatility"]

        theta_q1 = math.pi * _clamp(
            vol / QUANTUM_MAX_VOLATILITY,
            0.0,
            1.0
        )

        # --------------------------------------------------
        # q2 — Momentum
        # (green_streak - red_streak) / MAX_STREAK → [-1, 1]
        # mapped to [0, pi] so neutral = pi/2
        # --------------------------------------------------

        green = self.summary["LongestGreenStreak"]
        red   = self.summary["LongestRedStreak"]

        momentum = _clamp(
            (green - red) / QUANTUM_MAX_STREAK,
            -1.0,
            1.0
        )

        theta_q2 = (math.pi / 2.0) * (1.0 + momentum)

        # --------------------------------------------------
        # q3 — Trend
        # TrendSlope / MAX_TREND → [-1, 1]
        # mapped to [0, pi] so flat trend = pi/2
        # --------------------------------------------------

        trend = self.summary.get("TrendSlope", 0.0)

        trend_norm = _clamp(
            trend / QUANTUM_MAX_TREND,
            -1.0,
            1.0
        )

        theta_q3 = (math.pi / 2.0) * (1.0 + trend_norm)

        # --------------------------------------------------
        # q4 — Volume
        # AverageVolume (millions) / MAX_VOLUME → [0, 1]
        # mapped to [0, pi]
        # --------------------------------------------------

        avg_vol = self.summary.get("AverageVolume", 0.0)

        theta_q4 = math.pi * _clamp(
            avg_vol / QUANTUM_MAX_VOLUME,
            0.0,
            1.0
        )

        return MultiQubitState([
            theta_q0,
            theta_q1,
            theta_q2,
            theta_q3,
            theta_q4,
        ])

    # ---------------------------------------------------------

    def print(self) -> MultiQubitState:

        state = self.encode()

        state.print()

        return state
