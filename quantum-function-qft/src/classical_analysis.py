"""classical_analysis.py – DFT/FFT and ground-truth peak comparison.

Public API
----------
run_dft(prep, signal)          -> DFTResult
find_peaks(power, M, ...)      -> list[SpectralPeak]
compare_to_ground_truth(peaks, signal, prep) -> list[PeakMatch]
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from scipy.signal import find_peaks as scipy_find_peaks

from .function_parser import SampledSignal
from .preprocessing import PrepResult


# ─────────────────────────────────────────────────────────────────────────────
# Data structures
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class SpectralPeak:
    """One identified peak in the power spectrum."""
    bin_index: int
    freq_per_unit: float       # cycles / x-unit
    angular_freq: float        # rad / x-unit
    period: float              # x-units per cycle (inf for DC)
    power: float               # |A[k]|^2
    power_fraction: float      # power / total_power
    is_dc: bool
    is_negative_freq: bool     # k > M/2


@dataclass
class PeakMatch:
    """Comparison of a detected DFT peak against a known analytical component."""
    detected: SpectralPeak
    matched_label: Optional[str]      # label of the closest known component
    expected_bin: Optional[float]     # exact expected bin (may be non-integer)
    expected_freq: Optional[float]    # expected cycles/unit
    bin_error: Optional[float]        # |detected_bin - expected_bin|
    amplitude_known: Optional[float]  # known amplitude
    is_close: bool                    # True if bin_error < 1.5


@dataclass
class DFTResult:
    """Full output of classical FFT analysis."""
    M: int
    # QFT-convention: A[k] = ifft(psi)*sqrt(M)  (positive exponent)
    amplitudes: np.ndarray         # complex, shape (M,)
    power: np.ndarray              # |A[k]|^2, shape (M,)
    # Standard FFT convention (negative exponent, for reference)
    amplitudes_std: np.ndarray
    power_std: np.ndarray
    # Frequency axis
    freq_coords: np.ndarray        # k / M  (cycles per sample)
    freq_per_unit: np.ndarray      # k / x_span  (cycles per x-unit)
    # Peaks
    peaks: list[SpectralPeak] = field(default_factory=list)
    peak_matches: list[PeakMatch] = field(default_factory=list)

    def half_power(self) -> tuple[np.ndarray, np.ndarray]:
        """One-sided power spectrum (bins 0 … M//2), interior bins doubled."""
        half = self.M // 2 + 1
        p = self.power[:half].copy()
        p[1:half - 1] *= 2.0
        return self.freq_per_unit[:half], p

    def check_parseval(self, tol: float = 1e-6) -> bool:
        return abs(float(np.sum(self.power)) - 1.0) < tol


# ─────────────────────────────────────────────────────────────────────────────
# Main FFT function
# ─────────────────────────────────────────────────────────────────────────────

def run_dft(prep: PrepResult, signal: SampledSignal) -> DFTResult:
    """
    Compute DFT of the normalised amplitude vector psi.

    Uses the positive-exponent (QFT-matching) convention:
        A[k] = (1/√M) Σ_j psi[j] · exp(+2πijk/M)
             = numpy.fft.ifft(psi) * sqrt(M)

    Also computes the standard (negative-exponent) FFT for reference.
    """
    M = prep.n_padded
    psi = prep.psi
    x_span = signal.x_end - signal.x_start

    # QFT convention
    A_qft = np.fft.ifft(psi) * math.sqrt(M)
    power_qft = np.abs(A_qft) ** 2

    # Standard convention
    A_std = np.fft.fft(psi)
    power_std = np.abs(A_std) ** 2 / M

    # Frequency axes
    k = np.arange(M)
    freq_coords = k / M                  # cycles per sample
    freq_per_unit = k / x_span           # cycles per x-unit

    result = DFTResult(
        M=M,
        amplitudes=A_qft,
        power=power_qft,
        amplitudes_std=A_std,
        power_std=power_std,
        freq_coords=freq_coords,
        freq_per_unit=freq_per_unit,
    )

    # Find peaks
    result.peaks = find_peaks(power_qft, M, freq_per_unit, x_span)
    result.peak_matches = compare_to_ground_truth(result.peaks, signal, prep)

    return result


# ─────────────────────────────────────────────────────────────────────────────
# Peak detection
# ─────────────────────────────────────────────────────────────────────────────

def find_peaks(
    power: np.ndarray,
    M: int,
    freq_per_unit: np.ndarray,
    x_span: float,
    threshold_fraction: float = 0.02,
    top_k: int = 20,
) -> list[SpectralPeak]:
    """
    Identify spectral peaks by prominence, limited to the positive half-spectrum.

    Returns SpectralPeak list sorted by descending power.
    """
    half = M // 2 + 1
    half_power = power[:half].copy()
    half_power[1:half - 1] *= 2.0  # one-sided doubling

    max_power = float(np.max(half_power))
    if max_power < 1e-30:
        return []

    threshold = threshold_fraction * max_power

    # scipy peak finder on one-sided spectrum
    peak_indices, props = scipy_find_peaks(
        half_power,
        height=threshold,
        prominence=threshold * 0.1,
    )

    peaks: list[SpectralPeak] = []
    for k in peak_indices:
        f = float(freq_per_unit[k])
        omega = 2 * math.pi * f
        period = math.inf if k == 0 else 1.0 / f
        pwr = float(half_power[k])
        peaks.append(SpectralPeak(
            bin_index=int(k),
            freq_per_unit=f,
            angular_freq=omega,
            period=period,
            power=pwr,
            power_fraction=pwr / max_power,
            is_dc=(k == 0),
            is_negative_freq=False,
        ))

    peaks.sort(key=lambda p: p.power, reverse=True)
    return peaks[:top_k]


# ─────────────────────────────────────────────────────────────────────────────
# Ground-truth comparison
# ─────────────────────────────────────────────────────────────────────────────

def compare_to_ground_truth(
    peaks: list[SpectralPeak],
    signal: SampledSignal,
    prep: PrepResult,
) -> list[PeakMatch]:
    """
    Match each detected peak to the nearest known analytical component.

    Expected DFT bin for a component with frequency f (cycles/x-unit):
        expected_bin = f × x_span
    """
    x_span = signal.x_end - signal.x_start
    known = signal.known_freq_bins(prep.n_padded)  # [(component, expected_bin)]

    matches: list[PeakMatch] = []
    for peak in peaks:
        if not known:
            matches.append(PeakMatch(
                detected=peak, matched_label=None, expected_bin=None,
                expected_freq=None, bin_error=None, amplitude_known=None,
                is_close=False,
            ))
            continue

        # Find closest known component by bin distance
        best_comp, best_bin = min(known, key=lambda cb: abs(cb[1] - peak.bin_index))
        err = abs(peak.bin_index - best_bin)

        matches.append(PeakMatch(
            detected=peak,
            matched_label=best_comp.label,
            expected_bin=best_bin,
            expected_freq=best_comp.freq_per_unit,
            bin_error=err,
            amplitude_known=abs(best_comp.amplitude),
            is_close=err < 1.5,
        ))

    return matches
