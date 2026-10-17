"""
walk_forward.py

Runs the experiment over a date range (walk-forward validation).

For each trading day D in [start_date, end_date]:
    - Train on N prior trading days
    - Run static + adaptive modes
    - Record metrics

Aggregates results across all days:
    mean ± std for each metric
    static vs adaptive delta
    per-day breakdown table

Version : 6.1.0
"""

from __future__ import annotations

from datetime import date
from typing   import Callable

import numpy as np
import pandas as pd

from live.trading_calendar  import trading_days_in_range
from live.experiment_runner import ExperimentRunner, ExperimentResult


class WalkForwardValidator:
    """
    Walk-forward validation over a date range.

    Parameters
    ----------
    symbol          : str
    start_date      : date   first prediction day
    end_date        : date   last prediction day
    n_training_days : int    training window (default 100)
    interval        : str    bar interval (default "5m")
    top_k           : int    similarity search k (default 20)
    fwd_bars        : int    bars ahead for pct_change (default 3)
    min_confidence  : float  confidence threshold for signal emission (default 0.10)
    """

    def __init__(
        self,
        symbol          : str,
        start_date      : date,
        end_date        : date,
        n_training_days : int   = 100,
        interval        : str   = "5m",
        top_k           : int   = 20,
        fwd_bars        : int   = 3,
        min_confidence  : float = 0.10,
    ):
        self.symbol          = symbol.upper()
        self.start_date      = start_date
        self.end_date        = end_date
        self.n_training_days = n_training_days
        self.interval        = interval
        self.top_k           = top_k
        self.fwd_bars        = fwd_bars
        self.min_confidence  = min_confidence

        self.results  : list[ExperimentResult] = []
        self.errors   : list[dict]             = []

    # ------------------------------------------------------------------

    def run(
        self,
        progress_cb : Callable[[str], None] | None = None,
    ) -> dict:
        """
        Run walk-forward experiment over all trading days in range.

        Parameters
        ----------
        progress_cb : callable(str) | None

        Returns
        -------
        dict with keys:
            summary_static   dict   aggregated metrics for static mode
            summary_adaptive dict   aggregated metrics for adaptive mode
            summary_delta    dict   mean delta (adaptive − static)
            per_day_df       pd.DataFrame   one row per prediction day
            n_days           int
            n_errors         int
        """
        def _log(msg: str):
            if progress_cb:
                progress_cb(msg)

        days = trading_days_in_range(self.start_date, self.end_date)
        _log(f"Walk-forward: {len(days)} trading days to evaluate.")

        for i, day in enumerate(days):
            _log(f"[{i+1}/{len(days)}] Predicting {day}...")
            runner = ExperimentRunner(
                symbol          = self.symbol,
                prediction_date = day,
                n_training_days = self.n_training_days,
                interval        = self.interval,
                top_k           = self.top_k,
                fwd_bars        = self.fwd_bars,
                min_confidence  = self.min_confidence,
            )
            result = runner.run(progress_cb=_log)

            if result.error:
                self.errors.append({"date": day, "error": result.error})
                _log(f"  ✗ {day}: {result.error}")
            else:
                self.results.append(result)
                _log(f"  ✓ {day}: fid_static={result.static.metrics.get('avg_fidelity','—')}  "
                     f"fid_adaptive={result.adaptive.metrics.get('avg_fidelity','—')}")

        return self._aggregate()

    # ------------------------------------------------------------------

    def _aggregate(self) -> dict:
        if not self.results:
            return {
                "summary_static"  : {},
                "summary_adaptive": {},
                "summary_delta"   : {},
                "per_day_df"      : pd.DataFrame(),
                "n_days"          : 0,
                "n_errors"        : len(self.errors),
            }

        metric_keys = [
            "avg_fidelity", "dir_accuracy", "dir_accuracy_filtered",
            "signal_rate", "mae", "rmse",
            "avg_confidence", "entropy_accuracy", "sharpe_ratio",
        ]

        def _agg(mode_attr: str) -> dict:
            agg = {}
            for key in metric_keys:
                vals = [
                    getattr(r, mode_attr).metrics.get(key, np.nan)
                    for r in self.results
                ]
                vals_clean = [v for v in vals if v == v]   # drop NaN
                agg[key]             = round(float(np.mean(vals_clean)),  4) if vals_clean else None
                agg[f"{key}_std"]    = round(float(np.std(vals_clean)),   4) if vals_clean else None
            return agg

        s_agg = _agg("static")
        a_agg = _agg("adaptive")

        delta = {}
        for key in metric_keys:
            sv = s_agg.get(key)
            av = a_agg.get(key)
            if sv is not None and av is not None:
                if key in ("mae", "rmse"):
                    delta[f"delta_{key}"] = round(sv - av, 4)
                else:
                    delta[f"delta_{key}"] = round(av - sv, 4)

        # Per-day table
        rows = []
        for r in self.results:
            row = {
                "date"            : r.prediction_date,
                "training_bars"   : r.n_training_bars,
                "prediction_bars" : r.n_prediction_bars,
            }
            for key in metric_keys:
                row[f"static_{key}"]   = r.static.metrics.get(key)
                row[f"adaptive_{key}"] = r.adaptive.metrics.get(key)
            for k, v in r.delta.items():
                row[k] = v
            rows.append(row)

        return {
            "summary_static"  : s_agg,
            "summary_adaptive": a_agg,
            "summary_delta"   : delta,
            "per_day_df"      : pd.DataFrame(rows),
            "n_days"          : len(self.results),
            "n_errors"        : len(self.errors),
        }
