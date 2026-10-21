"""
research_tracker.py

v11.0.1 — Actual vs Predicted Research Tracker.

Accumulates, within a single trading session, pairs of:
    (timestamp, actual_close, predicted_close, signal, exp_return, confidence)

Design rules
------------
* Prediction recorded at time T refers to the *next* bar T+1.
* Actual close for T is recorded when the bar at T arrives.
* Because we predict 30 minutes ahead we keep two queues:
    - _pending  : {bar_ts → prediction_dict}  written when prediction fires
    - records   : final resolved row when actual bar T+1 is observed

This gives the "prediction lags live data by 30 min" display the caller
wants: the prediction line is plotted 30 minutes *before* the bar it
targets, while the actual line reflects the close as it happens.

Version : 11.0.1
"""

from __future__ import annotations

import re
from collections import deque
from dataclasses import dataclass, field


def _normalise_ts(ts: str) -> str:
    """
    Normalise any timestamp string to 'YYYY-MM-DD HH:MM:SS'.

    Strips timezone offset (+05:30, Z, …) and sub-second precision so that
    keys written by record_prediction() always match keys looked up by
    record_actual() regardless of how Yahoo Finance serialises the timestamp.
    """
    s = str(ts).strip()
    # Remove timezone designators: +HH:MM, -HH:MM, Z
    s = re.sub(r"[+-]\d{2}:\d{2}$", "", s).rstrip("Z").strip()
    # Truncate to 19 characters: YYYY-MM-DD HH:MM:SS
    return s[:19]


@dataclass
class ResearchRecord:
    """
    One matched (actual, predicted) data point.

    ``correct_dir`` is set externally by ``record_actual()`` when the actual
    bar arrives and the pending prediction is resolved.  It is not computed
    in ``__post_init__`` because the open price needed for the direction check
    is only available at resolution time.
    """
    timestamp        : str          # bar timestamp (YYYY-MM-DD HH:MM:SS)
    actual_close     : float        # observed close for this bar
    predicted_close  : float        # predicted close made 30 min earlier
    signal           : str          # BUY / SELL / HOLD at prediction time
    exp_return       : float        # expected % return at prediction time
    confidence       : float        # confidence at prediction time
    p_up             : float        # P(up) at prediction time
    error_pct        : float = 0.0  # |actual - predicted| / actual × 100
    correct_dir      : bool  = False # did signal direction match actual direction?

    def __post_init__(self):
        if self.actual_close and self.actual_close != 0:
            self.error_pct = round(
                abs(self.actual_close - self.predicted_close)
                / self.actual_close * 100,
                4,
            )


class ResearchTracker:
    """
    Session-scoped Actual vs Predicted tracker.

    Parameters
    ----------
    capacity   : int   max records to keep in memory  (default 390 = 1 trading day of 1-min bars)
    fwd_bars   : int   number of bars ahead the prediction targets  (default 30)
    """

    def __init__(self, capacity: int = 390, fwd_bars: int = 30):
        self.capacity  = capacity
        self.fwd_bars  = fwd_bars

        # circular buffer of resolved records
        self._records  : deque[ResearchRecord] = deque(maxlen=capacity)

        # pending predictions keyed by the *target* bar timestamp
        # (i.e. the bar fwd_bars ahead of when the prediction was made)
        self._pending  : dict[str, dict] = {}

        # raw price history for reference
        self._prices   : deque[tuple[str, float]] = deque(maxlen=capacity)

        # running accuracy
        self.n_total   : int = 0
        self.n_correct : int = 0

    # ------------------------------------------------------------------
    # Ingestion
    # ------------------------------------------------------------------

    def record_prediction(
        self,
        prediction_ts   : str,
        predicted_close : float,
        signal          : str,
        exp_return      : float,
        confidence      : float,
        p_up            : float,
        target_ts       : str = "",
    ):
        """
        Store a prediction made at prediction_ts.

        Parameters
        ----------
        prediction_ts   : timestamp when the prediction was made
        predicted_close : the predicted price value
        signal          : BUY / SELL / HOLD
        exp_return      : expected % change
        confidence      : model confidence [0,1]
        p_up            : P(up) [0,1]
        target_ts       : optional explicit timestamp for the target bar;
                          if blank, uses prediction_ts as key (caller resolves later)
        """
        key = _normalise_ts(target_ts or prediction_ts)
        self._pending[key] = {
            "prediction_ts"   : _normalise_ts(prediction_ts),
            "predicted_close" : predicted_close,
            "signal"          : signal,
            "exp_return"      : exp_return,
            "confidence"      : confidence,
            "p_up"            : p_up,
        }

    def record_actual(
        self,
        bar_ts       : str,
        actual_close : float,
        actual_open  : float,
    ):
        """
        Record an observed bar; if there is a pending prediction for this
        timestamp, produce a resolved ResearchRecord.

        Parameters
        ----------
        bar_ts       : bar timestamp
        actual_close : observed close price
        actual_open  : observed open price (used for direction check)
        """
        bar_ts = _normalise_ts(bar_ts)
        self._prices.append((bar_ts, actual_close))

        if bar_ts in self._pending:
            pred = self._pending.pop(bar_ts)
            actual_green    = actual_close >= actual_open
            predicted_green = pred["p_up"] >= 0.5

            error_pct = 0.0
            if actual_close and actual_close != 0:
                error_pct = abs(actual_close - pred["predicted_close"]) \
                            / actual_close * 100

            rec = ResearchRecord(
                timestamp        = bar_ts,
                actual_close     = actual_close,
                predicted_close  = pred["predicted_close"],
                signal           = pred["signal"],
                exp_return       = pred["exp_return"],
                confidence       = pred["confidence"],
                p_up             = pred["p_up"],
                error_pct        = round(error_pct, 4),
                correct_dir      = (actual_green == predicted_green),
            )
            self._records.append(rec)
            self.n_total += 1
            if rec.correct_dir:
                self.n_correct += 1

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    def records(self) -> list[ResearchRecord]:
        return list(self._records)

    def prices(self) -> list[tuple[str, float]]:
        """All recorded actual prices (timestamp, close)."""
        return list(self._prices)

    def pending_predictions(self) -> dict[str, dict]:
        """Predictions not yet matched to an actual bar."""
        return dict(self._pending)

    def accuracy(self) -> float:
        return round(self.n_correct / self.n_total, 4) if self.n_total else 0.0

    def mean_error_pct(self) -> float:
        recs = list(self._records)
        if not recs:
            return 0.0
        return round(sum(r.error_pct for r in recs) / len(recs), 4)

    def reset(self):
        """Clear all records (call at session start)."""
        self._records.clear()
        self._pending.clear()
        self._prices.clear()
        self.n_total   = 0
        self.n_correct = 0
