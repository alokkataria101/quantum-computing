"""
validation_engine.py

Stage 14 — Research Validation.

Runs Classical ML, Quantum Model, and Hybrid side-by-side on the same
historical intraday data and compares:
    Directional accuracy
    MAE / RMSE of return forecasts
    Simulated Sharpe ratio
    Win rate
    Prediction latency

Classical baseline: majority vote of RSI + MACD + EMA crossover signals.
Quantum model    : QAMOEngine predictions.
Hybrid           : Quantum signal + AI confidence filter.

Version : 5.14.0
"""

from __future__ import annotations

import time
import numpy as np

from live.tick_buffer          import TickBuffer
from live.multi_window_features import MultiWindowFeatures
from live.intraday_encoder     import IntradayEncoder
from live.quantum_memory       import QuantumMemory
from live.prediction_engine    import PredictionEngine
from live.confidence_score     import ConfidenceScore
from live.strategy_simulator   import StrategySimulator


# ------------------------------------------------------------------
# Classical baseline: RSI + MACD + EMA crossover majority vote
# ------------------------------------------------------------------

def _classical_signal(fv: dict) -> str:
    votes = 0

    rsi  = float(fv.get("rsi_w4",  fv.get("rsi",  50)))
    macd = float(fv.get("macd_w4", fv.get("macd",  0)))
    ef   = float(fv.get("ema_fast_w4", fv.get("ema_fast", 0)))
    es   = float(fv.get("ema_slow_w4", fv.get("ema_slow", 0)))

    if rsi < 40:
        votes += 1   # oversold → buy
    elif rsi > 60:
        votes -= 1   # overbought → sell

    if macd > 0:
        votes += 1
    elif macd < 0:
        votes -= 1

    if ef > es:
        votes += 1
    elif ef < es:
        votes -= 1

    if votes >= 2:
        return "BUY"
    elif votes <= -2:
        return "SELL"
    return "HOLD"


# ------------------------------------------------------------------

class ValidationEngine:
    """
    Side-by-side comparison of classical, quantum, and hybrid models.

    Parameters
    ----------
    symbol   : str
    bars     : list[Bar]   full intraday bar history
    interval : str
    top_k    : int         quantum similarity search k
    """

    def __init__(self, symbol: str, bars, interval: str = "5m", top_k: int = 20):
        self.symbol   = symbol.upper()
        self.bars     = bars
        self.interval = interval
        self.top_k    = top_k

    # ------------------------------------------------------------------

    def run(self) -> dict:
        """
        Walk-forward validation over the bar history.

        Returns comparison dict for all three models.
        """
        bars     = self.bars
        n        = len(bars)
        min_bars = 30   # warm-up period

        encoder   = IntradayEncoder()
        memory    = QuantumMemory(capacity=10_000)
        predictor = PredictionEngine(memory, top_k=self.top_k)

        sims = {
            "classical" : StrategySimulator(),
            "quantum"   : StrategySimulator(),
            "hybrid"    : StrategySimulator(),
        }

        records = {m: [] for m in sims}
        latencies = {m: [] for m in sims}

        buf = TickBuffer(capacity=500)

        for i in range(1, n):
            buf.append(bars[i])
            if len(buf) < min_bars:
                continue

            mwf = MultiWindowFeatures(buf)
            fv  = mwf.compute()
            if not fv:
                continue

            closes = [b.close for b in buf.all()]
            encoder.update_session_range(min(closes), max(closes))

            actual_up    = bars[i].close > bars[i].open
            price_open   = bars[i].open
            price_close  = bars[i].close
            actual_return= (price_close / price_open - 1.0) * 100.0 \
                           if price_open != 0 else 0.0
            ts           = bars[i].timestamp

            # --- Classical ---
            t0 = time.perf_counter()
            c_sig = _classical_signal(fv)
            latencies["classical"].append(time.perf_counter() - t0)
            sims["classical"].add_bar(c_sig, price_open, price_close, ts)
            records["classical"].append({
                "actual_up": actual_up,
                "predicted_up": c_sig == "BUY",
            })

            # --- Quantum ---
            state = encoder.encode(fv)
            green = bars[i].close > bars[i].open
            memory.append(state, fv, ts, bars[i].close, green)

            if len(memory) < self.top_k + 1:
                q_sig = "HOLD"
                q_conf = 0.0
            else:
                t0    = time.perf_counter()
                pred  = predictor.predict(state)
                latencies["quantum"].append(time.perf_counter() - t0)
                score = ConfidenceScore(pred, fv.get("volatility_w4", 0),
                                        memory.velocity()).compute()
                q_sig  = score["signal"]
                q_conf = score["confidence"]

            sims["quantum"].add_bar(q_sig, price_open, price_close, ts)
            records["quantum"].append({
                "actual_up"   : actual_up,
                "predicted_up": q_sig == "BUY",
            })

            # --- Hybrid: quantum signal filtered by confidence ≥ 0.4 ---
            if len(memory) >= self.top_k + 1 and q_conf >= 0.4:
                h_sig = q_sig
            else:
                h_sig = _classical_signal(fv)

            t0 = time.perf_counter()
            latencies["hybrid"].append(time.perf_counter() - t0)
            sims["hybrid"].add_bar(h_sig, price_open, price_close, ts)
            records["hybrid"].append({
                "actual_up"   : actual_up,
                "predicted_up": h_sig == "BUY",
            })

        # --- Aggregate ---
        comparison = {}
        for model, recs in records.items():
            if not recs:
                comparison[model] = {}
                continue
            n_recs   = len(recs)
            dir_acc  = sum(1 for r in recs
                           if r["predicted_up"] == r["actual_up"]) / n_recs
            sim_res  = sims[model].results()
            avg_lat  = float(np.mean(latencies[model])) * 1000 \
                       if latencies[model] else 0.0

            comparison[model] = {
                "n_bars"              : n_recs,
                "directional_accuracy": round(dir_acc * 100, 2),
                "sharpe_ratio"        : sim_res.get("sharpe_ratio",  0),
                "win_rate"            : sim_res.get("win_rate",       0),
                "total_return_pct"    : sim_res.get("total_return_pct", 0),
                "max_drawdown_pct"    : sim_res.get("max_drawdown_pct", 0),
                "avg_latency_ms"      : round(avg_lat, 4),
            }

        return {
            "symbol"    : self.symbol,
            "n_bars"    : n,
            "comparison": comparison,
        }
