"""
portfolio_quantum.py

Creates 5-qubit quantum states for an entire stock portfolio.

Version : 2.6.0
"""

from __future__ import annotations

from quantum.quantum_encoder import QuantumEncoder


class QuantumPortfolio:

    # ---------------------------------------------------------

    def __init__(self, portfolio):

        """
        portfolio : PortfolioAnalyzer
        """

        self.portfolio = portfolio

        self.states = {}

    # ---------------------------------------------------------

    def build(self):

        self.states.clear()

        for symbol, analyzer in self.portfolio.analyzers.items():

            summary = analyzer.get_summary()

            state = QuantumEncoder(summary).encode()

            self.states[symbol] = state

        return self.states

    # ---------------------------------------------------------

    def get_state(self, symbol):

        return self.states[symbol]

    # ---------------------------------------------------------

    def symbols(self):

        return list(self.states.keys())

    # ---------------------------------------------------------

    def print(self):

        print()
        print("=" * 72)
        print("Quantum Portfolio  (Multi-Qubit v2.6  —  5 qubits per stock)")
        print("=" * 72)

        for symbol in self.symbols():

            state = self.states[symbol]

            print()
            print(symbol)
            print("-" * len(symbol))
            print(state)

        print()
        print("=" * 72)
