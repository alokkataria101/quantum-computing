# Research & Engineering Projects — CV Summary

> Copy the **CV Blurb** for each project directly into your CV.

---

## Book Knowledge Service
**Tags:** EdTech · DevOps · IBM watsonx AI · FastAPI · Docker
**Repo:** `github.com/alokkataria101/quantum-computing / book-knowledge-service/`

Production-grade FastAPI microservice that transforms physics PDF textbooks into a searchable knowledge base with AI-powered Q&A.

- PDF ingestion, chapter detection, FTS5 full-text search, and auto-load on startup
- Pattern-based question extractor (Examples, Exercises, Objective I/II, Short Answer) with page tracking
- Browser UI: page reader, question browser, figure thumbnails, RAG Q&A via IBM watsonx (llama-3-3-70b)
- Containerised with Docker + docker-compose; shared secrets; zero-restart Jinja2 template updates

**CV Blurb:**
> Built a full-stack FastAPI microservice (Python) ingesting physics PDFs, indexing content with FTS5, and serving a browser-based study platform with chapter-aware question extraction and IBM watsonx AI-powered RAG Q&A. Deployed via Docker with shared secrets architecture.

---

## Quantum Portfolio Intelligence Platform (QPIP)
**Tags:** Quantum · Finance · IBM watsonx AI · Streamlit · Docker
**Repo:** `github.com/alokkataria101/quantum-computing / stock-analyzer/`

9-page Streamlit investment dashboard combining quantum-inspired signal processing with IBM watsonx AI for NSE portfolio analysis.

- Quantum state similarity matching generates BUY/ADD/HOLD/REDUCE/AVOID signals with probability distributions
- IBM watsonx (Granite/llama) produces natural-language signal explanations and analyst-style research reports
- Portfolio Doctor, What-if Simulator, Opportunity Scanner, live intraday feed, adaptive memory
- Containerised with Docker; graceful AI fallback when credentials absent

**CV Blurb:**
> Designed a quantum-inspired NSE portfolio intelligence platform (Python/Streamlit) applying quantum state similarity matching for trading signals, augmented by IBM watsonx AI for natural-language explanations and report generation. Includes live feeds, portfolio diagnostics, and containerised deployment.

---

## Quantum Computing & Physics Research
**Tags:** Quantum Computing · Qiskit · VQE · QFT · Physics Research
**Repo:** `github.com/alokkataria101/quantum-computing / (Hamiltonian, VQE, QFT, phase-estimation)`

End-to-end quantum computing experiments from first principles — Schrödinger solvers through Qiskit circuit implementations.

- FDM-based Schrödinger solvers for particle-in-a-box and hydrogen atom; Hartree–Fock vs VQE comparison
- Five-stage VQE: HF → helium → H₂ dissociation → CO₂ active space → CCSD benchmark on Qiskit Aer
- QFT applied to NSE financial time series and mathematical functions — QFT vs classical FFT comparison
- Full Quantum Phase Estimation, Grover's algorithm, and Shor's algorithm demonstrations

**CV Blurb:**
> Independent quantum computing research: VQE for molecular ground-state energy estimation, Quantum Phase Estimation, Grover/Shor algorithms, and QFT analysis of financial time series using Qiskit. Bridges theoretical quantum physics (Schrödinger, Hartree–Fock) with circuit-level Qiskit implementations.

---

## Profile Summary Line

> Independent researcher and full-stack engineer applying quantum computing, IBM watsonx AI, and DevOps to real-world problems in EdTech and quantitative finance — building production-grade microservices, quantum-inspired trading platforms, and AI-powered physics study tools, all open-sourced on GitHub.
