# QAMO v11.0.1 — Developer Reference

Complete technical reference for contributors and developers building on QAMO.

---

## Table of Contents

1. [Repository Layout](#repository-layout)
2. [Architecture Overview](#architecture-overview)
3. [Two-Track Design](#two-track-design)
4. [Configuration — config.py](#configuration--configpy)
5. [Module Catalogue](#module-catalogue)
   - [Entry Points](#entry-points)
   - [Classical Pipeline Modules](#classical-pipeline-modules)
   - [Quantum Portfolio Modules](#quantum-portfolio-modules)
   - [Live / Intraday Modules](#live--intraday-modules)
   - [New Modules — v11.0.1](#new-modules--v1101)
   - [Dashboard Modules](#dashboard-modules)
6. [Data Flow — Portfolio Classical + Quantum Pipeline](#data-flow--portfolio-classical--quantum-pipeline)
7. [Data Flow — QAMO v2 Intraday Pipeline](#data-flow--qamo-v2-intraday-pipeline)
8. [Data Flow — Track 1 Intraday Assistant](#data-flow--track-1-intraday-assistant)
9. [Data Contracts](#data-contracts)
10. [Caching Strategy](#caching-strategy)
11. [Quantum Encoding Reference](#quantum-encoding-reference)
12. [Bug Fixes Applied in v11.0.1](#bug-fixes-applied-in-v1101)
13. [Testing](#testing)
14. [Adding a New Dashboard Page](#adding-a-new-dashboard-page)
15. [Adding a New Live Feed Adapter](#adding-a-new-live-feed-adapter)
16. [Coding Conventions](#coding-conventions)
17. [Version Numbering](#version-numbering)

---

## Repository Layout

```
stock-analysis/
│
├── app.py                       Streamlit entry point — track selector + routing
├── main.py                      CLI entry point
├── config.py                    Central config + APP_VERSION + signal thresholds
├── logger.py                    Rotating file + console logger
├── models.py                    Shared dataclasses
│
├── analyzer.py                  StockAnalyzer — classical per-stock statistics
├── data_loader.py               Yahoo Finance download + CSV cache
├── portfolio.py                 PortfolioAnalyzer — multi-stock orchestration
├── comparison.py                ComparisonEngine — side-by-side table
├── correlation.py               CorrelationEngine — Pearson matrix + heatmap
├── insights.py                  InsightEngine — rule-based BUY/HOLD text
├── portfolio_summary.py         PortfolioSummary — executive summary printer
├── portfolio_export.py          PortfolioExporter — full portfolio JSON
├── markdown_report.py           MarkdownReport — Portfolio_Report.md
├── report.py                    ReportGenerator — per-stock CSV + JSON
├── visualization.py             StockVisualizer — price/returns/volume PNGs
├── prompt_builder.py            Builds watsonx prompt from portfolio data
├── ai_report.py                 AIReport — Granite AI integration
├── watsonx_client.py            Low-level watsonx API wrapper
├── cache.py                     Cache helpers
│
├── quantum/                     Portfolio-level quantum modules
│   ├── quantum_encoder.py           5 features → 5 Ry angles
│   ├── quantum_state.py             MultiQubitState product state
│   ├── quantum_circuit.py           Qiskit circuit builder + Aer simulation
│   ├── portfolio_quantum.py         QuantumPortfolio — encodes all stocks
│   ├── fidelity.py                  |<ψ1|ψ2>|² fidelity function
│   ├── fidelity_matrix.py           Pairwise fidelity matrix
│   ├── fidelity_heatmap.py          PNG heatmap export
│   ├── entanglement_pair.py         CNOT → entropy, concurrence, Bell state
│   ├── entanglement_matrix.py       All portfolio pairs
│   ├── entanglement_report.py       Print + CSV/JSON export
│   ├── qft_analyzer.py              QFT periodicity on return series
│   ├── qft_portfolio.py             QFT for all portfolio stocks
│   ├── qft_report.py                Print + CSV/JSON export
│   ├── qpe_analyzer.py              Quantum Phase Estimation P(up)
│   ├── qpe_portfolio.py             QPE for all portfolio stocks
│   ├── qpe_report.py                Print + CSV/JSON export
│   ├── vqc_optimizer.py             VQC Sharpe optimiser (COBYLA)
│   ├── portfolio_optimizer.py       Runs VQC for full portfolio
│   ├── optimizer_report.py          Print + CSV/JSON export
│   └── bloch_visualizer.py          Bloch sphere utility
│
├── live/                        QAMO intraday engine
│   ├── feed_base.py                 Abstract LiveFeed + Bar dataclass
│   ├── yahoo_feed.py                YahooFeed adapter
│   ├── zerodha_feed.py              ZerodhaFeed adapter
│   ├── polygon_feed.py              PolygonFeed stub
│   ├── alpaca_feed.py               AlpacaFeed stub
│   ├── tick_buffer.py               TickBuffer — FIFO ring buffer
│   ├── feature_generator.py         FeatureGenerator — single-window 15 features
│   ├── multi_window_features.py     MultiWindowFeatures — 5 windows × 10 features
│   ├── intraday_encoder.py          IntradayEncoder — fixed 8-qubit (QAMO v1)
│   ├── quantum_memory.py            QuantumMemory — 10k ring buffer (QAMO v1)
│   ├── state_database.py            StateDatabase — Parquet persistence (QAMO v1)
│   ├── quantum_similarity.py        QuantumSimilaritySearch — fidelity k-NN (QAMO v1)
│   ├── prediction_engine.py         PredictionEngine — BUY/SELL/HOLD (QAMO v1)
│   ├── online_engine.py             OnlineEngine — walk-forward accuracy + offsets
│   ├── confidence_score.py          ConfidenceScore — 4-metric signal profile
│   ├── hybrid_ai.py                 HybridAI — watsonx Granite explanation
│   ├── strategy_simulator.py        StrategySimulator — equity curve + Sharpe
│   ├── self_evaluation.py           SelfEvaluation — nightly error analysis
│   ├── validation_engine.py         ValidationEngine — Classical/Quantum/Hybrid bench
│   ├── qamo_engine.py               QAMOEngine v1 — 12-stage orchestrator
│   ├── complexity_estimator.py      ComplexityEstimator — C(t)
│   ├── qubit_allocator.py           QubitAllocator — A+B dynamic qubit count
│   ├── adaptive_encoder_v2.py       AdaptiveEncoderV2 — n-qubit learnable encoder
│   ├── adaptive_memory.py           AdaptiveMemory — variable-dim ring buffer
│   ├── trajectory_engine.py         TrajectoryEngine — velocity/accel/curvature
│   ├── circuit_adaptor.py           CircuitAdaptor — real-time angle correction
│   ├── next_state_predictor_v2.py   NextStatePredictorV2 — predict |ψ(t+1)⟩
│   ├── qamo_engine_v2.py            QAMOEngineV2 — 10-stage adaptive orchestrator
│   ├── trading_calendar.py          NSE trading calendar
│   ├── historical_loader.py         N-day 5-min bars + Parquet cache
│   ├── experiment_metrics.py        Benchmark metric computations
│   ├── state_comparator.py          Per-bar state comparison table
│   ├── experiment_runner.py         Static + Adaptive experiment runner
│   ├── walk_forward.py              Date-range walk-forward aggregator
│   ├── research_tracker.py          ResearchTracker — actual vs predicted (FIXED v11)
│   │
│   ├── ── NEW in v11.0.1 ──────────────────────────────────────
│   ├── price_level_forecaster.py    PriceLevelForecaster — exp OHLC from ATR + exp_return
│   ├── trend_classifier.py          TrendClassifier — Bullish/Bearish/Sideways + strength
│   ├── support_resistance.py        SupportResistance — pivot-point S/R levels
│   ├── reason_builder.py            ReasonBuilder — rule-based signal reasons (3–5 bullets)
│   └── intraday_assistant.py        IntradayAssistant — Track 1 orchestrator
│
├── dashboard/                   Streamlit page modules
│   ├── runner.py                    Portfolio pipeline orchestrator
│   ├── page_live_monitor.py         📡 Live Monitor
│   ├── page_qamo_v2.py              ⚛️ QAMO v2 Adaptive Circuit
│   ├── page_qamo.py                 ⚛️ QAMO v1 Fixed Circuit
│   ├── page_validation.py           🔬 Model Comparison
│   ├── page_experiment.py           🧪 Trajectory Experiment
│   ├── page_research_tracker.py     📊 Research Tracker
│   ├── page_overview.py             Portfolio Overview
│   ├── page_classical.py            Classical Analysis
│   ├── page_quantum.py              Quantum Encoding & Fidelity
│   ├── page_entanglement.py         Entanglement
│   ├── page_qft.py                  QFT Periodicity
│   ├── page_qpe.py                  Phase Estimation (QPE)
│   ├── page_optimizer.py            Portfolio Optimizer (VQC)
│   ├── page_report.py               Export Report
│   │
│   ├── ── NEW in v11.0.1 ──────────────────────────────────────
│   ├── page_intraday_assistant.py   🎯 Track 1 — Intraday Assistant
│   └── page_comparison.py           📊 Classical vs Quantum Comparison
│
├── data/
│   ├── <SYMBOL>_<DAYS>.csv          Daily OHLCV cache
│   ├── hist_cache/                  5-min Parquet bar cache
│   └── qamo_states/                 Persisted quantum states
├── output/
│   ├── charts/                      PNG output
│   └── reports/                     CSV / JSON / Markdown output
├── logs/
│
├── requirements.txt
├── README.md                        User-facing documentation
└── README-FOR-DEVELOPER.md          This file
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│  Presentation Layer                                             │
│  app.py  →  Track selector  →  page routing                    │
│  main.py →  CLI                                                 │
└─────────────────────────────────────────────────────────────────┘
                             │
┌─────────────────────────────────────────────────────────────────┐
│  Orchestration Layer                                            │
│  live/intraday_assistant.py    Track 1 orchestrator (NEW)       │
│  live/qamo_engine_v2.py        QAMO v2 adaptive pipeline        │
│  live/qamo_engine.py           QAMO v1 fixed pipeline           │
│  dashboard/runner.py           Portfolio pipeline               │
│  live/experiment_runner.py     Static vs adaptive experiment    │
└─────────────────────────────────────────────────────────────────┘
                             │
┌─────────────────────────────────────────────────────────────────┐
│  Computation Layer                                              │
│  Classical:  analyzer, comparison, correlation, insights        │
│  Quantum portfolio: quantum/ — encoding, fidelity, entanglement,│
│              QFT, QPE, VQC                                      │
│  Quantum intraday: live/ — encoder, memory, predictor,          │
│              trajectory, adaptor, confidence, simulator         │
│  Track 1 new: price_level_forecaster, trend_classifier,         │
│              support_resistance, reason_builder                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Two-Track Design

`app.py` top-level `track` radio selector:

```python
track = st.radio("", ["🎯 Trading Assistant", "🔬 Research Platform"])
```

**Track 1** — `if track == "🎯 Trading Assistant":`
- Calls `page_intraday_assistant.render({})` — self-contained, no portfolio run needed
- Controls (symbols, interval, n_bars, auto-refresh) are inside the page

**Track 2** — `if track == "🔬 Research Platform":`
- Renders the full v6.2.0 sidebar navigation
- Adds "📊 Classical vs Quantum Comparison" to the Live/Research group
- Portfolio pages still require Run Analysis (unchanged)

**Zero breaking changes** to any existing module — Track 1 is purely additive.

---

## Configuration — config.py

Single source of truth for all constants.

```python
from config import (
    APP_VERSION,
    STRONG_BUY_P_UP, BUY_P_UP, SELL_P_UP, STRONG_SELL_P_UP,
    STRONG_SIGNAL_CONF,
    DEFAULT_QUBITS, DEFAULT_SHOTS,
    WATSONX_API_KEY, WATSONX_MODEL, WATSONX_MAX_NEW_TOKENS,
)
```

### New in v11.0.1

```python
APP_VERSION        = "11.0.1"

STRONG_BUY_P_UP    = 0.65   # P(Up) threshold for STRONG BUY
BUY_P_UP           = 0.55   # P(Up) threshold for BUY
SELL_P_UP          = 0.45   # P(Up) threshold for SELL
STRONG_SELL_P_UP   = 0.35   # P(Up) threshold for STRONG SELL
STRONG_SIGNAL_CONF = 0.55   # minimum confidence for STRONG labels
```

All output directories are auto-created on `import config`.

---

## Module Catalogue

### Entry Points

#### `app.py`
Sets Streamlit page config, renders `track` radio, conditionally renders Track 1 or
Track 2 sidebar and pages. Version caption uses `APP_VERSION` from `config.py`.

#### `main.py`
CLI entry. `parse_arguments()` → `run_single_stock()` or `run_portfolio()`.
Banner uses `APP_VERSION`.

---

### Classical Pipeline Modules

#### `data_loader.py` — `load_stock_data(symbol, days) -> pd.DataFrame`
Appends `.NS`, downloads via `yfinance`, caches to `data/<SYM>_<DAYS>.csv`.
Raises `DataLoaderError` on failure.

#### `analyzer.py` — `StockAnalyzer(df, symbol)`
`run_analysis()` → `get_summary()` dict with keys:
`TradingDays`, `GreenDays`, `RedDays`, `ProbabilityUp`, `ProbabilityDown`,
`AverageGain`, `AverageLoss`, `MaxGain`, `MaxLoss`, `Volatility`, `StdDev`,
`LongestGreenStreak`, `LongestRedStreak`, `TrendSlope`, `AverageVolume`.

#### `portfolio.py` — `PortfolioAnalyzer(symbols, days)`
Calls `StockAnalyzer` per symbol, exposes `get_analyzer(symbol)`.

#### `comparison.py` — `ComparisonEngine(portfolio)`
`print_table()`, `best_probability()`, `highest_gain()`, `lowest_risk()`.

#### `correlation.py` — `CorrelationEngine(portfolio)`
`build()`, `export_csv()`, `export_heatmap()`, `highest_pair()`, `lowest_pair()`.
`.correlation` → `pd.DataFrame` Pearson matrix.

---

### Quantum Portfolio Modules (`quantum/`)

All accept pre-built portfolio/quantum objects. No direct data fetching.

| Module | Key class / function | What it does |
|--------|---------------------|-------------|
| `quantum_encoder.py` | `QuantumEncoder` | 5 features → 5 Ry angles |
| `portfolio_quantum.py` | `QuantumPortfolio` | Encodes all stocks |
| `fidelity_matrix.py` | `FidelityMatrix` | Pairwise \|⟨ψi\|ψj⟩\|² |
| `entanglement_pair.py` | `EntanglementPair` | CNOT entropy, concurrence, Bell state |
| `qft_analyzer.py` | `QFTAnalyzer` | Return series → QFT dominant cycles |
| `qpe_analyzer.py` | `QPEAnalyzer` | Phase kickback P(up) estimate |
| `vqc_optimizer.py` | `VQCOptimizer` | COBYLA Sharpe maximisation |

---

### Live / Intraday Modules (`live/`)

#### `live/feed_base.py` — `Bar` dataclass + `LiveFeed` ABC

```python
@dataclass
class Bar:
    timestamp: str;  symbol: str;  open: float;  high: float
    low: float;  close: float;  volume: float;  vwap: float
    interval: str;  source: str;  bid: float=0.0;  ask: float=0.0;  spread: float=0.0
```

#### `live/tick_buffer.py` — `TickBuffer(capacity=2000)`
`append(bar)`, `extend(bars)`, `all() -> list[Bar]` (oldest→newest).

#### `live/multi_window_features.py` — `MultiWindowFeatures(buf)`
`compute() -> dict | None` — 50+ keys: `<feature>_w1` … `<feature>_w5` plus
scalar fields `price`, `volume`, `spread`, `order_imbalance`, `n_bars`.

Windows: w1=6, w2=12, w3=36, w4=60, w5=180 bars.

#### `live/adaptive_encoder_v2.py` — `AdaptiveEncoderV2(allocator)` + `AdaptiveState`

```python
AdaptiveEncoderV2.encode(fv, timestamp="") -> AdaptiveState
AdaptiveState.vector      # (2^n_qubits,) complex statevector
AdaptiveState.probabilities()   # measurement probabilities
AdaptiveState.qubit_p1(q)       # P(|1>) for qubit q
AdaptiveState.padded_vector(dim) # zero-pad to target dimension
```

Feature priority: `return_w4, volatility_w4, rsi_w4, macd_w4, momentum_w4,
volume_spike_w4, vwap_dev_w4, atr_w4, return_w2, volatility_w2, rsi_w2,
return_w5, volatility_w5` (top n_qubits selected).

#### `live/adaptive_memory.py` — `AdaptiveMemory(capacity=10_000)`
`append(state, n_qubits, fv, timestamp, price, green, complexity)`
`search(query, top_k=20, fwd_bars=3) -> list[dict]`
`velocity() -> float` — 1 − F(ψ_t, ψ_{t-1})

#### `live/complexity_estimator.py` — `ComplexityEstimator`
`estimate(fv) -> {complexity, entropy, eff_rank, correlation, n_features}`
C(t) = 0.4·H_norm + 0.4·rank_norm + 0.2·decorr

#### `live/qubit_allocator.py` — `QubitAllocator`
`allocate(complexity, timestamp) -> int` (3–12)
`update_from_error(error)` — B correction

#### `live/confidence_score.py` — `ConfidenceScore(prediction, volatility, velocity)`
`compute() -> dict` with keys:
`signal`, `p_up`, `p_down`, `exp_return`, `confidence`, `confidence_pct`,
`stability`, `stability_pct`, `risk`, `n_matches`.

#### `live/qamo_engine_v2.py` — `QAMOEngineV2`
`refresh() -> dict` — full signal dict + explanation.
Key attributes after refresh: `buf`, `latest_fv`, `latest_state`,
`latest_prediction`, `latest_score`, `latest_traj`.

#### `live/research_tracker.py` — `ResearchTracker` (FIXED v11)
`record_prediction(...)`, `record_actual(...)`.
Timestamps normalised via `_normalise_ts()` — eliminates timezone mismatch bugs.
`accuracy() -> float`, `mean_error_pct() -> float`.

#### `live/self_evaluation.py` — `SelfEvaluation` (FIXED v11)
`evaluate() -> dict` — nightly error report.
`apply_recommendations(engine) -> list[str]` — NEW: acts on `retrain_flag`.

---

### New Modules — v11.0.1

#### `live/price_level_forecaster.py` — `PriceLevelForecaster(fv, signal)`

```python
forecast() -> {
    exp_open, exp_high, exp_low, exp_close,   # float ₹
    exp_pct,   # float %
    atr_range, # float ₹
}
```

`exp_close = price × (1 + exp_return/100)` · `exp_high/low = exp_close ± ATR×0.6`
Clipped to price ± 20%.

#### `live/trend_classifier.py` — `TrendClassifier(fv, buf, n=15)`

```python
classify() -> {
    trend:      "Bullish" | "Bearish" | "Sideways",
    strength:   "Weak"    | "Moderate" | "Strong",
    ema_cross:  "golden"  | "death"    | "neutral",
    slope:      float,   # price units per bar
    slope_norm: float,   # slope / ATR
    macd_sign:  int,     # +1 / -1 / 0
}
```

All three signals (slope, EMA cross, MACD) must agree for Bullish/Bearish.

#### `live/support_resistance.py` — `SupportResistance(buf, window=20)`

```python
compute() -> {
    pivot, r1, r2, s1, s2,         # float ₹  (standard floor pivot formulas)
    session_high, session_low,     # float ₹  (full buffer rolling extremes)
}
```

#### `live/reason_builder.py` — `ReasonBuilder(signal, fv, trend, sr)`

```python
build() -> list[str]   # 3–5 bullet strings
```

Priority order: (1) quantum vote summary, (2) confidence/stability, (3) RSI,
(4) MACD, (5) volume, (6) trend alignment, (7) VWAP deviation, (8) S/R proximity.
Risk caveat always last when risk is Medium or High.

#### `live/intraday_assistant.py` — `IntradayAssistant(symbol, interval, n_bars, feed, fwd_bars=6)`

```python
refresh() -> dict          # full Track 1 signal dict
get_price_levels() -> dict
get_trend() -> dict
get_support_resistance() -> dict
get_reasons() -> list[str]
get_5level_signal() -> str  # STRONG BUY / BUY / HOLD / SELL / STRONG SELL
get_tracker() -> ResearchTracker
is_market_open() -> bool
```

`_map_5level(p_up, confidence)` applies `config.py` thresholds.
Stored in `st.session_state[f"assistant_{symbol}_{interval}"]`.

---

### Dashboard Modules

Every page exports exactly one function:

```python
def render(results: dict) -> None: ...
```

Live/research pages receive `results = {}`.
Portfolio pages receive `st.session_state["results"]` from `runner.run_pipeline()`.
Pages must **not** import from each other.

---

## Data Flow — Portfolio Classical + Quantum Pipeline

```
load_stock_data() × N symbols
    → PortfolioAnalyzer.analyze()
        → StockAnalyzer.run_analysis() per symbol
    → ComparisonEngine  →  CorrelationEngine  →  PortfolioSummary
    → PortfolioExporter.export_json()
    → QuantumPortfolio.build()   ← 5-qubit Ry encoding
    → FidelityMatrix.calculate()
    → EntanglementMatrix.calculate()
    → QFTPortfolio.run()
    → QPEPortfolio.run()
    → PortfolioOptimizer.run()   ← VQC COBYLA
    → MarkdownReport.export()
    → AIReport.generate()        ← optional
```

---

## Data Flow — QAMO v2 Intraday Pipeline

Per `QAMOEngineV2.refresh()`:

```
YahooFeed.fetch_latest()  →  TickBuffer.extend()
MultiWindowFeatures.compute()  →  fv dict
ComplexityEstimator.estimate(fv)  →  {complexity, entropy, eff_rank}
QubitAllocator.allocate(complexity)  →  n_qubits (3–12)
AdaptiveEncoderV2.encode(fv)  →  AdaptiveState
CircuitAdaptor.update(prev_pred, actual, fv)  →  angle corrections  ← feedback
AdaptiveMemory.append(state, ...)
TrajectoryEngine.compute()  →  {velocity, acceleration, curvature}
NextStatePredictorV2.predict(state, fwd_bars=3)  →  {predicted_state, p_up, exp_return}
ConfidenceScore.compute()  →  {signal, confidence_pct, stability_pct, risk}
HybridAI.explain(score, fv)  →  str
StrategySimulator.add_bar(signal, open, close)
refresh()  returns  score + {"explanation": str}
```

---

## Data Flow — Track 1 Intraday Assistant

```
IntradayAssistant.refresh()
    ↓
    QAMOEngineV2.refresh()  →  score dict  +  engine.buf  +  engine.latest_fv
    ↓
    PriceLevelForecaster(fv, score).forecast()
        →  {exp_open, exp_high, exp_low, exp_close, exp_pct, atr_range}
    ↓
    TrendClassifier(fv, engine.buf).classify()
        →  {trend, strength, ema_cross, slope_norm, macd_sign}
    ↓
    SupportResistance(engine.buf).compute()
        →  {pivot, r1, r2, s1, s2, session_high, session_low}
    ↓
    ReasonBuilder(score, fv, trend, sr).build()
        →  list[str]  (3–5 bullets)
    ↓
    _map_5level(p_up, confidence)
        →  "STRONG BUY" | "BUY" | "HOLD" | "SELL" | "STRONG SELL"
    ↓
    ResearchTracker.record_actual() + record_prediction()
        →  live Actual vs Predicted chart data
```

---

## Data Contracts

### Feature Vector (fv dict) — minimum required keys for Track 1

```python
{
    "price"           : float,
    "atr_w4"          : float,   # used by PriceLevelForecaster
    "ema_fast_w4"     : float,   # used by TrendClassifier
    "ema_slow_w4"     : float,
    "macd_w4"         : float,
    "rsi_w4"          : float,   # used by ReasonBuilder
    "momentum_w4"     : float,
    "volume_spike_w4" : float,
    "vwap_dev_w4"     : float,
    "volatility_w4"   : float,
}
```

### ConfidenceScore output dict

```python
{
    "signal"         : "BUY" | "SELL" | "HOLD",
    "p_up"           : float,   # [0, 1]
    "p_down"         : float,
    "exp_return"     : float,   # expected % return
    "confidence"     : float,   # [0, 1]
    "confidence_pct" : float,   # 0–100
    "stability"      : float,   # [0, 1]
    "stability_pct"  : float,
    "risk"           : "Low" | "Medium" | "High",
    "n_matches"      : int,
}
```

### IntradayAssistant.refresh() output dict

All keys from `ConfidenceScore.compute()` plus:

```python
{
    "explanation"        : str,     # from HybridAI
    "price_levels"       : dict,    # from PriceLevelForecaster
    "trend"              : dict,    # from TrendClassifier
    "support_resistance" : dict,    # from SupportResistance
    "reasons"            : list[str],  # from ReasonBuilder
    "signal_5level"      : str,     # STRONG BUY / BUY / HOLD / SELL / STRONG SELL
}
```

---

## Caching Strategy

| Layer | Location | Format | Expiry |
|-------|----------|--------|--------|
| Daily OHLCV | `data/<SYM>_<DAYS>.csv` | CSV | 24 h |
| 5-min intraday | `data/hist_cache/<SYM>_5m_<start>_<end>.parquet` | Parquet | Permanent (date-keyed) |
| QAMO v1 states | `data/qamo_states/<SYM>_states.parquet` | Parquet | Permanent |
| Streamlit session | `st.session_state` | Python objects | Browser session |
| Output | `output/charts/`, `output/reports/` | PNG/CSV/JSON/MD | Overwritten per run |

Clear cache:
```bash
rm data/RELIANCE_365.csv
rm data/hist_cache/RELIANCE_5m_*.parquet
rm data/qamo_states/RELIANCE_states.parquet
```

---

## Quantum Encoding Reference

### Portfolio encoder (5-qubit, `quantum/quantum_encoder.py`)

| q | Feature | Formula |
|---|---------|---------|
| 0 | P(Up) | `Ry(2·arcsin(√p_up))` |
| 1 | Volatility | `Ry(π · clamp(vol/5.0))` |
| 2 | Momentum | `Ry(π/2 · (1 + clamp((G−R)/20)))` |
| 3 | Trend slope | `Ry(π/2 · (1 + clamp(slope/0.5)))` |
| 4 | Volume (M) | `Ry(π · clamp(vol_M/50.0))` |

### Intraday encoder (n-qubit adaptive, `live/adaptive_encoder_v2.py`)

Angle types:
- `pos`  → `Ry = π · clamp(v/cap, 0, 1)` — non-negative features
- `mid`  → `Ry = π/2 · (1 + clamp(v/cap, −1, 1))` — signed features
- `rsi`  → `Ry = π · clamp(v/100, 0, 1)` — RSI

Cross-dimensional fidelity: smaller statevector zero-padded to larger dimension
before `|⟨ψ1|ψ2⟩|²` — implemented in `live/adaptive_memory._fidelity()`.

---

## Bug Fixes Applied in v11.0.1

### Fix 1 — Version string centralised
`config.py`: `APP_VERSION = "11.0.1"`. Referenced from `app.py` and `main.py`.
No more hardcoded scattered version strings.

### Fix 2 — ResearchRecord dead code removed
`live/research_tracker.py` `__post_init__`: removed the dead
`actual_green` / `predicted_green` assignments that never wrote to `self.correct_dir`.
Added docstring clarifying that `correct_dir` is set by `record_actual()`.

### Fix 3 — Timestamp normalisation in ResearchTracker
`live/research_tracker.py`: new `_normalise_ts(ts) -> str` helper strips timezone
designators and truncates to `YYYY-MM-DD HH:MM:SS`. Applied in
`record_prediction()` (to `target_ts`, `prediction_ts`) and `record_actual()` (to `bar_ts`).
Prevents silent resolution failures when Yahoo Finance alternates timestamp formats.

### Fix 4 — Retrain loop closed
`live/self_evaluation.py`: new `apply_recommendations(engine) -> list[str]`.
When `retrain_flag=True`, widens encoder normalisation caps by 10% and resets
online-engine angle offsets to zero. Called from the Nightly Eval button handler.

---

## Testing

```bash
pytest                         # run all tests
pytest test_analyzer.py
pytest test_loader.py
pytest test_quantum.py
pytest test_report.py
pytest test_visualization.py
```

### Smoke tests for new v11.0.1 modules

```python
# PriceLevelForecaster
from live.price_level_forecaster import PriceLevelForecaster
levels = PriceLevelForecaster(
    {"price": 2000.0, "atr_w4": 20.0},
    {"exp_return": 0.5}
).forecast()
assert levels["exp_high"] > levels["exp_close"] > levels["exp_low"]

# TrendClassifier
from live.trend_classifier import TrendClassifier
from live.tick_buffer import TickBuffer
# (populate buf with at least 15 bars, compute fv)
t = TrendClassifier(fv, buf).classify()
assert t["trend"] in ("Bullish", "Bearish", "Sideways")
assert t["strength"] in ("Weak", "Moderate", "Strong")

# SupportResistance
from live.support_resistance import SupportResistance
sr = SupportResistance(buf).compute()
assert sr["r1"] > sr["pivot"] > sr["s1"]
assert sr["r2"] > sr["r1"]  and  sr["s2"] < sr["s1"]

# IntradayAssistant._map_5level
from live.intraday_assistant import IntradayAssistant
assert IntradayAssistant._map_5level(0.70, 0.60) == "STRONG BUY"
assert IntradayAssistant._map_5level(0.50, 0.50) == "HOLD"
assert IntradayAssistant._map_5level(0.30, 0.60) == "STRONG SELL"
```

---

## Adding a New Dashboard Page

1. Create `dashboard/page_mypage.py`:
```python
def render(results: dict) -> None:
    import streamlit as st
    st.title("My Page")
    ...
```

2. Import in `app.py`:
```python
from dashboard import page_mypage
```

3. Add to the appropriate `page` radio `options` list in `app.py`.

4. Add dispatch:
```python
if page == "My Page":
    page_mypage.render(results)   # or {}
    st.stop()
```

Track 1 pages: add to Track 1 block.
Track 2 live/research pages: add before the portfolio separator.
Track 2 portfolio pages: add to `_PORTFOLIO_PAGES` set and `PAGE_MAP` dict.

---

## Adding a New Live Feed Adapter

```python
# live/myfeed.py
from live.feed_base import LiveFeed, Bar

class MyFeed(LiveFeed):
    def __init__(self, symbol: str, interval: str, api_key: str): ...
    def fetch_latest(self, n_bars: int = 200) -> list[Bar]: ...
    def is_market_open(self) -> bool: ...
```

Pass to `QAMOEngineV2` or `IntradayAssistant`:
```python
engine = QAMOEngineV2("RELIANCE", feed=MyFeed("RELIANCE", "5m", key))
```

---

## Coding Conventions

- Python 3.10+. `from __future__ import annotations` in every file.
- Type hints on all public methods.
- Module docstring at top: purpose, version, key class/function name.
- No circular imports. Dependency order: `config` ← `live/*` ← `dashboard/*`.
- No global mutable state outside `st.session_state` and class instance variables.
- `round(x, n)` for all float output — never raw float precision in display code.
- `f-strings` for all string formatting.
- One class per orchestrator/engine file; helpers at module level are fine.
- `pytest` from project root. All new modules must have at least a smoke test.

---

## Version Numbering

Single source of truth:

```python
# config.py
APP_VERSION = "11.0.1"
```

Referenced everywhere else:

```python
from config import APP_VERSION
st.caption(f"v{APP_VERSION}  ·  Quantum Adaptive Market Observer")
print(f"      QAMO v{APP_VERSION}")
```

Format: `MAJOR.MINOR.PATCH`
- **MAJOR** — architectural change (new track, pipeline redesign)
- **MINOR** — new page, new module, new quantum algorithm
- **PATCH** — bug fix, documentation, configuration tweak
