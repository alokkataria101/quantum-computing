"""
fidelity_matrix.py

Computes a quantum fidelity matrix for an entire portfolio.

Version : 2.6.0
"""

from __future__ import annotations

import pandas as pd

from quantum.fidelity import FidelityCalculator


class FidelityMatrix:

    # ---------------------------------------------------------

    def __init__(self, quantum_portfolio):

        self.quantum_portfolio = quantum_portfolio

        self.matrix = None

    # ---------------------------------------------------------

    def calculate(self):

        symbols = self.quantum_portfolio.symbols()

        data = []

        for s1 in symbols:

            row = []

            state1 = self.quantum_portfolio.get_state(s1)

            for s2 in symbols:

                state2 = self.quantum_portfolio.get_state(s2)

                value = FidelityCalculator.fidelity(

                    state1,

                    state2

                )

                row.append(value)

            data.append(row)

        self.matrix = pd.DataFrame(

            data,

            index=symbols,

            columns=symbols

        )

        return self.matrix

    # ---------------------------------------------------------

    def print(self):

        if self.matrix is None:

            self.calculate()

        print()

        print("=" * 72)

        print("Quantum Fidelity Matrix")

        print("=" * 72)

        print(

            self.matrix.round(6)

        )

        print("=" * 72)

    # ---------------------------------------------------------

    def export_csv(

        self,

        filename="output/reports/portfolio_fidelity.csv"

    ):

        if self.matrix is None:

            self.calculate()

        self.matrix.to_csv(

            filename

        )

        print()

        print(

            f"Quantum Fidelity CSV saved : {filename}"

        )

    # ---------------------------------------------------------

    def highest_pair(self):

        if self.matrix is None:

            self.calculate()

        best = -1

        pair = (None, None)

        symbols = self.matrix.index

        for i in range(len(symbols)):

            for j in range(i + 1, len(symbols)):

                value = self.matrix.iloc[i, j]

                if value > best:

                    best = value

                    pair = (

                        symbols[i],

                        symbols[j]

                    )

        return pair[0], pair[1], best

    # ---------------------------------------------------------

    def lowest_pair(self):

        if self.matrix is None:

            self.calculate()

        worst = 2

        pair = (None, None)

        symbols = self.matrix.index

        for i in range(len(symbols)):

            for j in range(i + 1, len(symbols)):

                value = self.matrix.iloc[i, j]

                if value < worst:

                    worst = value

                    pair = (

                        symbols[i],

                        symbols[j]

                    )

        return pair[0], pair[1], worst
