"""
quantum_similarity.py

Stage 6 — Quantum Similarity Search.

Given the current state |ψ_now⟩, search QuantumMemory for the top-20
most similar historical states by fidelity F = |⟨ψ_now|ψ_k⟩|².

Returns each match plus what happened in the next bar (successor).

Version : 5.6.0
"""

from __future__ import annotations

import numpy as np

from live.intraday_encoder import IntradayState
from live.quantum_memory   import QuantumMemory


class QuantumSimilaritySearch:
    """
    Fidelity-based nearest-neighbour search in quantum state space.

    Parameters
    ----------
    memory : QuantumMemory
    top_k  : int            number of neighbours to return (default 20)
    """

    def __init__(self, memory: QuantumMemory, top_k: int = 20):
        self.memory = memory
        self.top_k  = top_k

    # ------------------------------------------------------------------

    def search(self, query: IntradayState) -> list[dict]:
        """
        Find the top-k most similar states to `query`.

        Returns list of dicts sorted by fidelity (desc):
        {
            rank         : int
            fidelity     : float
            timestamp    : str
            price        : float
            green        : bool      this bar green?
            next_price   : float | None
            next_green   : bool  | None
            pct_change   : float | None   (next_price / price - 1) * 100
        }
        """
        records = self.memory.records()
        n       = len(records)
        if n == 0:
            return []

        psi_q = query.statevector()

        # Batch fidelity computation
        scores = []
        for i, rec in enumerate(records):
            psi_k = rec["state"].statevector()
            f     = float(abs(psi_q.conj() @ psi_k) ** 2)
            scores.append((f, i))

        scores.sort(key=lambda x: x[0], reverse=True)
        top = scores[: self.top_k]

        results = []
        for rank, (fidelity, idx) in enumerate(top, start=1):
            rec      = records[idx]
            next_rec = records[idx + 1] if idx + 1 < n else None

            pct = None
            if next_rec and rec["price"] != 0:
                pct = (next_rec["price"] / rec["price"] - 1.0) * 100.0

            results.append({
                "rank"       : rank,
                "fidelity"   : round(fidelity, 6),
                "timestamp"  : rec["timestamp"],
                "price"      : rec["price"],
                "green"      : rec["green"],
                "next_price" : next_rec["price"]  if next_rec else None,
                "next_green" : next_rec["green"]  if next_rec else None,
                "pct_change" : round(pct, 4)       if pct is not None else None,
            })

        return results

    # ------------------------------------------------------------------

    @staticmethod
    def aggregate(matches: list[dict]) -> dict:
        """
        Summarise top-k matches into a weighted signal.

        Returns:
            p_up        float   weighted green fraction
            p_down      float
            exp_return  float   weighted expected % change
            confidence  float   mean fidelity
            n_matches   int
        """
        valid = [m for m in matches if m["next_green"] is not None]
        if not valid:
            return {"p_up": 0.5, "p_down": 0.5,
                    "exp_return": 0.0, "confidence": 0.0, "n_matches": 0}

        w  = np.array([m["fidelity"]   for m in valid], dtype=float)
        g  = np.array([m["next_green"] for m in valid], dtype=float)
        pc = np.array([m["pct_change"] for m in valid], dtype=float)

        ws = w.sum()
        if ws == 0:
            w  = np.ones(len(valid))
            ws = float(len(valid))

        p_up       = float((w * g).sum()  / ws)
        exp_return = float((w * pc).sum() / ws)
        confidence = float(w.mean())

        return {
            "p_up"       : round(p_up,       4),
            "p_down"     : round(1 - p_up,   4),
            "exp_return" : round(exp_return,  4),
            "confidence" : round(confidence,  6),
            "n_matches"  : len(valid),
        }
