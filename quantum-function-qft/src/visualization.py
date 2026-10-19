"""visualization.py – all Matplotlib figures for quantum-function-qft."""

from __future__ import annotations

from typing import Optional

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np

from .classical_analysis import DFTResult, PeakMatch
from .function_parser import SampledSignal
from .preprocessing import PrepResult
from .quantum_analysis import QFTResult

BLUE   = "#1f77b4"
ORANGE = "#ff7f0e"
GREEN  = "#2ca02c"
RED    = "#d62728"
PURPLE = "#9467bd"
GREY   = "#7f7f7f"


def _tight(fig: plt.Figure) -> plt.Figure:
    fig.tight_layout()
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# 1. Raw signal
# ─────────────────────────────────────────────────────────────────────────────

def plot_signal(signal: SampledSignal) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(11, 3))
    ax.plot(signal.x, signal.y, color=BLUE, lw=1.1)
    ax.axhline(signal.dc_offset, color=GREY, lw=0.9, ls="--",
               label=f"DC offset (mean) = {signal.dc_offset:.4f}")
    ax.set_title(f"f(x) = {signal.expr}", fontweight="bold", fontsize=10)
    ax.set_xlabel("x")
    ax.set_ylabel("f(x)")
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3)
    return _tight(fig)


# ─────────────────────────────────────────────────────────────────────────────
# 2. Preprocessed amplitude vector
# ─────────────────────────────────────────────────────────────────────────────

def plot_amplitude(prep: PrepResult) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(11, 3))
    ax.plot(prep.psi, color=PURPLE, lw=0.9)
    if prep.n_zeros_added > 0:
        ax.axvline(prep.n_original - 0.5, color=RED, ls="--", lw=1.2,
                   label=f"Padding boundary ({prep.n_zeros_added} zeros added)")
        ax.legend(fontsize=9)
    ax.set_title(
        rf"L2-normalised amplitude vector $\psi$  "
        f"(M={prep.n_padded}, q={prep.n_qubits} qubits, repr='{prep.representation}')",
        fontweight="bold", fontsize=10,
    )
    ax.set_xlabel("Index j")
    ax.set_ylabel(r"$\psi_j$")
    ax.grid(alpha=0.3)
    return _tight(fig)


# ─────────────────────────────────────────────────────────────────────────────
# 3. DFT power spectrum with known-peak annotations
# ─────────────────────────────────────────────────────────────────────────────

def plot_dft_spectrum(dft: DFTResult, signal: SampledSignal, prep: PrepResult) -> plt.Figure:
    freqs, half_p = dft.half_power()

    fig, ax = plt.subplots(figsize=(12, 4))
    ax.bar(freqs, half_p, width=(freqs[1] - freqs[0]) * 0.85 if len(freqs) > 1 else 0.01,
           color=BLUE, alpha=0.8, label="DFT power (one-sided)")

    # Annotate known components
    x_span = signal.x_end - signal.x_start
    for comp in signal.known_components:
        exp_f = comp.freq_per_unit
        exp_bin = comp.freq_per_unit * x_span
        # Find closest DFT freq value
        ax.axvline(exp_f, color=RED, lw=1.3, ls="--", alpha=0.8)
        ax.text(exp_f, ax.get_ylim()[1] * 0.02,
                f" ω={comp.angular_freq:.3g}\nA={comp.amplitude:.3g}",
                fontsize=7, color=RED, rotation=90, va="bottom")

    ax.set_title("Classical DFT power spectrum (one-sided) with known frequency annotations",
                 fontweight="bold")
    ax.set_xlabel("Frequency (cycles / x-unit)")
    ax.set_ylabel(r"$|A[k]|^2$ (one-sided)")
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3)
    return _tight(fig)


# ─────────────────────────────────────────────────────────────────────────────
# 4. QFT probability spectrum
# ─────────────────────────────────────────────────────────────────────────────

def plot_qft_spectrum(
    qft: QFTResult,
    dft: DFTResult,
    signal: SampledSignal,
) -> plt.Figure:
    freqs, half_p_dft = dft.half_power()
    _, half_p_qft = qft.half_power(dft.freq_per_unit)

    fig, axes = plt.subplots(1, 2, figsize=(13, 4))

    # Left: side-by-side comparison
    w = (freqs[1] - freqs[0]) * 0.4 if len(freqs) > 1 else 0.005
    axes[0].bar(freqs - w / 2, half_p_dft, width=w, color=BLUE, alpha=0.8, label="DFT")
    axes[0].bar(freqs + w / 2, half_p_qft, width=w, color=ORANGE, alpha=0.8, label="QFT")
    axes[0].set_title("DFT vs QFT — one-sided power (side by side)", fontweight="bold")
    axes[0].set_xlabel("Frequency (cycles / x-unit)")
    axes[0].set_ylabel("Power")
    axes[0].legend(fontsize=9)
    axes[0].grid(alpha=0.3)

    # Right: absolute difference
    M = dft.M
    diff = np.abs(qft.probabilities - dft.power)
    half_diff = diff[: M // 2 + 1]
    axes[1].bar(freqs, half_diff, width=(freqs[1] - freqs[0]) * 0.85 if len(freqs) > 1 else 0.01,
                color=RED, alpha=0.8)
    axes[1].set_title(r"$|P_{QFT}[k] - P_{DFT}[k]|$ — deviation", fontweight="bold")
    axes[1].set_xlabel("Frequency (cycles / x-unit)")
    axes[1].set_ylabel("Absolute deviation")
    axes[1].grid(alpha=0.3)

    return _tight(fig)


# ─────────────────────────────────────────────────────────────────────────────
# 5. Peak match table figure
# ─────────────────────────────────────────────────────────────────────────────

def plot_peak_table(matches: list[PeakMatch], signal: SampledSignal) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(12, max(2.5, len(matches) * 0.45 + 1.2)))
    ax.axis("off")

    headers = ["Bin k", "f (cyc/unit)", "ω (rad/unit)", "Power", "Power %",
               "Matched component", "Expected bin", "Bin error", "✓"]
    rows = []
    for m in matches:
        d = m.detected
        rows.append([
            str(d.bin_index),
            f"{d.freq_per_unit:.4f}",
            f"{d.angular_freq:.4f}",
            f"{d.power:.5f}",
            f"{d.power_fraction * 100:.2f}%",
            m.matched_label or "—",
            f"{m.expected_bin:.2f}" if m.expected_bin is not None else "—",
            f"{m.bin_error:.2f}" if m.bin_error is not None else "—",
            "✓" if m.is_close else "~",
        ])

    table = ax.table(
        cellText=rows, colLabels=headers,
        cellLoc="center", loc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.4)

    # Colour header row
    for j in range(len(headers)):
        table[0, j].set_facecolor("#dce6f7")

    # Highlight close matches
    for i, m in enumerate(matches):
        color = "#e6f9ee" if m.is_close else "#fff8e1"
        for j in range(len(headers)):
            table[i + 1, j].set_facecolor(color)

    ax.set_title("Detected peaks vs. known analytical components", fontweight="bold", pad=12)
    return _tight(fig)


