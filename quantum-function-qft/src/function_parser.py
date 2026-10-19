"""function_parser.py – safe evaluation of user-supplied f(x) expressions.

Public API
----------
parse_and_sample(expr, x_start, x_end, n_points) -> SampledSignal
extract_known_components(expr)                    -> list[KnownComponent]
SAMPLE_FUNCTIONS                                  -> list[SampleFunction]
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

# ─────────────────────────────────────────────────────────────────────────────
# Safe evaluation namespace
# ─────────────────────────────────────────────────────────────────────────────

_SAFE_NAMESPACE: dict = {
    "__builtins__": {},
    # trig
    "sin": np.sin, "cos": np.cos, "tan": np.tan,
    "arcsin": np.arcsin, "arccos": np.arccos, "arctan": np.arctan,
    # exp / log
    "exp": np.exp, "log": np.log, "log10": np.log10, "log2": np.log2,
    "sqrt": np.sqrt, "abs": np.abs,
    # constants
    "pi": math.pi, "e": math.e,
    # numpy itself for power-users
    "np": np,
}


# ─────────────────────────────────────────────────────────────────────────────
# Data structures
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class KnownComponent:
    """One sinusoidal term extracted analytically from the expression."""
    amplitude: float        # coefficient A in A·sin(ω·x + φ)
    angular_freq: float     # ω  (rad / x-unit)
    phase: float            # φ  (rad)
    freq_per_unit: float    # f = ω / (2π)  cycles per x-unit
    label: str              # human-readable e.g. "2·sin(5x)"


@dataclass
class SampledSignal:
    """Container for sampled function data and metadata."""
    expr: str
    x: np.ndarray                             # sample positions
    y: np.ndarray                             # f(x) values
    x_start: float
    x_end: float
    n_points: int
    dx: float                                 # sample spacing
    sample_rate: float                        # 1 / dx  (samples per x-unit)
    known_components: list[KnownComponent] = field(default_factory=list)

    # ── derived quantities ────────────────────────────────────────────────────
    @property
    def dc_offset(self) -> float:
        return float(np.mean(self.y))

    def known_freq_bins(self, M: int) -> list[tuple[KnownComponent, float]]:
        """
        Map each known component to its expected DFT bin index (float).
        bin_index = f_cycles_per_unit × x_span   (for a DFT on [x_start, x_end])
        """
        x_span = self.x_end - self.x_start
        return [(c, c.freq_per_unit * x_span) for c in self.known_components]


@dataclass
class SampleFunction:
    """A preset function shown in the gallery."""
    name: str
    expr: str
    x_start: float
    x_end: float
    n_points: int
    difficulty: str          # "Easy to verify" | "Moderate" | "Advanced"
    description: str
    why_works: list[str]


# ─────────────────────────────────────────────────────────────────────────────
# Sample function gallery
# ─────────────────────────────────────────────────────────────────────────────

SAMPLE_FUNCTIONS: list[SampleFunction] = [
    SampleFunction(
        name="Sample 1 — Recommended starting point",
        expr="2*sin(2*pi*3*x) + 1.5*sin(2*pi*7*x + pi/4) + 2",
        x_start=0.0, x_end=1.0, n_points=256,
        difficulty="Easy to verify",
        description="Two sinusoids at 3 and 7 cycles/unit with a DC offset of 2.",
        why_works=[
            "Frequencies of **3 and 7 cycles per unit interval** fall exactly on DFT bins 3 and 7.",
            "Interval [0, 1] with 256 points: both frequencies are integer multiples of 1/x_span.",
            "256 = 2⁸ → no padding needed for the QFT.",
            "The constant offset creates a DC component, observable separately from sinusoidal peaks.",
        ],
    ),
    SampleFunction(
        name="Sample 2 — Two clean sinusoids with DC",
        expr="2*sin(2*pi*3*x) + 1.5*sin(2*pi*7*x + pi/4) + 2",
        x_start=0.0, x_end=1.0, n_points=256,
        difficulty="Moderate",
        description=(
            "Two sinusoidal components at f = 3 and 7 cycles/unit with a DC offset of 2. "
            "Amplitudes 2 and 1.5, phase shift π/4 on the 7 Hz component."
        ),
        why_works=[
            "Frequencies 3 and 7 cycles/unit land exactly on DFT bins (integer × 1/x_span) → zero spectral leakage.",
            "With N=256 points over [0,1], bin k corresponds to f = k cycles/unit; peaks at k=3 and k=7.",
            "DC offset 2 dominates bin 0; mean-centring removes it cleanly before QFT.",
            "Phase offset π/4 on f=7 component is visible in the complex spectrum but not the power spectrum.",
        ],
    ),
    SampleFunction(
        name="Sample 3 — Single clean sinusoid",
        expr="3*sin(2*pi*5*x)",
        x_start=0.0, x_end=1.0, n_points=64,
        difficulty="Easy to verify",
        description="Pure sinusoid at 5 cycles/unit, amplitude 3, no DC offset.",
        why_works=[
            "Single frequency at bin 5 (positive) and bin 59 (negative mirror).",
            "Zero DC offset → bin 0 power = 0.",
            "64 = 2⁶ → exactly 6 qubits, no padding.",
            "Power spectrum has exactly two non-zero bins (for real input).",
        ],
    ),
    SampleFunction(
        name="Sample 4 — Four components, integer bins",
        expr="sin(2*pi*2*x) + 2*sin(2*pi*8*x) + 0.5*sin(2*pi*15*x) + 1.5*cos(2*pi*20*x)",
        x_start=0.0, x_end=1.0, n_points=128,
        difficulty="Moderate",
        description="Four components at bins 2, 8, 15, 20. Amplitude ratios 1:2:0.5:1.5.",
        why_works=[
            "All four frequencies are exact integers → no spectral leakage.",
            "cos = sin(x + π/2) → same DFT bin, different phase.",
            "128 = 2⁷ → exactly 7 qubits, no padding.",
            "Power ordering 2:1.5:1:0.5 at bins 8:20:2:15 is easy to verify.",
        ],
    ),
    SampleFunction(
        name="Sample 5 — Advanced: close frequencies + noise",
        expr="sin(2*pi*10*x) + sin(2*pi*11*x) + 0.3*sin(2*pi*50*x)",
        x_start=0.0, x_end=1.0, n_points=256,
        difficulty="Advanced",
        description=(
            "Two near-identical frequencies (10 and 11 cycles/unit) plus a weak high-frequency component. "
            "Tests frequency resolution."
        ),
        why_works=[
            "Frequency resolution = 1/x_span = 1 cycle/unit → bins 10 and 11 are just resolvable.",
            "Weak component at bin 50 should still appear above noise floor.",
            "Equal amplitudes → two equal dominant peaks in the spectrum.",
            "No DC offset → bin 0 = 0.",
        ],
    ),
]


# ─────────────────────────────────────────────────────────────────────────────
# Expression parser: extract known sinusoidal components
# ─────────────────────────────────────────────────────────────────────────────

# Matches patterns like:  A*sin(ω*x + φ)  or  A*cos(ω*x)
# This is a best-effort heuristic for display; does not affect numerical results.
_SINCOS_RE = re.compile(
    r"""
    (?P<sign>[+-])?                        # optional leading sign
    \s*
    (?P<amp>[0-9]*\.?[0-9]+)\*?           # amplitude coefficient (optional)
    \s*
    (?P<func>sin|cos)                      # sin or cos
    \s*\(\s*
    (?P<omega>[0-9]*\.?[0-9]*\*?(?:2\*pi\*)?[0-9]*\.?[0-9]*)  # omega part
    \s*\*\s*x                              # * x
    (?:\s*[+-]\s*[^)]+)?                   # optional phase
    \s*\)
    """,
    re.VERBOSE | re.IGNORECASE,
)


def extract_known_components(expr: str) -> list[KnownComponent]:
    """
    Best-effort extraction of sinusoidal terms from a string expression.
    Returns a list of KnownComponent for display and ground-truth comparison.
    Falls back gracefully if parsing is incomplete.
    """
    components: list[KnownComponent] = []

    # Replace symbolic constants so eval works
    expr_eval = (
        expr
        .replace("pi", str(math.pi))
        .replace("e", str(math.e))
    )

    # Walk through additive / subtractive terms
    # Split on + or - that are NOT inside parentheses
    depth = 0
    terms: list[str] = []
    current = ""
    i = 0
    while i < len(expr):
        c = expr[i]
        if c == "(":
            depth += 1
            current += c
        elif c == ")":
            depth -= 1
            current += c
        elif c in "+-" and depth == 0 and i > 0:
            if current.strip():
                terms.append(current.strip())
            current = c
        else:
            current += c
        i += 1
    if current.strip():
        terms.append(current.strip())

    for term in terms:
        sign = -1.0 if term.startswith("-") else 1.0
        t = term.lstrip("+-").strip()

        # Check for sin/cos
        func_match = re.search(r"(sin|cos)\s*\((.+)\)", t, re.IGNORECASE)
        if not func_match:
            continue

        func_name = func_match.group(1).lower()

        # Extract amplitude (coefficient before sin/cos)
        before = t[: func_match.start()].strip().rstrip("*").strip()
        try:
            amp = float(eval(before, {"pi": math.pi, "e": math.e})) if before else 1.0
        except Exception:
            amp = 1.0
        amp *= sign

        # Parse the argument: ω*x + φ
        arg_str = func_match.group(2).strip()
        # Split arg at x
        parts = re.split(r"\*\s*x|x\s*\*", arg_str, maxsplit=1)
        omega_str = parts[0].strip() if parts else "1"
        phase_str = parts[1].strip() if len(parts) > 1 else "0"

        try:
            omega = float(eval(omega_str.replace("pi", str(math.pi)), {}))
        except Exception:
            continue
        try:
            phase = float(eval(phase_str.replace("pi", str(math.pi)), {})) if phase_str else 0.0
        except Exception:
            phase = 0.0

        # cos(ωx+φ) = sin(ωx + φ + π/2)
        if func_name == "cos":
            phase += math.pi / 2

        freq = abs(omega) / (2 * math.pi)
        label = f"{amp:+.3g}·{func_name}({omega:.4g}·x)"
        components.append(KnownComponent(
            amplitude=amp,
            angular_freq=omega,
            phase=phase,
            freq_per_unit=freq,
            label=label,
        ))

    return components


# ─────────────────────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────────────────────

def parse_and_sample(
    expr: str,
    x_start: float = 0.0,
    x_end: float = 1.0,
    n_points: int = 256,
) -> SampledSignal:
    """
    Evaluate f(x) = expr on n_points equally-spaced points in [x_start, x_end].

    Parameters
    ----------
    expr     : Python expression string using variable x.
               Allowed names: sin, cos, tan, exp, log, sqrt, abs, pi, e, np.
    x_start  : Left boundary of the domain.
    x_end    : Right boundary (inclusive endpoint).
    n_points : Number of sample points (power of two recommended).

    Returns
    -------
    SampledSignal with x, y arrays and known sinusoidal components.

    Raises
    ------
    ValueError : expression is empty, domain is invalid, or evaluation fails.
    """
    expr = expr.strip()
    if not expr:
        raise ValueError("Function expression must not be empty.")
    if x_end <= x_start:
        raise ValueError(f"x_end ({x_end}) must be greater than x_start ({x_start}).")
    if n_points < 2:
        raise ValueError("n_points must be at least 2.")

    x = np.linspace(x_start, x_end, n_points)
    ns = dict(_SAFE_NAMESPACE)
    ns["x"] = x

    try:
        y = np.asarray(eval(expr, ns), dtype=np.float64)  # noqa: S307
    except Exception as exc:
        raise ValueError(
            f"Could not evaluate expression '{expr}': {exc}\n"
            "Allowed names: sin, cos, tan, exp, log, sqrt, abs, pi, e, np, x."
        ) from exc

    if y.shape != x.shape:
        raise ValueError(
            f"Expression did not return an array of shape {x.shape}. "
            f"Got shape {y.shape}. Make sure the expression uses 'x' as the variable."
        )
    if not np.all(np.isfinite(y)):
        raise ValueError("Expression produced non-finite values (NaN or Inf). Check for division by zero.")

    dx = float(x[1] - x[0])
    components = extract_known_components(expr)

    return SampledSignal(
        expr=expr,
        x=x,
        y=y,
        x_start=x_start,
        x_end=x_end,
        n_points=n_points,
        dx=dx,
        sample_rate=1.0 / dx,
        known_components=components,
    )
