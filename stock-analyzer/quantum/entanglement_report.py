"""
entanglement_report.py

Prints and exports portfolio entanglement results.

Version : 2.7.0
"""

from __future__ import annotations

import json
from pathlib import Path

from quantum.entanglement_matrix import EntanglementMatrix


class EntanglementReport:
    """
    Prints and exports entanglement results.

    Parameters
    ----------
    matrix : EntanglementMatrix  (already calculated)
    """

    # ---------------------------------------------------------

    def __init__(self, matrix: EntanglementMatrix):

        self.matrix = matrix

    # ---------------------------------------------------------

    def print(self):

        pairs = self.matrix.pairs

        print()
        print("=" * 72)
        print("Portfolio Entanglement  (CNOT v2.7)")
        print("=" * 72)

        for pair in pairs:

            label = f"{pair.symbol_a}  ↔  {pair.symbol_b}"

            print()
            print(label)
            print("-" * len(label))
            print(pair)

        print()
        print("=" * 72)
        print("Entanglement Entropy Matrix")
        print("=" * 72)
        print(self.matrix.entropy_dataframe().round(6))

        print()
        print("=" * 72)
        print("Concurrence Matrix")
        print("=" * 72)
        print(self.matrix.concurrence_dataframe().round(6))

        print()

        hi = self.matrix.highest_entanglement()
        lo = self.matrix.lowest_entanglement()

        print(
            f"Highest Entanglement : "
            f"{hi.symbol_a} ↔ {hi.symbol_b}  "
            f"(entropy={hi.entropy:.6f}  concurrence={hi.concurrence:.6f})"
        )
        print(
            f"Lowest  Entanglement : "
            f"{lo.symbol_a} ↔ {lo.symbol_b}  "
            f"(entropy={lo.entropy:.6f}  concurrence={lo.concurrence:.6f})"
        )

        print()
        print("Quantum vs Classical Correlation")
        print("-" * 40)

        for pair in pairs:
            qvc = pair.quantum_vs_classical()
            print(
                f"  {pair.symbol_a:<10} ↔ {pair.symbol_b:<10}  "
                f"Classical={qvc['ClassicalCorrelation']:+.4f}  "
                f"Concurrence={qvc['Concurrence']:.4f}  "
                f"Bell={qvc['BellState']}"
            )

        print("=" * 72)

    # ---------------------------------------------------------

    def export_csv(
        self,
        entropy_file: str  = "output/reports/portfolio_entanglement_entropy.csv",
        concurrence_file: str = "output/reports/portfolio_entanglement_concurrence.csv",
    ):
        self.matrix.entropy_dataframe().to_csv(entropy_file)
        self.matrix.concurrence_dataframe().to_csv(concurrence_file)

        print(f"Entanglement Entropy CSV    : {entropy_file}")
        print(f"Entanglement Concurrence CSV: {concurrence_file}")

    # ---------------------------------------------------------

    def export_json(
        self,
        filename: str = "output/reports/portfolio_entanglement.json",
    ):
        data = [pair.to_dict() for pair in self.matrix.pairs]

        Path(filename).write_text(
            json.dumps(data, indent=2),
            encoding="utf-8"
        )

        print(f"Entanglement JSON saved     : {filename}")
