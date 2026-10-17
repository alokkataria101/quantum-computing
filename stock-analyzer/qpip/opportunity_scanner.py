"""
qpip/opportunity_scanner.py

Opportunity Scanner.

Ranks all symbols from best to worst opportunity using a composite
Opportunity Score (0–100) built from:

    Expected Return  30 %
    Quantum Confidence 25 %
    P(Up)            25 %
    Risk (inverted)  20 %

Output is a ranked table — the kind fund managers use:
    Rank  |  Symbol  |  Score  |  P(Up)  |  Risk  |  Signal  |  Confidence

Version : 11.0.1
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Opportunity:
    rank        : int
    symbol      : str
    score       : float   # 0–100
    p_up        : float   # 0–1
    risk        : str     # "Low" / "Medium" / "High"
    signal      : str     # 5-level
    confidence  : float   # 0–100
    exp_return  : float   # % expected move
    trend       : str     # "Bullish" / "Bearish" / "Sideways"


_RISK_PENALTY = {"Low": 0, "Medium": 15, "High": 35}


class OpportunityScanner:
    """
    Scans and ranks all symbols by opportunity score.

    Parameters
    ----------
    signals_map : dict[str, dict]   symbol → refresh() result
    """

    def __init__(self, signals_map: dict[str, dict]):
        self.signals_map = {
            sym: sig for sym, sig in signals_map.items()
            if "error" not in sig
        }

    # ------------------------------------------------------------------

    def scan(self) -> list[Opportunity]:
        """Return ranked opportunity list (best first)."""
        rows = []
        for symbol, sig in self.signals_map.items():
            p_up     = float(sig.get("p_up", 0.5))
            conf     = float(sig.get("confidence_pct",
                              sig.get("confidence", 0.0) * 100))
            exp_ret  = float(sig.get("exp_return", 0.0))
            risk     = sig.get("risk", "Medium")
            signal5  = sig.get("signal_5level", sig.get("signal", "HOLD"))
            trend_d  = sig.get("trend", {})
            trend    = trend_d.get("trend", "Sideways") if isinstance(trend_d, dict) else "Sideways"

            # Opportunity Score
            ret_score  = min(max(50.0 + exp_ret * 20.0, 0.0), 100.0)
            conf_score = min(conf, 100.0)
            pup_score  = p_up * 100.0
            risk_pen   = _RISK_PENALTY.get(risk, 15)

            raw_score = (
                ret_score  * 0.30 +
                conf_score * 0.25 +
                pup_score  * 0.25
            )
            score = max(0.0, raw_score - risk_pen * 0.20)
            score = round(min(score, 100.0), 1)

            rows.append(Opportunity(
                rank       = 0,
                symbol     = symbol,
                score      = score,
                p_up       = round(p_up, 3),
                risk       = risk,
                signal     = signal5,
                confidence = round(conf, 1),
                exp_return = round(exp_ret, 2),
                trend      = trend,
            ))

        rows.sort(key=lambda r: -r.score)
        for i, r in enumerate(rows, 1):
            r.rank = i
        return rows
