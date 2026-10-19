"""data_loader.py – download and cache historical stock data from Yahoo Finance.

Public API
----------
load_stock_data(ticker, n_observations, use_adjusted_close, start_date, end_date,
                download_period, data_dir) -> DataBundle
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Data structures
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class DataBundle:
    """Container for the downloaded price series and associated metadata."""

    ticker: str
    series_label: str                  # "Close" or "Adj Close"
    prices: pd.Series                  # DatetimeIndex, float64
    first_date: date
    last_date: date
    n_requested: int
    n_downloaded: int
    n_missing_filled: int
    csv_path: Optional[Path] = None
    raw_df: pd.DataFrame = field(default_factory=pd.DataFrame)

    # ── convenience ──────────────────────────────────────────────────────────
    def summary(self) -> dict:
        return {
            "ticker": self.ticker,
            "series": self.series_label,
            "n_requested": self.n_requested,
            "n_downloaded": self.n_downloaded,
            "n_missing_filled": self.n_missing_filled,
            "first_date": str(self.first_date),
            "last_date": str(self.last_date),
            "csv_path": str(self.csv_path) if self.csv_path else None,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _next_power_of_two(n: int) -> int:
    """Return the smallest power of two >= n."""
    p = 1
    while p < n:
        p <<= 1
    return p


def _resolve_dates(
    n_observations: int,
    representation: str,
    start_date: Optional[str],
    end_date: Optional[str],
    download_period: str,
) -> tuple[Optional[str], Optional[str], str]:
    """
    Return (start, end, period) arguments for yfinance.

    If the user specified returns-based representations we need n+1 closes.
    """
    needs_extra = representation in ("returns", "centred_returns")
    n_needed = n_observations + (1 if needs_extra else 0)

    if start_date and end_date:
        return start_date, end_date, ""
    if start_date:
        return start_date, None, ""
    # Auto: assume ~252 trading days per year; request enough calendar days
    calendar_days = int(n_needed * 1.6) + 30
    auto_start = (datetime.today() - timedelta(days=calendar_days)).strftime("%Y-%m-%d")
    return auto_start, None, ""


# ─────────────────────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────────────────────

def load_stock_data(
    ticker: str,
    n_observations: int,
    use_adjusted_close: bool = False,
    representation: str = "centred_returns",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    download_period: str = "5y",
    data_dir: str = "data",
) -> DataBundle:
    """
    Download historical daily closing prices from Yahoo Finance.

    Parameters
    ----------
    ticker            : Yahoo Finance ticker symbol (e.g. "IBM").
    n_observations    : Number of price rows (or return rows) to use.
    use_adjusted_close: Use 'Adj Close' instead of 'Close'.
    representation    : Preprocessing mode – used to decide if n+1 prices needed.
    start_date        : ISO date string or None.
    end_date          : ISO date string or None.
    download_period   : yfinance period string used when no explicit dates given.
    data_dir          : Directory where CSV cache will be written.

    Returns
    -------
    DataBundle with prices, metadata, and CSV path.

    Raises
    ------
    ValueError  : ticker is empty, or no data returned, or too few observations.
    RuntimeError: download failed for any other reason.
    """
    ticker = ticker.strip().upper()
    if not ticker:
        raise ValueError("Ticker symbol must not be empty.")

    series_label = "Adj Close" if use_adjusted_close else "Close"

    start, end, period = _resolve_dates(
        n_observations, representation, start_date, end_date, download_period
    )

    logger.info("Downloading %s from Yahoo Finance …", ticker)
    try:
        raw = yf.download(
            ticker,
            start=start or None,
            end=end or None,
            period=period or None,
            auto_adjust=False,
            progress=False,
            multi_level_index=False,
        )
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"yfinance download failed for '{ticker}': {exc}") from exc

    if raw is None or raw.empty:
        raise ValueError(
            f"No data returned for ticker '{ticker}'. "
            "Check the symbol and your internet connection."
        )

    # ── normalise column access ───────────────────────────────────────────────
    raw.index = pd.to_datetime(raw.index)
    raw.sort_index(inplace=True)
    raw = raw[~raw.index.duplicated(keep="last")]

    if series_label not in raw.columns:
        available = list(raw.columns)
        raise ValueError(
            f"Column '{series_label}' not found in downloaded data. "
            f"Available columns: {available}"
        )

    prices_full: pd.Series = raw[series_label].dropna()

    # Determine how many price rows we actually need
    needs_extra = representation in ("returns", "centred_returns")
    n_needed = n_observations + (1 if needs_extra else 0)

    if len(prices_full) < n_needed:
        raise ValueError(
            f"Only {len(prices_full)} rows available for '{ticker}' but "
            f"{n_needed} are needed for {n_observations} observations "
            f"with representation='{representation}'. "
            "Try a longer date range or fewer observations."
        )

    prices = prices_full.iloc[-n_needed:]
    n_missing = int(prices_full.isna().sum())  # already dropped, kept for info

    # ── persist to CSV ────────────────────────────────────────────────────────
    Path(data_dir).mkdir(parents=True, exist_ok=True)
    csv_name = (
        f"{ticker}_{prices.index[0].strftime('%Y%m%d')}"
        f"_{prices.index[-1].strftime('%Y%m%d')}.csv"
    )
    csv_path = Path(data_dir) / csv_name

    save_df = raw.loc[prices.index, [c for c in ["Close", "Adj Close"] if c in raw.columns]]
    save_df.index.name = "Date"
    save_df.to_csv(csv_path)
    logger.info("Saved price data to %s", csv_path)

    return DataBundle(
        ticker=ticker,
        series_label=series_label,
        prices=prices,
        first_date=prices.index[0].date(),
        last_date=prices.index[-1].date(),
        n_requested=n_observations,
        n_downloaded=len(prices),
        n_missing_filled=n_missing,
        csv_path=csv_path,
        raw_df=save_df,
    )


def load_from_csv(csv_path: str, series_label: str = "Close") -> pd.Series:
    """Reload a previously saved price CSV for reproducibility experiments."""
    df = pd.read_csv(csv_path, index_col="Date", parse_dates=True)
    if series_label not in df.columns:
        raise ValueError(f"Column '{series_label}' not found in {csv_path}.")
    return df[series_label].dropna().sort_index()
