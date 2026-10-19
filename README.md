# Quantum Computing and Physics

Hands-on quantum computing and quantum physics experiments in Python: Schrödinger-equation solvers, Hartree–Fock chemistry, the Variational Quantum Eigensolver (VQE), phase estimation, Grover/Shor demos, and a small stock-analysis app that uses quantum states.

## Repository map

| Folder | What it contains | Guide |
|---|---|---|
| [`Hamiltonian/`](Hamiltonian/) | Particle-in-a-box and hydrogen (finite differences), Hartree–Fock, H₂ with VQE, circuit basics, Grover, Shor, Monte Carlo π | [`Hamiltonian/README.md`](Hamiltonian/README.md) |
| [`phase-estimation-basics/`](phase-estimation-basics/) | From one-qubit phase measurement to full Quantum Phase Estimation | [`README.md`](phase-estimation-basics/README.md) |
| [`VQE/`](VQE/) | Five-step VQE tutorial: Hartree–Fock → helium → H₂ dissociation → CO₂ active space → CCSD benchmark | [`VQE/README.md`](VQE/README.md) |
| [`quantum-computing-portfolio/`](quantum-computing-portfolio/) | Six small projects (`quantum_lab` library, demos, tests, Streamlit app) | [`README.md`](quantum-computing-portfolio/README.md) |
| [`stock-analyzer/`](stock-analyzer/) | Stock analysis with quantum encodings; needs internet for most features | [`README.md`](stock-analyzer/README.md) |
| [`quantum-stock-qft/`](quantum-stock-qft/) | **Quantum Fourier Analysis of Financial Time Series** — downloads Yahoo Finance data, applies QFT via Qiskit, compares against classical FFT, Streamlit dashboard, HTML report | [`quantum-stock-qft/README.md`](quantum-stock-qft/README.md) |
| [`misc/`](misc/) | Notes and documents | – |

## 1. Prerequisites

- **Python 3.11** (tested). Python 3.10 and 3.12 may work, but the pinned versions in `requirements.txt` were only tested on 3.11.
- `git`, and about 2 GB of free disk space for the packages.
- macOS or Linux (tested on macOS). On Windows, use WSL; native Windows was not tested.

Check your version:

```bash
python3.11 --version
```

## 2. Get the code

```bash
git clone https://github.com/alokkataria101/quantum-computing.git
cd quantum-computing
```

## 3. Create a virtual environment and install the requirements

Run these from the repository root (the folder that contains `requirements.txt`).

```bash
python3.11 -m venv .venv          # 1. create the environment in a folder called .venv
source .venv/bin/activate         # 2. activate it (your prompt now starts with "(.venv)")
python -m pip install --upgrade pip
pip install -r requirements.txt   # 3. install everything
```

Verify the install:

```bash
python -c "import qiskit, qiskit_aer, qiskit_algorithms, qiskit_nature, pyscf, numpy, scipy; print('qiskit', qiskit.__version__, '| numpy', numpy.__version__, '| scipy', scipy.__version__)"
```

Expected: `qiskit 1.1.0 | numpy 1.23.5 | scipy 1.10.1`.

To leave the environment later, run `deactivate`. To activate it again in a new terminal, run `source .venv/bin/activate` from the repository root.

### About `requirements.txt`

The root [`requirements.txt`](requirements.txt) is a superset of the requirements of every folder:

| Source | Packages |
|---|---|
| [`VQE/requirements.txt`](VQE/requirements.txt) | `qiskit`, `qiskit-aer`, `qiskit-algorithms`, `qiskit-nature`, `pyscf`, `numpy`, `scipy` (exact pins) |
| [`Hamiltonian/h2-quantum-simulation/requirements.txt`](Hamiltonian/h2-quantum-simulation/requirements.txt) | same libraries plus `matplotlib` |
| [`quantum-computing-portfolio/requirements.txt`](quantum-computing-portfolio/requirements.txt) | `matplotlib`, `streamlit`, `pytest`, `pytest-cov` |
| [`stock-analyzer/requirements.txt`](stock-analyzer/requirements.txt) | `pandas`, `yfinance`, `plotly`, `tabulate`, `colorama`, `ibm-watsonx-ai`, `kiteconnect`, `pyarrow` |
| [`quantum-stock-qft/requirements.txt`](quantum-stock-qft/requirements.txt) | `numpy`, `scipy`, `pandas`, `yfinance`, `qiskit`, `qiskit-aer`, `matplotlib`, `plotly`, `kaleido`, `streamlit`, `pyyaml`, `jinja2`, `pytest`, `pytest-cov` |

Where folders disagree, the **older, pinned versions win**, because the VQE/Hamiltonian code breaks on newer ones (Qiskit 2.x removed the V1 `Estimator`, and SciPy ≥ 1.14 removed sparse `.H`). `stock-analyzer/requirements.txt` asks for `numpy>=2.5` and `qiskit>=2.5`; the root file uses the older versions instead. The stock analyzer only needs `QuantumCircuit` and `AerSimulator`, which Qiskit 1.x provides, and its offline test passes with them. Its network features were not tested here.

**`quantum-stock-qft/` is designed to run in its own virtual environment** (see its own `README.md`). Its packages (`pyyaml`, `jinja2`, `kaleido`, `pytest-cov`) are also listed in the root `requirements.txt` for completeness, but the sub-project venv is the recommended way to run it.

## 4. Run everything and save the results

