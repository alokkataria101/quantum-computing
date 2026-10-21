"""
qamo_engine_v2.py

QAMO v2 — Self-Evolving Adaptive Quantum Market Observer.

Full 10-stage feedback loop for one symbol:

    Stage 1   LiveFeed + TickBuffer
    Stage 2   MultiWindowFeatures → Feature Vector(t)
    Stage 3   ComplexityEstimator → C(t)
    Stage 4   QubitAllocator → n_qubits(t)   ← A+B combined
    Stage 5   AdaptiveEncoderV2 → |ψ(t)⟩     ← learnable θ(t)
    Stage 6   AdaptiveMemory → ring buffer
    Stage 7   TrajectoryEngine → velocity, accel, curvature
    Stage 8   NextStatePredictorV2 → |ψ(t+1)⟩
    Stage 9   Signal extraction → BUY/SELL/HOLD + P(up) + confidence
    Stage 10  CircuitAdaptor → Δθ, Δn_qubits  ← closes the loop

The feedback loop (Stage 10) fires after every bar:
    Observe actual next bar → encode → compare to prediction
    → update angles + normalisation + qubit count → predict again

Version : 5.2.0
"""

from __future__ import annotations

from live.feed_base              import LiveFeed
from live.yahoo_feed             import YahooFeed
from live.tick_buffer            import TickBuffer
from live.multi_window_features  import MultiWindowFeatures
from live.complexity_estimator   import ComplexityEstimator
from live.qubit_allocator        import QubitAllocator
from live.adaptive_encoder_v2    import AdaptiveEncoderV2, AdaptiveState
from live.adaptive_memory        import AdaptiveMemory
from live.trajectory_engine      import TrajectoryEngine
from live.next_state_predictor_v2 import NextStatePredictorV2
from live.circuit_adaptor        import CircuitAdaptor
from live.confidence_score       import ConfidenceScore
from live.hybrid_ai              import HybridAI
from live.strategy_simulator     import StrategySimulator
from live.self_evaluation        import SelfEvaluation
from live.online_engine          import OnlineEngine


