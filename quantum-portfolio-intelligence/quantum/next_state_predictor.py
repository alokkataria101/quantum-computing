"""
next_state_predictor.py

Predicts the next quantum state |ψ(t+1)> from the current state |ψ_now>
by aggregating the successors of the top-k nearest historical neighbours.

Outputs:
    |ψ(t+1)>  — predicted next state (normalised weighted average)
    P(up)     — probability the next day is green (Close > Open)
    P(down)   — 1 - P(up)
    confidence — mean fidelity of the k matches used

Version : 4.1.0
"""

from __future__ import annotations

import numpy as np

from quantum.quantum_state import MultiQubitState
from quantum.state_memory import StateMemory
from quantum.similarity_search import SimilaritySearch


class NextStatePredictor:
    """
    Predicts |ψ(t+1)> using fidelity-weighted superposition of successor states.

    Parameters
    ----------
    memory : StateMemory
    top_k  : int   nearest neighbours to use (default 5)
    """

    def __init__(self, memory: StateMemory, top_k: int = 5):
        self.memory = memory
        self.top_k  = top_k
        self._search = SimilaritySearch(memory, top_k=top_k)

    # ------------------------------------------------------------------

    def predict(self, current: MultiQubitState) -> dict:
        """
        Given the current state, return the next-state forecast.

        Returns
        -------
        dict with keys:
            predicted_state : MultiQubitState | None
            p_up            : float
            p_down          : float
            exp_return      : float   (expected % change)
            confidence      : float   (mean fidelity of matches)
            n_matches       : int
            matches         : list[dict]  (raw top-k results)
        """
        matches    = self._search.search(current)
        aggregated = SimilaritySearch.aggregate(matches)

        predicted_state = self._build_next_state(matches)

        return {
            "predicted_state" : predicted_state,
            "p_up"            : aggregated["p_up"],
            "p_down"          : aggregated["p_down"],
            "exp_return"      : aggregated["exp_return"],
            "confidence"      : aggregated["confidence"],
            "n_matches"       : aggregated["n_matches"],
            "matches"         : matches,
        }

    # ------------------------------------------------------------------

    def _build_next_state(self, matches: list[dict]) -> MultiQubitState | None:
        """
        Build |ψ(t+1)> as a fidelity-weighted average of successor statevectors,
        then find the closest valid MultiQubitState by re-normalising.
        """
        records = self.memory.records()
        n       = len(records)

        valid = []
        for m in matches:
            if m["next_green"] is None:
                continue
            # find successor statevector in memory
            for i, rec in enumerate(records):
                if rec["date"] == m["date"] and i + 1 < n:
                    valid.append((m["fidelity"], records[i + 1]["state"]))
                    break

        if not valid:
            return None

        weights = np.array([w for w, _ in valid], dtype=complex)
        w_sum   = weights.sum()
        if abs(w_sum) < 1e-12:
            weights = np.ones(len(valid), dtype=complex) / len(valid)
        else:
            weights = weights / w_sum

        # Weighted sum of statevectors
        dim    = len(valid[0][1].statevector())
        psi    = np.zeros(dim, dtype=complex)
        for w, state in valid:
            psi += (w / w_sum) * state.statevector()

        # Normalise
        norm = np.linalg.norm(psi)
        if norm > 1e-12:
            psi = psi / norm

        # Recover approximate angles from marginal probabilities of the
        # predicted statevector (treat as product state approximation)
        import math
        angles = []
        for q in range(5):
            # P(|1>) for qubit q from the 5-qubit tensor product structure
            dim_each = 2
            n_qubits = 5
            stride   = 2 ** (n_qubits - q - 1)
            p1       = 0.0
            for idx in range(dim):
                bit = (idx // stride) % dim_each
                if bit == 1:
                    p1 += abs(psi[idx]) ** 2
            p1 = float(np.clip(p1, 0.0, 1.0))
            angles.append(2.0 * math.asin(math.sqrt(p1)))

        return MultiQubitState(angles)
