"""
next_state_predictor_v2.py

Stage 8 — Next-State Predictor (v2).

Predicts |ψ(t+1)⟩ — the next quantum state — not just a direction.

Method:
    1. Search AdaptiveMemory for top-k states most similar to |ψ_now⟩
       (cross-dimensional fidelity via padding)
    2. Collect their successor states |ψ_k+1⟩
    3. Build predicted |ψ(t+1)⟩ as a fidelity-weighted normalised
       superposition of those successors
    4. Recover approximate Ry angles from the predicted statevector
       (marginal qubit probabilities)
    5. Derive all signals from |ψ(t+1)⟩:
       P(up), P(down), expected return, confidence, stability, risk

Price is one observable derived from the predicted state — not the target.

Version : 6.1.0
"""

from __future__ import annotations

import math
import numpy as np

from live.adaptive_encoder_v2 import AdaptiveState
from live.adaptive_memory      import AdaptiveMemory
from live.qubit_allocator      import MIN_QUBITS, MAX_QUBITS


def _recover_angles(psi: np.ndarray, n_qubits: int) -> list[float]:
    """
    Recover approximate Ry angles from a statevector by computing
    marginal P(|1⟩) for each qubit in the tensor-product structure.
    """
    angles = []
    dim    = 2 ** n_qubits
    for q in range(n_qubits):
        stride = 2 ** (n_qubits - q - 1)
        p1     = 0.0
        for idx in range(dim):
            if (idx // stride) % 2 == 1:
                p1 += abs(psi[idx]) ** 2
        p1 = float(np.clip(p1, 0.0, 1.0))
        angles.append(2.0 * math.asin(math.sqrt(p1)))
    return angles


class NextStatePredictorV2:
    """
    Predicts the next quantum state |ψ(t+1)⟩ using fidelity-weighted
    superposition of successor states from adaptive memory.

    Parameters
    ----------
    memory : AdaptiveMemory
    top_k  : int   neighbours (default 20)
    """

    def __init__(self, memory: AdaptiveMemory, top_k: int = 20):
        self.memory = memory
        self.top_k  = top_k

    # ------------------------------------------------------------------

    def predict(self, current: AdaptiveState, fwd_bars: int = 3) -> dict:
        """
        Predict |ψ(t+1)⟩ and derive all market signals.

        Parameters
        ----------
        current  : AdaptiveState   current quantum state
        fwd_bars : int             bars ahead used for pct_change in memory
                                   search (passed through to AdaptiveMemory.search)

        Returns
        -------
        dict:
            predicted_state  : AdaptiveState | None
            signal           : "BUY" | "SELL" | "HOLD"
            p_up             : float
            p_down           : float
            exp_return       : float   expected % change (over fwd_bars)
            confidence       : float   mean fidelity of matches
            stability        : float   directional unanimity [0,1]
            n_matches        : int
            matches          : list[dict]
        """
        matches = self.memory.search(current, top_k=self.top_k, fwd_bars=fwd_bars)

        if not matches:
            return self._no_signal()

        # Aggregate direction + return
        valid = [m for m in matches if m["next_green"] is not None]
        if not valid:
            return self._no_signal()

        weights    = np.array([m["fidelity"]   for m in valid], dtype=float)
        greens     = np.array([m["next_green"] for m in valid], dtype=float)
        pct_chg    = np.array([m["pct_change"] for m in valid], dtype=float)

        ws = weights.sum()
        if ws < 1e-12:
            weights = np.ones(len(valid))
            ws      = float(len(valid))

        p_up       = float((weights * greens).sum()  / ws)
        exp_return = float((weights * pct_chg).sum() / ws)
        confidence = float(weights.mean())
        stability  = float(2.0 * abs(p_up - 0.5))

        signal = "BUY" if p_up >= 0.55 else ("SELL" if p_up <= 0.45 else "HOLD")

        # Build predicted |ψ(t+1)⟩
        predicted_state = self._build_next_state(matches)

        return {
            "predicted_state" : predicted_state,
            "signal"          : signal,
            "p_up"            : round(p_up,       4),
            "p_down"          : round(1 - p_up,   4),
            "exp_return"      : round(exp_return,  4),
            "confidence"      : round(confidence,  6),
            "stability"       : round(stability,   4),
            "n_matches"       : len(valid),
            "matches"         : matches,
        }

    # ------------------------------------------------------------------

    def _build_next_state(self, matches: list[dict]) -> AdaptiveState | None:
        """
        Build |ψ(t+1)⟩ as fidelity-weighted superposition of
        successor statevectors from memory.
        """
        records = self.memory.records()
        n       = len(records)

        # Collect (weight, successor_state) pairs
        pairs = []
        for m in matches:
            if m["next_green"] is None:
                continue
            for i, rec in enumerate(records):
                if str(rec["timestamp"]) == str(m["timestamp"]) and i + 1 < n:
                    pairs.append((m["fidelity"], records[i + 1]["state"]))
                    break

        if not pairs:
            return None

        # Target dimension = max of successor dimensions
        max_dim = max(len(s.vector) for _, s in pairs)
        max_dim = max(max_dim, 2 ** MIN_QUBITS)

        weights = np.array([w for w, _ in pairs], dtype=complex)
        ws      = weights.sum()
        if abs(ws) < 1e-12:
            weights = np.ones(len(pairs), dtype=complex) / len(pairs)
            ws      = complex(len(pairs))

        psi = np.zeros(max_dim, dtype=complex)
        for w, state in pairs:
            sv = state.padded_vector(max_dim)
            psi += (w / ws) * sv

        norm = np.linalg.norm(psi)
        if norm > 1e-12:
            psi = psi / norm

        # Recover angles — n_qubits from log2(max_dim)
        n_q    = int(round(math.log2(max_dim)))
        n_q    = int(np.clip(n_q, MIN_QUBITS, MAX_QUBITS))
        angles = _recover_angles(psi, n_q)
        labels = [f"pred_q{i}" for i in range(n_q)]

        return AdaptiveState(angles, labels)

    # ------------------------------------------------------------------

    def _no_signal(self) -> dict:
        return {
            "predicted_state" : None,
            "signal"          : "HOLD",
            "p_up"            : 0.5,
            "p_down"          : 0.5,
            "exp_return"      : 0.0,
            "confidence"      : 0.0,
            "stability"       : 0.0,
            "n_matches"       : 0,
            "matches"         : [],
        }
