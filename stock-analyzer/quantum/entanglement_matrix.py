"""
entanglement_matrix.py

Computes pairwise entanglement for all stocks in a portfolio.

Version : 2.7.0
"""

from __future__ import annotations

import pandas as pd

from quantum.entanglement_pair import EntanglementPair


class EntanglementMatrix:
    """
    Builds entanglement metrics for every unique stock pair.

    Parameters
    ----------
    quantum_portfolio : QuantumPortfolio
    correlation_matrix : pd.DataFrame   classical Pearson correlations
    """

    # ---------------------------------------------------------

    def __init__(self, quantum_portfolio, correlation_matrix: pd.DataFrame):

        self.quantum_portfolio    = quantum_portfolio
        self.correlation_matrix   = correlation_matrix
        self.pairs: list[EntanglementPair] = []
        self._entropy_df      = None
        self._concurrence_df  = None

    # ---------------------------------------------------------

    def calculate(self):

        symbols = self.quantum_portfolio.symbols()

        self.pairs.clear()

        for i in range(len(symbols)):
            for j in range(i + 1, len(symbols)):

                sa = symbols[i]
                sb = symbols[j]

                state_a = self.quantum_portfolio.get_state(sa)
                state_b = self.quantum_portfolio.get_state(sb)

                classical_corr = float(
                    self.correlation_matrix.loc[sa, sb]
                ) if sa in self.correlation_matrix.index else 0.0

                pair = EntanglementPair(
                    sa, state_a,
                    sb, state_b,
                    classical_corr=classical_corr,
                )

                self.pairs.append(pair)

        self._build_matrices(symbols)

        return self.pairs

    # ---------------------------------------------------------

    def _build_matrices(self, symbols: list[str]):

        n = len(symbols)
        idx = {s: i for i, s in enumerate(symbols)}

        ent  = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
        conc = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]

        for pair in self.pairs:
            i = idx[pair.symbol_a]
            j = idx[pair.symbol_b]
            ent[i][j]  = ent[j][i]  = pair.entropy
            conc[i][j] = conc[j][i] = pair.concurrence

        self._entropy_df     = pd.DataFrame(ent,  index=symbols, columns=symbols)
        self._concurrence_df = pd.DataFrame(conc, index=symbols, columns=symbols)

    # ---------------------------------------------------------

    def highest_entanglement(self) -> EntanglementPair:
        return max(self.pairs, key=lambda p: p.entropy)

    # ---------------------------------------------------------

    def lowest_entanglement(self) -> EntanglementPair:
        return min(self.pairs, key=lambda p: p.entropy)

    # ---------------------------------------------------------

    def entropy_dataframe(self) -> pd.DataFrame:
        return self._entropy_df

    # ---------------------------------------------------------

    def concurrence_dataframe(self) -> pd.DataFrame:
        return self._concurrence_df
