"""
similarity_search.py

Nearest-neighbour search in quantum state space using fidelity as the
similarity metric.

Given the current state |ψ_now>, search the StateMemory for the k most
similar historical states and return what happened *after* each match.

This is nearest-neighbour prediction in quantum state space (Step 5).

Version : 4.1.0
"""

from __future__ import annotations

import numpy as np

from quantum.quantum_state import MultiQubitState
from quantum.state_memory import StateMemory
from quantum.fidelity import FidelityCalculator


class SimilaritySearch:
    """
    Performs fidelity-based nearest-neighbour lookup against a StateMemory.

    Parameters
    ----------
    memory : StateMemory
    top_k  : int   number of nearest neighbours to return (default 5)
    """

    def __init__(self, memory: StateMemory, top_k: int = 5):
        self.memory = memory
        self.top_k  = top_k
        self._fc    = FidelityCalculator()

    # ------------------------------------------------------------------

    def search(self, query: MultiQubitState) -> list[dict]:
        """
        Search memory for the top-k states most similar to `query`.

        Returns a list of dicts (sorted by fidelity descending):
            {
                "rank"          : int,
                "fidelity"      : float,
                "date"          : any,
                "green"         : bool,   ← the matched day itself
                "close"         : float,
                "next_green"    : bool | None,   ← what happened next day
                "next_close"    : float | None,
                "pct_change"    : float | None,  ← next_close / close - 1
            }
        """
        records = self.memory.records()
        n       = len(records)

        if n == 0:
            return []

        scores = []
        for i, rec in enumerate(records):
            f = self._fc.fidelity(query, rec["state"])
            scores.append((f, i))

        scores.sort(key=lambda x: x[0], reverse=True)
        top = scores[: self.top_k]

        results = []
        for rank, (fidelity, idx) in enumerate(top, start=1):
            rec      = records[idx]
            next_rec = records[idx + 1] if idx + 1 < n else None

            pct = None
            if next_rec is not None and rec["close"] != 0:
                pct = (next_rec["close"] / rec["close"] - 1.0) * 100.0

            results.append({
                "rank"       : rank,
                "fidelity"   : round(fidelity, 6),
                "date"       : rec["date"],
                "green"      : rec["green"],
                "close"      : rec["close"],
                "next_green" : next_rec["green"]  if next_rec else None,
                "next_close" : next_rec["close"]  if next_rec else None,
                "pct_change" : round(pct, 4)      if pct is not None else None,
            })

        return results

    # ------------------------------------------------------------------

    @staticmethod
    def aggregate(matches: list[dict]) -> dict:
        """
        Summarise top-k matches into a weighted prediction.

        Weights are proportional to fidelity.
        Returns:
            p_up        : weighted fraction of matches where next day was green
            p_down      : 1 - p_up
            exp_return  : fidelity-weighted average of pct_change
            confidence  : mean fidelity of top-k matches
            n_matches   : number of matches with known next-day outcome
        """
        valid = [m for m in matches if m["next_green"] is not None]
        if not valid:
            return {
                "p_up"       : 0.5,
                "p_down"     : 0.5,
                "exp_return" : 0.0,
                "confidence" : 0.0,
                "n_matches"  : 0,
            }

        weights    = np.array([m["fidelity"]   for m in valid], dtype=float)
        greens     = np.array([m["next_green"] for m in valid], dtype=float)
        pct_change = np.array([m["pct_change"] for m in valid], dtype=float)

        w_sum = weights.sum()
        if w_sum == 0:
            weights = np.ones(len(valid))
            w_sum   = float(len(valid))

        p_up       = float(np.dot(weights, greens)     / w_sum)
        exp_return = float(np.dot(weights, pct_change) / w_sum)
        confidence = float(weights.mean())

        return {
            "p_up"       : round(p_up,       4),
            "p_down"     : round(1.0 - p_up, 4),
            "exp_return" : round(exp_return,  4),
            "confidence" : round(confidence,  6),
            "n_matches"  : len(valid),
        }
