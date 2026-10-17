"""
qft_analyzer.py

Applies Quantum Fourier Transform to a stock's daily return sequence
to detect hidden periodicities.

Version : 2.8.0

Version 2.8 — QFT Periodicity Detection:

    Pipeline
    --------
    1. Extract daily % returns from the StockAnalyzer dataframe.
    2. Truncate to the largest power-of-2 window (≤ 2^n, max 8 qubits = 256 points).
    3. Amplitude-encode the normalised returns into a quantum statevector.
    4. Apply the QFT matrix (exact simulation via numpy).
    5. Read out frequency-domain magnitudes.
    6. Identify the top-K dominant frequency bins and translate each
       to a period in trading days.

    Note: QFT is simulated classically via the exact unitary matrix.
    The encoding and transform are quantum-correct; simulation is used
    because the statevector is available without measurement collapse.
"""

from __future__ import annotations

import math
import numpy as np


# Maximum qubits → 2^MAX_QUBITS statevector elements
_MAX_QUBITS = 8   # 256 points
_TOP_K      = 5   # dominant peaks to report


def _next_power_of_two(n: int) -> int:
    """Largest 2^k ≤ n."""
    k = int(math.floor(math.log2(n))) if n >= 1 else 0
    return 2 ** k


def _build_qft_matrix(n: int) -> np.ndarray:
    """
    Returns the n×n QFT unitary matrix.

        QFT_jk = (1/√n) · exp(2πi·j·k / n)
    """
    j = np.arange(n, dtype=complex)
    k = np.arange(n, dtype=complex)
    omega = np.exp(2j * math.pi / n)
    return (omega ** np.outer(j, k)) / math.sqrt(n)


def _amplitude_encode(signal: np.ndarray) -> np.ndarray:
    """
    Encode a real signal into a unit-norm complex statevector.

    Steps:
        1. Shift so all values are non-negative.
        2. Normalise to unit L2 norm.
        3. Return as complex128 array.
    """
    shifted = signal - signal.min()
    norm    = np.linalg.norm(shifted)
    if norm < 1e-12:
        # Flat signal — uniform superposition
        n = len(shifted)
        return np.ones(n, dtype=complex) / math.sqrt(n)
    return (shifted / norm).astype(complex)


class QFTAnalyzer:
    """
    Runs QFT on a single stock's return series.

    Parameters
    ----------
    symbol   : str
    analyzer : StockAnalyzer   (already run_analysis() called)
    """

    # ---------------------------------------------------------

    def __init__(self, symbol: str, analyzer):

        self.symbol   = symbol
        self.analyzer = analyzer

        self.n_qubits       : int              = 0
        self.n_points       : int              = 0
        self.signal         : np.ndarray | None = None
        self.statevector    : np.ndarray | None = None
        self.qft_output     : np.ndarray | None = None
        self.magnitudes     : np.ndarray | None = None
        self.top_peaks      : list[dict]        = []

    # ---------------------------------------------------------

    def run(self):
        """Full pipeline: encode → QFT → peaks."""

        self._extract_signal()
        self._encode()
        self._apply_qft()
        self._find_peaks()

    # ---------------------------------------------------------

    def _extract_signal(self):
        """Pull daily % returns from the dataframe."""
        df = self.analyzer.get_dataframe()

        returns = df["PercentChange"].dropna().values.astype(float)

        # Truncate to largest 2^k ≤ len(returns), capped at 2^MAX_QUBITS
        max_pts = min(len(returns), 2 ** _MAX_QUBITS)
        n_pts   = _next_power_of_two(max_pts)

        self.signal   = returns[-n_pts:]          # use most recent n_pts days
        self.n_points = n_pts
        self.n_qubits = int(math.log2(n_pts))

    # ---------------------------------------------------------

    def _encode(self):
        """Amplitude-encode the return signal."""
        self.statevector = _amplitude_encode(self.signal)

    # ---------------------------------------------------------

    def _apply_qft(self):
        """Multiply statevector by the QFT unitary matrix."""
        qft_matrix      = _build_qft_matrix(self.n_points)
        self.qft_output = qft_matrix @ self.statevector
        self.magnitudes = np.abs(self.qft_output)

    # ---------------------------------------------------------

    def _find_peaks(self):
        """
        Identify the top-K frequency bins by magnitude
        (skip bin 0 = DC / mean offset).
        """
        mags = self.magnitudes.copy()
        mags[0] = 0.0           # suppress DC component

        # Only look at first half (symmetric spectrum)
        half = self.n_points // 2
        mags[half:] = 0.0

        top_indices = np.argsort(mags)[::-1][:_TOP_K]

        self.top_peaks = []

        for rank, bin_idx in enumerate(top_indices):

            freq      = bin_idx / self.n_points   # cycles per day
            period    = (1.0 / freq) if freq > 0 else float("inf")
            magnitude = float(mags[bin_idx])
            power     = magnitude ** 2

            self.top_peaks.append({
                "Rank"      : rank + 1,
                "Bin"       : int(bin_idx),
                "Frequency" : round(freq, 6),
                "Period"    : round(period, 2),
                "Magnitude" : round(magnitude, 6),
                "Power"     : round(power, 6),
            })

    # ---------------------------------------------------------

    def dominant_period(self) -> float:
        """Trading-day period of the strongest frequency peak."""
        if self.top_peaks:
            return self.top_peaks[0]["Period"]
        return float("inf")

    # ---------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "Symbol"          : self.symbol,
            "Qubits"          : self.n_qubits,
            "Points"          : self.n_points,
            "DominantPeriod"  : self.dominant_period(),
            "TopPeaks"        : self.top_peaks,
        }

    # ---------------------------------------------------------

    def __str__(self) -> str:

        lines = [
            f"  Qubits   : {self.n_qubits}  ({self.n_points} data points)",
            f"  Dominant Period : {self.dominant_period():.1f} trading days",
            "",
            f"  {'Rank':<5} {'Bin':<6} {'Freq (cyc/day)':<17} "
            f"{'Period (days)':<16} {'Magnitude':<12} {'Power'}",
            f"  {'-'*4:<5} {'-'*5:<6} {'-'*13:<17} "
            f"{'-'*12:<16} {'-'*9:<12} {'-'*7}",
        ]

        for p in self.top_peaks:
            lines.append(
                f"  {p['Rank']:<5} {p['Bin']:<6} "
                f"{p['Frequency']:<17.6f} "
                f"{p['Period']:<16.2f} "
                f"{p['Magnitude']:<12.6f} "
                f"{p['Power']:.6f}"
            )

        return "\n".join(lines)
