"""
prompt_builder.py

Builds a professional prompt for IBM watsonx
(or any LLM) from the portfolio analysis.

Version : 2.6.0
"""

from __future__ import annotations


class PromptBuilder:

    def __init__(self, portfolio_json: dict):

        self.data = portfolio_json

    # -----------------------------------------------------

    def build(self):

        meta = self.data["metadata"]

        portfolio = self.data["portfolio"]

        comparison = self.data["comparison"]

        correlation = self.data["correlation"]

        stocks = self.data["stocks"]

        prompt = []

        prompt.append(
            "You are an experienced financial analyst."
        )

        prompt.append(
            "Analyze the following stock portfolio using only "
            "the supplied historical statistics."
        )

        prompt.append(
            "Do not predict future stock prices."
        )

        prompt.append(
            "Base every conclusion only on the data provided."
        )

        prompt.append("")

        prompt.append("=" * 60)

        prompt.append("PORTFOLIO INFORMATION")

        prompt.append("=" * 60)

        prompt.append(
            f"Number of Stocks : {meta['stocks']}"
        )

        prompt.append(
            "Symbols : "
            + ", ".join(portfolio["symbols"])
        )

        prompt.append("")

        prompt.append("=" * 60)

        prompt.append("PORTFOLIO COMPARISON")

        prompt.append("=" * 60)

        hp = comparison["highest_probability"]

        hg = comparison["highest_gain"]

        lv = comparison["lowest_volatility"]

        prompt.append(
            f"Highest Probability Up : "
            f"{hp['symbol']} "
            f"({hp['value']:.2f}%)"
        )

        prompt.append(
            f"Highest Average Gain : "
            f"{hg['symbol']} "
            f"({hg['value']:.2f}%)"
        )

        prompt.append(
            f"Lowest Volatility : "
            f"{lv['symbol']} "
            f"({lv['value']:.2f})"
        )

        prompt.append("")

        prompt.append("=" * 60)

        prompt.append("CORRELATION")

        prompt.append("=" * 60)

        hc = correlation["highest"]

        lc = correlation["lowest"]

        prompt.append(
            f"Highest Correlation : "
            f"{hc['stock1']} <-> {hc['stock2']} "
            f"({hc['value']:.3f})"
        )

        prompt.append(
            f"Lowest Correlation : "
            f"{lc['stock1']} <-> {lc['stock2']} "
            f"({lc['value']:.3f})"
        )

        prompt.append("")

        prompt.append("=" * 60)

        prompt.append("INDIVIDUAL STOCK STATISTICS")

        prompt.append("=" * 60)

        for stock in stocks:

            stats = stock["statistics"]

            prompt.append("")

            prompt.append(f"Stock : {stock['symbol']}")

            prompt.append(
                f"Trading Days : "
                f"{stats['TradingDays']}"
            )

            prompt.append(
                f"Probability Up : "
                f"{stats['ProbabilityUp'] * 100:.2f}%"
            )

            prompt.append(
                f"Probability Down : "
                f"{stats['ProbabilityDown'] * 100:.2f}%"
            )

            prompt.append(
                f"Average Gain : "
                f"{stats['AverageGain']:.2f}%"
            )

            prompt.append(
                f"Average Loss : "
                f"{stats['AverageLoss']:.2f}%"
            )

            prompt.append(
                f"Maximum Gain : "
                f"{stats['MaxGain']:.2f}%"
            )

            prompt.append(
                f"Maximum Loss : "
                f"{stats['MaxLoss']:.2f}%"
            )

            prompt.append(
                f"Volatility : "
                f"{stats['Volatility']:.2f}"
            )

            prompt.append(
                f"Longest Green Streak : "
                f"{stats['LongestGreenStreak']}"
            )

            prompt.append(
                f"Longest Red Streak : "
                f"{stats['LongestRedStreak']}"
            )

        prompt.append("")

        prompt.append("=" * 60)

        prompt.append("TASK")

        prompt.append("=" * 60)

        prompt.append(
            "Prepare a professional investment report."
        )

        prompt.append("")

        prompt.append(
            "Include the following sections:"
        )

        prompt.append(
            "1. Executive Summary"
        )

        prompt.append(
            "2. Portfolio Strengths"
        )

        prompt.append(
            "3. Portfolio Weaknesses"
        )

        prompt.append(
            "4. Risk Analysis"
        )

        prompt.append(
            "5. Diversification Analysis"
        )

        prompt.append(
            "6. Individual Stock Observations"
        )

        prompt.append(
            "7. Overall Recommendation"
        )

        prompt.append(
            "8. Important Disclaimer"
        )

        prompt.append("")

        prompt.append(
            "Use a professional tone."
        )

        prompt.append(
            "Do not guarantee profits."
        )

        prompt.append(
            "Mention that historical performance "
            "does not guarantee future returns."
        )

        return "\n".join(prompt)

    # -----------------------------------------------------

    def save(self, filename):

        prompt = self.build()

        with open(

            filename,

            "w",

            encoding="utf-8"

        ) as fp:

            fp.write(prompt)

        return filename
