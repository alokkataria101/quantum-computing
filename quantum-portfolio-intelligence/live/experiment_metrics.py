"""
experiment_metrics.py

Computes all benchmark metrics for one prediction day.

Given:
    predicted_closes  : list[float]   predicted close prices
    actual_closes     : list[float]   actual close prices
    predicted_states  : list[AdaptiveState]
    actual_states     : list[AdaptiveState]
    predicted_entropy : list[float]
    actual_entropy    : list[float]
    confidences       : list[float]
    signal_mask       : list[bool]    True = signal was issued this bar (v6.1.0)

Returns a flat metrics dict:
    avg_fidelity            float
    dir_accuracy            float  %   all bars (incl. zero-signal bars)
    dir_accuracy_filtered   float  %   only bars where signal was issued
    signal_rate             float  %   % of bars where signal was issued
    mae                     float  %
    rmse                    float  %
    avg_confidence          float
    entropy_accuracy        float  %
    sharpe_ratio            float
    n_bars                  int
    n_signal_bars           int

Version : 6.1.0
"""

from __future__ import annotations

import math
import numpy as np

from live.adaptive_memory import _fidelity
from live.adaptive_encoder_v2 import AdaptiveState

_ENTROPY_THRESHOLD = 0.30   # tolerance for entropy accuracy check


def compute_metrics(
    predicted_closes  : list[float],
    actual_closes     : list[float],
    predicted_states  : list[AdaptiveState | None],
    actual_states     : list[AdaptiveState | None],
    predicted_entropy : list[float],
    actual_entropy    : list[float],
    confidences       : list[float],
    signal_mask       : list[bool] | None = None,
    annualise_factor  : float = 78.0,  # ~78 bars/day for 5-min
) -> dict:
    """
    Compute all benchmark metrics.

    All lists must be aligned (same index = same bar).
    None entries in state lists are skipped for fidelity.
    signal_mask : optional bool list (v6.1.0).  True = signal was issued.
                  Used to compute dir_accuracy_filtered which excludes bars
                  where the model abstained (confidence below threshold).
    """
    n = min(len(predicted_closes), len(actual_closes))
    if n == 0:
        return {"n_bars": 0}

    pred_c = np.array(predicted_closes[:n], dtype=float)
    act_c  = np.array(actual_closes[:n],    dtype=float)

    # ------------------------------------------------------------------
    # 1. Directional accuracy (all bars)
    # ------------------------------------------------------------------
    pred_ret = np.diff(pred_c)
    act_ret  = np.diff(act_c)
    if len(pred_ret) > 0:
        dir_acc = float(np.mean(np.sign(pred_ret) == np.sign(act_ret))) * 100
    else:
        dir_acc = 0.0

    # Filtered directional accuracy — only bars where signal was issued
    # (both the current bar i and bar i-1 must have had a signal for the
    # direction comparison at position i to be meaningful)
    if signal_mask and len(signal_mask) == n:
        mask_arr = np.array(signal_mask, dtype=bool)
        # diff index i corresponds to bars i and i+1; signal must be on at i+1
        sig_diff_mask = mask_arr[1:]   # aligned to pred_ret / act_ret
        if sig_diff_mask.sum() > 0:
            dir_acc_filtered = float(
                np.mean((np.sign(pred_ret) == np.sign(act_ret))[sig_diff_mask])
            ) * 100
            n_signal_bars = int(sig_diff_mask.sum())
            signal_rate   = float(sig_diff_mask.mean()) * 100
        else:
            dir_acc_filtered = 0.0
            n_signal_bars    = 0
            signal_rate      = 0.0
    else:
        dir_acc_filtered = dir_acc    # no mask → same as unfiltered
        n_signal_bars    = n
        signal_rate      = 100.0

    # ------------------------------------------------------------------
    # 2. MAE (% of actual price)
    # ------------------------------------------------------------------
    pct_errors = np.abs(pred_c - act_c) / np.where(act_c != 0, act_c, 1.0) * 100
    mae  = float(np.mean(pct_errors))
    rmse = float(np.sqrt(np.mean(pct_errors ** 2)))

    # ------------------------------------------------------------------
    # 3. Fidelity
    # ------------------------------------------------------------------
    fidelities = []
    ns = min(len(predicted_states), len(actual_states))
    for i in range(ns):
        ps = predicted_states[i]
        as_ = actual_states[i]
        if ps is not None and as_ is not None:
            fidelities.append(_fidelity(ps, as_))
    avg_fidelity = float(np.mean(fidelities)) if fidelities else 0.0

    # ------------------------------------------------------------------
    # 4. Confidence
    # ------------------------------------------------------------------
    avg_confidence = float(np.mean(confidences[:n])) if confidences else 0.0

    # ------------------------------------------------------------------
    # 5. Entropy accuracy
    # ------------------------------------------------------------------
    ne = min(len(predicted_entropy), len(actual_entropy), n)
    if ne > 0:
        pe = np.array(predicted_entropy[:ne])
        ae = np.array(actual_entropy[:ne])
        ent_acc = float(
            np.mean(np.abs(pe - ae) <= _ENTROPY_THRESHOLD)
        ) * 100
    else:
        ent_acc = 0.0

    # ------------------------------------------------------------------
    # 6. Sharpe ratio (on signal bars only — bars where we actually traded)
    # ------------------------------------------------------------------
    if signal_mask and len(signal_mask) == n:
        mask_arr  = np.array(signal_mask, dtype=bool)
        sig_diff  = mask_arr[1:]
        s_pred    = pred_ret[sig_diff] if sig_diff.sum() > 0 else np.array([])
        s_act     = act_ret[sig_diff]  if sig_diff.sum() > 0 else np.array([])
    else:
        s_pred, s_act = pred_ret, act_ret

    strat_returns = np.sign(s_pred) * s_act if len(s_pred) > 0 else np.array([])
    if len(strat_returns) > 1 and strat_returns.std() > 0:
        sharpe = float(
            strat_returns.mean() / strat_returns.std() * math.sqrt(annualise_factor * 252)
        )
    else:
        sharpe = 0.0

    return {
        "n_bars"               : n,
        "n_signal_bars"        : n_signal_bars,
        "signal_rate"          : round(signal_rate,        2),
        "avg_fidelity"         : round(avg_fidelity,       4),
        "dir_accuracy"         : round(dir_acc,            2),
        "dir_accuracy_filtered": round(dir_acc_filtered,   2),
        "mae"                  : round(mae,                4),
        "rmse"                 : round(rmse,               4),
        "avg_confidence"       : round(avg_confidence,     4),
        "entropy_accuracy"     : round(ent_acc,            2),
        "sharpe_ratio"         : round(sharpe,             4),
    }


def compare_modes(static_metrics: dict, adaptive_metrics: dict) -> dict:
    """
    Compute the delta (adaptive − static) for each metric.
    Positive delta = adaptive is better.
    """
    delta = {}
    for key in ["avg_fidelity", "dir_accuracy", "mae",
                "rmse", "avg_confidence", "entropy_accuracy", "sharpe_ratio"]:
        s = static_metrics.get(key, 0.0)
        a = adaptive_metrics.get(key, 0.0)
        # For MAE/RMSE lower is better — negate the delta
        if key in ("mae", "rmse"):
            delta[f"delta_{key}"] = round(s - a, 4)   # positive = adaptive improved
        else:
            delta[f"delta_{key}"] = round(a - s, 4)   # positive = adaptive improved
    return delta
