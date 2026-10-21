"""
qft_report.py

Prints and exports QFT periodicity results for a portfolio.

Version : 2.8.0
"""

from __future__ import annotations

import json
import csv
from pathlib import Path

from quantum.qft_portfolio import QFTPortfolio


class QFTReport:
    """
    Prints and exports QFT results.

    Parameters
    ----------
    qft_portfolio : QFTPortfolio  (already run() called)
    """

    # ---------------------------------------------------------

    def __init__(self, qft_portfolio: QFTPortfolio):

        self.qft_portfolio = qft_portfolio

    # ---------------------------------------------------------

    def print(self):

        print()
        print("=" * 72)
        print("Quantum Fourier Transform — Periodicity Analysis  (v2.8)")
        print("=" * 72)
        print("  Pipeline : Returns → Amplitude Encoding → QFT → Frequency Peaks")
        print("=" * 72)

        for symbol in self.qft_portfolio.symbols():

            qft = self.qft_portfolio.get(symbol)

            print()
            print(symbol)
            print("-" * len(symbol))
            print(qft)

        print()
        print("=" * 72)
        print("Dominant Cycle Summary")
        print("=" * 72)

        for symbol, period in self.qft_portfolio.dominant_periods().items():
            bar = "█" * min(int(period / 5), 30)
            print(f"  {symbol:<12} {period:>8.1f} days  {bar}")

        print()

        sym, period = self.qft_portfolio.shortest_cycle()
        print(f"  Shortest Cycle : {sym} ({period:.1f} trading days)")

        sym, period = self.qft_portfolio.longest_cycle()
        print(f"  Longest  Cycle : {sym} ({period:.1f} trading days)")

        print("=" * 72)

    # ---------------------------------------------------------

    def export_csv(
        self,
        filename: str = "output/reports/portfolio_qft_peaks.csv",
    ):
        rows = []
        for symbol in self.qft_portfolio.symbols():
            qft = self.qft_portfolio.get(symbol)
            for peak in qft.top_peaks:
                rows.append({
                    "Symbol"    : symbol,
                    "Rank"      : peak["Rank"],
                    "Bin"       : peak["Bin"],
                    "Frequency" : peak["Frequency"],
                    "Period"    : peak["Period"],
                    "Magnitude" : peak["Magnitude"],
                    "Power"     : peak["Power"],
                })

        if rows:
            with open(filename, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)

        print(f"QFT Peaks CSV saved         : {filename}")

    # ---------------------------------------------------------

    def export_json(
        self,
        filename: str = "output/reports/portfolio_qft.json",
    ):
        data = [
            self.qft_portfolio.get(s).to_dict()
            for s in self.qft_portfolio.symbols()
        ]

        Path(filename).write_text(
            json.dumps(data, indent=2),
            encoding="utf-8"
        )

        print(f"QFT JSON saved              : {filename}")
