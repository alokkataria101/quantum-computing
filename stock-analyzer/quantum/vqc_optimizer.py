"""
vqc_optimizer.py

Variational Quantum Circuit (VQC) for portfolio weight optimisation.

Version : 3.0.0

Version 3.0 — Quantum Portfolio Optimizer:

    Pipeline
    --------
    Historical Data
        |
    Feature Extraction  (StockAnalyzer — ProbUp, Vol, Gain, Trend, Volume)
        |
    Quantum Encoding    (MultiQubitState — 5 Ry angles per stock)
        |
    Entanglement        (CNOT ring across n stocks on their q0 qubits)
        |
    Variational Circuit (trainable Ry layer per stock, optimised classically)
        |
    Measurement         (marginal P(|1>) per stock → softmax weights)
        |
    Portfolio Allocation (weights, Sharpe, expected return, risk)

    VQC Ansatz (per optimisation iteration)
    ----------------------------------------
    For n stocks, the circuit operates on n qubits (one per stock):

        Layer 1 — Encoding:
            qubit i ← Ry(θᵢ_enc)   (fixed, from MultiQubitState q0)

        Layer 2 — Entanglement:
            CNOT ring: (0→1), (1→2), …, (n-2→n-1), (n-1→0)

        Layer 3 — Variational:
            qubit i ← Ry(φᵢ)       (trainable parameters φ)

    Measurement:
        wᵢ_raw = P(|1>) on qubit i  = sin²((θᵢ_enc + φᵢ)/2)  (after CNOT)
        weights = softmax(w_raw)     (sums to 1)

    Cost function (minimised):
        cost(φ) = −Sharpe(φ)
                = −(Σ wᵢ·μᵢ) / √(wᵀ·Cov·w + ε)

        where μᵢ = average daily gain for stock i
              Cov = covariance matrix of daily returns (n×n)
              ε   = 1e-8  (numerical stability)

    Optimiser: scipy.optimize.minimize (COBYLA — derivative-free,
               handles bounds naturally via softmax).
"""

from __future__ import annotations

import math
import numpy as np
from scipy.optimize import minimize


_EPSILON = 1e-8


def _softmax(x: np.ndarray) -> np.ndarray:
    """Numerically stable softmax."""
    e = np.exp(x - x.max())
    return e / e.sum()


def _cnot_ring_statevector(
    encoding_angles: np.ndarray,
    variational_angles: np.ndarray,
) -> np.ndarray:
    """
    Simulate the VQC and return the full 2^n statevector.

    Circuit:
        1. Ry(enc_i)|0>  for each qubit i
        2. CNOT ring: i → (i+1) % n
        3. Ry(var_i) on each qubit i

    Returns the full 2^n complex statevector.
    """
    n = len(encoding_angles)
    dim = 2 ** n

    # Initialise |000…0>
    sv = np.zeros(dim, dtype=complex)
    sv[0] = 1.0

    # Layer 1: Ry encoding gates
    for i in range(n):
        sv = _apply_single_qubit_gate(sv, n, i, _ry_matrix(encoding_angles[i]))

    # Layer 2: CNOT ring
    for i in range(n):
        control = i
        target  = (i + 1) % n
        sv = _apply_cnot(sv, n, control, target)

    # Layer 3: Ry variational gates
    for i in range(n):
        sv = _apply_single_qubit_gate(sv, n, i, _ry_matrix(variational_angles[i]))

    return sv


def _ry_matrix(theta: float) -> np.ndarray:
    c = math.cos(theta / 2)
    s = math.sin(theta / 2)
    return np.array([[c, -s], [s, c]], dtype=complex)


def _apply_single_qubit_gate(
    sv:   np.ndarray,
    n:    int,
    qubit: int,
    gate: np.ndarray,
) -> np.ndarray:
    """Apply a 2×2 gate to qubit `qubit` in an n-qubit statevector."""
    new_sv = np.zeros_like(sv)
    for idx in range(2 ** n):
        # Extract the bit for this qubit (big-endian: qubit 0 = MSB)
        bit = (idx >> (n - 1 - qubit)) & 1
        # Companion basis state (flip this qubit)
        partner = idx ^ (1 << (n - 1 - qubit))
        for new_bit in range(2):
            new_idx = (idx & ~(1 << (n - 1 - qubit))) | (new_bit << (n - 1 - qubit))
            new_sv[new_idx] += gate[new_bit, bit] * sv[idx]
    return new_sv


def _apply_cnot(
    sv:      np.ndarray,
    n:       int,
    control: int,
    target:  int,
) -> np.ndarray:
    """Apply CNOT(control, target) to an n-qubit statevector."""
    new_sv = sv.copy()
    for idx in range(2 ** n):
        ctrl_bit = (idx >> (n - 1 - control)) & 1
        if ctrl_bit == 1:
            # Flip the target bit
            flipped = idx ^ (1 << (n - 1 - target))
            new_sv[idx], new_sv[flipped] = sv[flipped], sv[idx]
    return new_sv


def _marginal_p1(sv: np.ndarray, n: int, qubit: int) -> float:
    """Marginal probability of qubit being |1>."""
    total = 0.0
    for idx in range(2 ** n):
        if (idx >> (n - 1 - qubit)) & 1:
            total += abs(sv[idx]) ** 2
    return total


