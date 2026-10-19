"""visualization.py – Matplotlib / Plotly figures for the analysis.

Public API
----------
plot_prices(prices, ticker, series_label)           -> Figure
plot_preprocessed(prep)                             -> Figure
plot_amplitude_vector(prep)                         -> Figure
plot_power_spectra(classical, qft_result, prep)     -> Figure
plot_shot_histogram(qft_result)                     -> Figure
plot_probability_diff(classical, qft_result)        -> Figure
plot_experiment_synthetic()                         -> Figure
All functions return a matplotlib Figure (or Plotly figure where noted).
"""

from __future__ import annotations

from typing import Optional

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np

from .classical_analysis import ClassicalFFTResult, half_spectrum
from .preprocessing import PrepResult
from .quantum_analysis import QFTResult

# ── shared style ──────────────────────────────────────────────────────────────
ACCENT   = "#1f77b4"
ORANGE   = "#ff7f0e"
GREEN    = "#2ca02c"
RED      = "#d62728"
PURPLE   = "#9467bd"
FIGSIZE  = (11, 4)


def _tight(fig: plt.Figure) -> plt.Figure:
    fig.tight_layout()
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# Price series
# ─────────────────────────────────────────────────────────────────────────────

def plot_prices(prices, ticker: str, series_label: str = "Close") -> plt.Figure:
    """Historical price series and daily returns, side by side."""
    fig, axes = plt.subplots(1, 2, figsize=FIGSIZE)

    ax = axes[0]
    ax.plot(prices.index, prices.values, color=ACCENT, lw=1.2)
    ax.set_title(f"{ticker} — {series_label}", fontweight="bold")
    ax.set_xlabel("Date")
    ax.set_ylabel(f"{series_label} (USD)")
    ax.grid(alpha=0.3)

    ax2 = axes[1]
    p = prices.to_numpy(dtype=float)
    returns = 100.0 * (p[1:] / p[:-1] - 1.0)
    ax2.plot(prices.index[1:], returns, color=ORANGE, lw=0.9)
    ax2.axhline(0, color="grey", lw=0.7, ls="--")
    ax2.set_title(f"{ticker} — Daily returns (%)", fontweight="bold")
    ax2.set_xlabel("Date")
    ax2.set_ylabel("Return (%)")
    ax2.grid(alpha=0.3)

    return _tight(fig)


# ─────────────────────────────────────────────────────────────────────────────
# Preprocessed signal
# ─────────────────────────────────────────────────────────────────────────────

def plot_preprocessed(prep: PrepResult) -> plt.Figure:
    """Show the raw signal used as QFT input."""
    fig, ax = plt.subplots(figsize=(10, 3))
    ax.plot(prep.raw_series, color=GREEN, lw=1.0)
    ax.axhline(0, color="grey", lw=0.7, ls="--")
    ax.set_title(
        f"Input signal — representation: {prep.mode}  "
        f"(N={prep.n_original})",
        fontweight="bold",
    )
    ax.set_xlabel("Observation index")
    ax.set_ylabel("Value")
    ax.grid(alpha=0.3)
    return _tight(fig)


# ─────────────────────────────────────────────────────────────────────────────
# Amplitude (normalised) vector
# ─────────────────────────────────────────────────────────────────────────────

def plot_amplitude_vector(prep: PrepResult) -> plt.Figure:
    """Show the L2-normalised amplitude vector ψ including zero-padding."""
    fig, ax = plt.subplots(figsize=(10, 3))
    ax.plot(prep.psi, color=PURPLE, lw=0.9, label=r"$\psi_i$ (L2 normalised)")
    if prep.n_zeros_added > 0:
        ax.axvline(prep.n_original - 0.5, color=RED, ls="--", lw=1.2, label="Padding boundary")
    ax.set_title(
        rf"Normalised amplitude vector $\psi$  "
        f"(M={prep.n_padded}, {prep.n_qubits} qubits)",
        fontweight="bold",
    )
    ax.set_xlabel("Index j")
    ax.set_ylabel(r"$\psi_j$")
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3)
    return _tight(fig)


# ─────────────────────────────────────────────────────────────────────────────
# Power spectra comparison
# ─────────────────────────────────────────────────────────────────────────────

def plot_power_spectra(
    classical: ClassicalFFTResult,
    qft_result: Optional[QFTResult],
    prep: PrepResult,
) -> plt.Figure:
    """Classical FFT power spectrum vs. QFT probability distribution."""
    M = classical.M
    freqs = classical.frequency_coords
    half = M // 2 + 1

    n_panels = 2 if qft_result is not None else 1
    fig, axes = plt.subplots(1, n_panels, figsize=FIGSIZE)
    if n_panels == 1:
        axes = [axes]

    # Panel 1: classical
    ks, half_p = half_spectrum(classical.power_qft_convention)
    half_freqs = ks / M
    ax = axes[0]
    ax.bar(half_freqs, half_p, width=1 / M * 0.8, color=ACCENT, alpha=0.85)
    ax.set_title("Classical FFT power spectrum (one-sided)", fontweight="bold")
    ax.set_xlabel("Frequency (cycles / sample)")
    ax.set_ylabel(r"$|A[k]|^2$")
    ax.grid(alpha=0.3)
    ax.set_xlim(0, 0.5)

    # Panel 2: QFT
    if qft_result is not None:
        ax2 = axes[1]
        qft_half = qft_result.probabilities[:half]
        ax2.bar(half_freqs, qft_half, width=1 / M * 0.8, color=ORANGE, alpha=0.85)
        ax2.set_title(
            f"QFT probability distribution ({qft_result.mode})\none-sided",
            fontweight="bold",
        )
        ax2.set_xlabel("Frequency (cycles / sample)")
        ax2.set_ylabel(r"$|A_{QFT}[k]|^2$")
        ax2.grid(alpha=0.3)
        ax2.set_xlim(0, 0.5)

    return _tight(fig)


