"""
markdown_report.py

Generates a comprehensive Markdown report for the entire portfolio,
including classical analysis, all quantum results, and embedded images.

Version : 3.1.0
"""

from __future__ import annotations

import os
from datetime import datetime

from config import OUTPUT_REPORT_DIR
from insights import InsightEngine


class MarkdownReport:

    def __init__(
        self,
        portfolio,
        comparison,
        correlation,
        quantum_portfolio=None,
        fidelity_matrix=None,
        entanglement_matrix=None,
        qft_portfolio=None,
        qpe_portfolio=None,
        optimizer=None,
    ):
        self.portfolio           = portfolio
        self.comparison          = comparison
        self.correlation         = correlation
        self.quantum_portfolio   = quantum_portfolio
        self.fidelity_matrix     = fidelity_matrix
        self.entanglement_matrix = entanglement_matrix
        self.qft_portfolio       = qft_portfolio
        self.qpe_portfolio       = qpe_portfolio
        self.optimizer           = optimizer

    # ----------------------------------------------------------

    def build(self):

        lines = []

        self._title(lines)
        self._portfolio_summary(lines)
        self._comparison_table(lines)
        self._correlation_section(lines)
        self._individual_stocks(lines)

        if self.quantum_portfolio:
            self._quantum_encoding(lines)

        if self.fidelity_matrix is not None:
            self._fidelity_section(lines)

        if self.entanglement_matrix is not None:
            self._entanglement_section(lines)

        if self.qft_portfolio is not None:
            self._qft_section(lines)

        if self.qpe_portfolio is not None:
            self._qpe_section(lines)

        if self.optimizer is not None:
            self._optimizer_section(lines)

        self._footer(lines)

        return "\n".join(lines)

    # ----------------------------------------------------------
    # Helpers
    # ----------------------------------------------------------

    def _h(self, lines, level, text):
        lines.append(f"{'#' * level} {text}")
        lines.append("")

    def _rule(self, lines):
        lines.append("---")
        lines.append("")

    def _table_row(self, cells):
        return "| " + " | ".join(str(c) for c in cells) + " |"

    def _table_header(self, lines, headers):
        lines.append(self._table_row(headers))
        lines.append(self._table_row(["---"] * len(headers)))

    # ----------------------------------------------------------
    # Sections
    # ----------------------------------------------------------

    def _title(self, lines):
        lines.append("# Quantum Stock Probability Analyzer")
        lines.append("")
        lines.append("## Portfolio Analysis Report")
        lines.append("")
        lines.append(
            f"**Generated :** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        lines.append("")
        lines.append(
            f"**Stocks :** "
            + ", ".join(f"`{s}`" for s in self.portfolio.get_symbols())
        )
        lines.append("")
        self._rule(lines)

    # ----------------------------------------------------------

    def _portfolio_summary(self, lines):

        self._h(lines, 2, "Portfolio Summary")

        best = self.comparison.best_probability()
        risk = self.comparison.lowest_risk()
        gain = self.comparison.highest_gain()
        s1h, s2h, ch = self.correlation.highest_pair()
        s1l, s2l, cl = self.correlation.lowest_pair()

        lines.append(
            f"| Metric | Stock | Value |"
        )
        lines.append("|--------|-------|-------|")
        lines.append(
            f"| Highest Probability | **{best['Symbol']}** | {best['ProbabilityUp']:.2f}% |"
        )
        lines.append(
            f"| Lowest Volatility | **{risk['Symbol']}** | {risk['Volatility']:.4f} |"
        )
        lines.append(
            f"| Highest Avg Gain | **{gain['Symbol']}** | {gain['AverageGain']:.2f}% |"
        )
        lines.append(
            f"| Highest Correlation | **{s1h} ↔ {s2h}** | {ch:.3f} |"
        )
        lines.append(
            f"| Lowest Correlation | **{s1l} ↔ {s2l}** | {cl:.3f} |"
        )
        lines.append("")
        self._rule(lines)

    # ----------------------------------------------------------

    def _comparison_table(self, lines):

        self._h(lines, 2, "Portfolio Comparison")

        headers = [
            "Symbol", "P(Close>Open)%", "P(Open>Close)%",
            "Avg Gain%", "Avg Loss%", "Volatility",
            "Green Days", "Red Days"
        ]
        self._table_header(lines, headers)

        for symbol in self.portfolio.get_symbols():
            s = self.portfolio.get_analyzer(symbol).get_summary()
            lines.append(self._table_row([
                f"**{symbol}**",
                f"{s['ProbabilityUp']*100:.2f}",
                f"{s['ProbabilityDown']*100:.2f}",
                f"{s['AverageGain']:.2f}",
                f"{s['AverageLoss']:.2f}",
                f"{s['Volatility']:.4f}",
                s['GreenDays'],
                s['RedDays'],
            ]))

        lines.append("")
        self._rule(lines)

    # ----------------------------------------------------------

    def _correlation_section(self, lines):

        self._h(lines, 2, "Classical Correlation Matrix")

        corr = self.correlation.correlation
        symbols = list(corr.index)

        # Header row
        lines.append("| | " + " | ".join(f"**{s}**" for s in symbols) + " |")
        lines.append("|---|" + "|".join(["---"] * len(symbols)) + "|")

        for s1 in symbols:
            row = [f"**{s1}**"] + [
                f"{corr.loc[s1, s2]:.3f}" for s2 in symbols
            ]
            lines.append(self._table_row(row))

        lines.append("")
        lines.append(
            "![Correlation Heatmap](../charts/portfolio_correlation.png)"
        )
        lines.append("")
        self._rule(lines)

    # ----------------------------------------------------------

    def _individual_stocks(self, lines):

        self._h(lines, 2, "Individual Stock Analysis")

        for symbol in self.portfolio.get_symbols():

            analyzer = self.portfolio.get_analyzer(symbol)
            summary  = analyzer.get_summary()
            insight  = InsightEngine(summary)

            self._h(lines, 3, symbol)

            # Stats table
            lines.append("| Metric | Value |")
            lines.append("|--------|-------|")
            lines.append(f"| Trading Days | {summary['TradingDays']} |")
            lines.append(f"| Green Days | {summary['GreenDays']} |")
            lines.append(f"| Red Days | {summary['RedDays']} |")
            lines.append(
                f"| P(Close > Open) | {summary['ProbabilityUp']*100:.2f}% |"
            )
            lines.append(
                f"| P(Open > Close) | {summary['ProbabilityDown']*100:.2f}% |"
            )
            lines.append(f"| Average Gain | {summary['AverageGain']:.2f}% |")
            lines.append(f"| Average Loss | {summary['AverageLoss']:.2f}% |")
            lines.append(f"| Max Gain | {summary['MaxGain']:.2f}% |")
            lines.append(f"| Max Loss | {summary['MaxLoss']:.2f}% |")
            lines.append(f"| Volatility | {summary['Volatility']:.4f} |")
            lines.append(
                f"| Longest Green Streak | {summary['LongestGreenStreak']} days |"
            )
            lines.append(
                f"| Longest Red Streak | {summary['LongestRedStreak']} days |"
            )
            lines.append(
                f"| Trend Slope | {summary.get('TrendSlope', 0):.4f}% /day |"
            )
            lines.append(
                f"| Avg Volume | {summary.get('AverageVolume', 0):.2f}M |"
            )
            lines.append("")

            # Charts
            lines.append(
                f"![{symbol} Price](../charts/{symbol}_price.png)"
            )
            lines.append(
                f"![{symbol} Returns](../charts/{symbol}_returns.png)"
            )
            lines.append(
                f"![{symbol} Volume](../charts/{symbol}_volume.png)"
            )
            lines.append("")

            # Insight
            lines.append("**Insight**")
            lines.append("")
            for line in insight.executive_summary().split("\n"):
                lines.append(f"> {line}")
            lines.append("")

        self._rule(lines)

    # ----------------------------------------------------------

    def _quantum_encoding(self, lines):

        self._h(lines, 2, "Quantum Encoding  (Multi-Qubit v3.0)")

        lines.append(
            "Each stock is encoded into a **5-qubit product state** "
            "|ψ⟩ = |q0⟩ ⊗ |q1⟩ ⊗ |q2⟩ ⊗ |q3⟩ ⊗ |q4⟩ "
            "where each qubit represents one market feature via Ry rotation."
        )
        lines.append("")

        lines.append(
            "| Qubit | Feature | Formula |"
        )
        lines.append("|-------|---------|---------|")
        lines.append("| q0 | Probability Up | Ry(2·arcsin(√P_up)) |")
        lines.append("| q1 | Volatility | Ry(π · vol / MAX_VOL) |")
        lines.append("| q2 | Momentum | Ry(π/2 · (1 + momentum)) |")
        lines.append("| q3 | Trend | Ry(π/2 · (1 + trend)) |")
        lines.append("| q4 | Volume | Ry(π · vol / MAX_VOLUME) |")
        lines.append("")

        # Per-stock qubit table
        symbols = self.quantum_portfolio.symbols()
        headers = ["Symbol"] + [f"q{i} Ry (rad)" for i in range(5)] + \
                  [f"q{i} P(|1>)" for i in range(5)]
        self._table_header(lines, headers)

        for sym in symbols:
            state = self.quantum_portfolio.get_state(sym)
            row = [f"**{sym}**"]
            row += [f"{a:.4f}" for a in state.angles]
            row += [f"{state.qubit_prob_one(i):.4f}" for i in range(5)]
            lines.append(self._table_row(row))

        lines.append("")
        self._rule(lines)

    # ----------------------------------------------------------

    def _fidelity_section(self, lines):

        self._h(lines, 2, "Quantum Fidelity Matrix")

        lines.append(
            "Fidelity F(ψᵢ, ψⱼ) = |⟨ψᵢ|ψⱼ⟩|² measures quantum state "
            "similarity between stocks. Range: 0 (orthogonal) → 1 (identical)."
        )
        lines.append("")
        lines.append(
            "| Interpretation | Range |"
        )
        lines.append("|----------------|-------|")
        lines.append("| Nearly identical | > 0.99 |")
        lines.append("| Very similar | 0.95 – 0.99 |")
        lines.append("| Moderately similar | 0.80 – 0.95 |")
        lines.append("| Different | < 0.80 |")
        lines.append("")

        mat = self.fidelity_matrix.matrix
        symbols = list(mat.index)

        lines.append("| | " + " | ".join(f"**{s}**" for s in symbols) + " |")
        lines.append("|---|" + "|".join(["---"] * len(symbols)) + "|")

        for s1 in symbols:
            row = [f"**{s1}**"] + [
                f"{mat.loc[s1, s2]:.6f}" for s2 in symbols
            ]
            lines.append(self._table_row(row))

        lines.append("")
        lines.append(
            "![Quantum Fidelity Heatmap](../charts/portfolio_fidelity_heatmap.png)"
        )
        lines.append("")
        self._rule(lines)

    # ----------------------------------------------------------

    def _entanglement_section(self, lines):

        self._h(lines, 2, "Portfolio Entanglement  (CNOT v3.0)")

        lines.append(
            "Two stocks are entangled via CNOT on their q0 (Probability) qubits. "
            "Metrics: **Entropy** (von Neumann, 0=separable, 1=max entangled), "
            "**Concurrence** (0=separable, 1=Bell state), "
            "**Bell State** (closest of Φ+, Φ−, Ψ+, Ψ−)."
        )
        lines.append("")

        self._table_header(
            lines,
            ["Pair", "Entropy", "Concurrence",
             "Bell State", "Classical Corr", "Dominant"]
        )

        for pair in self.entanglement_matrix.pairs:
            dominant = (
                "Quantum > Classical"
                if pair.concurrence > abs(pair.classical_corr)
                else "Classical ≥ Quantum"
            )
            lines.append(self._table_row([
                f"**{pair.symbol_a} ↔ {pair.symbol_b}**",
                f"{pair.entropy:.6f}",
                f"{pair.concurrence:.6f}",
                pair.bell_state,
                f"{pair.classical_corr:+.4f}",
                dominant,
            ]))

        lines.append("")
        self._rule(lines)

    # ----------------------------------------------------------

    def _qft_section(self, lines):

        self._h(lines, 2, "QFT Periodicity Analysis  (v3.0)")

        lines.append(
            "Daily returns are amplitude-encoded and transformed via QFT "
            "(8 qubits, 256 points). The dominant frequency bins are translated "
            "to trading-day periods."
        )
        lines.append("")

        self._table_header(
            lines,
            ["Symbol", "Dominant Period (days)",
             "Rank 2 Period", "Rank 3 Period"]
        )

        for sym in self.qft_portfolio.symbols():
            qft = self.qft_portfolio.get(sym)
            peaks = qft.top_peaks
            p1 = peaks[0]["Period"] if len(peaks) > 0 else "—"
            p2 = peaks[1]["Period"] if len(peaks) > 1 else "—"
            p3 = peaks[2]["Period"] if len(peaks) > 2 else "—"
            lines.append(self._table_row([
                f"**{sym}**", p1, p2, p3
            ]))

        lines.append("")

        sym_s, per_s = self.qft_portfolio.shortest_cycle()
        sym_l, per_l = self.qft_portfolio.longest_cycle()
        lines.append(
            f"> **Shortest Cycle :** {sym_s} — {per_s:.1f} trading days  "
        )
        lines.append(
            f"> **Longest Cycle :** {sym_l} — {per_l:.1f} trading days"
        )
        lines.append("")
        self._rule(lines)

    # ----------------------------------------------------------

    def _qpe_section(self, lines):

        self._h(lines, 2, "Quantum Phase Estimation  (QPE v3.0)")

        lines.append(
            "QPE estimates the eigenphase φ of U = Ry(θ_q0) for each stock "
            "using 6 counting qubits (64 phase bins, resolution ≈ 1.56%). "
            "The recovered phase is converted back to P(up) and compared "
            "against the classical value."
        )
        lines.append("")

        self._table_header(
            lines,
            ["Symbol", "Classical P(up)", "QPE P(up)",
             "Absolute Error", "Confidence"]
        )

        for sym in self.qpe_portfolio.symbols():
            qpe = self.qpe_portfolio.get(sym)
            lines.append(self._table_row([
                f"**{sym}**",
                f"{qpe.p_up_classical:.4f}",
                f"{qpe.p_up_estimate:.4f}",
                f"{qpe.p_up_error():.4f}",
                f"{qpe.confidence:.4f}",
            ]))

        lines.append("")
        sym_acc, _ = self.qpe_portfolio.most_accurate()
        sym_conf, conf = self.qpe_portfolio.highest_confidence()
        lines.append(
            f"> **Most Accurate :** {sym_acc}  |  "
            f"**Highest Confidence :** {sym_conf} ({conf:.4f})"
        )
        lines.append("")
        self._rule(lines)

    # ----------------------------------------------------------

    def _optimizer_section(self, lines):

        self._h(lines, 2, "VQC Portfolio Optimizer  (v3.0)")

        lines.append(
            "Ansatz: **Ry(encode) → CNOT ring → Ry(variational)**  "
            f"— Optimiser: COBYLA — Iterations: {self.optimizer.n_iterations} "
            f"— Converged: {'Yes' if self.optimizer.converged else 'No'}"
        )
        lines.append("")

        self._table_header(
            lines,
            ["Symbol", "Weight", "Weight %",
             "Return Contrib%", "Recommendation"]
        )

        for row in self.optimizer.allocation():
            lines.append(self._table_row([
                f"**{row['Symbol']}**",
                f"{row['Weight']:.4f}",
                f"{row['WeightPct']:.2f}%",
                f"{row['ReturnContrib']:.4f}",
                f"**{row['Recommendation']}**",
            ]))

        lines.append("")
        lines.append("**Portfolio Metrics**")
        lines.append("")
        lines.append("| Metric | VQC | Equal-Weight |")
        lines.append("|--------|-----|--------------|")

        import math, numpy as np
        n      = self.optimizer.n
        eq_w   = np.ones(n) / n
        eq_ret = float(np.dot(eq_w, self.optimizer.mu))
        eq_var = float(eq_w @ self.optimizer.cov @ eq_w)
        eq_risk = math.sqrt(max(eq_var, 0.0)) + 1e-8
        eq_sh  = eq_ret / eq_risk
        improvement = (
            (self.optimizer.optimal_sharpe - eq_sh) / abs(eq_sh)
        ) * 100 if eq_sh != 0 else 0

        lines.append(
            f"| Expected Daily Return | {self.optimizer.optimal_return:+.4f}% "
            f"| {eq_ret:+.4f}% |"
        )
        lines.append(
            f"| Portfolio Risk (σ) | {self.optimizer.optimal_risk:.4f} "
            f"| {eq_risk:.4f} |"
        )
        lines.append(
            f"| Sharpe Ratio | **{self.optimizer.optimal_sharpe:.4f}** "
            f"| {eq_sh:.4f} |"
        )
        lines.append("")
        arrow = "↑" if improvement >= 0 else "↓"
        lines.append(
            f"> Sharpe improvement vs equal-weight : "
            f"**{arrow} {abs(improvement):.1f}%**"
        )
        lines.append("")
        self._rule(lines)

    # ----------------------------------------------------------

    def _footer(self, lines):

        self._h(lines, 2, "Disclaimer")

        lines.append(
            "This report is generated by the **Quantum Stock Probability Analyzer v3.0.0** "
            "for educational and research purposes only. "
            "It does not constitute financial advice or guarantee future stock performance. "
            "All analysis is based on historical NSE price data and quantum simulation."
        )
        lines.append("")

    # ----------------------------------------------------------

    def export(self):

        os.makedirs(OUTPUT_REPORT_DIR, exist_ok=True)

        filename = os.path.join(
            OUTPUT_REPORT_DIR,
            "Portfolio_Report.md"
        )

        with open(filename, "w", encoding="utf-8") as fp:
            fp.write(self.build())

        print()
        print(f"Markdown report saved : {filename}")

        return filename
