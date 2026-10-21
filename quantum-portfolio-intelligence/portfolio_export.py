"""
portfolio_export.py

Exports the complete portfolio analysis into a
single JSON file.

Version : 2.6.0
"""

from __future__ import annotations

import json
import os
from datetime import datetime

from insights import InsightEngine
from config import OUTPUT_REPORT_DIR


class PortfolioExporter:

    def __init__(
        self,
        portfolio,
        comparison,
        correlation
    ):

        self.portfolio = portfolio
        self.comparison = comparison
        self.correlation = correlation

    # -----------------------------------------------------

    def build_json(self):

        data = {}

        #
        # Metadata
        #

        data["metadata"] = {

            "version": "2.6.0",

            "generated":

                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),

            "stocks":

                len(
                    self.portfolio.get_symbols()
                )

        }

        #
        # Portfolio
        #

        data["portfolio"] = {

            "symbols":

                self.portfolio.get_symbols()

        }

        #
        # Comparison
        #

        comparison = {}

        best = self.comparison.best_probability()

        comparison["highest_probability"] = {

            "symbol":

                best["Symbol"],

            "value":

                float(
                    best["ProbabilityUp"]
                )

        }

        gain = self.comparison.highest_gain()

        comparison["highest_gain"] = {

            "symbol":

                gain["Symbol"],

            "value":

                float(
                    gain["AverageGain"]
                )

        }

        risk = self.comparison.lowest_risk()

        comparison["lowest_volatility"] = {

            "symbol":

                risk["Symbol"],

            "value":

                float(
                    risk["Volatility"]
                )

        }

        data["comparison"] = comparison

        #
        # Correlation
        #

        s1, s2, corr = \
            self.correlation.highest_pair()

        high = {

            "stock1": s1,

            "stock2": s2,

            "value": float(corr)

        }

        s1, s2, corr = \
            self.correlation.lowest_pair()

        low = {

            "stock1": s1,

            "stock2": s2,

            "value": float(corr)

        }

        data["correlation"] = {

            "highest": high,

            "lowest": low,

            "matrix":

                self.correlation
                .dataframe()
                .round(4)
                .to_dict()

        }

        #
        # Individual Stocks
        #

        stocks = []

        for symbol in self.portfolio.get_symbols():

            analyzer = \
                self.portfolio.get_analyzer(
                    symbol
                )

            summary = \
                analyzer.get_summary()

            insight = \
                InsightEngine(summary)

            stocks.append({

                "symbol":

                    symbol,

                "statistics":

                    summary,

                "executive_summary":

                    insight.executive_summary(),

                "recommendation":

                    insight.recommendation()

            })

        data["stocks"] = stocks

        return data

    # -----------------------------------------------------

    def export_json(self):

        os.makedirs(

            OUTPUT_REPORT_DIR,

            exist_ok=True

        )

        filename = os.path.join(

            OUTPUT_REPORT_DIR,

            "portfolio_complete.json"

        )

        data = self.build_json()

        with open(

            filename,

            "w",

            encoding="utf-8"

        ) as fp:

            json.dump(

                data,

                fp,

                indent=4

            )

        print()

        print(
            f"Portfolio JSON saved : {filename}"
        )

        return filename