class QAMOEngineV2:
    """
    Self-evolving QAMO engine for one symbol.

    The key difference from v1:
        - n_qubits adapts every bar (A: entropy floor, B: error-driven)
        - Circuit angles θ(t) update immediately after each prediction
        - Predicts |ψ(t+1)⟩ not just direction
        - Feedback loop fires after every bar — no overnight retraining

    Parameters
    ----------
    symbol     : str
    interval   : str       "1m", "5m", "15m"
    feed       : LiveFeed | None
    n_bars     : int       bars to fetch per refresh
    memory_cap : int       state memory capacity
    top_k      : int       similarity search k
    lr         : float     learning rate for circuit adaptation
    """

    def __init__(
        self,
        symbol     : str,
        interval   : str            = "5m",
        feed       : LiveFeed | None = None,
        n_bars     : int            = 200,
        memory_cap : int            = 10_000,
        top_k      : int            = 20,
        lr         : float          = 0.05,
    ):
        self.symbol   = symbol.upper()
        self.interval = interval
        self.n_bars   = n_bars

        # Stage 1
        self.feed = feed or YahooFeed(symbol, interval)
        self.buf  = TickBuffer(capacity=max(n_bars * 2, 1000))

        # Stage 2
        self.complexity_est = ComplexityEstimator()

        # Stage 3 + 4  (A+B allocator)
        self.allocator = QubitAllocator()

        # Stage 5
        self.encoder = AdaptiveEncoderV2(self.allocator)

        # Stage 6
        self.memory = AdaptiveMemory(capacity=memory_cap)

        # Stage 7
        self.traj_engine = TrajectoryEngine(self.memory)

        # Stage 8
        self.predictor = NextStatePredictorV2(self.memory, top_k=top_k)

        # Stage 10 — circuit adaptor (feedback)
        self.adaptor = CircuitAdaptor(self.encoder, self.allocator, lr=lr)

        # Supporting modules
        self.ai        = HybridAI(symbol)
        self.simulator = StrategySimulator()
        self.online    = OnlineEngine(self.encoder, lr=lr)  # type: ignore

        # State
        self.latest_fv          : dict | None        = None
        self.latest_complexity  : dict | None        = None
        self.latest_state       : AdaptiveState | None = None
        self.latest_prediction  : dict | None        = None
        self.latest_score       : dict | None        = None
        self.latest_traj        : dict | None        = None
        self.latest_explain     : str                = ""
        self._prev_state        : AdaptiveState | None = None
        self._prev_fv           : dict | None        = None

    # ------------------------------------------------------------------

    def refresh(self) -> dict:
        """
        One full cycle of the feedback loop.

        Returns the complete signal dict.
        """
        # Stage 1 — fetch latest bars
        bars = self.feed.fetch_latest(n_bars=self.n_bars)
        if not bars:
            return {"error": "No data from feed."}
        self.buf.extend(bars)

        # Stage 2 — multi-window features
        mwf = MultiWindowFeatures(self.buf)
        fv  = mwf.compute()
        if not fv:
            return {"error": "Insufficient bars for features."}
        self.latest_fv = fv

        # Stage 3 — complexity
        closes = [b.close for b in self.buf.all()]
        comp   = self.complexity_est.estimate(fv)
        self.latest_complexity = comp

        # Stage 4 — allocate qubits (Approach A)
        n_q = self.allocator.allocate(
            comp["complexity"],
            timestamp = bars[-1].timestamp,
        )

        # Update session price range
        self.encoder.norm["price_lo"] = min(closes)
        self.encoder.norm["price_hi"] = max(closes)

        # Stage 5 — encode
        state = self.encoder.encode(fv, timestamp=bars[-1].timestamp)
        self.latest_state = state

        # Stage 10 (feedback) — if we have a prior prediction, correct now
        if self._prev_state is not None and self._prev_fv is not None:
            correction = self.adaptor.update(
                predicted  = self._prev_state,
                actual     = state,
                fv_actual  = fv,
            )
            # Record outcome for online learner
            actual_up = bars[-1].close > bars[-1].open
            predicted_up = (self.latest_prediction or {}).get("p_up", 0.5) >= 0.5
            self.online.record(
                predicted_up  = predicted_up,
                actual_up     = actual_up,
                confidence    = (self.latest_prediction or {}).get("confidence", 0.0),
                timestamp     = bars[-1].timestamp,
            )

        # Stage 6 — store in memory
        green = bars[-1].close > bars[-1].open
        self.memory.append(
            state      = state,
            n_qubits   = n_q,
            fv         = fv,
            timestamp  = bars[-1].timestamp,
            price      = bars[-1].close,
            green      = green,
            complexity = comp["complexity"],
        )

        # Stage 7 — trajectory
        traj = self.traj_engine.compute()
        self.latest_traj = traj

        # Stage 8 + 9 — predict next state + extract signals
        if len(self.memory) >= 5:
            prediction = self.predictor.predict(state)
        else:
            prediction = {
                "predicted_state": None, "signal": "HOLD",
                "p_up": 0.5, "p_down": 0.5, "exp_return": 0.0,
                "confidence": 0.0, "stability": 0.0,
                "n_matches": 0, "matches": [],
            }
        self.latest_prediction = prediction

        # Store current state as "previous" for next correction cycle
        self._prev_state = prediction.get("predicted_state")
        self._prev_fv    = fv

        # Confidence score
        vol   = fv.get("volatility_w4", 0.0)
        vel   = traj.get("latest_velocity", 0.0)
        score = ConfidenceScore(prediction, vol, vel).compute()
        self.latest_score = score

        # AI explanation
        self.latest_explain = self.ai.explain(score, fv)

        # Strategy simulator
        if len(bars) >= 2:
            self.simulator.add_bar(
                signal      = score["signal"],
                price_open  = bars[-1].open,
                price_close = bars[-1].close,
                timestamp   = bars[-1].timestamp,
            )

        return {**score, "explanation": self.latest_explain}

    # ------------------------------------------------------------------

    def is_market_open(self) -> bool:
        return self.feed.is_market_open()

    def nightly_eval(self) -> dict:
        """Run self-evaluation at end of session."""
        from live.self_evaluation import SelfEvaluation
        evaluator = SelfEvaluation(self.online, self.simulator, self.symbol)
        return evaluator.evaluate()
