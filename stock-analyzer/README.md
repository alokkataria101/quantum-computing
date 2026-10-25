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
cd stock-analyzer
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
.venv/bin/streamlit run app.py --server.port 8501
```

### Docker container setup

```bash
cd stock-analyzer
docker build -t quantum-stock-analyzer:latest .
docker run --rm -it -p 8501:8501 quantum-stock-analyzer:latest
```

Or with Compose:

```bash
cd stock-analyzer
docker compose up --build
```

Then open:

```text
http://localhost:8501
```

1. Enter your NSE symbols in the sidebar (e.g. `RELIANCE TCS INFY HDFCBANK`)
2. Click **⚡ Run Analysis**
3. The **Quantum Decision Center** loads instantly

### Test the running app

```bash
curl -I http://localhost:8501
```

If your container is running in Docker Compose, you can also check:

```bash
docker ps
docker logs -f quantum-stock-analyzer
```

---

## Expose publicly with ngrok

ngrok gives you a public HTTPS URL so you can access the dashboard from any device or share it with someone else.

> **Prerequisite:** the app must be running locally (port 8501).

**Install ngrok** (if not already):
```bash
brew install ngrok        # macOS
# or download from https://ngrok.com/download
```

**Start ngrok** (new terminal):
```bash
ngrok http 8501
```

Wait for:
```
Session Status: online
Forwarding: https://<your-ngrok-url> -> http://localhost:8501
```

**Access remotely** using the HTTPS URL ngrok shows:

| Resource | URL |
|---|---|
| Dashboard | https://\<your-ngrok-url\> |

**Monitor requests:** http://127.0.0.1:4040 — ngrok web UI for inspecting live traffic.

**Stop ngrok:** `Ctrl+C` in the ngrok terminal.

> **Security:** the public URL is reachable from the internet. Keep your watsonx credentials private — they are never sent to ngrok.

---

## Architecture

```
app.py                          ← QPIP entry point
qpip_runner.py                  ← Analysis orchestrator

qpip/                           ← Intelligence layer (NEW in v11)
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

## Research Pages

Research pages are available under **⚙ Research & Settings**:
QAMO v2 Adaptive, QAMO v1 Fixed, Model Comparison, Trajectory Experiment, Research Tracker, Classical vs Quantum, and the full Portfolio Analysis suite (Fidelity, Entanglement, QFT, QPE, VQC Optimizer).

---

*Built on QAMO quantum engine · IBM watsonx AI (optional) · Qiskit Aer*
