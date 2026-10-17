"""
insights.py

AI-ready Insight Engine

Version : 2.6.0

Converts statistical results into
human-readable investment insights.
"""

from __future__ import annotations


class InsightEngine:

    def __init__(self, summary: dict):

        self.summary = summary

    # ---------------------------------------------------------

    def market_bias(self):

        probability = self.summary["ProbabilityUp"]

        if probability >= 0.70:

            return "Strongly Bullish"

        elif probability >= 0.60:

            return "Bullish"

        elif probability >= 0.55:

            return "Slightly Bullish"

        elif probability >= 0.45:

            return "Neutral"

        elif probability >= 0.40:

            return "Slightly Bearish"

        elif probability >= 0.30:

            return "Bearish"

        return "Strongly Bearish"

    # ---------------------------------------------------------

    def volatility_level(self):

        volatility = self.summary["Volatility"]

        if volatility < 1:

            return "Low"

        elif volatility < 2:

            return "Moderate"

        return "High"

    # ---------------------------------------------------------

    def momentum(self):

        green = self.summary["LongestGreenStreak"]

        red = self.summary["LongestRedStreak"]

        if green > red:

            return "Positive"

        elif red > green:

            return "Negative"

        return "Neutral"

    # ---------------------------------------------------------

    def upside_strength(self):

        gain = self.summary["AverageGain"]

        loss = abs(self.summary["AverageLoss"])

        if gain > loss:

            return "Upside moves are stronger than downside moves."

        elif gain < loss:

            return "Downside moves dominate the upside."

        return "Upside and downside movements are balanced."

    # ---------------------------------------------------------

    def recommendation(self):

        score = 0

        if self.summary["ProbabilityUp"] > 0.55:
            score += 2

        if self.summary["AverageGain"] > abs(self.summary["AverageLoss"]):
            score += 2

        if self.summary["LongestGreenStreak"] > \
           self.summary["LongestRedStreak"]:
            score += 1

        if self.summary["Volatility"] < 1.5:
            score += 1

        if score >= 5:
            return "STRONG BUY"

        elif score >= 3:
            return "BUY"

        elif score >= 1:
            return "HOLD"

        return "SELL"

    # ---------------------------------------------------------

    def executive_summary(self):

        lines = []

        lines.append(
            f"The stock exhibited "
            f"{self.market_bias().lower()} behaviour "
            f"during the selected analysis period."
        )

        lines.append(
            f"The probability of closing above the opening price "
            f"was {self.summary['ProbabilityUp']*100:.2f}%."
        )

        lines.append(
            self.upside_strength()
        )

        lines.append(
            f"Observed volatility remained "
            f"{self.volatility_level().lower()}."
        )

        lines.append(
            f"Market momentum appears "
            f"{self.momentum().lower()}."
        )

        lines.append(
            f"Overall Recommendation : "
            f"{self.recommendation()}."
        )

        return "\n".join(lines)

    # ---------------------------------------------------------

    def print(self):

        print()

        print("=" * 72)

        print("Executive Insight")

        print("=" * 72)

        print(self.executive_summary())

        print("=" * 72)
