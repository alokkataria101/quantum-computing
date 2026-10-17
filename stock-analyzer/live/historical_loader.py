"""
historical_loader.py

Fetches N trading days of 5-minute bars for a symbol from Yahoo Finance
and caches the result to disk (Parquet).

Yahoo Finance supports 5-min data up to ~60 calendar days back.
For 100 trading days (~5 months) we fetch in chunks of 55 calendar days
and stitch them together.

Cache key: symbol + interval + start_date + end_date
Cache path: data/hist_cache/<SYMBOL>_5m_<start>_<end>.parquet

Version : 5.3.0
"""

from __future__ import annotations

from datetime import date, timedelta
from pathlib  import Path

import pandas as pd
import yfinance as yf

from live.trading_calendar import previous_trading_days, is_trading_day
from config import CACHE_DIR

_HIST_DIR = CACHE_DIR / "hist_cache"
_HIST_DIR.mkdir(parents=True, exist_ok=True)

# Yahoo Finance max lookback per call for 5-min data (calendar days)
_YF_MAX_DAYS = 55


def _cache_path(symbol: str, interval: str, start: date, end: date) -> Path:
    return _HIST_DIR / f"{symbol}_{interval}_{start}_{end}.parquet"


def _fetch_chunk(ticker_str: str, interval: str,
                 start: date, end: date) -> pd.DataFrame:
    """Fetch one chunk from Yahoo Finance."""
    df = yf.download(
        ticker_str,
        start       = start.isoformat(),
        end         = (end + timedelta(days=1)).isoformat(),
        interval    = interval,
        progress    = False,
        auto_adjust = False,
    )
    if df is None or df.empty:
        return pd.DataFrame()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.dropna(subset=["Close"])
    df.index = pd.to_datetime(df.index, utc=True)
    return df


def load_trading_days(
    symbol       : str,
    n_days       : int  = 100,
    reference    : date | None = None,
    interval     : str  = "5m",
    use_cache    : bool = True,
) -> pd.DataFrame:
    """
    Load `n_days` trading days of `interval` bars ending before `reference`.

    Parameters
    ----------
    symbol    : str    NSE symbol without .NS
    n_days    : int    number of trading days (default 100)
    reference : date   anchor date — training ends the day before this
                       (defaults to today)
    interval  : str    "5m", "15m", "1m" (1m limited to 7 days)
    use_cache : bool   use on-disk Parquet cache

    Returns
    -------
    pd.DataFrame with columns Open, High, Low, Close, Volume
    index = DatetimeIndex (UTC)  ordered oldest → newest
    """
    if reference is None:
        from datetime import date as _date
        reference = _date.today()

    # Get the actual trading days we need
    trading_days = previous_trading_days(reference, n_days)
    if not trading_days:
        return pd.DataFrame()

    start_date = trading_days[0]
    end_date   = trading_days[-1]

    ticker_str = f"{symbol.upper()}.NS"

    # Check cache
    cpath = _cache_path(symbol.upper(), interval, start_date, end_date)
    if use_cache and cpath.exists():
        df = pd.read_parquet(cpath)
        df.index = pd.to_datetime(df.index, utc=True)
        return df

    # Fetch in chunks (Yahoo 5-min limit is ~55 calendar days)
    chunks : list[pd.DataFrame] = []
    cur    : date = start_date

    while cur <= end_date:
        chunk_end = min(cur + timedelta(days=_YF_MAX_DAYS - 1), end_date)
        chunk     = _fetch_chunk(ticker_str, interval, cur, chunk_end)
        if not chunk.empty:
            chunks.append(chunk)
        cur = chunk_end + timedelta(days=1)

    if not chunks:
        return pd.DataFrame()

    df = pd.concat(chunks)
    df = df[~df.index.duplicated(keep="last")]
    df = df.sort_index()

    # Filter to only rows on actual trading days
    df_dates = df.index.date
    df = df[[d in set(trading_days) for d in df_dates]]

    # Cache to disk
    if use_cache:
        df.to_parquet(cpath)

    return df


def load_single_day(
    symbol   : str,
    day      : date,
    interval : str = "5m",
) -> pd.DataFrame:
    """
    Load all intraday bars for a single trading day.

    Parameters
    ----------
    symbol   : str
    day      : date
    interval : str

    Returns
    -------
    pd.DataFrame  ordered 9:15 → 15:30 IST
    """
    ticker_str = f"{symbol.upper()}.NS"
    df = _fetch_chunk(ticker_str, interval, day, day)
    if df.empty:
        return df
    # Filter to this day only
    df = df[df.index.date == day]
    return df.sort_index()
