"""interpretation.py – plain-text and structured interpretation of spectral results."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from .classical_analysis import DFTResult, PeakMatch
from .function_parser import SampledSignal
from .preprocessing import PrepResult
from .quantum_analysis import QFTResult


@dataclass
class InterpretationResult:
    # ── inputs ────────────────────────────────────────────────────────────────
    expr: str
    x_start: float
    x_end: float
    n_points: int
    representation: str
    n_qubits: int
    M: int
    n_zeros_added: int
    dc_offset: float
    norm_factor: float

    # ── DFT summary ───────────────────────────────────────────────────────────
    parseval_ok: bool
    n_peaks_found: int
    n_peaks_matched: int          # matched to a known component within 1.5 bins
    peak_summary_lines: list[str] = field(default_factory=list)

    # ── QFT summary ───────────────────────────────────────────────────────────
    qft_mode: str = "not run"
    qft_parseval_ok: bool = False
    max_qft_dft_deviation: float = 0.0
    qft_agreement: str = ""

    # ── narrative sections ────────────────────────────────────────────────────
    setup_summary: str = ""
    dft_narrative: str = ""
    qft_narrative: str = ""
    ground_truth_narrative: str = ""
    conclusion: str = ""


def build_interpretation(
    signal: SampledSignal,
    prep: PrepResult,
    dft: DFTResult,
    qft: Optional[QFTResult] = None,
) -> InterpretationResult:

    x_span = signal.x_end - signal.x_start
    M = prep.n_padded
    q = prep.n_qubits

    # ── Parseval check ────────────────────────────────────────────────────────
    parseval_ok = dft.check_parseval()
    qft_parseval = qft.check_normalisation() if qft else False
    max_dev = float(np.max(np.abs(qft.probabilities - dft.power))) if qft else 0.0

    # ── Peak summary ──────────────────────────────────────────────────────────
    n_matched = sum(1 for m in dft.peak_matches if m.is_close)
    lines = []
    for m in dft.peak_matches:
        d = m.detected
        tick = "✓" if m.is_close else "~"
        if m.matched_label:
            lines.append(
                f"  {tick} bin {d.bin_index:5d}  f={d.freq_per_unit:9.4f} cyc/unit  "
                f"ω={d.angular_freq:8.4f} rad/unit  power={d.power:.5f} ({d.power_fraction*100:.1f}%)  "
                f"→ {m.matched_label}  "
                f"(expected bin {m.expected_bin:.2f}, error {m.bin_error:.2f})"
            )
        else:
            lines.append(
                f"  {tick} bin {d.bin_index:5d}  f={d.freq_per_unit:9.4f} cyc/unit  "
                f"power={d.power:.5f} ({d.power_fraction*100:.1f}%)"
            )

    # ── Known components summary ──────────────────────────────────────────────
    known_lines = []
    for comp in signal.known_components:
        exp_bin = comp.freq_per_unit * x_span
        known_lines.append(
            f"  ω={comp.angular_freq:.4g} rad/unit  "
            f"f={comp.freq_per_unit:.4g} cyc/unit  "
            f"A={comp.amplitude:.4g}  "
            f"expected bin≈{exp_bin:.2f}"
        )

    # ── Narrative sections ────────────────────────────────────────────────────
    setup_summary = (
        f"Expression : {signal.expr}\n"
        f"Domain     : x ∈ [{signal.x_start}, {signal.x_end}]  (span = {x_span:.4g})\n"
        f"Grid points: {signal.n_points}  →  padded to M = {M} = 2^{q}\n"
        f"Qubits     : {q}\n"
        f"Zeros added: {prep.n_zeros_added}\n"
        f"Repr.      : {prep.representation}  (mean removed = {prep.mean_removed:.4f})\n"
        f"DC offset  : {signal.dc_offset:.4f}\n"
        f"L2 norm    : {prep.norm_factor:.4f}\n"
        f"‖ψ‖²       : {float(np.sum(prep.psi**2)):.8f}"
    )

    gt_narrative = "Known analytical components extracted from expression:\n"
    gt_narrative += "\n".join(known_lines) if known_lines else "  (none extracted)"
    gt_narrative += (
        f"\n\nFrequency resolution: Δf = 1/x_span = {1/x_span:.5f} cycles/unit  "
        f"(= 1 DFT bin width)"
    )
    gt_narrative += (
        "\n\nNote: if a component's expected bin is non-integer, its power leaks "
        "into adjacent bins (spectral leakage). Use x_end such that "
        "f × x_span is an integer to get clean single-bin peaks."
    )

    dft_narrative = (
        f"Parseval's theorem (Σ|A[k]|² = 1): {'✓ OK' if parseval_ok else '✗ FAIL'}\n"
        f"Peaks found: {len(dft.peaks)}  |  Matched to known components: {n_matched}\n\n"
        "Peak list:\n" + ("\n".join(lines) if lines else "  No peaks above threshold.")
    )

    if qft is None:
        qft_narrative = "QFT not run (classical_only mode selected)."
        qft_agreement = "—"
    else:
        if max_dev < 1e-6:
            qft_agreement = f"✓ Exact agreement (max |P_QFT − P_DFT| = {max_dev:.2e})"
        elif max_dev < 1e-3:
            qft_agreement = f"✓ Numerical agreement (max deviation {max_dev:.2e})"
        else:
            qft_agreement = f"⚠ Deviation {max_dev:.2e} — check bit-ordering or shot noise"

        qft_narrative = (
            f"Execution mode : {qft.mode}\n"
            f"Qubits         : {qft.n_qubits}  (M = {qft.M})\n"
            f"Shots          : {qft.n_shots if qft.n_shots else 'N/A (statevector)'}\n"
            f"Σ P_QFT        : {float(np.sum(qft.probabilities)):.8f}\n"
            f"Agreement      : {qft_agreement}"
        )

    conclusion = (
        f"The DFT found {len(dft.peaks)} spectral peaks, "
        f"{n_matched} of which match known analytical components within 1.5 bins. "
    )
    if signal.known_components:
        conclusion += (
            f"The input function has {len(signal.known_components)} sinusoidal components "
            f"at angular frequencies {', '.join(f'ω={c.angular_freq:.4g}' for c in signal.known_components)}. "
        )
    if qft:
        conclusion += (
            f"The QFT ({qft.mode}) reproduces the DFT power spectrum "
            f"with maximum deviation {max_dev:.2e}, "
            + ("confirming mathematical equivalence." if max_dev < 1e-3
               else "suggesting shot noise or ordering issues.")
        )

    return InterpretationResult(
        expr=signal.expr,
        x_start=signal.x_start, x_end=signal.x_end,
        n_points=signal.n_points, representation=prep.representation,
        n_qubits=q, M=M, n_zeros_added=prep.n_zeros_added,
        dc_offset=signal.dc_offset, norm_factor=prep.norm_factor,
        parseval_ok=parseval_ok,
        n_peaks_found=len(dft.peaks),
        n_peaks_matched=n_matched,
        peak_summary_lines=lines,
        qft_mode=qft.mode if qft else "not run",
        qft_parseval_ok=qft_parseval,
        max_qft_dft_deviation=max_dev,
        qft_agreement=qft_agreement if qft else "—",
        setup_summary=setup_summary,
        dft_narrative=dft_narrative,
        qft_narrative=qft_narrative,
        ground_truth_narrative=gt_narrative,
        conclusion=conclusion,
    )
