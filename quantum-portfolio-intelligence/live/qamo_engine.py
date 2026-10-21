"""
qamo_engine.py

QAMO — Quantum Adaptive Market Observer — Core Engine.

Wires all 14 stages into a single, stateful per-symbol engine:

    Stage 1   LiveFeed + TickBuffer
    Stage 2   MultiWindowFeatures
    Stage 3   IntradayEncoder (8-qubit)
    Stage 4   QuantumMemory (10k ring buffer)
    Stage 5   StateDatabase (Parquet persistence)
    Stage 6   QuantumSimilaritySearch (top-20)
    Stage 7   PredictionEngine (BUY/SELL/HOLD)
    Stage 8   OnlineEngine (continuous learning)
    Stage 9   ConfidenceScore
    Stage 10  HybridAI (watsonx explanation)
    Stage 11  StrategySimulator
    Stage 12  SelfEvaluation

Version : 5.13.0
"""

from __future__ import annotations

from live.feed_base            import LiveFeed
from live.yahoo_feed           import YahooFeed
from live.tick_buffer          import TickBuffer
from live.multi_window_features import MultiWindowFeatures
from live.intraday_encoder     import IntradayEncoder
from live.quantum_memory       import QuantumMemory
from live.state_database       import StateDatabase
from live.quantum_similarity   import QuantumSimilaritySearch
from live.prediction_engine    import PredictionEngine
from live.online_engine        import OnlineEngine
from live.confidence_score     import ConfidenceScore
from live.hybrid_ai            import HybridAI
from live.strategy_simulator   import StrategySimulator
from live.self_evaluation      import SelfEvaluation


class QAMOEngine:
    """
    Complete QAMO engine for one symbol.

    Parameters
    ----------
    symbol      : str
    interval    : str    "1m", "5m", "15m"
    feed        : LiveFeed | None   defaults to YahooFeed
    n_bars      : int    bars to fetch per refresh (default 200)
    memory_cap  : int    quantum memory capacity   (default 10_000)
    top_k       : int    similarity search k       (default 20)
    load_db     : bool   load persisted states on init (default True)
    """

    def __init__(
        self,
        symbol     : str,
        interval   : str       = "5m",
        feed       : LiveFeed | None = None,
        n_bars     : int       = 200,
        memory_cap : int       = 10_000,
        top_k      : int       = 20,
        load_db    : bool      = True,
    ):
        self.symbol   = symbol.upper()
        self.interval = interval
        self.n_bars   = n_bars

        # Stage 1
        self.feed = feed or YahooFeed(symbol, interval)
        self.buf  = TickBuffer(capacity=max(n_bars * 2, 1000))

        # Stage 3
        self.encoder = IntradayEncoder()

        # Stage 4
        self.memory = QuantumMemory(capacity=memory_cap)

        # Stage 5
        self.db = StateDatabase(symbol)

        # Stage 7
        self.predictor = PredictionEngine(self.memory, top_k=top_k)

        # Stage 8
        self.learner = OnlineEngine(self.encoder)

        # Stage 10
        self.ai = HybridAI(symbol)

        # Stage 11
        self.simulator = StrategySimulator()

        # Stage 12
        self.evaluator = SelfEvaluation(self.learner, self.simulator, symbol)

        # Latest computed state
        self.latest_fv      : dict | None = None
        self.latest_state   = None
        self.latest_signal  : dict | None = None
        self.latest_score   : dict | None = None
        self.latest_explain : str         = ""
        self.velocity       : float       = 0.0

        # Load persisted states
        if load_db:
            self.db.load_into_memory(self.memory, self.encoder)

    # ------------------------------------------------------------------

    def refresh(self) -> dict:
        """
        Fetch latest bars, encode, search, predict, score, explain.

        Returns the full signal dict (same as latest_score + explanation).
        """
        # Stage 1 — fetch
        bars = self.feed.fetch_latest(n_bars=self.n_bars)
        if not bars:
            return {"error": "No data returned from feed."}
        self.buf.extend(bars)

        # Stage 2 — multi-window features
        mwf = MultiWindowFeatures(self.buf)
        fv  = mwf.compute()
        if not fv:
            return {"error": "Insufficient bars for feature computation."}
        self.latest_fv = fv

        # Update session price range for encoder
        closes = [b.close for b in self.buf.all()]
        self.encoder.update_session_range(min(closes), max(closes))

        # Stage 3 — encode
        state = self.encoder.encode(fv)
        self.latest_state = state

        # Stage 4 — add to memory
        green = bars[-1].close > bars[-1].open
        self.memory.append(
            state     = state,
            fv        = fv,
            timestamp = bars[-1].timestamp,
            price     = bars[-1].close,
            green     = green,
        )
        self.velocity = self.memory.velocity()

        # Stage 6+7 — predict
        if len(self.memory) < 5:
            prediction = {
                "signal": "HOLD", "p_up": 0.5, "p_down": 0.5,
                "exp_return": 0.0, "confidence": 0.0,
                "n_matches": 0, "matches": [],
            }
        else:
            prediction = self.predictor.predict(state)
        self.latest_signal = prediction

        # Stage 9 — confidence score
        vol   = fv.get("volatility_w4", 0.0)
        score = ConfidenceScore(prediction, vol, self.velocity).compute()
        self.latest_score = score

        # Stage 10 — AI explanation
        self.latest_explain = self.ai.explain(score, fv)

        # Stage 11 — simulator
        if len(bars) >= 2:
            self.simulator.add_bar(
                signal      = score["signal"],
                price_open  = bars[-1].open,
                price_close = bars[-1].close,
                timestamp   = bars[-1].timestamp,
            )

        # Stage 5 — persist
        tmp_mem = QuantumMemory(capacity=1)
        tmp_mem.append(state, fv, bars[-1].timestamp, bars[-1].close, green)
        self.db.save(tmp_mem)

        return {**score, "explanation": self.latest_explain}

    # ------------------------------------------------------------------

    def nightly_eval(self) -> dict:
        """Stage 12 — run self-evaluation (call at end of session)."""
        report = self.evaluator.evaluate()
        self.evaluator.save_report(report)
        return report

    # ------------------------------------------------------------------

    def is_market_open(self) -> bool:
        return self.feed.is_market_open()
