"""
trajectory_portfolio.py

Orchestrates the full quantum trajectory pipeline for every stock
in the portfolio.

Pipeline per symbol (Steps 1–9):
    1. StateTrajectory     — encode each day → |ψ_t>
    2. StateVelocity       — Fidelity(t, t-1), velocity, acceleration
    3. RegimeDetector      — Stable / Reversal / Breakout / Shock
    4. StateMemory         — store all states (ring buffer)
    5. SimilaritySearch    — find nearest historical neighbours
    6. NextStatePredictor  — predict |ψ(t+1)>, P(up), P(down)
    7. OnlineLearner       — score walk-forward predictions, update weights
    8. AdaptiveEncoder     — re-encode latest state with learned offsets
    9. Final forecast      — P(up), P(down), confidence, regime, entropy

Version : 4.1.0
"""

from __future__ import annotations

from portfolio import PortfolioAnalyzer

from quantum.state_trajectory    import StateTrajectory
from quantum.state_velocity      import StateVelocity
from quantum.regime_detector     import RegimeDetector
from quantum.state_memory        import StateMemory
from quantum.similarity_search   import SimilaritySearch
from quantum.next_state_predictor import NextStatePredictor
from quantum.online_learner      import OnlineLearner
from quantum.adaptive_encoder    import AdaptiveEncoder


class TrajectoryPortfolio:
    """
    Runs the full quantum trajectory engine for every symbol and stores results.

    Parameters
    ----------
    portfolio : PortfolioAnalyzer
    window    : int   rolling window for feature encoding (default 20)
    memory_n  : int   state memory capacity (default 1000)
    top_k     : int   nearest neighbours for prediction (default 5)

    Attributes
    ----------
    results : dict[symbol → dict]   per-symbol trajectory results
    """

    def __init__(
        self,
        portfolio : PortfolioAnalyzer,
        window    : int = 20,
        memory_n  : int = 1000,
        top_k     : int = 5,
    ):
        self.portfolio = portfolio
        self.window    = window
        self.memory_n  = memory_n
        self.top_k     = top_k
        self.results   : dict = {}

    # ------------------------------------------------------------------

    def run(self):
        for symbol in self.portfolio.get_symbols():
            print(f"  Trajectory → {symbol}...")
            analyzer = self.portfolio.get_analyzer(symbol)
            df       = analyzer.get_dataframe()
            self.results[symbol] = self._run_symbol(symbol, df)
        print("  Trajectory pipeline complete.")

    # ------------------------------------------------------------------

    def _run_symbol(self, symbol: str, df) -> dict:

        # Step 1 — Trajectory
        learner  = OnlineLearner()
        traj     = StateTrajectory(symbol, df, window=self.window,
                                   weights=learner.weights)

        if len(traj) < 3:
            return {"error": "Insufficient data for trajectory analysis."}

        # Step 2 — Velocity
        velocity = StateVelocity(traj)

        # Step 3 — Regime
        regime   = RegimeDetector(traj, velocity,
                                  thresholds=learner.thresholds)

        # Step 4 — Memory (load all but last state; last = "current")
        memory   = StateMemory(capacity=self.memory_n)
        memory.load_trajectory(
            traj.states[:-1],
            traj.greens[:-1],
            traj.closes[:-1],
            traj.dates [:-1],
        )

        # Step 5 & 6 — Similarity search + prediction on current state
        predictor = NextStatePredictor(memory, top_k=self.top_k)
        current   = traj.latest_state()
        forecast  = predictor.predict(current)

        # Step 7 — Walk-forward scoring on held-out tail (last 20% of history)
        n       = len(traj)
        start   = max(1, int(n * 0.80))

        # Rebuild memory with first 80% for scoring
        train_mem = StateMemory(capacity=self.memory_n)
        train_mem.load_trajectory(
            traj.states[:start],
            traj.greens[:start],
            traj.closes[:start],
            traj.dates [:start],
        )
        wf_predictor = NextStatePredictor(train_mem, top_k=self.top_k)

        for t in range(start, n - 1):
            fc = wf_predictor.predict(traj.states[t])
            predicted_up = fc["p_up"] >= 0.5
            actual_up    = traj.greens[t + 1]
            learner.record(predicted_up, actual_up, fc["confidence"],
                           date=traj.dates[t])
            # Add this state to memory so model learns incrementally
            train_mem.append(
                traj.states[t], traj.greens[t], traj.closes[t], traj.dates[t]
            )

        # Step 8 — Adaptive encoder with learned offsets
        adaptive = AdaptiveEncoder(learner)

        return {
            "trajectory"      : traj,
            "velocity"        : velocity,
            "regime"          : regime,
            "memory"          : memory,
            "forecast"        : forecast,
            "learner"         : learner,
            "adaptive_encoder": adaptive,
        }

    # ------------------------------------------------------------------

    def get_result(self, symbol: str) -> dict:
        return self.results.get(symbol, {})

    def get_symbols(self) -> list[str]:
        return list(self.results.keys())
