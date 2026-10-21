# Quantum Portfolio Intelligence Platform (QPIP)

> **"Quantum-powered portfolio insights for faster risk analysis and better investment decisions."**

QPIP is a premium portfolio intelligence application for NSE investors. The quantum engine runs completely in the background — the UI speaks the language of investors, not physicists.

---

## What it does

| Feature | Detail |
|---|---|
| Home screen | **Quantum Decision Center** |
| Signal output | **Add / Buy / Hold / Reduce / Avoid Today** |
| Navigation | **9 investor-focused pages** |
| Risk display | **Plain-English: Medium / High / Low** |
| Portfolio Doctor | **Diagnosis + Prescription** |
| What-if Simulator | **Instant re-score on weight change** |
| Opportunity Scanner | **Ranked table by Opportunity Score** |
| Quantum Insights | **Market Stability / Hidden Correlation (no jargon)** |

---

## Design Philosophy

**The user thinks: "This tells me what to do." — not "How many qubits did it use?"**

- White background, clean cards, rounded corners
- Deep Blue + Purple + Teal accent palette
- Every page answers one question in < 5 seconds
- Quantum engine is 100% invisible to investors

---

## 9 Pages

| # | Page | What it answers |
|---|---|---|
| 🏠 | **Quantum Decision Center** | What do I do today? |
| 📊 | **Portfolio Summary** | How healthy is my portfolio? |
| 📈 | **Immediate Actions** | Buy / Sell / Hold — with reasons |
| 🔭 | **Opportunity Scanner** | What are the best opportunities right now? |
| ⚠ | **Risk Center** | Where is my risk concentrated? |
| 🔮 | **Quantum Insights** | What is the quantum engine seeing? |
| 🧪 | **What-if Simulator** | What happens if I change a position? |
| 📅 | **Strategy Planner** | How confident is tomorrow's prediction? |
| ⭐ | **Portfolio Doctor** | What is wrong and how do I fix it? |

---

## Quick Start

### Local Python setup

```bash
cd quantum-portfolio-intelligence
python3 -m venv .venv && source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
.venv/bin/streamlit run app.py --server.port 8503
```

Then open: **http://localhost:8503**

1. Enter your NSE symbols in the sidebar (e.g. `RELIANCE TCS INFY HDFCBANK`)
2. Click **⚡ Run Analysis**
3. The **Quantum Decision Center** loads instantly

### Docker

```bash
cd quantum-portfolio-intelligence
docker build -t quantum-portfolio-intelligence .
docker run --rm -it -p 8503:8501 quantum-portfolio-intelligence
```

Or with Compose:

```bash
docker compose up --build
```

---

## Architecture

```
app.py                          ← Entry point
qpip_runner.py                  ← Analysis orchestrator

qpip/                           ← Intelligence layer
├── action_engine.py            ← Verb recommendations (Add/Buy/Hold/Reduce/Avoid)
├── portfolio_scorer.py         ← 0–100 Portfolio Health Score
├── opportunity_scanner.py      ← Ranked opportunity table
├── risk_engine.py              ← Plain-English risk metrics + sector exposure
├── quantum_insights_bridge.py  ← Translates quantum outputs to investor language
├── whatif_simulator.py         ← Instant weight-change impact calculation
└── portfolio_doctor.py         ← Diagnosis + prescription

dashboard/                      ← UI pages
├── page_decision_center.py     ← Home screen
├── page_portfolio_summary.py
├── page_actions.py
├── page_scanner.py
├── page_risk.py
├── page_quantum_insights.py
├── page_whatif.py
├── page_strategy.py
└── page_doctor.py

live/                           ← Quantum engine
├── qamo_engine_v2.py           ← Core adaptive quantum pipeline
├── intraday_assistant.py       ← Per-symbol orchestrator
├── feed_with_fallback.py       ← Auto-fallback data quality
├── data_quality.py             ← Stage 0 validator
└── [35 other modules]

quantum/                        ← Daily analysis modules
data/                           ← Sample NSE CSVs (RELIANCE, TCS, INFY, etc.)
```

---

## Quantum Engine — What It Actually Does

Users see plain language. Behind each metric is a real computation:

| Investor sees | Quantum computation |
|---|---|
| Market Stability % | 1 − mean(entropy of quantum states) |
| Market Uncertainty % | Mean quantum state velocity |
| Hidden Correlation | Fidelity cluster analysis (quantum PCA proxy) |
| Risk Concentration | Fidelity variance across portfolio states |
| Portfolio Health Score | Weighted composite: returns + volatility + confidence + signal quality |
| Opportunity Score | Return × Confidence × P(up) − Risk penalty |

---

## Sample Data

The `data/` folder includes 365-day and 730-day CSVs for:
`RELIANCE` · `TCS` · `INFY` · `HDFCBANK` · `SBIN` · `ITC` · `LT` · `MARUTI` · `ACC` · `BEL` · `DMART` · `VBL` · `WIPRO` · `SHRIRAMFIN` · `M&M` · `MOMENTUM` · `MOMENTUM50`

---

*Built on QAMO quantum engine · IBM watsonx AI · Qiskit Aer*
