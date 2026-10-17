"""
strategy_simulator.py

Stage 11 — Strategy Simulator.

Replays a sequence of predictions against actual outcomes and computes:
    Profit / Loss curve
    Win rate
    Sharpe Ratio
    Sortino Ratio
    Information Ratio (vs buy-and-hold)
    Max Drawdown
    Total return %

Version : 5.11.0
"""

from __future__ import annotations

import math
import numpy as np


class StrategySimulator:
    """
    Simulates a long-only strategy based on BUY/SELL/HOLD signals.

    Parameters
    ----------
    initial_capital : float   starting capital in ₹ (default 100_000)
    transaction_cost: float   % cost per trade, both ways (default 0.05%)
    """

    def __init__(
        self,
        initial_capital  : float = 100_000.0,
        transaction_cost : float = 0.05,
    ):
        self.initial_capital  = initial_capital
        self.transaction_cost = transaction_cost / 100.0
        self._trades  : list[dict] = []
        self._equity  : list[float] = [initial_capital]
        self._in_position : bool = False

    # ------------------------------------------------------------------

    def add_bar(
        self,
        signal     : str,
        price_open : float,
        price_close: float,
        timestamp  : str = "",
    ):
        """
        Process one bar.

        Parameters
        ----------
        signal      : "BUY" | "SELL" | "HOLD"
        price_open  : float   open price of this bar
        price_close : float   close price of this bar
        """
        equity = self._equity[-1]
        bar_return = (price_close / price_open - 1.0) if price_open != 0 else 0.0

        # Entry
        if signal == "BUY" and not self._in_position:
            cost = equity * self.transaction_cost
            equity -= cost
            self._in_position = True

        # Mark-to-market while in position
        if self._in_position:
            equity *= (1.0 + bar_return)

        # Exit
        if signal == "SELL" and self._in_position:
            cost = equity * self.transaction_cost
            equity -= cost
            self._in_position = False

        self._equity.append(equity)
        self._trades.append({
            "timestamp"  : timestamp,
            "signal"     : signal,
            "price_open" : price_open,
            "price_close": price_close,
            "bar_return" : round(bar_return * 100, 4),
            "equity"     : round(equity, 2),
        })

    # ------------------------------------------------------------------

    def results(self) -> dict:
        """Compute full performance statistics."""
        if len(self._equity) < 2:
            return {}

        eq = np.array(self._equity, dtype=float)
        returns = np.diff(eq) / np.where(eq[:-1] != 0, eq[:-1], 1.0)

        total_return = (eq[-1] / eq[0] - 1.0) * 100.0

        # Win rate
        trades_with_return = [t for t in self._trades]
        wins = sum(1 for t in trades_with_return if t["bar_return"] > 0)
        win_rate = wins / len(trades_with_return) if trades_with_return else 0.0

        # Sharpe (annualised, assumes 252 * 78 bars/day for 5m)
        if returns.std() > 0:
            sharpe = float((returns.mean() / returns.std()) * math.sqrt(252 * 78))
        else:
            sharpe = 0.0

        # Sortino
        neg_returns = returns[returns < 0]
        if len(neg_returns) > 0 and neg_returns.std() > 0:
            sortino = float(
                (returns.mean() / neg_returns.std()) * math.sqrt(252 * 78)
            )
        else:
            sortino = 0.0

        # Max drawdown
        peak = eq[0]
        max_dd = 0.0
        for v in eq:
            if v > peak:
                peak = v
            dd = (peak - v) / peak if peak != 0 else 0.0
            if dd > max_dd:
                max_dd = dd

        return {
            "initial_capital" : round(self.initial_capital,      2),
            "final_equity"    : round(float(eq[-1]),              2),
            "total_return_pct": round(total_return,               2),
            "win_rate"        : round(win_rate * 100,             2),
            "sharpe_ratio"    : round(sharpe,                     4),
            "sortino_ratio"   : round(sortino,                    4),
            "max_drawdown_pct": round(max_dd * 100,               2),
            "n_bars"          : len(self._trades),
            "in_position"     : self._in_position,
        }

    # ------------------------------------------------------------------

    def equity_curve(self) -> list[float]:
        return list(self._equity)

    def trades(self) -> list[dict]:
        return list(self._trades)

    def reset(self):
        self._trades     = []
        self._equity     = [self.initial_capital]
        self._in_position = False
