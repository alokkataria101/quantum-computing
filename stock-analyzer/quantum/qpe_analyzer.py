"""
qpe_analyzer.py

Quantum Phase Estimation for a single stock.

Version : 2.9.0

Version 2.9 — Quantum Phase Estimation (QPE):

    Concept
    -------
    QPE estimates the eigenphase φ of a unitary operator U acting on
    a target qubit. For a stock, we construct U as the Ry rotation
    unitary built from the stock's q0 (Probability) angle θ:

        U = Ry(θ)   →   eigenvalues e^(±iθ/2)
        φ = θ / (4π)   (normalised to [0, 1))

    Circuit
    -------
    The standard QPE circuit uses:

        n_counting  counting qubits  (precision = 2^n_counting bins)
        1           target qubit     (initialised to |+> = H|0>)

    Steps:
        1.  Apply H to all counting qubits  → uniform superposition
        2.  Apply controlled-U^(2^k) for k = 0 … n_counting-1
        3.  Apply Inverse QFT to the counting register
        4.  Measure the counting register → read out phase integer j
        5.  φ_est = j / 2^n_counting

    Market interpretation
    ---------------------
    The estimated phase encodes the probability-up angle of the stock:

        φ_est  →  θ_est = 4π · φ_est
        P_up_est = sin²(θ_est / 2)

    QPE also produces a phase confidence score from the sharpness of
    the measurement distribution (ideal = single peak → confidence=1).

    Simulation note
    ---------------
    Exact statevector simulation is used (no sampling noise).
    The counting register is tracked as a 2^n_counting complex vector.
    Controlled-Ry and IQFT are applied as exact matrix multiplications.
"""

from __future__ import annotations

import math
import numpy as np


# Number of counting qubits: 6 → 64 phase bins (resolution = 1/64 ≈ 0.016)
_N_COUNTING = 6
_N_BINS     = 2 ** _N_COUNTING   # 64


def _iqft_matrix(n: int) -> np.ndarray:
    """
    Inverse QFT matrix (n×n).

        IQFT_jk = (1/√n) · exp(-2πi·j·k / n)
    """
    j = np.arange(n, dtype=complex)
    k = np.arange(n, dtype=complex)
    omega = np.exp(-2j * math.pi / n)
    return (omega ** np.outer(j, k)) / math.sqrt(n)


def _ry_matrix(theta: float) -> np.ndarray:
    """2×2 Ry(theta) matrix."""
    c = math.cos(theta / 2)
    s = math.sin(theta / 2)
    return np.array([[c, -s], [s, c]], dtype=complex)


