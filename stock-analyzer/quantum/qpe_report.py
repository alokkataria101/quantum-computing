"""
qpe_report.py

Prints and exports QPE results for a portfolio.

Version : 2.9.0
"""

from __future__ import annotations

import json
import csv
from pathlib import Path

from quantum.qpe_portfolio import QPEPortfolio


class QPEReport:
    """
    Prints and exports QPE results.

    Parameters
    ----------
    qpe_portfolio : QPEPortfolio  (already run() called)
    """

    # ---------------------------------------------------------

    def __init__(self, qpe_portfolio: QPEPortfolio):

        self.qpe_portfolio = qpe_portfolio

    # ---------------------------------------------------------

    def print(self):

        print()
        print("=" * 72)
        print("Quantum Phase Estimation  (QPE v2.9)")
        print("=" * 72)
        print("  Unitary  : U = Ry(θ_q0)  — Probability qubit of each stock")
        print(f"  Counting : {self.qpe_portfolio.get(self.qpe_portfolio.symbols()[0]).n_counting} qubits  "
              f"→  {self.qpe_portfolio.get(self.qpe_portfolio.symbols()[0]).n_bins} phase bins")
        print("  Output   : φ_est → θ_est → P(up)_est  vs  classical P(up)")
        print("=" * 72)

        for symbol in self.qpe_portfolio.symbols():

            qpe = self.qpe_portfolio.get(symbol)

            print()
            print(symbol)
            print("-" * len(symbol))
            print(qpe)

        print()
        print("=" * 72)
        print("QPE Summary")
        print("=" * 72)

        print()
        print(f"  {'Symbol':<12} {'P(up) Classical':>17} {'P(up) QPE':>11} "
              f"{'Error':>8} {'Confidence':>12}")
        print(f"  {'-'*11:<12} {'-'*15:>17} {'-'*9:>11} {'-'*6:>8} {'-'*10:>12}")

        for symbol in self.qpe_portfolio.symbols():
            qpe = self.qpe_portfolio.get(symbol)
            print(
                f"  {symbol:<12} "
                f"{qpe.p_up_classical:>17.4f} "
                f"{qpe.p_up_estimate:>11.4f} "
                f"{qpe.p_up_error():>8.4f} "
                f"{qpe.confidence:>12.4f}"
            )

        print()

        sym, err = self.qpe_portfolio.most_accurate()
        print(f"  Most Accurate  : {sym}  (error = {err:.4f})")

        sym, err = self.qpe_portfolio.least_accurate()
        print(f"  Least Accurate : {sym}  (error = {err:.4f})")

        sym, conf = self.qpe_portfolio.highest_confidence()
        print(f"  Highest Confidence : {sym}  ({conf:.4f})")

        sym, conf = self.qpe_portfolio.lowest_confidence()
        print(f"  Lowest  Confidence : {sym}  ({conf:.4f})")

        print("=" * 72)

    # ---------------------------------------------------------

    def export_csv(
        self,
        filename: str = "output/reports/portfolio_qpe.csv",
    ):
        rows = []
        for symbol in self.qpe_portfolio.symbols():
            qpe = self.qpe_portfolio.get(symbol)
            rows.append({
                "Symbol"         : symbol,
                "NCountingQubits": qpe.n_counting,
                "NBins"          : qpe.n_bins,
                "PhaseEstimate"  : qpe.phase_estimate,
                "ThetaEstimate"  : qpe.theta_estimate,
                "PUpEstimate"    : qpe.p_up_estimate,
                "PUpClassical"   : qpe.p_up_classical,
                "PUpError"       : qpe.p_up_error(),
                "Confidence"     : qpe.confidence,
            })

        if rows:
            with open(filename, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)

        print(f"QPE CSV saved               : {filename}")

    # ---------------------------------------------------------

    def export_json(
        self,
        filename: str = "output/reports/portfolio_qpe.json",
    ):
        data = [
            self.qpe_portfolio.get(s).to_dict()
            for s in self.qpe_portfolio.symbols()
        ]

        Path(filename).write_text(
            json.dumps(data, indent=2),
            encoding="utf-8"
        )

        print(f"QPE JSON saved              : {filename}")
