"""
analyzer.py

Performs statistical analysis on historical stock data.

Version : 2.6.0
"""

from __future__ import annotations

import pandas as pd

from config import PRICE_MOVING_AVERAGES


class StockAnalyzer:

    def __init__(self, df: pd.DataFrame, symbol: str):

        self.symbol = symbol.upper()
        self.df = df.copy()

        # Summary is maintained as a dictionary.
        self.summary = {}

    # ------------------------------------------------------

    def run_analysis(self):

        self._calculate_returns()
        self._calculate_probabilities()
        self._calculate_statistics()
        self._calculate_streaks()
        self._calculate_moving_averages()
        self._calculate_trend()
        self._calculate_volume()

    # ------------------------------------------------------

    def _calculate_returns(self):

        self.df["Difference"] = (
            self.df["Close"] - self.df["Open"]
        )

        self.df["PercentChange"] = (
            self.df["Difference"] / self.df["Open"]
        ) * 100

        self.df["DailyReturn"] = (
            self.df["Close"].pct_change() * 100
        )

        self.df["Green"] = (
            self.df["Difference"] > 0
        )

    # ------------------------------------------------------

    def _calculate_probabilities(self):

        total = len(self.df)

        green = int(self.df["Green"].sum())
        red = total - green

        self.summary["TradingDays"] = total
        self.summary["GreenDays"] = green
        self.summary["RedDays"] = red

        self.summary["ProbabilityUp"] = (
            green / total if total else 0
        )

        self.summary["ProbabilityDown"] = (
            red / total if total else 0
        )

    # ------------------------------------------------------

    def _calculate_statistics(self):

        gain = self.df[self.df["Green"]]
        loss = self.df[~self.df["Green"]]

        self.summary["AverageOpen"] = float(
            self.df["Open"].mean()
        )

        self.summary["AverageClose"] = float(
            self.df["Close"].mean()
        )

        self.summary["AverageDifference"] = float(
            self.df["Difference"].mean()
        )

        self.summary["AveragePercentChange"] = float(
            self.df["PercentChange"].mean()
        )

        self.summary["AverageGain"] = float(
            gain["PercentChange"].mean()
        ) if not gain.empty else 0.0

        self.summary["AverageLoss"] = float(
            loss["PercentChange"].mean()
        ) if not loss.empty else 0.0

        self.summary["MaxGain"] = float(
            self.df["PercentChange"].max()
        )

        self.summary["MaxLoss"] = float(
            self.df["PercentChange"].min()
        )

        self.summary["Volatility"] = float(
            self.df["DailyReturn"].std()
        )

        self.summary["StdDev"] = float(
            self.df["PercentChange"].std()
        )

    # ------------------------------------------------------

    def _calculate_streaks(self):

        longest_green = 0
        longest_red = 0

        current_green = 0
        current_red = 0

        for green_day in self.df["Green"]:

            if green_day:

                current_green += 1
                current_red = 0

            else:

                current_red += 1
                current_green = 0

            longest_green = max(
                longest_green,
                current_green
            )

            longest_red = max(
                longest_red,
                current_red
            )

        self.summary["LongestGreenStreak"] = longest_green
        self.summary["LongestRedStreak"] = longest_red

    # ------------------------------------------------------

    def _calculate_moving_averages(self):

        for period in PRICE_MOVING_AVERAGES:

            self.df[f"MA_{period}"] = (
                self.df["Close"]
                .rolling(period)
                .mean()
            )

    # ------------------------------------------------------

    def _calculate_trend(self):
        """
        Linear regression slope of Close prices (normalised).
        Positive → uptrend, negative → downtrend.
        Stored as TrendSlope (% per day, normalised by mean price).
        """
        import numpy as np

        closes = self.df["Close"].values
        x = np.arange(len(closes), dtype=float)

        if len(closes) < 2:
            self.summary["TrendSlope"] = 0.0
            return

        slope, _ = np.polyfit(x, closes, 1)

        mean_price = closes.mean()

        # Express as % per day relative to mean price
        self.summary["TrendSlope"] = float(
            (slope / mean_price) * 100
        ) if mean_price != 0 else 0.0

    # ------------------------------------------------------

    def _calculate_volume(self):
        """
        Average daily volume normalised to millions.
        Stored as AverageVolume (in millions).
        """
        if "Volume" in self.df.columns:
            self.summary["AverageVolume"] = float(
                self.df["Volume"].mean() / 1_000_000
            )
        else:
            self.summary["AverageVolume"] = 0.0

    # ------------------------------------------------------

    def get_dataframe(self):

        return self.df

    # ------------------------------------------------------

    def get_summary(self):

        return self.summary

    # ------------------------------------------------------

    def print_debug(self):

        print("\nSummary")
        print("-" * 50)

        for key, value in self.summary.items():
            print(f"{key:<25} : {value}")

        print("\nLast 5 Rows")
        print("-" * 50)
        print(self.df.tail())