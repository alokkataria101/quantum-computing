#!/usr/bin/env python3
"""Run every runnable Python script in this repository and record the output in one Markdown file.

Usage (from the repository root, inside the virtual environment):

    python run_all.py                    # run everything offline, write outputs/run_all_results.md
    python run_all.py --list             # only list what would run
    python run_all.py --only VQE         # run scripts whose path contains "VQE"
    python run_all.py --timeout 900      # per-script time limit in seconds (default 600)
    python run_all.py --with-network     # also run stock-analyzer scripts that download market data

Each script is run in its own process, with its own folder as working directory and the
matplotlib "Agg" backend (plt.show() does not open windows or block). After every script the
result is appended to the Markdown file, so you can watch it grow while the run is in progress.

Library modules (e.g. quantum-computing-portfolio/src, stock-analyzer/quantum) are not run on
their own; they are exercised through the demo scripts and the pytest suite listed below.
"""
from __future__ import annotations

import argparse
import ast
import os
import platform
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = ROOT / "outputs" / "run_all_results.md"

# Folders whose *.py files are standalone demos, in the order they are run.
SCRIPT_FOLDERS = [
    "Hamiltonian",
    "phase-estimation-basics",
    "VQE",
    "quantum-computing-portfolio/notebooks",
]

# stock-analyzer: only test_quantum.py works offline; the others call Yahoo Finance.
STOCK_OFFLINE = ["stock-analyzer/test_quantum.py"]
STOCK_NETWORK = [
    "stock-analyzer/test_loader.py",
    "stock-analyzer/test_analyzer.py",
    "stock-analyzer/test_report.py",
    "stock-analyzer/test_visualization.py",
    "stock-analyzer/test.py",
]

PYTEST_TARGET = "quantum-computing-portfolio/tests"


def first_doc_line(path: Path) -> str:
    """First line of the module docstring, or '' if there is none."""
    try:
        doc = ast.get_docstring(ast.parse(path.read_text(encoding="utf-8")))
    except (SyntaxError, UnicodeDecodeError):
        return ""
    return doc.strip().splitlines()[0] if doc else ""


def collect_jobs(with_network: bool) -> list[dict]:
    jobs: list[dict] = []
    for folder in SCRIPT_FOLDERS:
        for path in sorted((ROOT / folder).rglob("*.py")):
            jobs.append({"kind": "script", "path": path})
    for rel in STOCK_OFFLINE + (STOCK_NETWORK if with_network else []):
        jobs.append({"kind": "script", "path": ROOT / rel})
    jobs.append({"kind": "pytest", "path": ROOT / PYTEST_TARGET})
    return jobs


def command_for(job: dict) -> list[str]:
    if job["kind"] == "pytest":
        return [sys.executable, "-m", "pytest", "-q", str(job["path"])]
    return [sys.executable, str(job["path"])]


def workdir_for(job: dict) -> Path:
    if job["kind"] == "pytest":
        return ROOT / "quantum-computing-portfolio"
    return job["path"].parent


def scrub(text: str) -> str:
    """Hide machine-specific paths so the report can be shared."""
    for real, shown in ((str(ROOT), "<repo>"), (sys.prefix, "<venv>"),
                        (str(Path.home()), "~")):
        text = text.replace(real, shown)
    return text


def fence(text: str) -> str:
    text = scrub(text).rstrip("\n")
    return "```text\n" + (text if text else "(no output)") + "\n```\n"


def run_job(job: dict, timeout: int) -> dict:
    env = dict(os.environ, MPLBACKEND="Agg", PYTHONUNBUFFERED="1")
    start = time.time()
    try:
        proc = subprocess.run(
            command_for(job),
            cwd=workdir_for(job),
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        status = "PASS" if proc.returncode == 0 else f"FAIL (exit code {proc.returncode})"
        out, err = proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as exc:
        status = f"TIMEOUT (> {timeout}s)"
        out = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        err = exc.stderr.decode() if isinstance(exc.stderr, bytes) else (exc.stderr or "")
    return {"status": status, "seconds": time.time() - start, "stdout": out, "stderr": err}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Markdown file to write")
    parser.add_argument("--timeout", type=int, default=600, help="seconds allowed per script")
    parser.add_argument("--only", help="run only jobs whose relative path contains this text")
    parser.add_argument("--with-network", action="store_true", help="include stock-analyzer scripts that need internet")
    parser.add_argument("--list", action="store_true", help="list the jobs and exit")
    args = parser.parse_args()

    jobs = collect_jobs(args.with_network)
    if args.only:
        jobs = [j for j in jobs if args.only in str(j["path"].relative_to(ROOT))]
    if not jobs:
        print("No matching scripts.")
        return 1

    if args.list:
        for i, job in enumerate(jobs, 1):
            print(f"{i:2d}. {job['path'].relative_to(ROOT)}" + ("  (pytest)" if job["kind"] == "pytest" else ""))
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as md:
        md.write("# Run results\n\n")
        md.write(f"- Started: {datetime.now():%Y-%m-%d %H:%M:%S}\n")
        md.write(f"- Python: {platform.python_version()} (`{scrub(sys.executable)}`)\n")
        md.write(f"- Platform: {platform.system()} {platform.machine()}\n")
        md.write(f"- Scripts to run: {len(jobs)} (timeout {args.timeout}s each)\n\n")
        md.flush()

        results = []
        for i, job in enumerate(jobs, 1):
            rel = job["path"].relative_to(ROOT)
            cmd_text = "python -m pytest -q " + str(rel) if job["kind"] == "pytest" else f"python {rel}"
            print(f"[{i}/{len(jobs)}] {rel} ...", end=" ", flush=True)
            res = run_job(job, args.timeout)
            print(f"{res['status']} ({res['seconds']:.1f}s)", flush=True)
            results.append((rel, res))

            description = "" if job["kind"] == "pytest" else first_doc_line(job["path"])
            md.write(f"## {i}. `{rel}`\n\n")
            if description:
                md.write(f"{description}\n\n")
            md.write(f"- Command: `{cmd_text}` (run in `{workdir_for(job).relative_to(ROOT) or '.'}`)\n")
            md.write(f"- Status: **{res['status']}**\n")
            md.write(f"- Time: {res['seconds']:.1f} s\n\n")
            md.write("**Output**\n\n" + fence(res["stdout"]) + "\n")
            if res["stderr"].strip():
                md.write("**Errors / warnings (stderr)**\n\n" + fence(res["stderr"]) + "\n")
            md.flush()

        passed = sum(r["status"] == "PASS" for _, r in results)
        md.write("---\n\n## Summary\n\n| # | Script | Status | Time (s) |\n|---|---|---|---|\n")
        for i, (rel, res) in enumerate(results, 1):
            md.write(f"| {i} | `{rel}` | {res['status']} | {res['seconds']:.1f} |\n")
        md.write(f"\n**{passed} of {len(results)} passed.** Finished {datetime.now():%Y-%m-%d %H:%M:%S}.\n")

    print(f"\n{passed} of {len(results)} passed. Results written to {args.output.relative_to(ROOT)}")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