# ─────────────────────────────────────────────────────────────────────────────
# 6. Full comparison dashboard (4-panel)
# ─────────────────────────────────────────────────────────────────────────────

def plot_dashboard(
    signal: SampledSignal,
    prep: PrepResult,
    dft: DFTResult,
    qft: Optional[QFTResult] = None,
) -> plt.Figure:
    fig = plt.figure(figsize=(14, 10))
    gs = gridspec.GridSpec(3, 2, figure=fig, hspace=0.45, wspace=0.35)

    freqs, half_p_dft = dft.half_power()
    bar_w = (freqs[1] - freqs[0]) * 0.8 if len(freqs) > 1 else 0.01

    # Panel 1: raw signal
    ax1 = fig.add_subplot(gs[0, :])
    ax1.plot(signal.x, signal.y, color=BLUE, lw=0.9)
    ax1.axhline(signal.dc_offset, color=GREY, lw=0.8, ls="--",
                label=f"mean={signal.dc_offset:.3f}")
    ax1.set_title(f"f(x) = {signal.expr[:80]}{'…' if len(signal.expr) > 80 else ''}",
                  fontweight="bold", fontsize=9)
    ax1.set_xlabel("x"); ax1.set_ylabel("f(x)")
    ax1.legend(fontsize=8); ax1.grid(alpha=0.3)

    # Panel 2: preprocessed ψ
    ax2 = fig.add_subplot(gs[1, 0])
    ax2.plot(prep.psi, color=PURPLE, lw=0.8)
    if prep.n_zeros_added:
        ax2.axvline(prep.n_original - 0.5, color=RED, ls="--", lw=1.0)
    ax2.set_title(r"Normalised $\psi$ (amplitude vector)", fontweight="bold", fontsize=9)
    ax2.set_xlabel("j"); ax2.set_ylabel(r"$\psi_j$"); ax2.grid(alpha=0.3)

    # Panel 3: DFT spectrum
    ax3 = fig.add_subplot(gs[1, 1])
    ax3.bar(freqs, half_p_dft, width=bar_w, color=BLUE, alpha=0.85, label="DFT")
    if qft is not None:
        _, half_p_qft = qft.half_power(dft.freq_per_unit)
        ax3.plot(freqs, half_p_qft, color=ORANGE, lw=1.2, alpha=0.9, label="QFT")
    # Mark known components
    x_span = signal.x_end - signal.x_start
    for comp in signal.known_components:
        ax3.axvline(comp.freq_per_unit, color=RED, lw=1.0, ls="--", alpha=0.7)
    ax3.set_title("Power spectrum (one-sided)", fontweight="bold", fontsize=9)
    ax3.set_xlabel("f (cyc/x-unit)"); ax3.set_ylabel("Power")
    ax3.legend(fontsize=8); ax3.grid(alpha=0.3)

    # Panel 4: deviation
    ax4 = fig.add_subplot(gs[2, :])
    if qft is not None:
        diff = np.abs(qft.probabilities - dft.power)
        half_diff = diff[: dft.M // 2 + 1]
        ax4.bar(freqs, half_diff, width=bar_w, color=RED, alpha=0.8)
        ax4.set_title(r"$|P_{QFT} - P_{DFT}|$ deviation", fontweight="bold", fontsize=9)
        ax4.set_xlabel("f (cyc/x-unit)"); ax4.set_ylabel("Abs. deviation")
        ax4.grid(alpha=0.3)
        max_dev = float(np.max(diff))
        ax4.text(0.99, 0.95, f"max deviation = {max_dev:.2e}",
                 transform=ax4.transAxes, ha="right", va="top", fontsize=9,
                 color=RED if max_dev > 1e-3 else GREEN)
    else:
        ax4.text(0.5, 0.5, "Run in statevector or shot-based mode to see QFT vs DFT deviation.",
                 ha="center", va="center", transform=ax4.transAxes, fontsize=11, color=GREY)
        ax4.axis("off")

    fig.suptitle("Quantum Fourier Analysis — Function Dashboard", fontweight="bold", fontsize=12)
    return fig
