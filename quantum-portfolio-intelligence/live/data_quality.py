"""
data_quality.py

Stage 0 — Data Quality Validator.

Runs before any classical or quantum analysis to assess the health of
a downloaded bar dataset.  Poor-quality input should never flow silently
into the prediction pipeline — it corrupts quantum state encoding and
produces unreliable signals.

Checks performed
----------------
1. Stale bars        — O == H == L == C  AND  Volume == 0
2. Zero-volume bars  — Volume == 0  (but OHLC spread > 0)
3. Duplicate timestamps
4. Missing timestamps — expected grid gaps during market hours
5. Timestamp gaps    — consecutive bars separated by > 2× interval
6. Negative prices   — O / H / L / C < 0
7. NaN / null values — any OHLCV field is NaN
8. OHLC integrity    — High < Low  or  Close outside [Low, High]

Quality Score
-------------
  score = 100 × (1 − weighted_penalty_fraction)

Penalty weights (sum to 1.0):
  stale_bars        0.35
  zero_volume       0.10
  duplicates        0.10
  timestamp_gaps    0.15
  negative_prices   0.15
  nan_values        0.10
  ohlc_integrity    0.05

A score ≥ 90 is considered HIGH quality.
A score 70–89 is MEDIUM — predictions are less reliable.
A score < 70 is LOW — fallback to coarser interval recommended.

Version : 11.0.1
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field

from live.feed_base import Bar


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_INTERVAL_MINUTES: dict[str, int] = {
    "1m": 1, "2m": 2, "5m": 5, "10m": 10,
    "15m": 15, "30m": 30, "60m": 60, "1h": 60,
}

_PENALTY_WEIGHTS = {
    "stale_bars"       : 0.35,
    "zero_volume"      : 0.10,
    "duplicates"       : 0.10,
    "timestamp_gaps"   : 0.15,
    "negative_prices"  : 0.15,
    "nan_values"       : 0.10,
    "ohlc_integrity"   : 0.05,
}

# NSE market hours (IST)
_NSE_OPEN  = datetime.time(9, 15)
_NSE_CLOSE = datetime.time(15, 30)


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class DataQualityReport:
    """
    Complete data quality report for one bar dataset.

    Attributes
    ----------
    n_bars            : int    total bars examined
    n_stale           : int    bars where O==H==L==C and Volume==0
    n_zero_volume     : int    bars where Volume==0 (excluding stale)
    n_duplicates      : int    duplicate timestamps
    n_gaps            : int    large time gaps (> 2× interval) during market hours
    n_negative        : int    bars with any negative OHLCV value
    n_nan             : int    bars with NaN in any OHLCV field
    n_ohlc_bad        : int    bars where High < Low or Close outside [Low, High]
    score             : float  0–100 quality score
    grade             : str    "HIGH" / "MEDIUM" / "LOW"
    issues            : list[str]  human-readable issue descriptions
    effective_interval: str    interval string used for gap detection
    """
    n_bars            : int   = 0
    n_stale           : int   = 0
    n_zero_volume     : int   = 0
    n_duplicates      : int   = 0
    n_gaps            : int   = 0
    n_negative        : int   = 0
    n_nan             : int   = 0
    n_ohlc_bad        : int   = 0
    score             : float = 100.0
    grade             : str   = "HIGH"
    issues            : list  = field(default_factory=list)
    effective_interval: str   = "5m"

    # ------------------------------------------------------------------
    def is_usable(self, min_score: float = 70.0) -> bool:
        return self.score >= min_score

    def summary_lines(self) -> list[str]:
        """Return lines suitable for st.markdown() display."""
        tick = "✓"
        cross = "✗"
        lines = [
            f"{'Data Quality Score':25s}: **{self.score:.0f}%** ({self.grade})",
            f"{'Bars examined':25s}: {self.n_bars}",
            f"{tick if self.n_stale     == 0 else cross} {'Stale bars (O=H=L=C, Vol=0)':30s}: {self.n_stale}",
            f"{tick if self.n_zero_volume == 0 else cross} {'Zero-volume bars':30s}: {self.n_zero_volume}",
            f"{tick if self.n_duplicates == 0 else cross} {'Duplicate timestamps':30s}: {self.n_duplicates}",
            f"{tick if self.n_gaps       == 0 else cross} {'Timestamp gaps':30s}: {self.n_gaps}",
            f"{tick if self.n_negative   == 0 else cross} {'Negative prices/volumes':30s}: {self.n_negative}",
            f"{tick if self.n_nan        == 0 else cross} {'NaN / null values':30s}: {self.n_nan}",
            f"{tick if self.n_ohlc_bad   == 0 else cross} {'OHLC integrity errors':30s}: {self.n_ohlc_bad}",
        ]
        if self.issues:
            lines.append("")
            lines.append("**Issues detected:**")
            for iss in self.issues:
                lines.append(f"• {iss}")
        return lines


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------

class DataQualityValidator:
    """
    Validates a list of Bar objects and returns a DataQualityReport.

    Parameters
    ----------
    bars     : list[Bar]
    interval : str        "1m", "5m", etc.  used for gap detection
    """

    def __init__(self, bars: list[Bar], interval: str = "5m"):
        self.bars     = bars
        self.interval = interval
        self._int_min = _INTERVAL_MINUTES.get(interval, 5)

    # ------------------------------------------------------------------

    def validate(self) -> DataQualityReport:
        """Run all checks and return a DataQualityReport."""
        bars = self.bars
        n    = len(bars)
        rep  = DataQualityReport(n_bars=n, effective_interval=self.interval)

        if n == 0:
            rep.score = 0.0
            rep.grade = "LOW"
            rep.issues.append("No bars downloaded — empty dataset.")
            return rep

        # ── 1. Stale bars
        stale_idx = [
            i for i, b in enumerate(bars)
            if b.open == b.high == b.low == b.close and b.volume == 0
        ]
        rep.n_stale = len(stale_idx)
        if rep.n_stale:
            rep.issues.append(
                f"{rep.n_stale} stale bar(s) detected (O=H=L=C, Volume=0). "
                "Yahoo Finance may be returning placeholder data."
            )

        # ── 2. Zero-volume bars (excluding stale — already counted)
        zero_vol = [
            i for i, b in enumerate(bars)
            if b.volume == 0 and i not in set(stale_idx)
        ]
        rep.n_zero_volume = len(zero_vol)
        if rep.n_zero_volume:
            rep.issues.append(
                f"{rep.n_zero_volume} zero-volume bar(s) (OHLC spread present, "
                "no volume). May indicate illiquid periods."
            )

        # ── 3. Duplicate timestamps
        seen_ts   = {}
        dup_count = 0
        for b in bars:
            ts = str(b.timestamp)[:19]
            if ts in seen_ts:
                dup_count += 1
            seen_ts[ts] = True
        rep.n_duplicates = dup_count
        if dup_count:
            rep.issues.append(
                f"{dup_count} duplicate timestamp(s) found — "
                "data may have been fetched twice or feed returned overlapping bars."
            )

        # ── 4. Timestamp gaps (> 2× interval between consecutive bars,
        #       only checked during expected market hours)
        gap_count = 0
        threshold = datetime.timedelta(minutes=self._int_min * 2)
        for i in range(1, n):
            try:
                t_prev = _parse_ts(str(bars[i - 1].timestamp))
                t_curr = _parse_ts(str(bars[i].timestamp))
                if t_prev is None or t_curr is None:
                    continue
                diff = t_curr - t_prev
                if diff > threshold:
                    # Only flag if previous bar was during market hours
                    t_prev_naive = t_prev.replace(tzinfo=None).time()
                    if _NSE_OPEN <= t_prev_naive <= _NSE_CLOSE:
                        gap_count += 1
            except Exception:
                pass
        rep.n_gaps = gap_count
        if gap_count:
            rep.issues.append(
                f"{gap_count} timestamp gap(s) > {self._int_min * 2} min during "
                "market hours — bars may be missing."
            )

        # ── 5. Negative prices / volumes
        neg_count = sum(
            1 for b in bars
            if b.open < 0 or b.high < 0 or b.low < 0 or b.close < 0 or b.volume < 0
        )
        rep.n_negative = neg_count
        if neg_count:
            rep.issues.append(
                f"{neg_count} bar(s) with negative OHLCV value(s) — corrupt data."
            )

        # ── 6. NaN values (float NaN check)
        nan_count = 0
        for b in bars:
            for v in (b.open, b.high, b.low, b.close, b.volume):
                try:
                    if v != v:   # NaN != NaN is True
                        nan_count += 1
                        break
                except Exception:
                    nan_count += 1
                    break
        rep.n_nan = nan_count
        if nan_count:
            rep.issues.append(
                f"{nan_count} bar(s) with NaN in OHLCV fields — "
                "incomplete download, dropped by analysis."
            )

        # ── 7. OHLC integrity
        ohlc_bad = sum(
            1 for b in bars
            if b.high < b.low
            or b.close < b.low - 0.001
            or b.close > b.high + 0.001
        )
        rep.n_ohlc_bad = ohlc_bad
        if ohlc_bad:
            rep.issues.append(
                f"{ohlc_bad} bar(s) failed OHLC integrity (High < Low or "
                "Close outside [Low, High])."
            )

        # ── Compute score
        penalties: dict[str, float] = {
            "stale_bars"     : min(rep.n_stale        / max(n, 1), 1.0),
            "zero_volume"    : min(rep.n_zero_volume   / max(n, 1), 1.0),
            "duplicates"     : min(rep.n_duplicates    / max(n, 1), 1.0),
            "timestamp_gaps" : min(rep.n_gaps          / max(n, 1), 1.0),
            "negative_prices": min(rep.n_negative      / max(n, 1), 1.0),
            "nan_values"     : min(rep.n_nan           / max(n, 1), 1.0),
            "ohlc_integrity" : min(rep.n_ohlc_bad      / max(n, 1), 1.0),
        }

        total_penalty = sum(
            _PENALTY_WEIGHTS[k] * v for k, v in penalties.items()
        )
        rep.score = round(max(0.0, (1.0 - total_penalty) * 100.0), 1)

        if rep.score >= 90:
            rep.grade = "HIGH"
        elif rep.score >= 70:
            rep.grade = "MEDIUM"
        else:
            rep.grade = "LOW"

        return rep


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _parse_ts(ts_str: str):
    """Parse a timestamp string to datetime. Returns None on failure."""
    try:
        import dateutil.parser as dtp
        return dtp.parse(ts_str)
    except Exception:
        return None
