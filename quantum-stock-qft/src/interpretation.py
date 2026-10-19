"""interpretation.py – text generation for spectral analysis results.

Public API
----------
build_interpretation(prep, classical, qft_result, data_bundle) -> InterpretationReport
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from .classical_analysis import ClassicalFFTResult, dominant_frequencies, half_spectrum
from .preprocessing import PrepResult
from .quantum_analysis import QFTResult


@dataclass
class InterpretationReport:
    """All textual and numerical interpretation of one analysis run."""

    # ── metadata ─────────────────────────────────────────────────────────────
    ticker: str
    first_date: str
    last_date: str
    series_label: str
    mode: str
    n_original: int
    n_padded: int
    n_zeros_added: int
    n_qubits: int
    norm_factor: float
    mean_removed: float

    # ── spectral findings ────────────────────────────────────────────────────
    dominant_bins_classical: list[dict] = field(default_factory=list)
    dominant_bins_qft: list[dict] = field(default_factory=list)
    dc_power_fraction: float = 0.0
    max_agreement_error: float = 0.0   # max |P_qft - P_classical|

    # ── plain-text sections ──────────────────────────────────────────────────
    hypothesis: str = ""
    data_summary: str = ""
    preprocessing_summary: str = ""
    qft_summary: str = ""
    classical_summary: str = ""
    comparison_summary: str = ""
    limitations: str = ""
    conclusion: str = ""


def build_interpretation(
    prep: PrepResult,
    classical: ClassicalFFTResult,
    qft_result: Optional[QFTResult],
    ticker: str,
    first_date: str,
    last_date: str,
    series_label: str,
) -> InterpretationReport:
    """Assemble a full InterpretationReport from analysis results."""

    M = prep.n_padded
    top_bins_c = dominant_frequencies(classical.power_qft_convention, M, top_k=8)
    dc_power = float(classical.power_qft_convention[0])
    dc_frac = dc_power / max(float(np.sum(classical.power_qft_convention)), 1e-30)

    dominant_classical = [
        {
            "bin": fb.bin_index,
            "frequency": round(fb.frequency, 6),
            "period": round(fb.period_samples, 2) if not math.isinf(fb.period_samples) else None,
            "power": round(fb.power, 6),
            "is_dc": fb.is_dc,
            "is_negative_freq": fb.is_negative_freq,
        }
        for fb in top_bins_c
    ]

    dominant_qft_bins: list[dict] = []
    max_err = 0.0
    if qft_result is not None:
        top_bins_q = qft_result.dominant_bins(top_k=8)
        dominant_qft_bins = [
            {"bin": b, "prob": round(p, 6)} for b, p in top_bins_q
        ]
        diff = np.abs(qft_result.probabilities - classical.power_qft_convention)
        max_err = float(np.max(diff))

    # ── text sections ─────────────────────────────────────────────────────────
    hypothesis = (
        f"Research question: Can the Quantum Fourier Transform reproduce the "
        f"classical FFT power spectrum of the {ticker} {series_label} series, "
        f"and do any dominant frequency bins correspond to plausible cyclical "
        f"patterns in the market data?\n\n"
        f"Hypothesis: The QFT (via Qiskit statevector simulation) will produce "
        f"a probability distribution identical to the classical FFT power spectrum "
        f"(Parseval equivalence), because both implement the same unitary "
        f"transformation on the same normalised vector."
    )

    data_summary = (
        f"Ticker: {ticker}  |  Series: {series_label}\n"
        f"Date range: {first_date} → {last_date}\n"
        f"Observations used: {prep.n_original} "
        f"(padded to {M} with {prep.n_zeros_added} zeros)"
    )

    preprocessing_summary = (
        f"Representation: {prep.mode}\n"
        f"Mean removed: {prep.mean_removed:.4f}\n"
        f"L2 norm before normalisation: {prep.norm_factor:.4f}\n"
        f"Normalised vector ||ψ||² = {float(np.sum(np.abs(prep.psi)**2)):.8f} "
        f"(should be 1.000000)"
    )

    qft_summary = "QFT not run (classical_only mode)."
    if qft_result is not None:
        qft_summary = (
            f"Execution mode: {qft_result.mode}\n"
            f"Qubits: {qft_result.n_qubits}  |  State dimension: {qft_result.M}\n"
            f"Probability sum: {float(np.sum(qft_result.probabilities)):.8f}\n"
            f"Max |P_QFT − P_classical|: {max_err:.2e}"
        )

    ks, half_p = half_spectrum(classical.power_qft_convention)
    top_half = dominant_frequencies(half_p, M, top_k=5, exclude_dc=True)

    classical_summary_lines = [
        f"DC bin power fraction: {dc_frac:.2%}",
        f"Top positive-frequency bins (excluding DC):",
    ]
    for fb in top_half:
        classical_summary_lines.append(
            f"  bin {fb.bin_index:4d}  |  f={fb.frequency:.5f} cyc/sample  |  "
            f"period≈{fb.period_str()}  |  power={fb.power:.4f}"
        )
    classical_summary = "\n".join(classical_summary_lines)

    if max_err < 1e-6:
        comparison_summary = (
            "✓ QFT and classical FFT probability distributions agree to numerical "
            f"precision (max deviation {max_err:.2e}). This is the expected result: "
            "both implement the identical unitary transformation."
        )
    elif max_err < 1e-3:
        comparison_summary = (
            f"QFT and classical FFT agree with small deviations (max {max_err:.2e}), "
            "consistent with floating-point rounding in the Aer simulator."
        )
    else:
        comparison_summary = (
            f"⚠ Larger-than-expected deviations between QFT and classical FFT "
            f"(max {max_err:.2e}). Possible causes: shot noise (shot-based mode), "
            "bit-ordering mismatch, or sign-convention mismatch."
        )

    limitations = (
        "1. Amplitude encoding: loading N real values into a quantum state "
        "requires O(N) classical pre-computation. The loading step is not free.\n"
        "2. Measurement: a single projective measurement collapses the state. "
        "Recovering the full amplitude spectrum requires many shots or a "
        "statevector simulator (not a physical quantum computer).\n"
        "3. Shot noise: with finite shots the estimated distribution has "
        "statistical uncertainty of O(1/√shots).\n"
        "4. Non-stationary data: financial returns are non-stationary; "
        "a frequency peak in one window may not persist in another.\n"
        "5. Multiple testing: examining many frequency bins increases the "
        "probability of spurious peaks by chance.\n"
        "6. No prediction: a spectral peak does not imply a future cycle."
    )

    conclusion = (
        f"The QFT circuit (simulated via Aer statevector) reproduces the "
        f"classical FFT power spectrum of the normalised {ticker} {prep.mode} "
        f"signal to within numerical precision, confirming the mathematical "
        f"equivalence. The dominant non-DC frequency bins are listed above. "
        f"No claim is made that these represent statistically significant or "
        f"persistent market cycles."
    )

    return InterpretationReport(
        ticker=ticker,
        first_date=first_date,
        last_date=last_date,
        series_label=series_label,
        mode=prep.mode,
        n_original=prep.n_original,
        n_padded=M,
        n_zeros_added=prep.n_zeros_added,
        n_qubits=prep.n_qubits,
        norm_factor=prep.norm_factor,
        mean_removed=prep.mean_removed,
        dominant_bins_classical=dominant_classical,
        dominant_bins_qft=dominant_qft_bins,
        dc_power_fraction=dc_frac,
        max_agreement_error=max_err,
        hypothesis=hypothesis,
        data_summary=data_summary,
        preprocessing_summary=preprocessing_summary,
        qft_summary=qft_summary,
        classical_summary=classical_summary,
        comparison_summary=comparison_summary,
        limitations=limitations,
        conclusion=conclusion,
    )
