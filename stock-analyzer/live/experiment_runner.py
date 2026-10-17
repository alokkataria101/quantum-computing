"""
experiment_runner.py

Orchestrates one prediction day experiment.

Given:
    symbol          NSE ticker
    prediction_date the day to predict
    n_training_days how many prior trading days to use (default 100)
    interval        bar interval (default "5m")

Runs two modes:
    Mode 1 — Static:   build memory from training days,
                       encode only the first bar of prediction day,
                       predict all remaining bars WITHOUT updates.

    Mode 2 — Adaptive: same memory, but after each bar encode the
                       actual observed state and correct the circuit
                       before predicting the next.

v6.1.0 additions:
    fwd_bars        int  (default 3) — bars ahead used for pct_change in memory
                         search; reduces single-bar return cancellation so
                         exp_return becomes a non-trivial directional signal.
    min_confidence  float (default 0.10) — only bars where model confidence
                         meets this threshold contribute a directional signal;
                         below threshold the bar is treated as HOLD / neutral,
                         kept in the price series but excluded from directional
                         accuracy so coin-flip noise does not inflate the count.

Returns ExperimentResult with metrics for both modes + comparison df.

Version : 6.1.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime    import date

import numpy as np
import pandas as pd


def _entropy_of(state) -> float:
    """Shannon entropy of a quantum state — avoids np.sum(generator)."""
    if state is None:
        return 0.0
    probs = state.probabilities()
    probs = probs[probs > 1e-12]
    return float(-np.sum(probs * np.log2(probs)))


from live.trading_calendar      import is_trading_day
from live.historical_loader     import load_trading_days, load_single_day
from live.multi_window_features import MultiWindowFeatures
from live.tick_buffer           import TickBuffer
from live.complexity_estimator  import ComplexityEstimator
from live.qubit_allocator       import QubitAllocator
from live.adaptive_encoder_v2   import AdaptiveEncoderV2, AdaptiveState
from live.adaptive_memory       import AdaptiveMemory
from live.next_state_predictor_v2 import NextStatePredictorV2
from live.circuit_adaptor       import CircuitAdaptor
from live.trajectory_engine     import TrajectoryEngine
from live.experiment_metrics    import compute_metrics, compare_modes
from live.state_comparator      import StateComparator


@dataclass
class ModeResult:
    mode             : str           # "static" or "adaptive"
    predicted_closes : list[float]   = field(default_factory=list)
    actual_closes    : list[float]   = field(default_factory=list)
    predicted_states : list          = field(default_factory=list)
    actual_states    : list          = field(default_factory=list)
    pred_entropy     : list[float]   = field(default_factory=list)
    actual_entropy   : list[float]   = field(default_factory=list)
    confidences      : list[float]   = field(default_factory=list)
    signal_mask      : list[bool]    = field(default_factory=list)  # True = signal issued
    timestamps       : list[str]     = field(default_factory=list)
    metrics          : dict          = field(default_factory=dict)
    comparison_df    : pd.DataFrame  = field(default_factory=pd.DataFrame)


@dataclass
class ExperimentResult:
    symbol          : str
    prediction_date : date
    n_training_days : int
    interval        : str
    n_training_bars : int
    n_prediction_bars: int
    static          : ModeResult = field(default_factory=lambda: ModeResult("static"))
    adaptive        : ModeResult = field(default_factory=lambda: ModeResult("adaptive"))
    delta           : dict       = field(default_factory=dict)
    error           : str        = ""


class ExperimentRunner:
    """
    Runs one full prediction-day experiment (static + adaptive modes).

    Parameters
    ----------
    symbol          : str
    prediction_date : date
    n_training_days : int    (default 100)
    interval        : str    (default "5m")
    top_k           : int    similarity search k (default 20)
    fwd_bars        : int    bars ahead for pct_change in memory search
                             (default 3 — reduces single-bar noise cancellation)
    min_confidence  : float  minimum model confidence to emit a directional
                             signal (default 0.10). Bars below this threshold
                             are treated as HOLD; they appear in the price
                             series but are excluded from dir_accuracy_filtered.
    """

    def __init__(
        self,
        symbol          : str,
        prediction_date : date,
        n_training_days : int   = 100,
        interval        : str   = "5m",
        top_k           : int   = 20,
        fwd_bars        : int   = 3,
        min_confidence  : float = 0.10,
    ):
        self.symbol          = symbol.upper()
        self.prediction_date = prediction_date
        self.n_training_days = n_training_days
        self.interval        = interval
        self.top_k           = top_k
        self.fwd_bars        = max(1, int(fwd_bars))
        self.min_confidence  = float(min_confidence)

    # ------------------------------------------------------------------

    def run(self, progress_cb=None) -> ExperimentResult:
        """
        Execute the full experiment.

        Parameters
        ----------
        progress_cb : callable(str) | None   optional progress message callback

        Returns
        -------
        ExperimentResult
        """

        def _log(msg: str):
            if progress_cb:
                progress_cb(msg)

        result = ExperimentResult(
            symbol          = self.symbol,
            prediction_date = self.prediction_date,
            n_training_days = self.n_training_days,
            interval        = self.interval,
            n_training_bars = 0,
            n_prediction_bars= 0,
        )

        # ----------------------------------------------------------
        # Step 1 — Load training data (100 trading days)
        # ----------------------------------------------------------
        _log(f"Loading {self.n_training_days} trading days of training data...")
        train_df = load_trading_days(
            symbol    = self.symbol,
            n_days    = self.n_training_days,
            reference = self.prediction_date,
            interval  = self.interval,
        )

        if train_df.empty:
            result.error = "No training data available."
            return result

        result.n_training_bars = len(train_df)
        _log(f"Training bars loaded: {len(train_df)}")

        # ----------------------------------------------------------
        # Step 2 — Build quantum memory from training data
        # ----------------------------------------------------------
        _log("Building quantum memory...")
        memory_static   = self._build_memory(train_df)
        memory_adaptive = self._build_memory(train_df)
        _log(f"Memory built: {len(memory_static)} states")

        # ----------------------------------------------------------
        # Step 3 — Load prediction day bars
        # ----------------------------------------------------------
        _log(f"Loading prediction day: {self.prediction_date}...")
        pred_df = load_single_day(
            symbol   = self.symbol,
            day      = self.prediction_date,
            interval = self.interval,
        )

        if pred_df.empty:
            result.error = f"No data for prediction date {self.prediction_date}."
            return result

        result.n_prediction_bars = len(pred_df)
        _log(f"Prediction day bars: {len(pred_df)}")

        # ----------------------------------------------------------
        # Step 4 — Run both modes
        # ----------------------------------------------------------
        _log("Running Mode 1: Static...")
        result.static   = self._run_static(memory_static,   pred_df, train_df)

        _log("Running Mode 2: Adaptive...")
        result.adaptive = self._run_adaptive(memory_adaptive, pred_df, train_df)

        # ----------------------------------------------------------
        # Step 5 — Compare
        # ----------------------------------------------------------
        result.delta = compare_modes(result.static.metrics, result.adaptive.metrics)
        _log("Experiment complete.")

        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_memory(self, train_df: pd.DataFrame) -> AdaptiveMemory:
        """Encode all training bars into AdaptiveMemory.
        fwd_bars is NOT used here — it is applied at search time.
        """
        comp_est  = ComplexityEstimator()
        allocator = QubitAllocator()
        encoder   = AdaptiveEncoderV2(allocator)
        memory    = AdaptiveMemory(capacity=50_000)

        buf = TickBuffer(capacity=200)

        for ts, row in train_df.iterrows():
            bar_dict = {
                "timestamp": str(ts),
                "open"     : float(row.get("Open",   row["Close"])),
                "high"     : float(row.get("High",   row["Close"])),
                "low"      : float(row.get("Low",    row["Close"])),
                "close"    : float(row["Close"]),
                "volume"   : float(row.get("Volume", 0)),
            }
            from live.feed_base import Bar
            b = Bar(
                timestamp = bar_dict["timestamp"],
                symbol    = self.symbol,
                open      = bar_dict["open"],
                high      = bar_dict["high"],
                low       = bar_dict["low"],
                close     = bar_dict["close"],
                volume    = bar_dict["volume"],
                vwap      = round((bar_dict["high"] + bar_dict["low"] + bar_dict["close"]) / 3, 4),
                interval  = self.interval,
                source    = "yahoo",
            )
            buf.append(b)

            mwf = MultiWindowFeatures(buf)
            fv  = mwf.compute()
            if not fv:
                continue

            comp  = comp_est.estimate(fv)
            n_q   = allocator.allocate(comp["complexity"], timestamp=str(ts))
            state = encoder.encode(fv, timestamp=str(ts))
            green = float(row["Close"]) > float(row.get("Open", row["Close"]))

            memory.append(
                state      = state,
                n_qubits   = n_q,
                fv         = fv,
                timestamp  = str(ts),
                price      = float(row["Close"]),
                green      = green,
                complexity = comp["complexity"],
            )

        return memory

    # ------------------------------------------------------------------

    def _run_static(
        self,
        memory   : AdaptiveMemory,
        pred_df  : pd.DataFrame,
        train_df : pd.DataFrame,
    ) -> ModeResult:
        """
        Mode 1 — Static: encode only bar 0, predict all bars without
        updating the circuit.
        """
        result    = ModeResult(mode="static")
        comp_est  = ComplexityEstimator()
        allocator = QubitAllocator()
        encoder   = AdaptiveEncoderV2(allocator)
        predictor = NextStatePredictorV2(memory, top_k=self.top_k)
        min_conf  = self.min_confidence

        # Seed buffer with last few training bars for feature context
        train_buf = TickBuffer(capacity=200)
        for ts, row in train_df.tail(50).iterrows():
            from live.feed_base import Bar
            b = Bar(
                timestamp = str(ts), symbol = self.symbol,
                open=float(row.get("Open", row["Close"])),
                high=float(row.get("High", row["Close"])),
                low=float(row.get("Low",   row["Close"])),
                close=float(row["Close"]),
                volume=float(row.get("Volume", 0)),
                vwap=round((float(row.get("High", row["Close"])) +
                             float(row.get("Low",  row["Close"])) +
                             float(row["Close"])) / 3, 4),
                interval=self.interval, source="yahoo",
            )
            train_buf.append(b)

        # Encode first bar of prediction day
        first_ts, first_row = next(iter(pred_df.iterrows()))
        from live.feed_base import Bar as _Bar
        first_bar = _Bar(
            timestamp=str(first_ts), symbol=self.symbol,
            open=float(first_row.get("Open", first_row["Close"])),
            high=float(first_row.get("High", first_row["Close"])),
            low=float(first_row.get("Low",   first_row["Close"])),
            close=float(first_row["Close"]),
            volume=float(first_row.get("Volume", 0)),
            vwap=round((float(first_row.get("High", first_row["Close"])) +
                         float(first_row.get("Low",  first_row["Close"])) +
                         float(first_row["Close"])) / 3, 4),
            interval=self.interval, source="yahoo",
        )
        train_buf.append(first_bar)

        mwf = MultiWindowFeatures(train_buf)
        fv0 = mwf.compute()
        if not fv0:
            return result

        comp0  = comp_est.estimate(fv0)
        allocator.allocate(comp0["complexity"])
        state0 = encoder.encode(fv0)

        # Predict from state0 for all bars — no updates
        current_state = state0
        actual_rows   = list(pred_df.iterrows())
        prev_pred_close = float(first_row["Close"])

        for i, (ts, row) in enumerate(actual_rows):
            actual_close = float(row["Close"])
            actual_open  = float(row.get("Open", actual_close))
            actual_green = actual_close > actual_open

            # Encode actual state (for comparison only — not fed back)
            from live.feed_base import Bar as _Bar2
            ab = _Bar2(
                timestamp=str(ts), symbol=self.symbol,
                open=actual_open, high=float(row.get("High", actual_close)),
                low=float(row.get("Low", actual_close)), close=actual_close,
                volume=float(row.get("Volume", 0)),
                vwap=round((float(row.get("High", actual_close)) +
                             float(row.get("Low",  actual_close)) +
                             actual_close) / 3, 4),
                interval=self.interval, source="yahoo",
            )
            train_buf.append(ab)
            mwf_a = MultiWindowFeatures(train_buf)
            fv_a  = mwf_a.compute()
            comp_a = comp_est.estimate(fv_a) if fv_a else {"complexity": 0.5}
            allocator.allocate(comp_a["complexity"])
            actual_state = encoder.encode(fv_a) if fv_a else None

            # Predict next state from current (static — no correction)
            pred = predictor.predict(current_state, fwd_bars=self.fwd_bars)
            pred_state  = pred.get("predicted_state")
            confidence  = pred.get("confidence", 0.0)

            # Only apply directional signal when confidence meets threshold
            signal_on   = confidence >= min_conf
            exp_return  = pred.get("exp_return", 0.0) if signal_on else 0.0
            pred_close  = prev_pred_close * (1.0 + exp_return / 100.0)

            result.predicted_closes.append(pred_close)
            result.actual_closes.append(actual_close)
            result.predicted_states.append(pred_state)
            result.actual_states.append(actual_state)
            result.pred_entropy.append(_entropy_of(pred_state))
            result.actual_entropy.append(_entropy_of(actual_state))
            result.confidences.append(confidence)
            result.signal_mask.append(signal_on)
            result.timestamps.append(str(ts)[:19])

            prev_pred_close = pred_close
            # Static: current_state does NOT update

        result.metrics = compute_metrics(
            result.predicted_closes, result.actual_closes,
            result.predicted_states, result.actual_states,
            result.pred_entropy, result.actual_entropy,
            result.confidences,
            signal_mask = result.signal_mask,
        )
        result.comparison_df = StateComparator(
            result.predicted_states, result.actual_states,
            result.predicted_closes, result.actual_closes,
            result.timestamps, result.confidences,
        ).build()

        return result

    # ------------------------------------------------------------------

    def _run_adaptive(
        self,
        memory   : AdaptiveMemory,
        pred_df  : pd.DataFrame,
        train_df : pd.DataFrame,
    ) -> ModeResult:
        """
        Mode 2 — Adaptive: after each bar, encode actual state,
        correct circuit, update memory, predict next.
        """
        result    = ModeResult(mode="adaptive")
        comp_est  = ComplexityEstimator()
        allocator = QubitAllocator()
        encoder   = AdaptiveEncoderV2(allocator)
        adaptor   = CircuitAdaptor(encoder, allocator)
        predictor = NextStatePredictorV2(memory, top_k=self.top_k)
        min_conf  = self.min_confidence

        train_buf = TickBuffer(capacity=200)
        for ts, row in train_df.tail(50).iterrows():
            from live.feed_base import Bar as _Bar
            b = _Bar(
                timestamp=str(ts), symbol=self.symbol,
                open=float(row.get("Open", row["Close"])),
                high=float(row.get("High", row["Close"])),
                low=float(row.get("Low",  row["Close"])),
                close=float(row["Close"]),
                volume=float(row.get("Volume", 0)),
                vwap=round((float(row.get("High", row["Close"])) +
                             float(row.get("Low",  row["Close"])) +
                             float(row["Close"])) / 3, 4),
                interval=self.interval, source="yahoo",
            )
            train_buf.append(b)

        prev_actual_state : AdaptiveState | None = None
        prev_pred_state   : AdaptiveState | None = None
        prev_pred_close   : float = float(pred_df.iloc[0]["Close"])

        for i, (ts, row) in enumerate(pred_df.iterrows()):
            actual_close = float(row["Close"])
            actual_open  = float(row.get("Open", actual_close))
            actual_green = actual_close > actual_open

            from live.feed_base import Bar as _Bar2
            ab = _Bar2(
                timestamp=str(ts), symbol=self.symbol,
                open=actual_open,
                high=float(row.get("High", actual_close)),
                low=float(row.get("Low",   actual_close)),
                close=actual_close,
                volume=float(row.get("Volume", 0)),
                vwap=round((float(row.get("High", actual_close)) +
                             float(row.get("Low",  actual_close)) +
                             actual_close) / 3, 4),
                interval=self.interval, source="yahoo",
            )
            train_buf.append(ab)
            mwf    = MultiWindowFeatures(train_buf)
            fv     = mwf.compute()
            comp   = comp_est.estimate(fv) if fv else {"complexity": 0.5}
            n_q    = allocator.allocate(comp.get("complexity", 0.5), timestamp=str(ts))
            actual_state = encoder.encode(fv) if fv else None

            # Stage 10 feedback — correct circuit from previous prediction
            if prev_pred_state is not None and actual_state is not None:
                adaptor.update(prev_pred_state, actual_state, fv or {})

            # Add actual state to memory (adaptive updates memory too)
            if actual_state is not None:
                memory.append(
                    state      = actual_state,
                    n_qubits   = n_q,
                    fv         = fv or {},
                    timestamp  = str(ts),
                    price      = actual_close,
                    green      = actual_green,
                    complexity = comp.get("complexity", 0.5),
                )

            # Predict next state
            if actual_state is not None and len(memory) >= 5:
                pred        = predictor.predict(actual_state, fwd_bars=self.fwd_bars)
                pred_state  = pred.get("predicted_state")
                confidence  = pred.get("confidence", 0.0)
                raw_return  = pred.get("exp_return",  0.0)
            else:
                pred_state  = None
                confidence  = 0.0
                raw_return  = 0.0

            # Only apply directional signal when confidence meets threshold
            signal_on  = confidence >= min_conf
            exp_return = raw_return if signal_on else 0.0
            pred_close = prev_pred_close * (1.0 + exp_return / 100.0)

            result.predicted_closes.append(pred_close)
            result.actual_closes.append(actual_close)
            result.predicted_states.append(pred_state)
            result.actual_states.append(actual_state)
            result.pred_entropy.append(_entropy_of(pred_state))
            result.actual_entropy.append(_entropy_of(actual_state))
            result.confidences.append(confidence)
            result.signal_mask.append(signal_on)
            result.timestamps.append(str(ts)[:19])

            prev_pred_close = actual_close   # adaptive uses actual close as base
            prev_pred_state = pred_state
            prev_actual_state = actual_state

        result.metrics = compute_metrics(
            result.predicted_closes, result.actual_closes,
            result.predicted_states, result.actual_states,
            result.pred_entropy, result.actual_entropy,
            result.confidences,
            signal_mask = result.signal_mask,
        )
        result.comparison_df = StateComparator(
            result.predicted_states, result.actual_states,
            result.predicted_closes, result.actual_closes,
            result.timestamps, result.confidences,
        ).build()

        return result
