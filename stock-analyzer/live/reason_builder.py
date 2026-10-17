"""
reason_builder.py

Track 1 — Signal Reason Builder.

Translates the quantum signal, feature vector, trend, and support/resistance
levels into 3–5 human-readable bullet-point strings explaining the current
recommendation.

Rules are evaluated in priority order.  The last item is always a risk caveat
when risk is Medium or High.

Version : 11.0.1
"""

from __future__ import annotations

_MAX_REASONS = 5
_MIN_REASONS = 3

_RSI_OVERSOLD    = 35.0
_RSI_OVERBOUGHT  = 65.0
_VOL_SPIKE_HIGH  = 1.5
_MACD_STRONG     = 0.5
_CONF_HIGH       = 65.0
_PROXIMITY_PCT   = 0.005   # price within 0.5% of S/R level


class ReasonBuilder:
    """
    Generates human-readable signal reasons for Track 1.

    Parameters
    ----------
    signal : dict   output of ConfidenceScore.compute()
    fv     : dict   feature vector from MultiWindowFeatures.compute()
    trend  : dict   output of TrendClassifier.classify()
    sr     : dict   output of SupportResistance.compute()
    """

    def __init__(self, signal: dict, fv: dict, trend: dict, sr: dict):
        self._signal = signal
        self._fv     = fv
        self._trend  = trend
        self._sr     = sr

    # ------------------------------------------------------------------

    def build(self) -> list[str]:
        """
        Build reason list.

        Returns
        -------
        list[str]   3–5 strings (callers may prepend a bullet symbol)
        """
        s       = self._signal
        fv      = self._fv
        trend   = self._trend
        sr      = self._sr

        direction  = s.get("signal", "HOLD")
        p_up       = float(s.get("p_up",          0.5)) * 100
        conf_pct   = float(s.get("confidence_pct", 0.0))
        stab_pct   = float(s.get("stability_pct",  0.0))
        n_matches  = int(  s.get("n_matches",       0))
        exp_ret    = float(s.get("exp_return",      0.0))
        risk       = s.get("risk", "Medium")

        rsi       = float(fv.get("rsi_w4",          fv.get("rsi",          50.0)))
        macd      = float(fv.get("macd_w4",         fv.get("macd",          0.0)))
        vol_spike = float(fv.get("volume_spike_w4", fv.get("volume_spike",  1.0)))
        vwap_dev  = float(fv.get("vwap_dev_w4",     fv.get("vwap_dev",      0.0)))
        price     = float(fv.get("price",           0.0))
        volatility= float(fv.get("volatility_w4",   fv.get("volatility",    0.0)))

        is_bullish = direction in ("BUY", "STRONG BUY")
        is_bearish = direction in ("SELL", "STRONG SELL")
        dir_word   = "upward" if is_bullish else ("downward" if is_bearish else "neutral")

        reasons: list[str] = []

        # 1 — Primary quantum signal
        reasons.append(
            f"Quantum similarity search matched {n_matches} historical states — "
            f"{p_up:.0f}% predicted {dir_word} movement (P(Up) = {p_up:.1f}%)."
        )

        # 2 — Confidence / stability
        if conf_pct >= _CONF_HIGH:
            reasons.append(
                f"High model confidence {conf_pct:.0f}% with {stab_pct:.0f}% "
                f"stability — historical matches strongly agree on direction."
            )
        else:
            reasons.append(
                f"Moderate confidence {conf_pct:.0f}% — signal is directional "
                f"but top matches show mixed certainty ({stab_pct:.0f}% stability)."
            )

        # 3 — RSI
        if rsi < _RSI_OVERSOLD:
            reasons.append(
                f"RSI {rsi:.0f} is oversold — short-term mean-reversion "
                f"supports the BUY signal."
            )
        elif rsi > _RSI_OVERBOUGHT:
            reasons.append(
                f"RSI {rsi:.0f} is overbought — momentum risk elevated; "
                f"watch for a reversal before entering."
            )
        else:
            reasons.append(
                f"RSI {rsi:.0f} is in neutral range — no extreme momentum "
                f"bias detected."
            )

        # 4 — MACD
        if len(reasons) < _MAX_REASONS:
            macd_lbl      = "positive" if macd > 0 else "negative"
            macd_strength = "strong " if abs(macd) > _MACD_STRONG else ""
            aligned       = (macd > 0 and is_bullish) or (macd < 0 and is_bearish)
            reasons.append(
                f"MACD {macd:+.4f} — {macd_strength}{macd_lbl} momentum "
                f"{'aligns with' if aligned else 'diverges from'} "
                f"the {direction} signal."
            )

        # 5 — Volume
        if len(reasons) < _MAX_REASONS:
            if vol_spike >= _VOL_SPIKE_HIGH:
                reasons.append(
                    f"Volume {vol_spike:.1f}x above session average — "
                    f"elevated participation adds conviction."
                )
            else:
                reasons.append(
                    f"Volume at {vol_spike:.1f}x session average — "
                    f"normal participation; signal strength is moderate."
                )

        # 6 — Trend alignment
        if len(reasons) < _MAX_REASONS:
            t  = trend.get("trend",    "Sideways")
            st = trend.get("strength", "Weak")
            if t != "Sideways":
                aligned = (t == "Bullish" and is_bullish) or \
                          (t == "Bearish" and is_bearish)
                reasons.append(
                    f"Intraday trend is {t} ({st}) — EMA crossover "
                    f"{'aligns with' if aligned else 'diverges from'} "
                    f"the recommendation."
                )

        # 7 — VWAP deviation
        if len(reasons) < _MAX_REASONS and abs(vwap_dev) > 0.3:
            above = vwap_dev > 0
            reasons.append(
                f"Price is {'above' if above else 'below'} VWAP by "
                f"{abs(vwap_dev):.2f}% — "
                f"{'potential resistance near VWAP.' if above else 'potential support near VWAP.'}"
            )

        # 8 — S/R proximity
        if len(reasons) < _MAX_REASONS and price > 0:
            r1 = sr.get("r1", 0.0)
            s1 = sr.get("s1", 0.0)
            if r1 > 0 and abs(price - r1) / r1 < _PROXIMITY_PCT:
                reasons.append(
                    f"Price (Rs {price:,.2f}) approaching R1 resistance "
                    f"(Rs {r1:,.2f}) — watch for rejection."
                )
            elif s1 > 0 and abs(price - s1) / s1 < _PROXIMITY_PCT:
                reasons.append(
                    f"Price (Rs {price:,.2f}) near S1 support "
                    f"(Rs {s1:,.2f}) — potential bounce zone."
                )

        # Always-last: risk caveat
        if risk in ("Medium", "High"):
            caveat = (
                f"Risk level {risk}: "
                + (f"volatility {volatility:.3f} — " if volatility > 0 else "")
                + "size position carefully and set a stop-loss."
            )
            if len(reasons) >= _MAX_REASONS:
                reasons[-1] = caveat
            else:
                reasons.append(caveat)

        # Guarantee minimum
        reasons = reasons[:_MAX_REASONS]
        while len(reasons) < _MIN_REASONS:
            reasons.append(
                f"Expected return {exp_ret:+.2f}% over next bar based on "
                f"quantum state trajectory analysis."
            )

        return reasons
