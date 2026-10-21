"""
trajectory_engine.py

Stage 6 — Quantum Trajectory Engine.

Computes velocity, acceleration, and curvature of the quantum state
trajectory in Hilbert space. These become first-class prediction
features — not just diagnostics.

    Fidelity(t)      = |⟨ψ_t | ψ_{t-1}⟩|²
    Velocity(t)      = 1 − Fidelity(t)
    Acceleration(t)  = Velocity(t) − Velocity(t−1)
    Curvature(t)     = Acceleration(t) − Acceleration(t−1)

    Entropy(t)       = −Σ pᵢ log₂(pᵢ)    (measurement entropy)
    Purity(t)        = Σ pᵢ²

Version : 5.2.0
"""

from __future__ import annotations

import numpy as np

from live.adaptive_memory    import AdaptiveMemory, _fidelity
from live.adaptive_encoder_v2 import AdaptiveState


def _entropy(state: AdaptiveState) -> float:
    probs = state.probabilities()
    probs = probs[probs > 1e-12]
    return float(-np.sum(probs * np.log2(probs)))


def _purity(state: AdaptiveState) -> float:
    return float(np.sum(state.probabilities() ** 2))


class TrajectoryEngine:
    """
    Derives quantum trajectory metrics from an AdaptiveMemory.

    Parameters
    ----------
    memory  : AdaptiveMemory
    window  : int   how many recent states to use (default 100)
    """

    def __init__(self, memory: AdaptiveMemory, window: int = 100):
        self.memory = memory
        self.window = window

    # ------------------------------------------------------------------

    def compute(self) -> dict:
        """
        Compute the full trajectory metric set from recent memory.

        Returns
        -------
        dict:
            fidelities    list[float]
            velocities    list[float]
            accelerations list[float]
            curvatures    list[float]
            entropies     list[float]
            purities      list[float]
            timestamps    list[str]
            n_qubits_hist list[int]

            # Scalars (latest values)
            latest_fidelity     float
            latest_velocity     float
            latest_acceleration float
            latest_curvature    float
            latest_entropy      float
            latest_purity       float
            mean_velocity       float
            velocity_std        float
        """
        records = self.memory.records()[-self.window:]
        n       = len(records)

        fidelities    : list[float] = []
        velocities    : list[float] = []
        accelerations : list[float] = []
        curvatures    : list[float] = []
        entropies     : list[float] = []
        purities      : list[float] = []
        timestamps    : list[str]   = []
        n_qubits_hist : list[int]   = []

        for i, rec in enumerate(records):
            st = rec["state"]
            entropies.append(_entropy(st))
            purities.append(_purity(st))
            n_qubits_hist.append(rec["n_qubits"])
            timestamps.append(str(rec["timestamp"])[:19])

            if i >= 1:
                f = _fidelity(records[i - 1]["state"], st)
                v = 1.0 - f
                fidelities.append(round(f, 6))
                velocities.append(round(v, 6))

            if len(velocities) >= 2:
                a = velocities[-1] - velocities[-2]
                accelerations.append(round(a, 6))

            if len(accelerations) >= 2:
                c = accelerations[-1] - accelerations[-2]
                curvatures.append(round(c, 6))

        return {
            "fidelities"          : fidelities,
            "velocities"          : velocities,
            "accelerations"       : accelerations,
            "curvatures"          : curvatures,
            "entropies"           : entropies,
            "purities"            : purities,
            "timestamps"          : timestamps,
            "n_qubits_hist"       : n_qubits_hist,

            # Scalars
            "latest_fidelity"     : fidelities[-1]    if fidelities    else 1.0,
            "latest_velocity"     : velocities[-1]    if velocities    else 0.0,
            "latest_acceleration" : accelerations[-1] if accelerations else 0.0,
            "latest_curvature"    : curvatures[-1]    if curvatures    else 0.0,
            "latest_entropy"      : entropies[-1]     if entropies     else 0.0,
            "latest_purity"       : purities[-1]      if purities      else 1.0,
            "mean_velocity"       : round(float(np.mean(velocities)), 6) if velocities else 0.0,
            "velocity_std"        : round(float(np.std(velocities)),  6) if velocities else 0.0,
        }
