"""
correlation.py

Portfolio Correlation Engine

Version : 2.6.0
"""

from __future__ import annotations

import os

import pandas as pd
import matplotlib.pyplot as plt

from config import OUTPUT_REPORT_DIR, OUTPUT_CHART_DIR


class CorrelationEngine:

    def __init__(self, portfolio):

        self.portfolio = portfolio

        self.correlation = None

    # ----------------------------------------------------------

    def build(self):

        """
        Build correlation matrix using closing prices.
        """

        prices = pd.DataFrame()

        for symbol in self.portfolio.get_symbols():

            analyzer = self.portfolio.get_analyzer(symbol)

            df = analyzer.get_dataframe()

            temp = df[["Close"]].copy()

            temp.rename(
                columns={
                    "Close": symbol
                },
                inplace=True
            )

            if prices.empty:

                prices = temp

            else:

                prices = prices.join(
                    temp,
                    how="inner"
                )

        self.correlation = prices.corr()

        return self.correlation

    # ----------------------------------------------------------

    def dataframe(self):

        if self.correlation is None:

            self.build()

        return self.correlation

    # ----------------------------------------------------------

    def print(self):

        if self.correlation is None:

            self.build()

        print()

        print("=" * 70)

        print("Portfolio Correlation Matrix")

        print("=" * 70)

        print(self.correlation.round(3))

        print("=" * 70)

    # ----------------------------------------------------------

    def export_csv(self):

        if self.correlation is None:

            self.build()

        os.makedirs(
            OUTPUT_REPORT_DIR,
            exist_ok=True
        )

        filename = os.path.join(

            OUTPUT_REPORT_DIR,

            "portfolio_correlation.csv"

        )

        self.correlation.to_csv(filename)

        print()

        print(f"Correlation CSV saved : {filename}")

    # ----------------------------------------------------------

    def export_heatmap(self):

        if self.correlation is None:

            self.build()

        os.makedirs(
            OUTPUT_CHART_DIR,
            exist_ok=True
        )

        plt.figure(figsize=(8, 6))

        plt.imshow(

            self.correlation,

            interpolation="nearest",

            aspect="auto"

        )

        plt.colorbar()

        plt.xticks(

            range(len(self.correlation.columns)),

            self.correlation.columns,

            rotation=45

        )

        plt.yticks(

            range(len(self.correlation.columns)),

            self.correlation.columns

        )

        plt.title("Portfolio Correlation Heatmap")

        plt.tight_layout()

        filename = os.path.join(

            OUTPUT_CHART_DIR,

            "portfolio_correlation.png"

        )

        plt.savefig(

            filename,

            dpi=150

        )

        plt.close()

        print(

            f"Correlation Heatmap : {filename}"

        )

    # ----------------------------------------------------------

    def highest_pair(self):

        """
        Highest correlation excluding diagonal.
        """

        if self.correlation is None:

            self.build()

        corr = self.correlation.copy()

        for c in corr.columns:

            corr.loc[c, c] = -1

        max_value = corr.max().max()

        location = corr.stack().idxmax()

        return (

            location[0],

            location[1],

            max_value

        )

    # ----------------------------------------------------------

    def lowest_pair(self):

        """
        Lowest correlation excluding diagonal.
        """

        if self.correlation is None:

            self.build()

        corr = self.correlation.copy()

        for c in corr.columns:

            corr.loc[c, c] = 2

        min_value = corr.min().min()

        location = corr.stack().idxmin()

        return (

            location[0],

            location[1],

            min_value

        )
