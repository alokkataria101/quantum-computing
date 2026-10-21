"""
portfolio_summary.py

Portfolio Executive Summary

Version : 2.6.0
"""

from __future__ import annotations

from insights import InsightEngine


class PortfolioSummary:

    def __init__(self, portfolio, comparison, correlation):

        self.portfolio = portfolio
        self.comparison = comparison
        self.correlation = correlation

    # ----------------------------------------------------------

    def generate(self):

        lines = []

        lines.append("=" * 72)
        lines.append("PORTFOLIO EXECUTIVE SUMMARY")
        lines.append("=" * 72)

        lines.append(
            f"Total Stocks Analysed : {len(self.portfolio.get_symbols())}"
        )

        lines.append("")

        #
        # Best Performing Stock
        #

        best = self.comparison.best_probability()

        lines.append(
            f"Highest Probability Stock : "
            f"{best['Symbol']} "
            f"({best['ProbabilityUp']:.2f}%)"
        )

        #
        # Lowest Risk
        #

        risk = self.comparison.lowest_risk()

        lines.append(
            f"Lowest Volatility Stock : "
            f"{risk['Symbol']} "
            f"({risk['Volatility']:.2f})"
        )

        #
        # Highest Average Gain
        #

        gain = self.comparison.highest_gain()

        lines.append(
            f"Highest Average Gain : "
            f"{gain['Symbol']} "
            f"({gain['AverageGain']:.2f}%)"
        )

        #
        # Correlation
        #

        s1, s2, corr = self.correlation.highest_pair()

        lines.append(
            f"Highest Correlation : "
            f"{s1} ↔ {s2} "
            f"({corr:.3f})"
        )

        s1, s2, corr = self.correlation.lowest_pair()

        lines.append(
            f"Lowest Correlation : "
            f"{s1} ↔ {s2} "
            f"({corr:.3f})"
        )

        lines.append("")
        lines.append("=" * 72)
        lines.append("INDIVIDUAL STOCK INSIGHTS")
        lines.append("=" * 72)

        #
        # Each Stock
        #

        for symbol in self.portfolio.get_symbols():

            analyzer = self.portfolio.get_analyzer(symbol)

            summary = analyzer.get_summary()

            insight = InsightEngine(summary)

            lines.append("")
            lines.append(symbol)
            lines.append("-" * len(symbol))
            lines.append(
                insight.executive_summary()
            )

        return "\n".join(lines)

    # ----------------------------------------------------------

    def print(self):

        print()

        print(
            self.generate()
        )