def _controlled_ry_on_counting(
    counting_sv: np.ndarray,
    target_sv:   np.ndarray,
    theta:       float,
    power:       int,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Apply controlled-Ry(theta * 2^power) to the full system.

    Because the target is kept as a separate 2-vector and counting
    as a 2^n_counting vector, we work with the tensor-product space
    but exploit the product-state structure to avoid the full
    2^(n+1)-dimensional matrix.

    Implementation:
        For each counting basis state |j>:
            if bit k of j is 1 → apply Ry(theta * 2^k) to target
        We process all counting qubits simultaneously by iterating
        over counting basis states and applying the gate conditionally.
    """
    n_bins   = len(counting_sv)
    ry_power = _ry_matrix(theta * power)

    # Full joint statevector: counting ⊗ target
    joint = np.kron(counting_sv, target_sv)                    # shape: 2*n_bins

    new_joint = np.zeros_like(joint)

    for j in range(n_bins):
        # amplitude of |j> in counting register
        amp_c = counting_sv[j]
        if abs(amp_c) < 1e-15:
            continue

        # target amplitudes when counting is |j>
        t = target_sv.copy()

        # apply Ry^power to target (control = |j>, but we already factor it)
        t_new = ry_power @ t

        # write back into joint: positions j*2 and j*2+1
        new_joint[j * 2]     += amp_c * t_new[0]
        new_joint[j * 2 + 1] += amp_c * t_new[1]

    # Separate back: marginalise target
    # counting[j] = sqrt(sum |new_joint[j*2]|^2 + |new_joint[j*2+1]|^2)
    # but we need phases — so track via reduced density matrix approach.
    # Simpler: assume target always in same state after controlled-U
    # (valid for eigenvector input). We update counting amplitudes:
    #   new_counting[j] proportional to new_joint[j*2 .. j*2+1]
    # We sum out target by taking partial trace amplitude.

    # Since target is initialised to |+> = [1,1]/√2 and U has eigenvectors,
    # the counting register accumulates the phase kick.  We implement this
    # correctly via the phase kickback approach directly:
    #   Each |j> component of counting picks up phase e^(iφ·j) where
    #   φ = theta * power / 2  (half-angle of Ry eigenvalue)
    # This is the textbook phase kickback result.

    phase = math.cos(theta * power / 2) + 1j * math.sin(theta * power / 2)
    new_counting = counting_sv.copy()
    for j in range(n_bins):
        # Apply phase e^(i * theta * power / 2) to |j> component
        new_counting[j] = counting_sv[j] * phase

    return new_counting, target_sv


def _phase_kickback_step(
    counting_sv: np.ndarray,
    theta:       float,
    k:           int,
) -> np.ndarray:
    """
    Phase kickback for counting qubit k.

    Ry(θ) has eigenvalues e^(±iθ/2). The target is initialised to |+>
    which is an equal superposition of both eigenstates, so the effective
    accumulated phase per application of U is θ/2.

    For counting qubit k (MSB = qubit 0), controlled-U^(2^k) kicks back
    phase e^(i · (θ/2) · 2^k) onto the |1> component of that qubit.

    We represent the full counting register as a 2^n_counting statevector
    and apply the phase to every basis state |j> that has bit k set.
    """
    # Ry(θ) has eigenvalues e^(+iθ/2) and e^(-iθ/2).
    # The |+y> eigenstate corresponds to eigenvalue e^(+iθ/2).
    # Phase kickback accumulates θ/2 per application of U.
    eigenphase = theta / 2.0

    n_bins       = len(counting_sv)
    new_sv       = counting_sv.copy()
    bit_position = (_N_COUNTING - 1) - k    # MSB-first ordering

    for j in range(n_bins):
        if (j >> bit_position) & 1:
            phase      = cmath_exp(eigenphase * (2 ** k))
            new_sv[j]  = counting_sv[j] * phase

    return new_sv


def cmath_exp(angle: float) -> complex:
    return math.cos(angle) + 1j * math.sin(angle)


class QPEAnalyzer:
    """
    Runs QPE on a single stock's Probability qubit (q0).

    Parameters
    ----------
    symbol   : str
    state    : MultiQubitState   (from QuantumEncoder)
    analyzer : StockAnalyzer     (for classical cross-check)
    """

    # ---------------------------------------------------------

    def __init__(self, symbol: str, state, analyzer):

        self.symbol   = symbol
        self.state    = state
        self.analyzer = analyzer

        self.n_counting      : int   = _N_COUNTING
        self.n_bins          : int   = _N_BINS

        self.counting_sv     : np.ndarray | None = None   # after IQFT
        self.probabilities   : np.ndarray | None = None   # measurement probs
        self.phase_estimate  : float = 0.0
        self.theta_estimate  : float = 0.0
        self.p_up_estimate   : float = 0.0
        self.p_up_classical  : float = 0.0
        self.confidence      : float = 0.0
        self.top_phases      : list[dict] = []

    # ---------------------------------------------------------

    def run(self):
        """
        Full QPE pipeline.

        Standard QPE circuit (per-qubit implementation):

        For each counting qubit k (k=0 is MSB):
            1. Apply H to qubit k  →  (|0> + |1>) / √2
            2. Apply controlled-U^(2^k): kick back phase e^(i·φ·2^k) to |1>
               where φ = θ/2  (the eigenphase of Ry(θ))
        3. Collect per-qubit phases, form product state, apply IQFT.

        We track the full 2^n counting register as a product state:
        each qubit k is independently in state (|0> + e^(i·φ·2^k)|1>)/√2.
        The product state is then the tensor product of all n qubits.
        IQFT of this tensor product = the QPE measurement distribution.
        """

        # θ from q0 (Probability qubit)
        theta = self.state.angles[0]

        # Classical reference
        self.p_up_classical = self.analyzer.get_summary()["ProbabilityUp"]

        # Eigenphase of Ry(θ): φ = θ/2  (eigenvalue e^(iφ) of |+y> eigenstate)
        # QPE recovers φ_norm = φ/(2π) = θ/(4π)  →  θ = φ_norm × 4π
        eigenphase = theta / 2.0

        # Step 1 — build product state across counting qubits.
        # Each qubit k is prepared as (|0> + e^(i·φ·2^k)|1>) / √2.
        # LSB-first tensor order (qubit 0 = LSB = lowest power) is
        # required so that the IQFT maps the accumulated phase correctly
        # to the integer bin j = round(φ_norm · N).
        counting_sv = np.array([1.0 + 0j], dtype=complex)

        for k in range(self.n_counting):
            power   = 2 ** k
            phase   = cmath_exp(eigenphase * power)
            qubit_k = np.array([1.0, phase], dtype=complex) / math.sqrt(2)
            # kron(qubit_k, sv): qubit_k is MORE significant — LSB first
            counting_sv = np.kron(qubit_k, counting_sv)

        # Step 2 — apply Inverse QFT to counting register
        iqft = _iqft_matrix(_N_BINS)
        sv   = iqft @ counting_sv

        self.counting_sv   = sv
        self.probabilities = np.abs(sv) ** 2

        # Step 3 — find dominant phase bin
        self._extract_phases(theta)

    # ---------------------------------------------------------

    def _extract_phases(self, theta: float):
        """Read out top phase estimates from the measurement distribution."""

        probs = self.probabilities
        top_indices = np.argsort(probs)[::-1][:5]

        self.top_phases = []

        for rank, j in enumerate(top_indices):
            phi   = j / _N_BINS          # estimated φ_norm ∈ [0, 1)
            # QPE recovers φ_norm = eigenphase / (2π) = θ / (4π)
            # Reconstruct: θ_est = φ_norm × 4π
            # Fold to [0, π] using the complementary eigenvalue symmetry:
            #   if θ_est > 2π  →  θ_est mod 2π
            #   if θ_est > π   →  2π - θ_est
            theta_est = phi * 4.0 * math.pi
            theta_est = theta_est % (2.0 * math.pi)
            if theta_est > math.pi:
                theta_est = 2.0 * math.pi - theta_est
            p_up_est  = math.sin(theta_est / 2.0) ** 2
            prob      = float(probs[j])

            self.top_phases.append({
                "Rank"        : rank + 1,
                "Bin"         : int(j),
                "Phase"       : round(phi, 6),
                "ThetaEst"    : round(theta_est, 6),
                "PUpEst"      : round(p_up_est, 4),
                "Probability" : round(prob, 6),
            })

        # Best estimate = highest-probability bin
        best = self.top_phases[0]
        self.phase_estimate  = best["Phase"]
        self.theta_estimate  = best["ThetaEst"]
        self.p_up_estimate   = best["PUpEst"]

        # Confidence = ratio of top-bin probability to uniform (1/N_BINS)
        # 1.0 = perfectly sharp peak; near 0 = flat / noisy
        uniform_prob = 1.0 / _N_BINS
        self.confidence = min(
            float(best["Probability"]) / (uniform_prob * _N_BINS),
            1.0
        )

    # ---------------------------------------------------------

    def p_up_error(self) -> float:
        """Absolute error between QPE estimate and classical P_up."""
        return abs(self.p_up_estimate - self.p_up_classical)

    # ---------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "Symbol"          : self.symbol,
            "NCountingQubits" : self.n_counting,
            "NBins"           : self.n_bins,
            "PhaseEstimate"   : self.phase_estimate,
            "ThetaEstimate"   : self.theta_estimate,
            "PUpEstimate"     : self.p_up_estimate,
            "PUpClassical"    : round(self.p_up_classical, 4),
            "PUpError"        : round(self.p_up_error(), 4),
            "Confidence"      : round(self.confidence, 4),
            "TopPhases"       : self.top_phases,
        }

    # ---------------------------------------------------------

    def __str__(self) -> str:

        err_bar = "▓" * int(self.confidence * 20)

        lines = [
            f"  Counting Qubits  : {self.n_counting}  ({self.n_bins} phase bins, "
            f"resolution = 1/{self.n_bins} ≈ {1/self.n_bins:.4f})",
            f"",
            f"  Phase Estimate   : φ = {self.phase_estimate:.6f}",
            f"  θ Estimate       : {self.theta_estimate:.6f} rad",
            f"  P(up) QPE est.   : {self.p_up_estimate:.4f}",
            f"  P(up) Classical  : {self.p_up_classical:.4f}",
            f"  Absolute Error   : {self.p_up_error():.4f}",
            f"  Confidence       : {self.confidence:.4f}  {err_bar}",
            f"",
            f"  {'Rank':<5} {'Bin':<6} {'Phase φ':<12} {'θ_est (rad)':<14} "
            f"{'P(up)_est':<12} {'Prob'}",
            f"  {'-'*4:<5} {'-'*5:<6} {'-'*10:<12} {'-'*12:<14} "
            f"{'-'*9:<12} {'-'*6}",
        ]

        for p in self.top_phases:
            lines.append(
                f"  {p['Rank']:<5} {p['Bin']:<6} "
                f"{p['Phase']:<12.6f} "
                f"{p['ThetaEst']:<14.6f} "
                f"{p['PUpEst']:<12.4f} "
                f"{p['Probability']:.6f}"
            )

        return "\n".join(lines)
