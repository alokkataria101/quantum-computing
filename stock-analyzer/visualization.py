"""
visualization.py

Generates stock analysis charts.

Version : 2.6.0
"""

from __future__ import annotations

import os

import matplotlib.pyplot as plt

from config import (
    OUTPUT_CHART_DIR,
    FIGURE_SIZE,
    DPI,
    PRICE_CHART_SUFFIX,
    RETURN_CHART_SUFFIX
)


class StockVisualizer:

    def __init__(self, analyzer):

        self.analyzer = analyzer
        self.df = analyzer.get_dataframe()
        self.symbol = analyzer.symbol


    # -----------------------------------------------------

    def generate_all(self):

        self.generate_price_chart()

        self.generate_return_chart()

        self.generate_volume_chart()


    # -----------------------------------------------------

    def generate_price_chart(self):

        plt.figure(
            figsize=FIGURE_SIZE,
            dpi=DPI
        )

        plt.plot(
            self.df["Date"],
            self.df["Close"],
            label="Close Price"
        )


        for column in [
            "MA_20",
            "MA_50",
            "MA_100"
        ]:

            if column in self.df.columns:

                plt.plot(
                    self.df["Date"],
                    self.df[column],
                    label=column
                )


        plt.title(
            f"{self.symbol} Price Trend"
        )

        plt.xlabel("Date")

        plt.ylabel("Price")

        plt.legend()

        plt.grid(True)

        plt.xticks(rotation=45)

        plt.tight_layout()


        filename = os.path.join(
            OUTPUT_CHART_DIR,
            self.symbol +
            PRICE_CHART_SUFFIX
        )


        plt.savefig(filename)

        plt.close()


        print(
            "Created:",
            filename
        )


    # -----------------------------------------------------

    def generate_return_chart(self):

        plt.figure(
            figsize=FIGURE_SIZE,
            dpi=DPI
        )


        plt.hist(
            self.df["DailyReturn"].dropna(),
            bins=40
        )


        plt.title(
            f"{self.symbol} Daily Return Distribution"
        )


        plt.xlabel(
            "Daily Return (%)"
        )


        plt.ylabel(
            "Frequency"
        )


        plt.grid(True)


        filename = os.path.join(
            OUTPUT_CHART_DIR,
            self.symbol +
            RETURN_CHART_SUFFIX
        )


        plt.tight_layout()

        plt.savefig(filename)

        plt.close()


        print(
            "Created:",
            filename
        )


    # -----------------------------------------------------

    def generate_volume_chart(self):

        filename = os.path.join(
            OUTPUT_CHART_DIR,
            self.symbol +
            "_volume.png"
        )


        plt.figure(
            figsize=FIGURE_SIZE,
            dpi=DPI
        )


        plt.bar(
            self.df["Date"],
            self.df["Volume"]
        )


        plt.title(
            f"{self.symbol} Volume"
        )


        plt.xlabel(
            "Date"
        )


        plt.ylabel(
            "Volume"
        )


        plt.xticks(
            rotation=45
        )


        plt.grid(True)


        plt.tight_layout()


        plt.savefig(filename)

        plt.close()


        print(
            "Created:",
            filename
        )