The script [`run_all.py`](run_all.py) runs every demo script in the repository one by one and writes the output of each into a single Markdown file.

```bash
source .venv/bin/activate     # if not already active
python run_all.py
```

It prints progress as it goes:

```text
[1/36] Hamiltonian/h2-quantum-simulation/classical/h2_classical.py ... PASS (39.4s)
[2/36] Hamiltonian/h2-quantum-simulation/vqe/h2_vqe.py ... PASS (26.2s)
...
36 of 36 passed. Results written to outputs/run_all_results.md
```

A full run takes about 4–5 minutes. The Markdown report is created at **`outputs/run_all_results.md`** (the `outputs/` folder is git-ignored). For each script it records:

- the file name and the first line of its docstring (what it does),
- the exact command and working folder,
- status (`PASS`, `FAIL (exit code N)` or `TIMEOUT`) and run time,
- everything the script printed, and anything written to stderr,
- a summary table at the end.

The report is written after every script, so you can open it while the run is still in progress. Your home and repository paths are replaced with `~` and `<repo>`, so the file is safe to share.

### What gets run

| Group | Scripts |
|---|---|
| `Hamiltonian/` | 15 scripts |
| `phase-estimation-basics/` | 4 scripts |
| `VQE/` | 10 scripts |
| `quantum-computing-portfolio/notebooks/` | 5 demo scripts |
| `stock-analyzer/test_quantum.py` | the only stock-analyzer script that works offline |
| `quantum-computing-portfolio/tests/` | the pytest suite, run as one job |

> **Note:** `quantum-stock-qft/` is not included in `run_all.py` — it has its own venv, Streamlit UI, and test suite. Run it separately:
> ```bash
> cd quantum-stock-qft && source .venv/bin/activate
> pytest tests/ -v            # 36 pass, 11 skip (Qiskit optional)
> streamlit run app.py        # interactive dashboard
> ```

The library code (`quantum-computing-portfolio/src/`, most of `stock-analyzer/`) is not run directly; it is exercised through the demos and tests above.

### Options

```bash
python run_all.py --list                  # show what would run, run nothing
python run_all.py --only VQE              # only scripts whose path contains "VQE"
python run_all.py --only phase-estimation # only the phase-estimation folder
python run_all.py --timeout 1200          # allow 20 minutes per script (default 600 s)
python run_all.py --output my_results.md  # choose a different output file
python run_all.py --with-network          # also run stock-analyzer scripts that download data
```

`--with-network` adds five stock-analyzer scripts that fetch Indian-market prices from Yahoo Finance. They need internet and may fail if the data provider changes; they are not part of the default run.

Plots: scripts that call `plt.show()` run with the non-interactive `Agg` backend, so no window opens and nothing blocks. A harmless "FigureCanvasAgg is non-interactive" warning appears in the report. To see the plots, run those three scripts by hand (see their folder READMEs).

The exit code is `0` when every script passed and `1` otherwise, so the script can also be used in CI.

## 5. Run a single script

```bash
source .venv/bin/activate
python VQE/03-bond-dissociation-vqe/h2_bond_dissociation_vqe.py
```

Every script is self-contained. Run them from the repository root as shown (tested); the folder READMEs list the expected output.

Other entry points:

```bash
pytest quantum-computing-portfolio/tests          # portfolio unit tests
streamlit run quantum-computing-portfolio/apps/quantum_teaching_studio.py   # interactive app
```

## 6. quantum-stock-qft — Quick Reference

This sub-project has its own isolated environment and Streamlit dashboard.

```bash
cd quantum-stock-qft
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest tests/ -v                   # 36 passed, 11 skipped (Qiskit tests skip without install)
streamlit run app.py               # open http://localhost:8501
```

What it does:

1. Downloads daily closing prices from **Yahoo Finance** (`yfinance`).
2. Converts to one of four representations: raw prices, mean-centred prices, daily % returns, mean-centred returns.
3. Zero-pads to M = 2^q and L2-normalises → quantum amplitude state **ψ**.
4. Applies the **Quantum Fourier Transform** via Qiskit Aer statevector or shot-based simulation.
5. Compares QFT probability distribution against classical NumPy FFT power spectrum (Parseval equivalence verified).
6. Identifies dominant frequency bins and their approximate periods in trading observations.
7. Generates a self-contained **HTML research report** with all figures embedded.

See [`quantum-stock-qft/docs/methodology.md`](quantum-stock-qft/docs/methodology.md) for the full mathematical derivation and [`quantum-stock-qft/docs/research_limitations.md`](quantum-stock-qft/docs/research_limitations.md) for critical caveats before interpreting any results.

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `ImportError: cannot import name 'Estimator' from 'qiskit.primitives'` | Qiskit 2.x is installed. Reinstall with `pip install -r requirements.txt` in a fresh venv. |
| `AttributeError: 'csr_matrix' object has no attribute 'H'` | SciPy ≥ 1.14. The requirements pin `scipy==1.10.1`. |
| `pip` fails building `pyscf` | Use Python 3.11 on macOS/Linux; install a C compiler (`xcode-select --install` on macOS). |
| Python 3.12/3.13: `numpy==1.23.5` has no wheel | Use Python 3.11. |
| A script is reported `TIMEOUT` | Slow machine; raise the limit with `--timeout 1800`. |
| Different numbers in CO₂⁺ | That VQE run is not fully deterministic; results vary by about ±0.0001 Ha. |
