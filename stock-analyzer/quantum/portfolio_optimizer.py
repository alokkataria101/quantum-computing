"""
portfolio_optimizer.py

Runs VQC portfolio optimisation for a full portfolio.

Version : 3.0.0
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from quantum.vqc_optimizer import VQCOptimizer


class PortfolioOptimizer:
    """
    Orchestrates the full quantum portfolio optimisation pipeline.

    Parameters
    ----------
    portfolio         : PortfolioAnalyzer
    quantum_portfolio : QuantumPortfolio
    """

    # ---------------------------------------------------------

    def __init__(self, portfolio, quantum_portfolio):

        self.portfolio         = portfolio
        self.quantum_portfolio = quantum_portfolio
        self.optimizer: VQCOptimizer | None = None

    # ---------------------------------------------------------

    def run(self) -> VQCOptimizer:
        """Build inputs and run VQC optimisation."""

        symbols = self.quantum_portfolio.symbols()
        n       = len(symbols)

        # ── Encoding angles (q0 — Probability) ──────────────────
        encoding_angles = np.array([
            self.quantum_portfolio.get_state(s).angles[0]
            for s in symbols
        ])

        # ── Expected return vector μ ─────────────────────────────
        # Use AverageGain (% per green day) as proxy for expected return.
        mu = np.array([
            self.portfolio.get_analyzer(s).get_summary()["AverageGain"]
            for s in symbols
        ])

        # ── Covariance matrix Σ ──────────────────────────────────
        # Build from daily PercentChange series of each stock.
        returns_df = pd.DataFrame({
            s: self.portfolio.get_analyzer(s)
               .get_dataframe()["PercentChange"]
               .dropna()
               .values
            for s in symbols
        })

        # Align to same length (truncate to shortest)
        min_len = min(len(returns_df[s].dropna()) for s in symbols)
        aligned = returns_df.iloc[-min_len:]
        cov = aligned.cov().values  # shape (n, n)

        # ── Build and run VQC ────────────────────────────────────
        self.optimizer = VQCOptimizer(
            symbols         = symbols,
            encoding_angles = encoding_angles,
            mu              = mu,
            cov             = cov,
        )

        self.optimizer.optimise()

        return self.optimizer

    # ---------------------------------------------------------

    def get_optimizer(self) -> VQCOptimizer:
        if self.optimizer is None:
            raise RuntimeError("Call run() first.")
        return self.optimizer
