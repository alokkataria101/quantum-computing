"""
comparison.py

Compares results across a portfolio of stocks.

Version : 2.6.0
"""

from __future__ import annotations

import pandas as pd


class ComparisonEngine:

    def __init__(self, portfolio):

        self.portfolio = portfolio

        self.summary = portfolio.get_all_summaries()

        self.df = self._build_dataframe()

    # ------------------------------------------------------

    def _build_dataframe(self):

        rows = []

        for symbol, s in self.summary.items():

            rows.append({

                "Symbol": symbol,

                # P(Close>Open): probability that Close > Open (intraday up)
                "ProbabilityUp":
                    s["ProbabilityUp"] * 100,

                # P(Open>Close): probability that Open > Close (intraday down)
                "ProbabilityDown":
                    s["ProbabilityDown"] * 100,

                "AverageGain":
                    s["AverageGain"],

                "AverageLoss":
                    s["AverageLoss"],

                "Volatility":
                    s["Volatility"],

                "GreenDays":
                    s["GreenDays"],

                "RedDays":
                    s["RedDays"]

            })

        return pd.DataFrame(rows)

    # ------------------------------------------------------

    def dataframe(self):

        return self.df

    # ------------------------------------------------------

    def print_table(self):

        print()

        print("=" * 95)

        print("Portfolio Comparison")
        print("P(Close>Open) = probability Close > Open (intraday)  |  "
              "P(Open>Close) = probability Open > Close (intraday)")

        print("=" * 95)

        display = self.df.rename(columns={
            "ProbabilityUp":   "P(Close>Open)%",
            "ProbabilityDown": "P(Open>Close)%",
        })

        print(display.to_string(index=False))

        print("=" * 95)

    # ------------------------------------------------------

    def rank_probability(self):

        return self.df.sort_values(

            "ProbabilityUp",

            ascending=False

        )

    # ------------------------------------------------------

    def rank_gain(self):

        return self.df.sort_values(

            "AverageGain",

            ascending=False

        )

    # ------------------------------------------------------

    def rank_volatility(self):

        return self.df.sort_values(

            "Volatility"

        )

    # ------------------------------------------------------

    def best_probability(self):

        return self.rank_probability().iloc[0]

    # ------------------------------------------------------

    def highest_gain(self):

        return self.rank_gain().iloc[0]

    # ------------------------------------------------------

    def lowest_risk(self):

        return self.rank_volatility().iloc[0]
