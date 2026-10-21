"""
complexity_estimator.py

Stage 2 — Information Complexity Estimator.

Measures the information content of the current feature vector using:

    1. Shannon entropy   H = -Σ p_i log2(p_i)
       Applied to the normalised absolute feature values — how spread
       out / uncertain the feature distribution is.

    2. PCA effective rank   r = exp(H_eigenvalue)
       Measures how many independent dimensions the feature vector
       effectively occupies.

    3. Feature correlation   corr = mean |off-diagonal| of correlation matrix
       High correlation → low independent information → simpler state.

Combined complexity score C(t) ∈ [0, 1]:

    C(t) = α·H_norm + β·rank_norm + γ·(1 - corr_norm)

    where α=0.4, β=0.4, γ=0.2  (tunable)

Version : 5.2.0
"""

from __future__ import annotations

import numpy as np


# Weights for the three components
_ALPHA = 0.40   # Shannon entropy weight
_BETA  = 0.40   # PCA rank weight
_GAMMA = 0.20   # decorrelation weight

# Feature keys to use from the feature vector (multi-window w4 preferred)
_FEATURE_KEYS = [
    "return_w4", "volatility_w4", "rsi_w4", "macd_w4",
    "atr_w4", "momentum_w4", "volume_spike_w4", "vwap_dev_w4",
    "return_w2", "volatility_w2", "rsi_w2",
    "return_w5", "volatility_w5",
]

# Fallback single-window keys
_FALLBACK_KEYS = [
    "return_pct", "volatility", "rsi", "macd",
    "atr", "momentum", "volume_spike", "vwap_dev",
]


def _extract_values(fv: dict) -> np.ndarray:
    """Pull numeric feature values from the feature vector dict."""
    vals = []
    for k in _FEATURE_KEYS:
        if k in fv:
            vals.append(float(fv[k]))
    if len(vals) < 4:
        for k in _FALLBACK_KEYS:
            if k in fv:
                vals.append(float(fv[k]))
    return np.array(vals, dtype=float)


def _shannon_entropy(values: np.ndarray) -> float:
    """
    Shannon entropy of the normalised absolute feature magnitudes.
    Treats each feature's relative magnitude as a probability mass.
    """
    abs_v = np.abs(values)
    total = abs_v.sum()
    if total == 0:
        return 0.0
    probs = abs_v / total
    probs = probs[probs > 1e-12]
    return float(-np.sum(probs * np.log2(probs)))


def _pca_effective_rank(values: np.ndarray) -> float:
    """
    Effective rank of the feature vector via eigenvalue entropy.
    Uses the outer-product approximation for a single vector.

    For a trajectory of vectors this would be a full SVD —
    here we approximate using the feature values themselves as
    a pseudo-covariance diagonal.
    """
    abs_v = np.abs(values)
    total = abs_v.sum()
    if total == 0:
        return 1.0
    probs = abs_v / total
    probs = probs[probs > 1e-12]
    h = float(-np.sum(probs * np.log2(probs)))
    return float(2 ** h)   # effective rank = 2^H


def _mean_correlation(history: list[np.ndarray]) -> float:
    """
    Mean absolute off-diagonal correlation across recent feature vectors.
    Requires at least 3 vectors; returns 0.5 if insufficient history.
    """
    if len(history) < 3:
        return 0.5
    mat = np.stack(history[-20:], axis=0)   # shape (n_obs, n_features)
    if mat.shape[0] < 3 or mat.shape[1] < 2:
        return 0.5
    # Standardise columns
    std = mat.std(axis=0)
    std[std == 0] = 1.0
    mat = (mat - mat.mean(axis=0)) / std
    corr = np.corrcoef(mat.T)   # (n_features, n_features)
    n = corr.shape[0]
    if n < 2:
        return 0.0
    off_diag = corr[np.triu_indices(n, k=1)]
    return float(np.mean(np.abs(off_diag)))


class ComplexityEstimator:
    """
    Estimates the information complexity of the current market state.

    Maintains a rolling history of feature vectors for correlation
    computation.

    Parameters
    ----------
    history_len : int   how many past feature vectors to keep (default 50)
    alpha       : float Shannon entropy weight   (default 0.40)
    beta        : float PCA rank weight          (default 0.40)
    gamma       : float decorrelation weight     (default 0.20)
    """

    # Maximum theoretical entropy for n features (log2 n)
    _MAX_H     = np.log2(len(_FEATURE_KEYS) + len(_FALLBACK_KEYS))
    _MAX_RANK  = float(len(_FEATURE_KEYS) + len(_FALLBACK_KEYS))

    def __init__(
        self,
        history_len : int   = 50,
        alpha       : float = _ALPHA,
        beta        : float = _BETA,
        gamma       : float = _GAMMA,
    ):
        self.history_len = history_len
        self.alpha       = alpha
        self.beta        = beta
        self.gamma       = gamma
        self._history    : list[np.ndarray] = []

    # ------------------------------------------------------------------

    def estimate(self, fv: dict) -> dict:
        """
        Compute complexity score for the current feature vector.

        Parameters
        ----------
        fv : dict   output of MultiWindowFeatures.compute()

        Returns
        -------
        dict:
            complexity   float  [0, 1]   composite score
            entropy      float           Shannon entropy (nats)
            eff_rank     float           PCA effective rank
            correlation  float  [0, 1]   mean feature correlation
            n_features   int             features used
        """
        values = _extract_values(fv)
        n      = len(values)

        if n == 0:
            return {
                "complexity"  : 0.5,
                "entropy"     : 0.0,
                "eff_rank"    : 1.0,
                "correlation" : 0.5,
                "n_features"  : 0,
            }

        # Update history
        self._history.append(values)
        if len(self._history) > self.history_len:
            self._history.pop(0)

        # Component 1 — Shannon entropy (normalised)
        h      = _shannon_entropy(values)
        h_max  = np.log2(n) if n > 1 else 1.0
        h_norm = float(np.clip(h / h_max, 0.0, 1.0))

        # Component 2 — PCA effective rank (normalised)
        rank      = _pca_effective_rank(values)
        rank_norm = float(np.clip(rank / n, 0.0, 1.0))

        # Component 3 — decorrelation (low corr = more independent info)
        corr      = _mean_correlation(self._history)
        corr_norm = float(np.clip(corr, 0.0, 1.0))
        decorr    = 1.0 - corr_norm

        # Composite score
        complexity = (
            self.alpha * h_norm +
            self.beta  * rank_norm +
            self.gamma * decorr
        )
        complexity = float(np.clip(complexity, 0.0, 1.0))

        return {
            "complexity"  : round(complexity,  4),
            "entropy"     : round(h,            4),
            "eff_rank"    : round(rank,         4),
            "correlation" : round(corr_norm,    4),
            "n_features"  : n,
        }
