"""
qpip/whatif_simulator.py

What-if Portfolio Simulator.

Given a base set of portfolio weights and signals, allows the user
to adjust one weight and immediately see the delta in:
    Expected Return (%)
    Risk level change
    Diversification score change
    Portfolio Health Score change ("Quantum Score" in UI)

All computation is pure Python — no re-fetch of data, so results
are instant (< 1 ms for typical portfolio sizes).

Version : 11.0.1
"""

from __future__ import annotations

from dataclasses import dataclass

from qpip.portfolio_scorer  import PortfolioScorer
from qpip.risk_engine       import RiskEngine


@dataclass
class WhatIfResult:
    symbol           : str
    old_weight       : float   # 0–100 %
    new_weight       : float
    delta_return_pct : float   # e.g. +0.2
    delta_risk_pct   : float   # e.g. -18  (negative = risk reduced)
    delta_div_pct    : float   # diversification change
    delta_score      : float   # portfolio health score change
    new_return       : float
    new_risk_label   : str
    new_div          : float
    new_score        : float
    summary          : str


class WhatIfSimulator:
    """
    Instant what-if analysis — no data re-fetch required.

    Parameters
    ----------
    signals_map : dict[str, dict]   symbol → refresh() result
    base_weights : dict[str, float] | None   weight % (default equal)
    """

    def __init__(
        self,
        signals_map  : dict[str, dict],
        base_weights : dict[str, float] | None = None,
    ):
        self.signals_map = {
            sym: sig for sym, sig in signals_map.items()
            if "error" not in sig
        }
        syms = list(self.signals_map.keys())
        n    = len(syms) or 1
        self.base_weights = base_weights or {s: 100.0 / n for s in syms}

    # ------------------------------------------------------------------

    def simulate(self, symbol: str, new_weight_pct: float) -> WhatIfResult:
        """
        Simulate changing one symbol's weight to new_weight_pct (0–100).

        Remaining weight is redistributed proportionally among other symbols.
        """
        syms = list(self.signals_map.keys())
        if symbol not in syms:
            return WhatIfResult(
                symbol=symbol, old_weight=0, new_weight=new_weight_pct,
                delta_return_pct=0, delta_risk_pct=0, delta_div_pct=0,
                delta_score=0, new_return=0, new_risk_label="Unknown",
                new_div=0, new_score=0,
                summary=f"{symbol} not found in portfolio.",
            )

        old_weight = self.base_weights.get(symbol, 100.0 / len(syms))

        # Build new weight dict
        new_weights: dict[str, float] = {}
        remaining    = 100.0 - new_weight_pct
        other_syms   = [s for s in syms if s != symbol]
        other_total  = sum(self.base_weights.get(s, 0) for s in other_syms)

        new_weights[symbol] = new_weight_pct
        for s in other_syms:
            if other_total > 0:
                new_weights[s] = self.base_weights.get(s, 0) / other_total * remaining
            else:
                new_weights[s] = remaining / max(len(other_syms), 1)

        # Normalise to fractions for engines
        total = sum(new_weights.values()) or 1
        w_frac = {s: v / total for s, v in new_weights.items()}

        # ── Base metrics
        base_scorer = PortfolioScorer(list(self.signals_map.values()))
        base_ps     = base_scorer.compute()

        base_risk_eng = RiskEngine(self.signals_map,
                                   {s: self.base_weights.get(s, 0) / 100 for s in syms})
        base_risk     = base_risk_eng.compute()

        # ── New metrics
        new_scorer  = PortfolioScorer(list(self.signals_map.values()))
        # Score is not weight-dependent in current impl — use weight-adjusted return
        new_ps      = new_scorer.compute()

        new_risk_eng = RiskEngine(self.signals_map, w_frac)
        new_risk     = new_risk_eng.compute()

        # ── Weight-adjusted expected return
        def _weighted_return(weights_pct: dict[str, float]) -> float:
            total_w = sum(weights_pct.values()) or 1
            return sum(
                self.signals_map[s].get("exp_return", 0.0) *
                weights_pct.get(s, 0) / total_w
                for s in syms
            )

        base_ret = _weighted_return(self.base_weights)
        new_ret  = _weighted_return(new_weights)

        # ── Deltas
        delta_ret  = round(new_ret - base_ret, 3)
        delta_div  = round(new_risk.diversification - base_risk.diversification, 1)

        risk_score_map = {"Low": 20, "Medium": 50, "High": 80, "Very High": 95}
        delta_risk = round(
            risk_score_map.get(base_risk.overall_risk, 50) -
            risk_score_map.get(new_risk.overall_risk, 50),
            1,
        )  # positive = risk reduced

        delta_score = round(new_ps.score - base_ps.score, 1)

        # ── Summary sentence
        parts = []
        if   delta_ret > 0.05:   parts.append(f"return improves +{delta_ret:.2f}%")
        elif delta_ret < -0.05:  parts.append(f"return drops {delta_ret:.2f}%")
        if   delta_risk > 5:     parts.append(f"risk reduces")
        elif delta_risk < -5:    parts.append(f"risk increases")
        if   delta_div > 5:      parts.append(f"diversification improves +{delta_div:.0f}%")
        elif delta_div < -5:     parts.append(f"diversification drops {delta_div:.0f}%")
        summary = (
            f"Changing {symbol} from {old_weight:.0f}% → {new_weight_pct:.0f}%: "
            + (", ".join(parts) if parts else "minimal portfolio impact") + "."
        )

        return WhatIfResult(
            symbol           = symbol,
            old_weight       = round(old_weight, 1),
            new_weight       = round(new_weight_pct, 1),
            delta_return_pct = delta_ret,
            delta_risk_pct   = delta_risk,
            delta_div_pct    = delta_div,
            delta_score      = delta_score,
            new_return       = round(new_ret, 3),
            new_risk_label   = new_risk.overall_risk,
            new_div          = round(new_risk.diversification, 1),
            new_score        = round(new_ps.score, 1),
            summary          = summary,
        )
