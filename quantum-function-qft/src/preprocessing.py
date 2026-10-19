"""preprocessing.py – pad and L2-normalise a sampled signal for QFT amplitude encoding."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

import numpy as np

from .function_parser import SampledSignal


@dataclass
class PrepResult:
    """All preprocessed arrays and metadata."""
    representation: str        # "raw" | "mean_centred" | "normalised_only"
    raw_signal: np.ndarray     # y values after representation choice, before padding
    padded_signal: np.ndarray  # zero-padded to length M = 2^q
    psi: np.ndarray            # L2-normalised amplitude vector (unit norm)
    n_original: int            # length before padding
    n_padded: int              # M = 2^q
    n_zeros_added: int
    n_qubits: int              # q
    norm_factor: float         # ||padded_signal||
    mean_removed: float        # mean subtracted (0 if raw or normalised_only)

    def check_norm(self, tol: float = 1e-9) -> bool:
        return abs(float(np.sum(np.abs(self.psi) ** 2)) - 1.0) < tol


def _next_pow2_qubits(n: int) -> int:
    return max(1, math.ceil(math.log2(max(n, 2))))


def prepare_signal(
    signal: SampledSignal,
    representation: str = "mean_centred",
    n_qubits: Optional[int] = None,
    padding_policy: str = "next_pow2",
) -> PrepResult:
    """
    Pipeline: representation → pad to 2^q → L2 normalise.

    Representations
    ---------------
    raw              – use f(x) as-is
    mean_centred     – subtract mean (removes DC offset before QFT)
    normalised_only  – L2 normalise without mean removal
    """
    y = signal.y.copy()

    if representation == "mean_centred":
        mu = float(np.mean(y))
        y -= mu
    elif representation in ("raw", "normalised_only"):
        mu = 0.0
    else:
        raise ValueError(f"Unknown representation '{representation}'.")

    # Pad
    n = len(y)
    q = n_qubits if n_qubits is not None else _next_pow2_qubits(n)
    M = 2 ** q

    if padding_policy == "reject" and M != n:
        raise ValueError(
            f"n_points={n} is not a power of two and padding_policy='reject'."
        )
    if M < n:
        raise ValueError(f"{q} qubits gives M={M} < n_points={n}.")

    padded = np.zeros(M, dtype=np.float64)
    padded[:n] = y

    # Normalise
    norm = float(np.sqrt(np.sum(padded ** 2)))
    if norm < 1e-15:
        raise ValueError(
            "Signal norm is zero after preprocessing. "
            "Try 'raw' or 'normalised_only' representation, or a non-constant function."
        )
    psi = padded / norm

    return PrepResult(
        representation=representation,
        raw_signal=y,
        padded_signal=padded,
        psi=psi,
        n_original=n,
        n_padded=M,
        n_zeros_added=M - n,
        n_qubits=q,
        norm_factor=norm,
        mean_removed=float(np.mean(signal.y)) if representation == "mean_centred" else 0.0,
    )