# ─────────────────────────────────────────────────────────────────────────────
# Shot histogram
# ─────────────────────────────────────────────────────────────────────────────

def plot_shot_histogram(qft_result: QFTResult) -> plt.Figure:
    """Bar chart of measurement counts from shot-based simulation."""
    M = qft_result.M
    half = M // 2 + 1
    counts = qft_result.sampled_probs if qft_result.sampled_probs is not None else qft_result.probabilities
    freqs = np.arange(M) / M

    fig, ax = plt.subplots(figsize=FIGSIZE)
    ax.bar(freqs[:half], counts[:half], width=1 / M * 0.8, color=GREEN, alpha=0.85)
    ax.set_title(
        f"QFT shot-based measurement histogram  (shots={qft_result.n_shots}, one-sided)",
        fontweight="bold",
    )
    ax.set_xlabel("Frequency (cycles / sample)")
    ax.set_ylabel("Estimated probability (counts / shots)")
    ax.grid(alpha=0.3)
    ax.set_xlim(0, 0.5)
    return _tight(fig)


# ─────────────────────────────────────────────────────────────────────────────
# Classical vs QFT difference
# ─────────────────────────────────────────────────────────────────────────────

def plot_probability_diff(
    classical: ClassicalFFTResult,
    qft_result: QFTResult,
) -> plt.Figure:
    """Absolute difference |P_QFT[k] - P_classical[k]| across all bins."""
    M = classical.M
    diff = np.abs(qft_result.probabilities - classical.power_qft_convention)
    freqs = np.arange(M) / M

    fig, ax = plt.subplots(figsize=FIGSIZE)
    ax.bar(freqs, diff, width=1 / M * 0.8, color=RED, alpha=0.85)
    ax.set_title(
        r"$|P_{QFT}[k] - P_{classical}[k]|$ — deviation between QFT and FFT",
        fontweight="bold",
    )
    ax.set_xlabel("Frequency (cycles / sample)")
    ax.set_ylabel("Absolute deviation")
    ax.grid(alpha=0.3)
    return _tight(fig)


# ─────────────────────────────────────────────────────────────────────────────
# Synthetic experiment figures
# ─────────────────────────────────────────────────────────────────────────────

def plot_experiment_synthetic(n: int = 64, seed: int = 42) -> plt.Figure:
    """
    Experiment A: show classical FFT power spectra for four synthetic signals.
        1. Constant series
        2. Single-frequency sinusoid
        3. Two-frequency sinusoid
        4. White noise
    """
    rng = np.random.default_rng(seed)
    t = np.arange(n)
    M = n  # already power of two

    signals = {
        "Constant": np.ones(n),
        "Single sinusoid\n(f=4/N)": np.sin(2 * np.pi * 4 * t / n),
        "Two sinusoids\n(f=4/N, 12/N)": np.sin(2 * np.pi * 4 * t / n) + 0.5 * np.sin(2 * np.pi * 12 * t / n),
        "White noise": rng.standard_normal(n),
    }

    fig, axes = plt.subplots(2, 4, figsize=(14, 6))
    freqs = np.arange(M // 2 + 1) / M

    for col, (label, sig) in enumerate(signals.items()):
        norm = float(np.sqrt(np.sum(sig ** 2)))
        psi = sig / norm if norm > 1e-14 else sig
        A = np.fft.ifft(psi) * np.sqrt(M)
        power = np.abs(A) ** 2
        half_power = power[: M // 2 + 1].copy()
        half_power[1: M // 2] *= 2

        ax_top = axes[0, col]
        ax_top.plot(t, sig, color=ACCENT, lw=1.0)
        ax_top.set_title(f"Signal: {label}", fontsize=9, fontweight="bold")
        ax_top.set_xlabel("t")
        ax_top.grid(alpha=0.3)

        ax_bot = axes[1, col]
        ax_bot.bar(freqs, half_power, width=1 / M * 0.8, color=ORANGE, alpha=0.85)
        ax_bot.set_title("Power spectrum (one-sided)", fontsize=9)
        ax_bot.set_xlabel("f (cyc/sample)")
        ax_bot.grid(alpha=0.3)

    fig.suptitle("Experiment A — Synthetic Signals", fontweight="bold", fontsize=12)
    return _tight(fig)
