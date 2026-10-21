#!/usr/bin/env python3
"""
Quantum Stock Probability Analyzer

Version : 11.0.1
"""

from __future__ import annotations

import argparse
import sys

from analyzer import StockAnalyzer
from data_loader import DataLoaderError, load_stock_data
from logger import get_logger
from portfolio import PortfolioAnalyzer
from report import ReportGenerator
from visualization import StockVisualizer
from config import DEFAULT_ANALYSIS_DAYS

# NEW IMPORTS
from portfolio_summary import PortfolioSummary
from portfolio_export import PortfolioExporter
from markdown_report import MarkdownReport
from insights import InsightEngine
from comparison import ComparisonEngine
from correlation import CorrelationEngine
from ai_report import AIReport

from quantum.portfolio_quantum import QuantumPortfolio
from quantum.fidelity_matrix import FidelityMatrix
from quantum.fidelity_heatmap import FidelityHeatmap
from quantum.entanglement_matrix import EntanglementMatrix
from quantum.entanglement_report import EntanglementReport
from quantum.qft_portfolio import QFTPortfolio
from quantum.qft_report import QFTReport
from quantum.qpe_portfolio import QPEPortfolio
from quantum.qpe_report import QPEReport
from quantum.portfolio_optimizer import PortfolioOptimizer
from quantum.optimizer_report import OptimizerReport

logger = get_logger()


# -------------------------------------------------------------

def parse_arguments():

    parser = argparse.ArgumentParser(
        description="Quantum Stock Probability Analyzer"
    )

    parser.add_argument(

        "symbols",

        nargs="+",

        help="One or more NSE symbols"

    )

    parser.add_argument(

        "--days",

        "-d",

        default=DEFAULT_ANALYSIS_DAYS,

        type=int,

        help="Number of historical days (1–730)"

    )

    return parser.parse_args()


# -------------------------------------------------------------

def print_banner():

    print()

    print("=" * 72)

    from config import APP_VERSION
    print(f"      QAMO — Quantum Adaptive Market Observer v{APP_VERSION}")

    print("=" * 72)


# -------------------------------------------------------------

def run_single_stock(symbol, days):

    print(f"\nAnalyzing {symbol}\n")

    df = load_stock_data(symbol, days)

    analyzer = StockAnalyzer(df, symbol)

    analyzer.run_analysis()

    report = ReportGenerator(analyzer)

    report.print_summary()

    summary = analyzer.get_summary()

    insight = InsightEngine(summary)

    insight.print()

    report.export_csv()

    report.export_json()

    visualizer = StockVisualizer(analyzer)

    visualizer.generate_all()


# -------------------------------------------------------------

