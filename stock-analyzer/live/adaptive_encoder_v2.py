"""
adaptive_encoder_v2.py

Stage 4 — Adaptive Quantum Encoder.

Encodes the top-n most informative features into an n-qubit product
state |ψ(t)⟩ where n = QubitAllocator.current_n.

Key differences from v5.1 IntradayEncoder:
    - n_qubits is dynamic (3–12), not fixed at 8
    - Feature selection: picks the top-n features by absolute magnitude
      (most informative at this moment)
    - Rotation angles θ(t) are learnable — they start at the base
      encoding formula and drift with each CircuitAdaptor correction
    - Returns AdaptiveState (variable-dim statevector)

Version : 5.2.0
"""

from __future__ import annotations

import math
import numpy as np

from live.qubit_allocator import QubitAllocator


def _clamp(v: float, lo: float = -1.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


# All candidate features in priority order (most market-informative first)
_FEATURE_PRIORITY = [
    # Window 4 (~5m) — primary signals
    ("return_w4",       "return",       "mid",   3.0),
    ("volatility_w4",   "volatility",   "pos",   5.0),
    ("rsi_w4",          "rsi",          "rsi",   100.0),
    ("macd_w4",         "macd",         "mid",   10.0),
    ("momentum_w4",     "momentum",     "mid",   50.0),
    ("volume_spike_w4", "vol_spike",    "pos",   5.0),
    ("vwap_dev_w4",     "vwap_dev",     "mid",   3.0),
    ("atr_w4",          "atr",          "pos",   20.0),
    # Window 2 (~1m) — fast signals
    ("return_w2",       "ret_fast",     "mid",   3.0),
    ("volatility_w2",   "vol_fast",     "pos",   5.0),
    ("rsi_w2",          "rsi_fast",     "rsi",   100.0),
    # Window 5 (~15m) — slow signals
    ("return_w5",       "ret_slow",     "mid",   3.0),
    ("volatility_w5",   "vol_slow",     "pos",   5.0),
    # Fallbacks (single-window)
    ("return_pct",      "return",       "mid",   3.0),
    ("volatility",      "volatility",   "pos",   5.0),
    ("rsi",             "rsi",          "rsi",   100.0),
    ("macd",            "macd",         "mid",   10.0),
    ("momentum",        "momentum",     "mid",   50.0),
    ("volume_spike",    "vol_spike",    "pos",   5.0),
    ("vwap_dev",        "vwap_dev",     "mid",   3.0),
]

# angle_type:
#   "pos"  → Ry = π · clamp(v/max, 0, 1)
#   "mid"  → Ry = π/2 · (1 + clamp(v/max, -1, 1))
#   "rsi"  → Ry = π · clamp(v/100, 0, 1)


class AdaptiveState:
    """
    Variable-dimensional quantum product state |ψ(t)⟩.

    |ψ⟩ = |q0⟩ ⊗ |q1⟩ ⊗ … ⊗ |q_{n-1}⟩
    each qubit = Ry(θ_i)|0⟩

    Attributes
    ----------
    n_qubits    : int
    angles      : list[float]
    labels      : list[str]
    vector      : np.ndarray   (2^n_qubits,) complex
    """

    def __init__(self, angles: list[float], labels: list[str]):
        self.n_qubits = len(angles)
        self.angles   = angles
        self.labels   = labels
        self.vector   = self._build()

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
        return float(math.sin(self.angles[q] / 2) ** 2)

    def padded_vector(self, target_dim: int) -> np.ndarray:
        """Pad statevector to target_dim with zeros (for cross-dim fidelity)."""
        v = np.zeros(target_dim, dtype=complex)
        n = min(len(self.vector), target_dim)
        v[:n] = self.vector[:n]
        norm = np.linalg.norm(v)
        return v / norm if norm > 1e-12 else v

    def to_dict(self) -> dict:
        return {
            "n_qubits": self.n_qubits,
            **{f"q{i}_{lbl}_angle": round(a, 6)
               for i, (lbl, a) in enumerate(zip(self.labels, self.angles))},
            **{f"q{i}_{lbl}_P1": round(self.qubit_p1(i), 6)
               for i, lbl in enumerate(self.labels)},
        }


class AdaptiveEncoderV2:
    """
    Encodes the top-n features into an n-qubit AdaptiveState.

    Parameters
    ----------
    allocator  : QubitAllocator   determines n_qubits(t)
    offsets    : dict[str→float]  per-feature learnable angle offsets
                                  (updated by CircuitAdaptor)
    norm       : dict[str→float]  per-feature normalisation caps
    """

    def __init__(
        self,
        allocator : QubitAllocator,
        offsets   : dict | None = None,
        norm      : dict | None = None,
    ):
        self.allocator = allocator
        self.offsets   : dict[str, float] = offsets or {}
        self.norm      : dict[str, float] = norm    or {}

    # ------------------------------------------------------------------

    def encode(self, fv: dict, timestamp: str = "") -> AdaptiveState:
        """
        Encode feature vector into an AdaptiveState.

        1. Ask QubitAllocator for n_qubits
        2. Select top-n features by availability + priority
        3. Map each to a Ry angle + apply learned offset
        4. Return AdaptiveState
        """
        n_qubits = self.allocator.current_n

        # Select top-n features from priority list
        selected = []
        for fkey, label, atype, cap in _FEATURE_PRIORITY:
            if fkey in fv:
                selected.append((fkey, label, atype, cap))
            if len(selected) == n_qubits:
                break

        # Pad with zeros if not enough features
        while len(selected) < n_qubits:
            selected.append((None, f"pad{len(selected)}", "pos", 1.0))

        angles = []
        labels = []
        for fkey, label, atype, cap in selected:
            val    = float(fv.get(fkey, 0.0)) if fkey else 0.0
            offset = self.offsets.get(label, 0.0)
            cap    = self.norm.get(label, cap)
            angle  = self._to_angle(val, atype, cap)
            # Apply learned offset and clamp to valid range
            angle  = float(np.clip(angle + offset, 0.0, math.pi))
            angles.append(angle)
            labels.append(label)

        return AdaptiveState(angles, labels)

    # ------------------------------------------------------------------

    def _to_angle(self, val: float, atype: str, cap: float) -> float:
        if atype == "pos":
            return math.pi * _clamp(val / cap, 0.0, 1.0)
        elif atype == "rsi":
            return math.pi * _clamp(val / 100.0, 0.0, 1.0)
        else:   # "mid"
            return (math.pi / 2.0) * (1.0 + _clamp(val / cap, -1.0, 1.0))

    # ------------------------------------------------------------------

    def update_offset(self, label: str, delta: float):
        """Apply a correction delta to a feature's angle offset."""
        current = self.offsets.get(label, 0.0)
        self.offsets[label] = float(np.clip(current + delta, -0.5, 0.5))

    def to_summary(self) -> dict:
        return {
            "current_n_qubits" : self.allocator.current_n,
            "n_offsets"        : len(self.offsets),
            "offsets"          : {k: round(v, 6) for k, v in self.offsets.items()},
        }
