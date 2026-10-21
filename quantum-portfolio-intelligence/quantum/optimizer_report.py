"""
optimizer_report.py

Prints and exports VQC Portfolio Optimisation results.

Version : 3.0.0
"""

from __future__ import annotations

import json
import csv
import math
import numpy as np
from pathlib import Path

from quantum.vqc_optimizer import VQCOptimizer


# Colour blocks for weight bar
_BAR_CHAR  = "█"
_BAR_SCALE = 40   # full bar = 40 chars for 100%


class OptimizerReport:
    """
    Prints and exports the VQC optimisation results.

    Parameters
    ----------
    optimizer : VQCOptimizer  (already optimise() called)
    """

    # ---------------------------------------------------------

    def __init__(self, optimizer: VQCOptimizer):
        self.optimizer = optimizer

    # ---------------------------------------------------------

    def print(self):

        opt = self.optimizer

        print()
        print("=" * 72)
        print("Quantum Portfolio Optimizer  (VQC v3.0)")
        print("=" * 72)
        print("  Ansatz  : Ry(encode) → CNOT ring → Ry(variational)")
        print(f"  Stocks  : {opt.n}   Optimizer : COBYLA")
        print(f"  Iterations : {opt.n_iterations}   "
              f"Converged : {'Yes' if opt.converged else 'No (max iterations)'}")
        print("=" * 72)

        print()
        print("Optimal Portfolio Allocation")
        print("-" * 72)
        print(f"  {'Symbol':<12} {'Weight':>8} {'Weight%':>9} "
              f"{'ReturnContrib':>14} {'Rec':<12} Bar")
        print(f"  {'-'*11:<12} {'-'*6:>8} {'-'*7:>9} "
              f"{'-'*12:>14} {'-'*10:<12} {'-'*20}")

        for row in opt.allocation():
            bar = _BAR_CHAR * int(row["Weight"] * _BAR_SCALE)
            print(
                f"  {row['Symbol']:<12} "
                f"{row['Weight']:>8.4f} "
                f"{row['WeightPct']:>8.2f}% "
                f"{row['ReturnContrib']:>14.4f} "
                f"{row['Recommendation']:<12} "
                f"{bar}"
            )

        print()
        print("=" * 72)
        print("Portfolio Metrics")
        print("=" * 72)
        print(f"  Expected Daily Return : {opt.optimal_return:+.4f}%")
        print(f"  Portfolio Risk (σ)    : {opt.optimal_risk:.4f}")
        print(f"  Sharpe Ratio          : {opt.optimal_sharpe:.4f}")
        print()

        # Quantum vs Equal-weight comparison
        n       = opt.n
        eq_w    = np.ones(n) / n
        eq_ret  = float(np.dot(eq_w, opt.mu))
        eq_var  = float(eq_w @ opt.cov @ eq_w)
        import math
        eq_risk = math.sqrt(max(eq_var, 0.0)) + 1e-8
        eq_sh   = eq_ret / eq_risk

        print("  Comparison vs Equal-Weight Benchmark")
        print(f"  {'':30} {'VQC':>10} {'Equal-Wt':>10}")
        print(f"  {'Expected Return':30} {opt.optimal_return:>10.4f} {eq_ret:>10.4f}")
        print(f"  {'Portfolio Risk':30} {opt.optimal_risk:>10.4f} {eq_risk:>10.4f}")
        print(f"  {'Sharpe Ratio':30} {opt.optimal_sharpe:>10.4f} {eq_sh:>10.4f}")

        improvement = ((opt.optimal_sharpe - eq_sh) / abs(eq_sh)) * 100 if eq_sh != 0 else 0
        arrow = "↑" if improvement >= 0 else "↓"
        print(f"\n  Sharpe Improvement vs Equal-Weight : "
              f"{arrow} {abs(improvement):.1f}%")

        print("=" * 72)

    # ---------------------------------------------------------

    def export_csv(
        self,
        filename: str = "output/reports/portfolio_optimizer.csv",
    ):
        rows = self.optimizer.allocation()
        if rows:
            with open(filename, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
        print(f"Optimizer CSV saved         : {filename}")

    # ---------------------------------------------------------

    def export_json(
        self,
        filename: str = "output/reports/portfolio_optimizer.json",
    ):
        Path(filename).write_text(
            json.dumps(self.optimizer.to_dict(), indent=2),
            encoding="utf-8"
        )
        print(f"Optimizer JSON saved        : {filename}")


