"""
hybrid_ai.py

Stage 10 — Hybrid AI Layer (IBM watsonx Granite).

Takes the quantum signal + feature context and calls IBM Granite
to produce a human-readable explanation of the prediction.

Version : 5.10.0
"""

from __future__ import annotations

from config import (
    WATSONX_API_KEY,
    WATSONX_URL,
    WATSONX_PROJECT_ID,
    WATSONX_MODEL,
    WATSONX_MAX_NEW_TOKENS,
    WATSONX_TEMPERATURE,
    WATSONX_TOP_P,
    WATSONX_REPETITION_PENALTY,
)


_PROMPT_TEMPLATE = """You are a quantitative research assistant analysing NSE stock signals.

A quantum-inspired model has produced the following signal for {symbol}:

Signal       : {signal}
P(Close>Open): {p_up}%
P(Open>Close): {p_down}%
Expected Return: {exp_return}%
Confidence   : {confidence_pct}%
Stability    : {stability_pct}%
Risk Level   : {risk}

Current market features:
  Price        : ₹{price}
  RSI(14)      : {rsi}
  MACD         : {macd}
  Volatility   : {volatility}
  Volume Spike : {volume_spike}x
  VWAP Dev     : {vwap_dev}%
  Momentum     : {momentum}

The signal is based on finding the {n_matches} most similar historical quantum states
and observing what happened next in each case.

In 3–5 concise bullet points, explain:
• What the signal means
• Which features are driving the recommendation
• Key risks or caveats
• What a researcher should watch next

Keep it factual and research-oriented. Do not give financial advice."""


class HybridAI:
    """
    Generates a natural-language explanation of the quantum signal
    using IBM watsonx Granite.

    If watsonx credentials are not configured, returns a rule-based
    explanation instead (so the dashboard always shows something).

    Parameters
    ----------
    symbol : str
    """

    def __init__(self, symbol: str):
        self.symbol  = symbol.upper()
        self._client = None
        self._ready  = False
        self._init_client()

    # ------------------------------------------------------------------

    def _init_client(self):
        if not WATSONX_API_KEY or not WATSONX_PROJECT_ID:
            return
        try:
            from ibm_watsonx_ai.foundation_models import ModelInference  # type: ignore
            from ibm_watsonx_ai import Credentials                       # type: ignore
            creds = Credentials(url=WATSONX_URL, api_key=WATSONX_API_KEY)
            self._client = ModelInference(
                model_id   = WATSONX_MODEL,
                credentials= creds,
                project_id = WATSONX_PROJECT_ID,
                params     = {
                    "max_new_tokens"      : WATSONX_MAX_NEW_TOKENS,
                    "temperature"         : WATSONX_TEMPERATURE,
                    "top_p"               : WATSONX_TOP_P,
                    "repetition_penalty"  : WATSONX_REPETITION_PENALTY,
                },
            )
            self._ready = True
        except Exception:
            self._ready = False

    # ------------------------------------------------------------------

    def explain(self, signal: dict, fv: dict) -> str:
        """
        Generate explanation for a confidence signal.

        Parameters
        ----------
        signal : dict   output of ConfidenceScore.compute()
        fv     : dict   feature vector (FeatureGenerator or MultiWindowFeatures)

        Returns
        -------
        str   explanation text
        """
        prompt = _PROMPT_TEMPLATE.format(
            symbol         = self.symbol,
            signal         = signal["signal"],
            p_up           = round(signal["p_up"]    * 100, 1),
            p_down         = round(signal["p_down"]  * 100, 1),
            exp_return     = round(signal["exp_return"], 3),
            confidence_pct = signal["confidence_pct"],
            stability_pct  = signal["stability_pct"],
            risk           = signal["risk"],
            price          = fv.get("price", "—"),
            rsi            = fv.get("rsi_w4", fv.get("rsi", "—")),
            macd           = fv.get("macd_w4", fv.get("macd", "—")),
            volatility     = fv.get("volatility_w4", fv.get("volatility", "—")),
            volume_spike   = fv.get("volume_spike_w4", fv.get("volume_spike", "—")),
            vwap_dev       = fv.get("vwap_dev_w4", fv.get("vwap_dev", "—")),
            momentum       = fv.get("momentum_w4", fv.get("momentum", "—")),
            n_matches      = signal["n_matches"],
        )

        if self._ready:
            try:
                resp = self._client.generate_text(prompt=prompt)
                return resp.strip()
            except Exception as ex:
                return self._fallback(signal, fv, str(ex))

        return self._fallback(signal, fv)

    # ------------------------------------------------------------------

    def _fallback(self, signal: dict, fv: dict, err: str = "") -> str:
        """Rule-based explanation when watsonx is unavailable."""
        s   = signal["signal"]
        pu  = signal["p_up"] * 100
        cfg = signal["confidence_pct"]
        stb = signal["stability_pct"]
        rsk = signal["risk"]
        rsi = fv.get("rsi_w4", fv.get("rsi", 50))
        mcd = fv.get("macd_w4", fv.get("macd", 0))
        spk = fv.get("volume_spike_w4", fv.get("volume_spike", 1))
        vol = fv.get("volatility_w4", fv.get("volatility", 0))

        direction = "bullish" if s == "BUY" else ("bearish" if s == "SELL" else "neutral")

        lines = [
            f"**Quantum Signal: {s}** — The model found {signal['n_matches']} similar "
            f"historical states with {pu:.1f}% probability of next bar closing higher.",
            f"• **Confidence {cfg}%** / **Stability {stb}%**: "
            + ("High agreement among nearest historical matches." if stb > 60
               else "Mixed signals — treat with caution."),
            f"• **RSI {rsi:.1f}**: "
            + ("Overbought territory." if float(rsi) > 70
               else "Oversold territory." if float(rsi) < 30
               else "Neutral momentum."),
            f"• **MACD {float(mcd):+.4f}**: "
            + ("Positive — bullish momentum." if float(mcd) > 0
               else "Negative — bearish momentum."),
            f"• **Volume spike {float(spk):.2f}x**: "
            + ("Elevated volume — stronger signal." if float(spk) > 1.5
               else "Normal volume — signal strength moderate."),
            f"• **Risk {rsk}** | Volatility {float(vol):.4f}. "
            + ("High volatility increases prediction uncertainty." if rsk == "High"
               else "Risk is within acceptable range for research purposes."),
        ]

        note = "\n\n*watsonx AI unavailable"
        if err:
            note += f" ({err[:60]})"
        note += " — rule-based explanation shown.*"

        return "\n".join(lines) + note
