"""
portfolio.py

Portfolio analysis for multiple NSE stocks.

Version : 2.6.0
"""

from __future__ import annotations

from analyzer import StockAnalyzer
from data_loader import load_stock_data


class PortfolioAnalyzer:
    """
    Analyze multiple stocks and store their results.
    """

    def __init__(self, symbols, days):

        self.symbols = [s.upper() for s in symbols]
        self.days = days

        self.analyzers = {}
        self.summary = {}

    # --------------------------------------------------

    def analyze(self):

        print("\nStarting Portfolio Analysis")
        print("-" * 60)

        for symbol in self.symbols:

            print(f"\nAnalyzing {symbol}...")

            try:

                df = load_stock_data(
                    symbol,
                    self.days
                )

                analyzer = StockAnalyzer(
                    df,
                    symbol
                )

                analyzer.run_analysis()

                self.analyzers[symbol] = analyzer

                self.summary[symbol] = (
                    analyzer.get_summary()
                )

                print(f"✓ {symbol} completed.")

            except Exception as ex:

                print(f"✗ {symbol} failed : {ex}")

        print("\nPortfolio Analysis Finished.")

    # --------------------------------------------------

    def get_symbols(self):

        return list(self.summary.keys())

    # --------------------------------------------------

    def get_summary(self, symbol):

        return self.summary[symbol]

    # --------------------------------------------------

    def get_analyzer(self, symbol):

        return self.analyzers[symbol]

    # --------------------------------------------------

    def get_all_summaries(self):

        return self.summary

    # --------------------------------------------------

    def print_summary(self):

        print("\nPortfolio Summary")
        print("=" * 80)

        header = (
            f"{'Stock':12}"
            f"{'Up %':>10}"
            f"{'Avg Gain':>12}"
            f"{'Avg Loss':>12}"
            f"{'Volatility':>14}"
        )

        print(header)
        print("-" * len(header))

        for symbol, s in self.summary.items():

            print(
                f"{symbol:12}"
                f"{s['ProbabilityUp']*100:10.2f}"
                f"{s['AverageGain']:12.2f}"
                f"{s['AverageLoss']:12.2f}"
                f"{s['Volatility']:14.2f}"
            )

        print("=" * 80)

    # --------------------------------------------------

    def rank_by_probability(self):

        return sorted(

            self.summary.items(),

            key=lambda x: x[1]["ProbabilityUp"],

            reverse=True

        )

    # --------------------------------------------------

    def rank_by_volatility(self):

        return sorted(

            self.summary.items(),

            key=lambda x: x[1]["Volatility"]

        )

    # --------------------------------------------------

    def best_stock(self):

        return self.rank_by_probability()[0]

    # --------------------------------------------------

    def least_volatile(self):

        return self.rank_by_volatility()[0]