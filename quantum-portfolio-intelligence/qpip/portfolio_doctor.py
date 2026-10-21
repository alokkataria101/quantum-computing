"""
qpip/portfolio_doctor.py

Portfolio Doctor.

Diagnoses the portfolio like a doctor writing a prescription.
For each problem found it produces:
    Problem        plain English
    Impact         risk level
    Suggested Fix  "Sell X% SYMBOL, Buy X% SYMBOL"

The doctor uses three diagnosis types:
    1. Concentration risk (too much of one sector/symbol)
    2. Signal conflict (holding a SELL/STRONG SELL signal)
    3. Low diversification (too few uncorrelated positions)

Version : 11.0.1
"""

from __future__ import annotations

from dataclasses import dataclass, field

from qpip.risk_engine import RiskEngine, _SECTOR_MAP


@dataclass
class Diagnosis:
    problem        : str   # plain English problem title
    impact         : str   # "High Risk" / "Moderate Risk" / "Opportunity Cost"
    impact_color   : str   # hex
    fix_action     : str   # "Sell" / "Buy" / "Rebalance"
    fix_pct        : str   # e.g. "5%"
    fix_symbol     : str   # symbol to sell/buy
    fix_detail     : str   # full prescription sentence


@dataclass
class DoctorReport:
    diagnoses      : list[Diagnosis] = field(default_factory=list)
    clean_bill     : bool            = False
    clean_message  : str             = ""


_IMPACT_COLOR = {
    "High Risk"       : "#dc2626",
    "Moderate Risk"   : "#ea580c",
    "Opportunity Cost": "#d97706",
}

# Healthy diversification replacements by sector
_ALT_SYMBOLS = {
    "IT"      : ["HCLTECH", "TECHM"],
    "Banking" : ["KOTAKBANK", "HDFC"],
    "Energy"  : ["NTPC", "POWERGRID"],
    "Pharma"  : ["SUNPHARMA", "DRREDDY"],
    "Consumer": ["HINDUNILVR", "BRITANNIA"],
    "Auto"    : ["MARUTI", "HEROMOTOCO"],
    "Infra"   : ["LT", "ULTRACEMCO"],
    "default" : ["NIFTYBEES", "JUNIORBEES"],
}


class PortfolioDoctor:
    """
    Portfolio Doctor — diagnoses and prescribes fixes.

    Parameters
    ----------
    signals_map : dict[str, dict]   symbol → refresh() result
    weights     : dict[str, float] | None   % weights
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
        n    = len(syms) or 1
        self.weights = weights or {s: 100.0 / n for s in syms}

    # ------------------------------------------------------------------

    def diagnose(self) -> DoctorReport:
        diagnoses: list[Diagnosis] = []
        syms = list(self.signals_map.keys())

        # ── Diagnosis 1: Sector concentration
        sector_exp: dict[str, list[str]] = {}
        for sym in syms:
            sector = _SECTOR_MAP.get(sym, sym)
            sector_exp.setdefault(sector, []).append(sym)

        for sector, members in sector_exp.items():
            exposure = sum(self.weights.get(s, 0) for s in members)
            if exposure >= 35.0:
                alt_sector = _next_sector(sector, sector_exp)
                alt_sym = _ALT_SYMBOLS.get(alt_sector,
                          _ALT_SYMBOLS["default"])[0]
                sell_sym = members[0]
                _fix_val = min(round(exposure - 25.0, 0), exposure)
                fix_pct  = f"{_fix_val:.0f}%"
                diagnoses.append(Diagnosis(
                    problem      = f"Too much {sector}",
                    impact       = "High Risk",
                    impact_color = _IMPACT_COLOR["High Risk"],
                    fix_action   = "Sell",
                    fix_pct      = fix_pct,
                    fix_symbol   = sell_sym,
                    fix_detail   = (
                        f"Sell {fix_pct} {sell_sym} · "
                        f"Buy {fix_pct} {alt_sym} — "
                        f"reduces {sector} concentration from "
                        f"{exposure:.0f}% → {max(exposure - float(fix_pct.strip('%')), 0):.0f}%."
                    ),
                ))

        # ── Diagnosis 2: Holding strong sell signals
        for sym, sig in self.signals_map.items():
            signal5 = sig.get("signal_5level", "HOLD")
            conf    = sig.get("confidence_pct",
                      sig.get("confidence", 0.0) * 100)
            if signal5 == "STRONG SELL" and conf >= 60:
                w = self.weights.get(sym, 0)
                diagnoses.append(Diagnosis(
                    problem      = f"{sym} flagged STRONG SELL",
                    impact       = "High Risk",
                    impact_color = _IMPACT_COLOR["High Risk"],
                    fix_action   = "Sell",
                    fix_pct      = f"{w:.0f}%",
                    fix_symbol   = sym,
                    fix_detail   = (
                        f"Sell {w:.0f}% {sym} — quantum model confidence "
                        f"{conf:.0f}% for downside. "
                        "Reallocate to a HOLD or BUY position."
                    ),
                ))
            elif signal5 == "SELL" and conf >= 70:
                w = self.weights.get(sym, 0)
                diagnoses.append(Diagnosis(
                    problem      = f"{sym} showing Sell Signal",
                    impact       = "Moderate Risk",
                    impact_color = _IMPACT_COLOR["Moderate Risk"],
                    fix_action   = "Reduce",
                    fix_pct      = f"{max(w / 2, 3):.0f}%",
                    fix_symbol   = sym,
                    fix_detail   = (
                        f"Reduce {sym} by half — momentum weakening. "
                        "Consider rebalancing into a BUY signal."
                    ),
                ))

        # ── Diagnosis 3: Low diversification
        n_sectors = len(sector_exp)
        if n_sectors <= 2 and len(syms) >= 3:
            alt_sym = _ALT_SYMBOLS["default"][0]
            diagnoses.append(Diagnosis(
                problem      = "Low diversification across sectors",
                impact       = "Opportunity Cost",
                impact_color = _IMPACT_COLOR["Opportunity Cost"],
                fix_action   = "Buy",
                fix_pct      = "10%",
                fix_symbol   = alt_sym,
                fix_detail   = (
                    f"Add exposure to a new sector — consider {alt_sym} "
                    "to improve balance and reduce sector-specific risk."
                ),
            ))

        if not diagnoses:
            return DoctorReport(
                diagnoses  = [],
                clean_bill = True,
                clean_message = (
                    "Portfolio is well-balanced. No immediate action required. "
                    "Continue to monitor weekly."
                ),
            )

        # Limit to top 3 most urgent
        diagnoses = diagnoses[:3]
        return DoctorReport(diagnoses=diagnoses, clean_bill=False)


def _next_sector(current: str, sector_map: dict[str, list]) -> str:
    """Find a sector that is under-represented."""
    all_sectors = list(_SECTOR_MAP.values())
    for s in all_sectors:
        if s != current and s not in sector_map:
            return s
    for s in all_sectors:
        if s != current:
            return s
    return "default"