def _compute_weights(
    encoding_angles: np.ndarray,
    variational_angles: np.ndarray,
) -> np.ndarray:
    """Run VQC and return softmax portfolio weights."""
    n   = len(encoding_angles)
    sv  = _cnot_ring_statevector(encoding_angles, variational_angles)
    raw = np.array([
        _marginal_p1(sv, n, i) for i in range(n)
    ])
    return _softmax(raw)


def _sharpe(
    weights:    np.ndarray,
    mu:         np.ndarray,
    cov:        np.ndarray,
) -> float:
    """Sharpe ratio (risk-free rate = 0)."""
    ret  = float(np.dot(weights, mu))
    var  = float(weights @ cov @ weights)
    risk = math.sqrt(max(var, 0.0)) + _EPSILON
    return ret / risk


class VQCOptimizer:
    """
    Variational Quantum Circuit Portfolio Optimiser.

    Parameters
    ----------
    symbols          : list[str]
    encoding_angles  : np.ndarray   shape (n,)  — q0 angles from MultiQubitState
    mu               : np.ndarray   shape (n,)  — expected daily gain per stock
    cov              : np.ndarray   shape (n,n) — covariance matrix of returns
    max_iter         : int          COBYLA iteration limit (default 500)
    """

    # ---------------------------------------------------------

    def __init__(
        self,
        symbols:         list[str],
        encoding_angles: np.ndarray,
        mu:              np.ndarray,
        cov:             np.ndarray,
        max_iter:        int = 500,
    ):
        self.symbols         = symbols
        self.encoding_angles = encoding_angles
        self.mu              = mu
        self.cov             = cov
        self.max_iter        = max_iter
        self.n               = len(symbols)

        # Results (populated after optimise())
        self.optimal_angles  : np.ndarray | None = None
        self.optimal_weights : np.ndarray | None = None
        self.optimal_sharpe  : float = 0.0
        self.optimal_return  : float = 0.0
        self.optimal_risk    : float = 0.0
        self.n_iterations    : int   = 0
        self.converged       : bool  = False

    # ---------------------------------------------------------

    def _cost(self, phi: np.ndarray) -> float:
        """Negative Sharpe (minimised by COBYLA)."""
        weights = _compute_weights(self.encoding_angles, phi)
        return -_sharpe(weights, self.mu, self.cov)

    # ---------------------------------------------------------

    def optimise(self) -> np.ndarray:
        """
        Run COBYLA optimisation.
        Initial point: variational angles = encoding angles (warm start).
        Returns the optimal weight vector.
        """

        phi0 = self.encoding_angles.copy()

        result = minimize(
            self._cost,
            phi0,
            method="COBYLA",
            options={
                "maxiter" : self.max_iter,
                "rhobeg"  : 0.5,
                "disp"    : False,
            },
        )

        self.optimal_angles  = result.x
        self.optimal_weights = _compute_weights(
            self.encoding_angles,
            self.optimal_angles
        )
        self.optimal_sharpe  = _sharpe(
            self.optimal_weights,
            self.mu,
            self.cov
        )
        self.optimal_return  = float(
            np.dot(self.optimal_weights, self.mu)
        )
        self.optimal_risk    = math.sqrt(
            max(float(self.optimal_weights @ self.cov @ self.optimal_weights), 0.0)
        )
        self.n_iterations    = result.nfev
        self.converged       = result.success

        return self.optimal_weights

    # ---------------------------------------------------------

    def allocation(self) -> list[dict]:
        """
        Returns list of {Symbol, Weight, ExpectedReturn, Recommendation}.
        Sorted by weight descending.
        """
        if self.optimal_weights is None:
            raise RuntimeError("Call optimise() first.")

        results = []
        for i, symbol in enumerate(self.symbols):
            w       = float(self.optimal_weights[i])
            contrib = w * float(self.mu[i])

            if w >= 0.25:
                rec = "STRONG BUY"
            elif w >= 0.15:
                rec = "BUY"
            elif w >= 0.08:
                rec = "HOLD"
            else:
                rec = "AVOID"

            results.append({
                "Symbol"         : symbol,
                "Weight"         : round(w, 4),
                "WeightPct"      : round(w * 100, 2),
                "ReturnContrib"  : round(contrib, 4),
                "Recommendation" : rec,
            })

        return sorted(results, key=lambda x: -x["Weight"])

    # ---------------------------------------------------------

    def to_dict(self) -> dict:
        alloc = self.allocation()
        # Ensure all values are plain Python types for JSON serialisation
        for row in alloc:
            for k, v in row.items():
                if hasattr(v, "item"):          # numpy scalar
                    row[k] = v.item()
                elif isinstance(v, float):
                    row[k] = round(v, 6)
        return {
            "Symbols"       : self.symbols,
            "OptimalWeights": [round(float(w), 6)
                               for w in (self.optimal_weights if self.optimal_weights is not None else [])],
            "OptimalSharpe" : round(self.optimal_sharpe, 6),
            "ExpectedReturn": round(self.optimal_return, 6),
            "Risk"          : round(self.optimal_risk, 6),
            "Iterations"    : int(self.n_iterations),
            "Converged"     : bool(self.converged),
            "Allocation"    : alloc,
        }
