"""
intraday_encoder.py

Stage 3 — Quantum State Builder (8-qubit intraday register).

Maps the Feature Vector(t) → |ψ(t)⟩ using an 8-qubit product state.

Each qubit encodes one intraday feature via Ry rotation:

    q0  Price           Ry(2·arcsin(√P_norm))   normalised close vs session range
    q1  Return          Ry(π/2·(1+clamp(ret/MAX_RET)))
    q2  Volatility      Ry(π·clamp(vol/MAX_VOL))
    q3  RSI             Ry(π·RSI/100)
    q4  MACD            Ry(π/2·(1+clamp(macd/MAX_MACD)))
    q5  Volume Spike    Ry(π·clamp(spike/MAX_SPIKE, 0, 1))
    q6  Spread          Ry(π·clamp(spread/MAX_SPREAD, 0, 1))
    q7  Momentum        Ry(π/2·(1+clamp(mom/MAX_MOM)))

The statevector lives in a 2^8 = 256-dimensional Hilbert space.

Version : 5.3.0
"""

from __future__ import annotations

import math
import numpy as np


def _clamp(v: float, lo: float = -1.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


# Normalisation constants (overridable by OnlineLearner)
DEFAULT_NORM = {
    "max_ret"    : 3.0,    # max expected % return in one bar
    "max_vol"    : 5.0,    # max expected bar volatility %
    "max_macd"   : 10.0,   # max expected MACD value
    "max_spike"  : 5.0,    # max volume spike multiplier
    "max_spread" : 2.0,    # max spread %
    "max_mom"    : 50.0,   # max momentum (price units)
    "price_lo"   : 0.0,    # session low (updated per session)
    "price_hi"   : 1.0,    # session high (updated per session)
}


class IntradayState:
    """
    8-qubit product state |ψ⟩ = |q0⟩⊗|q1⟩⊗…⊗|q7⟩

    Each qubit is Ry(θ)|0⟩ = cos(θ/2)|0⟩ + sin(θ/2)|1⟩

    Attributes
    ----------
    angles  : list[float]    8 Ry angles
    labels  : list[str]      feature label per qubit
    vector  : np.ndarray     256-element complex statevector
    """

    LABELS = [
        "Price", "Return", "Volatility", "RSI",
        "MACD", "VolSpike", "Spread", "Momentum",
    ]

    def __init__(self, angles: list[float]):
        if len(angles) != 8:
            raise ValueError("IntradayState requires exactly 8 angles.")
        self.angles = angles
        self.vector = self._build()

    def _ry(self, theta: float) -> np.ndarray:
        c = math.cos(theta / 2)
        s = math.sin(theta / 2)
        return np.array([c, s], dtype=complex)

    def _build(self) -> np.ndarray:
        sv = self._ry(self.angles[0])
        for theta in self.angles[1:]:
            sv = np.kron(sv, self._ry(theta))
        return sv

    def statevector(self) -> np.ndarray:
        return self.vector

    def probabilities(self) -> np.ndarray:
        return np.abs(self.vector) ** 2

    def qubit_p1(self, q: int) -> float:
        return math.sin(self.angles[q] / 2) ** 2

    def to_dict(self) -> dict:
        d = {}
        for i, (lbl, ang) in enumerate(zip(self.LABELS, self.angles)):
            d[f"q{i}_{lbl}_angle"] = round(ang, 6)
            d[f"q{i}_{lbl}_P1"]    = round(self.qubit_p1(i), 6)
        return d


class IntradayEncoder:
    """
    Encodes a Feature Vector(t) dict into an IntradayState (8 qubits).

    Parameters
    ----------
    norm : dict   normalisation constants (uses DEFAULT_NORM if None)
    """

    def __init__(self, norm: dict | None = None):
        self.norm = dict(DEFAULT_NORM)
        if norm:
            self.norm.update(norm)

    # ------------------------------------------------------------------

    def encode(self, fv: dict) -> IntradayState:
        """
        Map Feature Vector(t) → IntradayState.

        Parameters
        ----------
        fv : dict   output of FeatureGenerator.compute() or
                    MultiWindowFeatures.compute() (uses w4 = ~5m window)
        """
        n = self.norm

        # q0 — price normalised to [0,1] within session range
        lo  = n["price_lo"]
        hi  = n["price_hi"]
        rng = hi - lo if hi != lo else 1.0
        p_norm = _clamp((fv["price"] - lo) / rng, 0.0, 1.0)
        theta0 = 2.0 * math.asin(math.sqrt(p_norm))

        # q1 — return (use w4 if multi-window, else return_pct)
        ret    = fv.get("return_w4", fv.get("return_pct", 0.0))
        theta1 = (math.pi / 2.0) * (1.0 + _clamp(ret / n["max_ret"]))

        # q2 — volatility
        vol    = fv.get("volatility_w4", fv.get("volatility", 0.0))
        theta2 = math.pi * _clamp(vol / n["max_vol"], 0.0, 1.0)

        # q3 — RSI (use w4 if available)
        rsi    = fv.get("rsi_w4", fv.get("rsi", 50.0))
        theta3 = math.pi * _clamp(rsi / 100.0, 0.0, 1.0)

        # q4 — MACD
        macd   = fv.get("macd_w4", fv.get("macd", 0.0))
        theta4 = (math.pi / 2.0) * (1.0 + _clamp(macd / n["max_macd"]))

        # q5 — volume spike
        spike  = fv.get("volume_spike_w4", fv.get("volume_spike", 1.0))
        theta5 = math.pi * _clamp(spike / n["max_spike"], 0.0, 1.0)

        # q6 — spread
        spread = fv.get("spread", 0.0)
        theta6 = math.pi * _clamp(spread / n["max_spread"], 0.0, 1.0)

        # q7 — momentum
        mom    = fv.get("momentum_w4", fv.get("momentum", 0.0))
        theta7 = (math.pi / 2.0) * (1.0 + _clamp(mom / n["max_mom"]))

        return IntradayState([
            theta0, theta1, theta2, theta3,
            theta4, theta5, theta6, theta7,
        ])

    # ------------------------------------------------------------------

    def update_session_range(self, price_lo: float, price_hi: float):
        """Call once per session with today's price range."""
        self.norm["price_lo"] = price_lo
        self.norm["price_hi"] = price_hi
