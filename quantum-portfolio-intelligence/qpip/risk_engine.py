"""
qpip/risk_engine.py

Portfolio Risk Engine.

Produces plain-language risk metrics — no technical jargon shown to users.

Outputs:
    overall_risk     : "Low" / "Medium" / "High" / "Very High"
    risk_color       : hex
    largest_risk     : str   (e.g. "Banking Sector" or symbol name)
    exposure_pct     : float (exposure of top concentration)
    diversification  : float 0–100
    volatility_label : "Low" / "Moderate" / "High"
    suggested_action : str   plain English recommendation
    alerts           : list[str]   max 3 actionable alerts

Version : 11.0.1
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Simple sector mapping for common NSE symbols
_SECTOR_MAP: dict[str, str] = {
    "HDFCBANK": "Banking", "ICICIBANK": "Banking", "SBIN": "Banking",
    "KOTAKBANK": "Banking", "AXISBANK": "Banking", "BANDHANBNK": "Banking",
    "RELIANCE": "Energy", "ONGC": "Energy", "IOC": "Energy",
    "BPCL": "Energy", "NTPC": "Energy", "POWERGRID": "Energy",
    "TCS": "IT", "INFY": "IT", "WIPRO": "IT",
    "HCLTECH": "IT", "TECHM": "IT", "LTI": "IT",
    "SUNPHARMA": "Pharma", "DRREDDY": "Pharma", "CIPLA": "Pharma",
    "DIVISLAB": "Pharma", "BIOCON": "Pharma",
    "TITAN": "Consumer", "HINDUNILVR": "Consumer", "ITC": "Consumer",
    "NESTLEIND": "Consumer", "BRITANNIA": "Consumer",
    "MARUTI": "Auto", "TATAMOTORS": "Auto", "BAJAJ-AUTO": "Auto",
    "HEROMOTOCO": "Auto", "EICHERMOT": "Auto",
    "LT": "Infra", "ULTRACEMCO": "Infra", "ACC": "Infra",
    "DMART": "Retail", "TRENT": "Retail",
    "ADANIPORTS": "Port / Logistics", "ADANIENT": "Conglomerate",
}


@dataclass
class RiskReport:
    overall_risk     : str
    risk_color       : str
    largest_risk     : str
    exposure_pct     : float
    diversification  : float     # 0–100
    volatility_label : str
    suggested_action : str
    alerts           : list = field(default_factory=list)


_RISK_COLOR = {
    "Low"      : "#16a34a",
    "Medium"   : "#d97706",
    "High"     : "#ea580c",
    "Very High": "#dc2626",
}


class RiskEngine:
    """
    Computes portfolio-level risk metrics.

    Parameters
    ----------
    signals_map : dict[str, dict]   symbol → refresh() result
    weights     : dict[str, float] | None   portfolio weights (default equal-weight)
    """

    def __init__(
        self,
        signals_map : dict[str, dict],
        weights     : dict[str, float] | None = None,
    ):
        self.signals_map = {
            sym: sig for sym, sig in signals_map.items()
            if "error" not in sig
        }
        syms = list(self.signals_map.keys())
        if weights:
            total = sum(weights.get(s, 0) for s in syms)
            self.weights = {
                s: weights.get(s, 1.0 / len(syms)) / (total or 1)
                for s in syms
            }
        else:
            n = len(syms) or 1
            self.weights = {s: 1.0 / n for s in syms}

    # ------------------------------------------------------------------

    def compute(self) -> RiskReport:
        if not self.signals_map:
            return RiskReport(
                overall_risk="Unknown", risk_color="#57606a",
                largest_risk="—", exposure_pct=0.0,
                diversification=0.0, volatility_label="Unknown",
                suggested_action="Add stocks to your portfolio to see risk analysis.",
            )

        # ── Sector concentration
        sector_exposure: dict[str, float] = {}
        for sym, w in self.weights.items():
            sector = _SECTOR_MAP.get(sym, sym)
            sector_exposure[sector] = sector_exposure.get(sector, 0.0) + w * 100.0

        top_sector = max(sector_exposure, key=sector_exposure.get)
        top_exp    = sector_exposure[top_sector]

        # ── Volatility: fraction of High-risk signals
        risk_counts = {"Low": 0, "Medium": 0, "High": 0}
        for sig in self.signals_map.values():
            r = sig.get("risk", "Medium")
            risk_counts[r] = risk_counts.get(r, 0) + 1
        n = len(self.signals_map)
        high_frac = risk_counts["High"] / n
        low_frac  = risk_counts["Low"]  / n

        if   high_frac >= 0.5:              vol_label = "High"
        elif high_frac >= 0.25:             vol_label = "Moderate"
        elif low_frac >= 0.5:               vol_label = "Low"
        else:                               vol_label = "Moderate"

        # ── Diversification score
        n_sectors = len(sector_exposure)
        # More sectors + lower top concentration = higher diversification
        div_score  = min(n_sectors * 10.0, 50.0) + max(0.0, 50.0 - top_exp * 0.5)
        div_score  = round(min(div_score, 100.0), 1)

        # ── Overall risk
        if   top_exp >= 60 or high_frac >= 0.5:  overall = "Very High"
        elif top_exp >= 40 or high_frac >= 0.3:  overall = "High"
        elif top_exp >= 25 or high_frac >= 0.1:  overall = "Medium"
        else:                                     overall = "Low"

        risk_color = _RISK_COLOR.get(overall, "#d97706")

        # ── Suggested action
        if top_exp >= 40:
            _reduce_by = max(5, round(top_exp - 25, 0))
            action = (
                f"Reduce {top_sector} exposure by "
                f"{_reduce_by:.0f}% "
                f"to improve diversification."
            )
        elif high_frac >= 0.3:
            action = "Consider replacing high-risk positions with lower-volatility alternatives."
        elif div_score < 50:
            action = "Add exposure to under-represented sectors to improve balance."
        else:
            action = "Portfolio risk is within acceptable bounds. Continue monitoring."

        # ── Alerts (max 3, plain English)
        alerts: list[str] = []
        if top_exp >= 40:
            alerts.append(
                f"⚠ {top_sector} sector is {top_exp:.0f}% of portfolio — "
                "high concentration risk."
            )
        if high_frac >= 0.3:
            alerts.append(
                f"⚠ {risk_counts['High']} of {n} stocks flagged High Risk — "
                "portfolio volatility is elevated."
            )
        if div_score < 40:
            alerts.append(
                "⚠ Diversification is low — consider adding uncorrelated positions."
            )
        alerts = alerts[:3]

        return RiskReport(
            overall_risk    = overall,
            risk_color      = risk_color,
            largest_risk    = f"{top_sector}",
            exposure_pct    = round(top_exp, 1),
            diversification = div_score,
            volatility_label= vol_label,
            suggested_action= action,
            alerts          = alerts,
        )
