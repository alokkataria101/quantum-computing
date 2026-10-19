"""classical_analysis.py – NumPy FFT baseline and frequency-domain utilities.

Public API
----------
classical_fft(psi, unnorm_signal)  -> ClassicalFFTResult
dominant_frequencies(power, M, top_k)  -> list[FrequencyBin]
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

import numpy as np


# ─────────────────────────────────────────────────────────────────────────────
# Data structures
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class FrequencyBin:
    """A single identified spectral peak."""

    bin_index: int
    frequency: float          # cycles per sample  (k / M)
    period_samples: float     # M / k  (trading observations); inf for k=0
    power: float              # |A[k]|^2
    is_dc: bool               # True for bin 0
    is_negative_freq: bool    # True for k > M/2

    def period_str(self, label: str = "observations") -> str:
        if self.is_dc:
            return "DC (mean level)"
        if math.isinf(self.period_samples):
            return "DC (mean level)"
        return f"{self.period_samples:.1f} {label}"


@dataclass
class ClassicalFFTResult:
    """Output of the classical FFT analysis."""

    M: int
    # Normalised FFT (matches QFT sign convention: positive exponent / ifft)
    amplitudes_qft_convention: np.ndarray   # complex, shape (M,)
    power_qft_convention: np.ndarray        # |A[k]|^2, shape (M,)

    # Standard signal-processing FFT (forward, negative exponent)
    amplitudes_standard: np.ndarray         # complex, shape (M,)
    power_standard: np.ndarray              # |A[k]|^2 / M, shape (M,)

    # Unnormalised signal FFT (on raw series before L2 normalisation)
    unnorm_amplitudes: Optional[np.ndarray] = None
    unnorm_power: Optional[np.ndarray] = None

    frequency_coords: np.ndarray = field(default_factory=lambda: np.array([]))

    def check_normalisation(self, tol: float = 1e-6) -> bool:
        """Parseval: sum of power spectrum should equal 1 for unit-norm psi."""
        return abs(float(np.sum(self.power_qft_convention)) - 1.0) < tol


# ─────────────────────────────────────────────────────────────────────────────
# Main FFT function
# ─────────────────────────────────────────────────────────────────────────────

def classical_fft(
    psi: np.ndarray,
    unnorm_signal: Optional[np.ndarray] = None,
) -> ClassicalFFTResult:
    """
    Compute classical DFT of the normalised amplitude vector psi.

    Two conventions are provided:

    QFT convention (positive exponent):
        A[k] = (1/√M) Σ_j psi[j] · exp(+2πijk/M)
             = numpy.fft.ifft(psi) * sqrt(M)

    Standard signal-processing convention (negative exponent):
        A_std[k] = Σ_j psi[j] · exp(-2πijk/M)
                 = numpy.fft.fft(psi)

    Parameters
    ----------
    psi           : L2-normalised input vector (unit norm), length M.
    unnorm_signal : Original (un-normalised) signal for a raw reference FFT.

    Returns
    -------
    ClassicalFFTResult
    """
    M = len(psi)
    freqs = np.arange(M) / M

    # QFT-convention amplitudes
    A_qft = np.fft.ifft(psi) * math.sqrt(M)
    power_qft = np.abs(A_qft) ** 2

    # Standard FFT amplitudes
    A_std = np.fft.fft(psi)
    # Normalise so power sums to 1 (divide by M to match Parseval for unit psi)
    power_std = (np.abs(A_std) ** 2) / M

    # Unnormalised signal
    unnorm_A = unnorm_power = None
    if unnorm_signal is not None:
        unnorm_A = np.fft.fft(unnorm_signal)
        unnorm_power = np.abs(unnorm_A) ** 2 / len(unnorm_signal)

    return ClassicalFFTResult(
        M=M,
        amplitudes_qft_convention=A_qft,
        power_qft_convention=power_qft,
        amplitudes_standard=A_std,
        power_standard=power_std,
        unnorm_amplitudes=unnorm_A,
        unnorm_power=unnorm_power,
        frequency_coords=freqs,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Frequency peak identification
# ─────────────────────────────────────────────────────────────────────────────

def dominant_frequencies(
    power: np.ndarray,
    M: int,
    top_k: int = 8,
    exclude_dc: bool = False,
) -> list[FrequencyBin]:
    """
    Identify the top-k spectral peaks by power.

    Parameters
    ----------
    power      : Power spectrum array of length M.
    M          : Total number of frequency bins (= len(power)).
    top_k      : Number of peaks to return.
    exclude_dc : If True, skip bin 0.

    Returns
    -------
    List of FrequencyBin sorted by descending power.
    """
    sorted_indices = np.argsort(power)[::-1]
    result: list[FrequencyBin] = []

    for idx in sorted_indices:
        k = int(idx)
        if exclude_dc and k == 0:
            continue

        freq = k / M
        period = math.inf if k == 0 else M / k
        is_neg = k > M // 2

        result.append(FrequencyBin(
            bin_index=k,
            frequency=freq,
            period_samples=period,
            power=float(power[k]),
            is_dc=(k == 0),
            is_negative_freq=is_neg,
        ))

        if len(result) >= top_k:
            break

    return result


# ─────────────────────────────────────────────────────────────────────────────
# Positive half-spectrum utilities
# ─────────────────────────────────────────────────────────────────────────────

def half_spectrum(power: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    Return (k_indices, one-sided_power) for k = 0 … M//2.

    For k in 1 … M//2 - 1 the power is doubled to account for the negative-
    frequency mirror.  Bin 0 (DC) and bin M/2 (Nyquist) are not doubled.
    """
    M = len(power)
    half = M // 2 + 1
    ks = np.arange(half)
    p = power[:half].copy()
    p[1:half - 1] *= 2.0
    return ks, p
