"""
regime_detector.py

Classifies each point in a StateTrajectory into one of four market regimes
using quantum-geometric diagnostics.

    Entropy    H(ψ) = -Σ pᵢ log₂(pᵢ)   (measurement entropy of statevector)
    Purity     P(ψ) = Σ pᵢ²             (1 for pure state)
    Velocity   v(t) = 1 - Fidelity(t, t-1)
    Accel      a(t) = v(t) - v(t-1)

Classification rules (applied per velocity step):
    SHOCK    — v  ≥ shock_velocity threshold
    BREAKOUT — v  ≥ high_velocity  AND  a ≥ 0
    REVERSAL — v  ≥ high_velocity  AND  a < 0
    STABLE   — otherwise (low entropy / slow change)

Version : 4.1.0
"""

from __future__ import annotations

import numpy as np

from quantum.state_trajectory import StateTrajectory
from quantum.state_velocity import StateVelocity
from quantum.quantum_state import MultiQubitState

STABLE   = "Stable"
REVERSAL = "Reversal"
BREAKOUT = "Breakout"
SHOCK    = "Shock"

DEFAULT_THRESHOLDS = {
    "shock_velocity" : 0.40,
    "high_velocity"  : 0.15,
}


def _entropy(state: MultiQubitState) -> float:
    probs = state.probabilities()
    probs = probs[probs > 1e-12]
    return float(-np.sum(probs * np.log2(probs)))


def _purity(state: MultiQubitState) -> float:
    return float(np.sum(state.probabilities() ** 2))


class RegimeDetector:
    """
    Assigns a regime label to every velocity step in the trajectory.

    Attributes
    ----------
    trajectory : StateTrajectory
    velocity   : StateVelocity
    thresholds : dict
    regimes    : list[str]    one label per velocity step
    entropies  : list[float]  one per state (all T states)
    purities   : list[float]  one per state
    dates      : list         aligned to regimes
    """

    def __init__(
        self,
        trajectory : StateTrajectory,
        velocity   : StateVelocity,
        thresholds : dict | None = None,
    ):
        self.trajectory = trajectory
        self.velocity   = velocity
        self.thresholds = dict(DEFAULT_THRESHOLDS)
        if thresholds:
            self.thresholds.update(thresholds)

        self.regimes   : list[str]   = []
        self.entropies : list[float] = []
        self.purities  : list[float] = []
        self.dates     : list        = []

        self._classify()

    # ------------------------------------------------------------------

    def _classify(self):
        thr_shock = self.thresholds["shock_velocity"]
        thr_high  = self.thresholds["high_velocity"]

        for state in self.trajectory.states:
            self.entropies.append(_entropy(state))
            self.purities.append(_purity(state))

        for i, v in enumerate(self.velocity.velocities):
            a = self.velocity.accelerations[i - 1] if i > 0 else 0.0

            if v >= thr_shock:
                regime = SHOCK
            elif v >= thr_high and a >= 0:
                regime = BREAKOUT
            elif v >= thr_high and a < 0:
                regime = REVERSAL
            else:
                regime = STABLE

            self.regimes.append(regime)
            self.dates.append(self.velocity.dates_v[i])

    # ------------------------------------------------------------------

    def latest_regime(self) -> str:
        return self.regimes[-1] if self.regimes else STABLE

    def latest_entropy(self) -> float:
        return self.entropies[-1] if self.entropies else 0.0

    def latest_purity(self) -> float:
        return self.purities[-1] if self.purities else 1.0

    def regime_counts(self) -> dict:
        counts = {STABLE: 0, REVERSAL: 0, BREAKOUT: 0, SHOCK: 0}
        for r in self.regimes:
            counts[r] = counts.get(r, 0) + 1
        return counts

    # ------------------------------------------------------------------

    def to_summary(self) -> dict:
        return {
            "latest_regime"  : self.latest_regime(),
            "latest_entropy" : round(self.latest_entropy(), 4),
            "latest_purity"  : round(self.latest_purity(),  4),
            "regime_counts"  : self.regime_counts(),
        }