def run_portfolio(symbols, days):

    #
    # Analyze Portfolio
    #

    portfolio = PortfolioAnalyzer(

        symbols,

        days

    )

    portfolio.analyze()

    #
    # Comparison
    #

    comparison = ComparisonEngine(

        portfolio

    )

    comparison.print_table()

    #
    # Correlation
    #

    correlation = CorrelationEngine(

        portfolio

    )

    correlation.print()

    correlation.export_csv()

    correlation.export_heatmap()

    #
    # Portfolio Statistics
    #

    print()

    print("=" * 72)

    print("Portfolio Statistics")

    print("=" * 72)

    best = comparison.best_probability()

    print(

        f"Highest Probability : "

        f"{best['Symbol']} "

        f"({best['ProbabilityUp']:.2f}%)"

    )

    gain = comparison.highest_gain()

    print(

        f"Highest Average Gain : "

        f"{gain['Symbol']} "

        f"({gain['AverageGain']:.2f}%)"

    )

    risk = comparison.lowest_risk()

    print(

        f"Lowest Volatility : "

        f"{risk['Symbol']} "

        f"({risk['Volatility']:.2f})"

    )

    s1, s2, value = correlation.highest_pair()

    print(

        f"Highest Correlation : "

        f"{s1} <-> {s2} "

        f"({value:.3f})"

    )

    s1, s2, value = correlation.lowest_pair()

    print(

        f"Lowest Correlation : "

        f"{s1} <-> {s2} "

        f"({value:.3f})"

    )

    #
    # Executive Portfolio Summary
    #

    summary = PortfolioSummary(

        portfolio,

        comparison,

        correlation

    )

    summary.print()

    #
    # Export Complete Portfolio JSON
    #

    exporter = PortfolioExporter(

        portfolio,

        comparison,

        correlation

    )

    exporter.export_json()

    #
    # Markdown Report
    #

    # Markdown report is built after all quantum sections —
    # updated call is deferred to after the VQC optimizer below.

    #
    # ==========================================================
    # Quantum Portfolio Analysis
    # ==========================================================
    #

    print()
    print("=" * 72)
    print("Quantum Portfolio Analysis")
    print("=" * 72)

    quantum_portfolio = QuantumPortfolio(portfolio)

    quantum_portfolio.build()

    quantum_portfolio.print()

    #
    # Fidelity Matrix
    #

    fidelity = FidelityMatrix(quantum_portfolio)

    fidelity.calculate()

    fidelity.print()

    fidelity.export_csv()

    #
    # Heatmap
    #

    heatmap = FidelityHeatmap(fidelity)

    heatmap.save()

    #
    # Summary
    #

    s1, s2, value = fidelity.highest_pair()

    print()
    print(
        f"Highest Quantum Fidelity : "
        f"{s1} <-> {s2} "
        f"({value:.6f})"
    )

    s1, s2, value = fidelity.lowest_pair()

    print(
        f"Lowest Quantum Fidelity : "
        f"{s1} <-> {s2} "
        f"({value:.6f})"
    )

    print("=" * 72)

    #
    # ==========================================================
    # Portfolio Entanglement Analysis
    # ==========================================================
    #

    print()
    print("=" * 72)
    print("Portfolio Entanglement Analysis")
    print("=" * 72)

    entanglement = EntanglementMatrix(
        quantum_portfolio,
        correlation.correlation
    )

    entanglement.calculate()

    ent_report = EntanglementReport(entanglement)

    ent_report.print()

    ent_report.export_csv()

    ent_report.export_json()

    #
    # ==========================================================
    # QFT Periodicity Analysis
    # ==========================================================
    #

    print()
    print("=" * 72)
    print("QFT Periodicity Analysis")
    print("=" * 72)

    qft_portfolio = QFTPortfolio(portfolio)

    qft_portfolio.run()

    qft_report = QFTReport(qft_portfolio)

    qft_report.print()

    qft_report.export_csv()

    qft_report.export_json()

    #
    # ==========================================================
    # QPE — Quantum Phase Estimation
    # ==========================================================
    #

    print()
    print("=" * 72)
    print("Quantum Phase Estimation (QPE)")
    print("=" * 72)

    qpe_portfolio = QPEPortfolio(portfolio, quantum_portfolio)

    qpe_portfolio.run()

    qpe_report = QPEReport(qpe_portfolio)

    qpe_report.print()

    qpe_report.export_csv()

    qpe_report.export_json()

    #
    # ==========================================================
    # VQC Portfolio Optimizer  (v3.0)
    # ==========================================================
    #

    print()
    print("=" * 72)
    print("Quantum Portfolio Optimizer (VQC v3.0)")
    print("=" * 72)

    port_optimizer = PortfolioOptimizer(portfolio, quantum_portfolio)

    port_optimizer.run()

    opt_report = OptimizerReport(port_optimizer.get_optimizer())

    opt_report.print()

    opt_report.export_csv()

    opt_report.export_json()

    #
    # ==========================================================
    # Full Markdown Report  (all sections)
    # ==========================================================
    #

    print()
    print("=" * 72)
    print("Generating Full Markdown Report")
    print("=" * 72)

    markdown = MarkdownReport(
        portfolio,
        comparison,
        correlation,
        quantum_portfolio   = quantum_portfolio,
        fidelity_matrix     = fidelity,
        entanglement_matrix = entanglement,
        qft_portfolio       = qft_portfolio,
        qpe_portfolio       = qpe_portfolio,
        optimizer           = port_optimizer.get_optimizer(),
    )

    markdown.export()

    #
    # AI Investment Report (Optional)
    #

    print()

    print("=" * 72)

    print("IBM watsonx AI Report")

    print("=" * 72)

    ai = AIReport()

    ai.generate()



# -------------------------------------------------------------

def main():

    args = parse_arguments()

    print_banner()

    logger.info("Application Started")

    logger.info(

        "Symbols=%s Days=%d",

        args.symbols,

        args.days

    )

    try:

        #
        # One Stock
        #

        if len(args.symbols) == 1:

            run_single_stock(

                args.symbols[0],

                args.days

            )

        #
        # Portfolio
        #

        else:

            run_portfolio(

                args.symbols,

                args.days

            )

        print()

        print("Analysis completed successfully.")

        print()

    except DataLoaderError as ex:

        logger.error(str(ex))

        print()

        print("ERROR:", ex)

        print()

        sys.exit(1)

    except KeyboardInterrupt:

        logger.warning(

            "Interrupted by user"

        )

        print("\nInterrupted.")

        sys.exit(1)

    except Exception as ex:

        logger.exception(ex)

        print()

        print("Unexpected Error")

        print(ex)

        print()

        sys.exit(1)


# -------------------------------------------------------------

if __name__ == "__main__":

    main()