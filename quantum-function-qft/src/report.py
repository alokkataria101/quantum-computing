"""report.py – generate a self-contained HTML research report."""

from __future__ import annotations

import base64, io
from pathlib import Path
from typing import Optional
import matplotlib.pyplot as plt
from .interpretation import InterpretationResult


def _b64(fig: plt.Figure, dpi: int = 110) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()


def _img(fig: Optional[plt.Figure], caption: str = "") -> str:
    if fig is None:
        return ""
    cap = f"<p><em>{caption}</em></p>" if caption else ""
    return f'<img src="data:image/png;base64,{_b64(fig)}" alt="{caption}"/>{cap}'


_CSS = """
body{font-family:"Segoe UI",system-ui,sans-serif;max-width:920px;margin:40px auto;
     padding:0 20px;color:#1f2328;line-height:1.65}
h1{color:#0f3460;border-bottom:2px solid #e5e7eb;padding-bottom:6px}
h2{color:#16213e;margin-top:2em}
pre{background:#f7f8fa;border:1px solid #e5e7eb;border-radius:6px;
    padding:12px 16px;overflow-x:auto;font-size:.84em;white-space:pre-wrap}
img{max-width:100%;border:1px solid #e5e7eb;border-radius:4px;margin:10px 0}
table{border-collapse:collapse;width:100%;margin:1em 0;font-size:.88em}
th,td{border:1px solid #e5e7eb;padding:5px 9px;text-align:left}
th{background:#f0f4ff}
.ok{background:#e6f9ee;border-left:4px solid #28a745;padding:8px 12px;
    margin:1em 0;border-radius:0 4px 4px 0}
.warn{background:#fff8e1;border-left:4px solid #f0ad4e;padding:8px 12px;
      margin:1em 0;border-radius:0 4px 4px 0}
footer{margin-top:3em;border-top:1px solid #e5e7eb;padding-top:8px;
       font-size:.78em;color:#57606a;text-align:center}
"""


def generate_report(
    interp: InterpretationResult,
    figures: Optional[dict] = None,
    output_path: Optional[str] = None,
) -> Path:
    figs = figures or {}
    if output_path is None:
        Path("outputs").mkdir(parents=True, exist_ok=True)
        output_path = "outputs/function_qft_report.html"

    agree_cls = "ok" if interp.max_qft_dft_deviation < 1e-3 else "warn"

    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"/>
<title>Quantum Fourier Analysis — Function Report</title>
<style>{_CSS}</style></head><body>
<h1>⚛️ Quantum Fourier Analysis of f(x)</h1>

<h2>1. Setup</h2>
<pre>{interp.setup_summary}</pre>
{_img(figs.get("signal"), "Sampled function f(x)")}

<h2>2. Known analytical components</h2>
<pre>{interp.ground_truth_narrative}</pre>

<h2>3. Preprocessed amplitude vector ψ</h2>
{_img(figs.get("amplitude"), "L2-normalised amplitude vector ψ")}

<h2>4. Classical DFT power spectrum</h2>
<pre>{interp.dft_narrative}</pre>
{_img(figs.get("dft"), "Classical DFT power spectrum with known-frequency annotations")}

<h2>5. QFT results</h2>
<pre>{interp.qft_narrative}</pre>
{_img(figs.get("qft"), "QFT vs DFT comparison and deviation")}

<h2>6. Peak match table</h2>
{_img(figs.get("table"), "Detected peaks vs. known analytical components")}

<h2>7. Dashboard</h2>
{_img(figs.get("dashboard"), "Full analysis dashboard")}

<h2>8. Spectral agreement</h2>
<div class="{agree_cls}">{interp.qft_agreement}</div>

<h2>9. Conclusion</h2>
<pre>{interp.conclusion}</pre>

<footer>quantum-function-qft &nbsp;|&nbsp; Educational demonstration — not financial advice</footer>
</body></html>"""

    p = Path(output_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(html, encoding="utf-8")
    return p
