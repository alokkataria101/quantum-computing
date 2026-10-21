"""
report.py

Generates reports for the Quantum Stock Probability Analyzer.

Version : 2.6.0
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from config import (
    OUTPUT_REPORT_DIR,
    CSV_SUFFIX,
    JSON_SUFFIX,
    PERCENT_PRECISION,
    PRICE_PRECISION
)


class ReportGenerator:

    def __init__(self, analyzer):

        self.analyzer = analyzer
        self.df = analyzer.get_dataframe()
        self.summary = analyzer.get_summary()
        self.symbol = analyzer.symbol

    # ---------------------------------------------------------

    def print_summary(self):

        print("\n" + "=" * 70)
        print(f"        {self.symbol} Stock Analysis Report")
        print("=" * 70)

        self._print_section("General")

        self._print_item(
            "Trading Days",
            self.summary["TradingDays"]
        )

        self._print_item(
            "Green Days",
            self.summary["GreenDays"]
        )

        self._print_item(
            "Red Days",
            self.summary["RedDays"]
        )

        self._print_section("Probability")

        self._print_item(
            "Close > Open",
            self._percent(
                self.summary["ProbabilityUp"] * 100
            )
        )

        self._print_item(
            "Open > Close",
            self._percent(
                self.summary["ProbabilityDown"] * 100
            )
        )

        self._print_section("Performance")

        self._print_item(
            "Average Open",
            self._price(
                self.summary["AverageOpen"]
            )
        )

        self._print_item(
            "Average Close",
            self._price(
                self.summary["AverageClose"]
            )
        )

        self._print_item(
            "Average Gain",
            self._percent(
                self.summary["AverageGain"]
            )
        )

        self._print_item(
            "Average Loss",
            self._percent(
                self.summary["AverageLoss"]
            )
        )

        self._print_item(
            "Maximum Gain",
            self._percent(
                self.summary["MaxGain"]
            )
        )

        self._print_item(
            "Maximum Loss",
            self._percent(
                self.summary["MaxLoss"]
            )
        )

        self._print_section("Risk")

        self._print_item(
            "Volatility",
            round(
                self.summary["Volatility"],
                3
            )
        )

        self._print_item(
            "Standard Deviation",
            round(
                self.summary["StdDev"],
                3
            )
        )

        self._print_section("Trend")

        self._print_item(
            "Longest Green Streak",
            self.summary["LongestGreenStreak"]
        )

        self._print_item(
            "Longest Red Streak",
            self.summary["LongestRedStreak"]
        )

        print("=" * 70)
        print()

    # ---------------------------------------------------------

    def export_csv(self):

        filename = (
            Path(OUTPUT_REPORT_DIR)
            / f"{self.symbol}{CSV_SUFFIX}"
        )

        self.df.to_csv(
            filename,
            index=False
        )

        print(f"CSV report saved : {filename}")

    # ---------------------------------------------------------

    def export_json(self):

        filename = (
            Path(OUTPUT_REPORT_DIR)
            / f"{self.symbol}{JSON_SUFFIX}"
        )

        report = {

            "stock": self.symbol,

            "analysis": {

                "trading_days":
                    self.summary["TradingDays"],

                "green_days":
                    self.summary["GreenDays"],

                "red_days":
                    self.summary["RedDays"]

            },

            "probability": {

                "close_above_open":
                    round(
                        self.summary["ProbabilityUp"],
                        4
                    ),

                "close_below_open":
                    round(
                        self.summary["ProbabilityDown"],
                        4
                    )

            },

            "performance": {

                "average_open":
                    round(
                        self.summary["AverageOpen"],
                        PRICE_PRECISION
                    ),

                "average_close":
                    round(
                        self.summary["AverageClose"],
                        PRICE_PRECISION
                    ),

                "average_gain":
                    round(
                        self.summary["AverageGain"],
                        PERCENT_PRECISION
                    ),

                "average_loss":
                    round(
                        self.summary["AverageLoss"],
                        PERCENT_PRECISION
                    ),

                "maximum_gain":
                    round(
                        self.summary["MaxGain"],
                        PERCENT_PRECISION
                    ),

                "maximum_loss":
                    round(
                        self.summary["MaxLoss"],
                        PERCENT_PRECISION
                    )

            },

            "risk": {

                "volatility":
                    round(
                        self.summary["Volatility"],
                        4
                    ),

                "standard_deviation":
                    round(
                        self.summary["StdDev"],
                        4
                    )

            },

            "streaks": {

                "longest_green":
                    self.summary["LongestGreenStreak"],

                "longest_red":
                    self.summary["LongestRedStreak"]

            }

        }

        with open(filename, "w") as fp:

            json.dump(
                report,
                fp,
                indent=4
            )

        print(f"JSON report saved: {filename}")

    # ---------------------------------------------------------

    @staticmethod
    def _print_section(title):

        print(f"\n[{title}]")

    # ---------------------------------------------------------

    @staticmethod
    def _print_item(name, value):

        print(f"{name:<30} : {value}")

    # ---------------------------------------------------------

    @staticmethod
    def _percent(value):

        return f"{value:.2f}%"

    # ---------------------------------------------------------

    @staticmethod
    def _price(value):

        return f"₹{value:.2f}"