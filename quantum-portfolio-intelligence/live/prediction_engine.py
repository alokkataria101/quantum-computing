"""
prediction_engine.py

Stage 7 — Prediction Engine.

Case-based reasoning in quantum state space.

Given current state |ψ_now⟩:
    1. Find top-k similar historical states (SimilaritySearch)
    2. Look at what happened after each match
    3. Compute fidelity-weighted expected move
    4. Output: BUY / SELL / HOLD + expected % change

Version : 5.7.0
"""

from __future__ import annotations

from live.intraday_encoder  import IntradayState
from live.quantum_memory    import QuantumMemory
from live.quantum_similarity import QuantumSimilaritySearch


# Signal thresholds
_BUY_THRESHOLD  = 0.55   # p_up ≥ 0.55 → BUY
_SELL_THRESHOLD = 0.45   # p_up ≤ 0.45 → SELL
                          # between    → HOLD


class PredictionEngine:
    """
    Produces a BUY / SELL / HOLD signal with expected return.

    Parameters
    ----------
    memory : QuantumMemory
    top_k  : int            neighbours to use (default 20)
    """

    def __init__(self, memory: QuantumMemory, top_k: int = 20):
        self.memory  = memory
        self.top_k   = top_k
        self._search = QuantumSimilaritySearch(memory, top_k=top_k)

    # ------------------------------------------------------------------

    def predict(self, current: IntradayState) -> dict:
        """
        Generate a prediction for the next bar.

        Returns
        -------
        dict:
            signal       : "BUY" | "SELL" | "HOLD"
            p_up         : float
            p_down       : float
            exp_return   : float   expected % price change
            confidence   : float   mean fidelity of matches [0,1]
            n_matches    : int
            matches      : list[dict]   raw top-k results
        """
        matches    = self._search.search(current)
        aggregated = QuantumSimilaritySearch.aggregate(matches)

        p_up = aggregated["p_up"]

        if p_up >= _BUY_THRESHOLD:
            signal = "BUY"
        elif p_up <= _SELL_THRESHOLD:
            signal = "SELL"
        else:
            signal = "HOLD"

        return {
            "signal"     : signal,
            "p_up"       : aggregated["p_up"],
            "p_down"     : aggregated["p_down"],
            "exp_return" : aggregated["exp_return"],
            "confidence" : aggregated["confidence"],
            "n_matches"  : aggregated["n_matches"],
            "matches"    : matches,
        }
