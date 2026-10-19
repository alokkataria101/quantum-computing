"""preprocessing.py – signal preparation for QFT amplitude encoding.

Public API
----------
compute_representation(prices, mode) -> np.ndarray   (raw numeric series)
pad_to_power_of_two(x, policy)       -> (np.ndarray, int, int)
normalize_amplitude(x)               -> np.ndarray   (L2 unit vector)
prepare_signal(prices, mode, n_qubits, padding_policy)
    -> PrepResult
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal, Optional

import numpy as np
import pandas as pd

# ── types ─────────────────────────────────────────────────────────────────────
RepresentationMode = Literal[
    "raw_prices", "centred_prices", "returns", "centred_returns"
]
PaddingPolicy = Literal["next_pow2", "reject"]


# ─────────────────────────────────────────────────────────────────────────────
# Data structure
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class PrepResult:
    """All preprocessed arrays and metadata in one place."""

    mode: str
    raw_series: np.ndarray       # original (price or return) values, no padding
    padded_series: np.ndarray    # zero-padded to length M = 2^q
    psi: np.ndarray              # L2-normalised amplitude vector (unit norm)
    n_original: int              # length before padding
    n_padded: int                # M = 2^q
    n_zeros_added: int           # M - n_original
    n_qubits: int                # q
    norm_factor: float           # ||raw_series|| before normalisation
    mean_removed: float          # mean subtracted (0.0 if mode is not centred)

    def check_norm(self, tol: float = 1e-9) -> bool:
        """Return True if ||psi||² == 1 within tolerance."""
        return abs(float(np.sum(np.abs(self.psi) ** 2)) - 1.0) < tol


# ─────────────────────────────────────────────────────────────────────────────
# Step 1 – compute the chosen representation
# ─────────────────────────────────────────────────────────────────────────────

def compute_representation(
    prices: pd.Series,
    mode: RepresentationMode = "centred_returns",
) -> tuple[np.ndarray, float]:
    """
    Convert a price series to the chosen numeric representation.

    Returns
    -------
    (array, mean_removed)
        array       : 1-D float64 ndarray of the signal values
        mean_removed: the mean that was subtracted (0.0 for non-centred modes)
    """
    p = prices.to_numpy(dtype=np.float64)

    if mode == "raw_prices":
        return p.copy(), 0.0

    if mode == "centred_prices":
        mu = float(np.mean(p))
        return p - mu, mu

    if mode == "returns":
        if len(p) < 2:
            raise ValueError("Need at least 2 price observations to compute returns.")
        r = 100.0 * (p[1:] / p[:-1] - 1.0)
        return r, 0.0

    if mode == "centred_returns":
        if len(p) < 2:
            raise ValueError("Need at least 2 price observations to compute returns.")
        r = 100.0 * (p[1:] / p[:-1] - 1.0)
        mu = float(np.mean(r))
        return r - mu, mu

    raise ValueError(
        f"Unknown representation mode '{mode}'. "
        "Choose from: raw_prices, centred_prices, returns, centred_returns."
    )


# ─────────────────────────────────────────────────────────────────────────────
# Step 2 – pad to power of two
# ─────────────────────────────────────────────────────────────────────────────

def _is_power_of_two(n: int) -> bool:
    return n > 0 and (n & (n - 1)) == 0


def pad_to_power_of_two(
    x: np.ndarray,
    n_qubits: Optional[int] = None,
    policy: PaddingPolicy = "next_pow2",
) -> tuple[np.ndarray, int, int]:
    """
    Pad x with trailing zeros to length M = 2^q.

    Parameters
    ----------
    x        : Input 1-D array.
    n_qubits : Desired qubit count.  None → automatic (ceil(log2(len(x)))).
    policy   : 'next_pow2' pads; 'reject' raises if len(x) is not already 2^q.

    Returns
    -------
    (padded, n_qubits, n_zeros_added)
    """
    n = len(x)

    if n_qubits is None:
        q = max(1, math.ceil(math.log2(n))) if not _is_power_of_two(n) else int(math.log2(n))
    else:
        q = int(n_qubits)

    M = 2 ** q

    if M < n:
        raise ValueError(
            f"Requested {q} qubits gives M={M} states, "
            f"but the signal has {n} samples (M must be >= n)."
        )

    if policy == "reject" and not _is_power_of_two(n):
        raise ValueError(
            f"Signal length {n} is not a power of two and padding_policy='reject'. "
            "Enable padding or choose a power-of-two observation count."
        )

    padded = np.zeros(M, dtype=np.float64)
    padded[:n] = x
    return padded, q, M - n


# ─────────────────────────────────────────────────────────────────────────────
# Step 3 – L2 normalisation
# ─────────────────────────────────────────────────────────────────────────────

def normalize_amplitude(x: np.ndarray) -> tuple[np.ndarray, float]:
    """
    Normalise x to unit Euclidean norm for amplitude encoding.

    Returns (psi, norm) where psi = x / norm.

    Raises
    ------
    ValueError if ||x|| == 0 (constant or all-zero input after centring).
    """
    norm = float(np.sqrt(np.sum(np.abs(x) ** 2)))
    if norm < 1e-15:
        raise ValueError(
            "Signal norm is zero – the input is constant or all-zeros after "
            "centring. Choose a different representation or date range."
        )
    return x / norm, norm


# ─────────────────────────────────────────────────────────────────────────────
# Convenience: full pipeline
# ─────────────────────────────────────────────────────────────────────────────

def prepare_signal(
    prices: pd.Series,
    mode: RepresentationMode = "centred_returns",
    n_qubits: Optional[int] = None,
    padding_policy: PaddingPolicy = "next_pow2",
) -> PrepResult:
    """
    Run the full preprocessing pipeline:
        prices → representation → pad → L2 normalise → PrepResult
    """
    raw, mean_removed = compute_representation(prices, mode)
    padded, q, n_zeros = pad_to_power_of_two(raw, n_qubits, padding_policy)
    psi, norm = normalize_amplitude(padded)

    return PrepResult(
        mode=mode,
        raw_series=raw,
        padded_series=padded,
        psi=psi,
        n_original=len(raw),
        n_padded=len(padded),
        n_zeros_added=n_zeros,
        n_qubits=q,
        norm_factor=norm,
        mean_removed=mean_removed,
    )
