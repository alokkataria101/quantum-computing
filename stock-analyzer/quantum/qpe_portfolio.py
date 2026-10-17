"""
qpe_portfolio.py

Runs Quantum Phase Estimation for every stock in a portfolio.

Version : 2.9.0
"""

from __future__ import annotations

from quantum.qpe_analyzer import QPEAnalyzer


class QPEPortfolio:
    """
    Runs QPE on each stock using its MultiQubitState q0 angle.

    Parameters
    ----------
    portfolio        : PortfolioAnalyzer
    quantum_portfolio : QuantumPortfolio
    """

    # ---------------------------------------------------------

    def __init__(self, portfolio, quantum_portfolio):

        self.portfolio         = portfolio
        self.quantum_portfolio = quantum_portfolio
        self.results: dict[str, QPEAnalyzer] = {}

    # ---------------------------------------------------------

    def run(self):

        self.results.clear()

        for symbol, analyzer in self.portfolio.analyzers.items():

            state = self.quantum_portfolio.get_state(symbol)

            qpe = QPEAnalyzer(symbol, state, analyzer)
            qpe.run()
            self.results[symbol] = qpe

        return self.results

    # ---------------------------------------------------------

    def get(self, symbol: str) -> QPEAnalyzer:
        return self.results[symbol]

    # ---------------------------------------------------------

    def symbols(self) -> list[str]:
        return list(self.results.keys())

    # ---------------------------------------------------------

    def most_accurate(self) -> tuple[str, float]:
        """Stock whose QPE P(up) estimate is closest to classical value."""
        symbol = min(
            self.results,
            key=lambda s: self.results[s].p_up_error()
        )
        return symbol, self.results[symbol].p_up_error()

    # ---------------------------------------------------------

    def least_accurate(self) -> tuple[str, float]:
        """Stock whose QPE P(up) estimate deviates most from classical."""
        symbol = max(
            self.results,
            key=lambda s: self.results[s].p_up_error()
        )
        return symbol, self.results[symbol].p_up_error()

    # ---------------------------------------------------------

    def highest_confidence(self) -> tuple[str, float]:
        symbol = max(
            self.results,
            key=lambda s: self.results[s].confidence
        )
        return symbol, self.results[symbol].confidence

    # ---------------------------------------------------------

    def lowest_confidence(self) -> tuple[str, float]:
        symbol = min(
            self.results,
            key=lambda s: self.results[s].confidence
        )
        return symbol, self.results[symbol].confidence
