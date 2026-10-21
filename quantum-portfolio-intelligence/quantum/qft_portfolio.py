"""
qft_portfolio.py

Runs QFT analysis for every stock in a portfolio.

Version : 2.8.0
"""

from __future__ import annotations

from quantum.qft_analyzer import QFTAnalyzer


class QFTPortfolio:
    """
    Runs QFT on each stock and collects results.

    Parameters
    ----------
    portfolio : PortfolioAnalyzer
    """

    # ---------------------------------------------------------

    def __init__(self, portfolio):

        self.portfolio = portfolio
        self.results: dict[str, QFTAnalyzer] = {}

    # ---------------------------------------------------------

    def run(self):

        self.results.clear()

        for symbol, analyzer in self.portfolio.analyzers.items():

            qft = QFTAnalyzer(symbol, analyzer)
            qft.run()
            self.results[symbol] = qft

        return self.results

    # ---------------------------------------------------------

    def get(self, symbol: str) -> QFTAnalyzer:
        return self.results[symbol]

    # ---------------------------------------------------------

    def symbols(self) -> list[str]:
        return list(self.results.keys())

    # ---------------------------------------------------------

    def dominant_periods(self) -> dict[str, float]:
        """Returns {symbol: dominant_period_days} for all stocks."""
        return {
            symbol: qft.dominant_period()
            for symbol, qft in self.results.items()
        }

    # ---------------------------------------------------------

    def shortest_cycle(self) -> tuple[str, float]:
        """Stock with the shortest dominant period (most active cycle)."""
        periods = self.dominant_periods()
        symbol  = min(periods, key=lambda s: periods[s])
        return symbol, periods[symbol]

    # ---------------------------------------------------------

    def longest_cycle(self) -> tuple[str, float]:
        """Stock with the longest dominant period (slowest cycle)."""
        periods = self.dominant_periods()
        symbol  = max(periods, key=lambda s: periods[s])
        return symbol, periods[symbol]
