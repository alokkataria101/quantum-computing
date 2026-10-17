"""
state_comparator.py

Given two aligned trajectories — predicted ψ̂₁…ψ̂ₙ and actual ψ₁…ψₙ —
computes a per-bar comparison table.

Columns:
    bar_idx         int
    timestamp       str
    pred_close      float
    actual_close    float
    close_error_pct float
    pred_direction  int   +1 up / -1 down vs prev bar
    actual_direction int
    direction_match bool
    fidelity        float   F(ψ̂, ψ)
    pred_entropy    float
    actual_entropy  float
    confidence      float

Version : 5.3.0
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from live.adaptive_encoder_v2 import AdaptiveState
from live.adaptive_memory      import _fidelity


def _entropy(state: AdaptiveState) -> float:
    probs = state.probabilities()
    probs = probs[probs > 1e-12]
    return float(-np.sum(probs * np.log2(probs)))


class StateComparator:
    """
    Builds a per-bar comparison DataFrame from two aligned trajectories.

    Parameters
    ----------
    predicted_states  : list[AdaptiveState | None]
    actual_states     : list[AdaptiveState | None]
    predicted_closes  : list[float]
    actual_closes     : list[float]
    timestamps        : list[str]
    confidences       : list[float]
    """

    def __init__(
        self,
        predicted_states : list,
        actual_states    : list,
        predicted_closes : list[float],
        actual_closes    : list[float],
        timestamps       : list[str],
        confidences      : list[float] | None = None,
    ):
        self.predicted_states  = predicted_states
        self.actual_states     = actual_states
        self.predicted_closes  = predicted_closes
        self.actual_closes     = actual_closes
        self.timestamps        = timestamps
        self.confidences       = confidences or []

    # ------------------------------------------------------------------

    def build(self) -> pd.DataFrame:
        """Return per-bar comparison DataFrame."""
        n = min(
            len(self.predicted_states),
            len(self.actual_states),
            len(self.predicted_closes),
            len(self.actual_closes),
        )
        rows = []
        for i in range(n):
            ps   = self.predicted_states[i]
            as_  = self.actual_states[i]
            pc   = self.predicted_closes[i]
            ac   = self.actual_closes[i]
            ts   = self.timestamps[i] if i < len(self.timestamps) else ""
            conf = self.confidences[i] if i < len(self.confidences) else 0.0

            # Fidelity
            fid = _fidelity(ps, as_) if (ps and as_) else None

            # Entropy
            pe = _entropy(ps)  if ps  else None
            ae = _entropy(as_) if as_ else None

            # Price error
            err_pct = abs(pc - ac) / ac * 100 if ac != 0 else None

            # Direction vs previous bar
            if i > 0:
                pred_dir   = int(np.sign(pc - self.predicted_closes[i - 1]))
                actual_dir = int(np.sign(ac - self.actual_closes[i - 1]))
                dir_match  = pred_dir == actual_dir
            else:
                pred_dir = actual_dir = dir_match = None

            rows.append({
                "bar"              : i,
                "timestamp"        : str(ts)[:19],
                "pred_close"       : round(pc,       4),
                "actual_close"     : round(ac,       4),
                "close_error_pct"  : round(err_pct,  4) if err_pct is not None else None,
                "pred_direction"   : pred_dir,
                "actual_direction" : actual_dir,
                "direction_match"  : dir_match,
                "fidelity"         : round(fid, 6)  if fid is not None else None,
                "pred_entropy"     : round(pe,  4)  if pe  is not None else None,
                "actual_entropy"   : round(ae,  4)  if ae  is not None else None,
                "confidence"       : round(conf, 4),
            })

        return pd.DataFrame(rows)
