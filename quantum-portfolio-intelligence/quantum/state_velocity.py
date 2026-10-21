"""
state_velocity.py

Computes quantum velocity and acceleration from a StateTrajectory.

    Fidelity(t)     = |<ψ_t | ψ_{t-1}>|²
    Velocity(t)     = 1 - Fidelity(t)          (state change per step)
    Acceleration(t) = Velocity(t) - Velocity(t-1)   (d²ψ/dt²)

High velocity  → rapid state change (regime shift candidate)
High accel     → velocity itself accelerating (shock / breakout)

Version : 4.1.0
"""

from __future__ import annotations

import numpy as np

from quantum.state_trajectory import StateTrajectory
from quantum.fidelity import FidelityCalculator


class StateVelocity:
    """
    Derives quantum velocity and acceleration time-series from a trajectory.

    Attributes
    ----------
    trajectory    : StateTrajectory
    fidelities    : list[float]   len = n_states - 1
    velocities    : list[float]   len = n_states - 1
    accelerations : list[float]   len = n_states - 2
    dates_v       : list          aligned to velocities
    dates_a       : list          aligned to accelerations
    """

    def __init__(self, trajectory: StateTrajectory):
        self.trajectory    = trajectory
        self.fidelities    : list[float] = []
        self.velocities    : list[float] = []
        self.accelerations : list[float] = []
        self.dates_v       : list        = []
        self.dates_a       : list        = []
        self._compute()

    # ------------------------------------------------------------------

    def _compute(self):
        states = self.trajectory.states
        dates  = self.trajectory.dates
        n      = len(states)

        if n < 2:
            return

        fc = FidelityCalculator()

        for t in range(1, n):
            f = fc.fidelity(states[t - 1], states[t])
            v = 1.0 - f
            self.fidelities.append(f)
            self.velocities.append(v)
            self.dates_v.append(dates[t])

        for t in range(1, len(self.velocities)):
            a = self.velocities[t] - self.velocities[t - 1]
            self.accelerations.append(a)
            self.dates_a.append(self.dates_v[t])

    # ------------------------------------------------------------------

    def latest_velocity(self) -> float:
        return self.velocities[-1] if self.velocities else 0.0

    def latest_acceleration(self) -> float:
        return self.accelerations[-1] if self.accelerations else 0.0

    def latest_fidelity(self) -> float:
        return self.fidelities[-1] if self.fidelities else 1.0

    def mean_velocity(self) -> float:
        return float(np.mean(self.velocities)) if self.velocities else 0.0

    def velocity_std(self) -> float:
        return float(np.std(self.velocities)) if len(self.velocities) > 1 else 0.0

    # ------------------------------------------------------------------

    def to_summary(self) -> dict:
        return {
            "latest_fidelity"     : round(self.latest_fidelity(),     6),
            "latest_velocity"     : round(self.latest_velocity(),     6),
            "latest_acceleration" : round(self.latest_acceleration(), 6),
            "mean_velocity"       : round(self.mean_velocity(),       6),
            "velocity_std"        : round(self.velocity_std(),        6),
        }
