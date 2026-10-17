"""
data_loader.py

Downloads and prepares NSE stock data.

Version : 2.6.0

Features:
- Yahoo Finance data source
- MultiIndex handling
- Local CSV caching
- Logging
"""

from __future__ import annotations

import os

import pandas as pd
import yfinance as yf

from logger import get_logger


logger = get_logger()


CACHE_DIR = "data"



class DataLoaderError(Exception):
    """
    Custom exception for data loading problems.
    """
    pass



def _flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Handles newer yfinance MultiIndex columns.

    Example:

    ('Open','RELIANCE.NS')

    becomes:

    Open
    """

    if isinstance(df.columns, pd.MultiIndex):

        df.columns = (
            df.columns
            .get_level_values(0)
        )

    return df



def _get_cache_file(symbol: str, days: int):

    os.makedirs(
        CACHE_DIR,
        exist_ok=True
    )

    return os.path.join(
        CACHE_DIR,
        f"{symbol}_{days}.csv"
    )



def load_stock_data(
        symbol: str,
        days: int = 180
) -> pd.DataFrame:


    symbol = symbol.upper().strip()

    ticker = f"{symbol}.NS"


    cache_file = _get_cache_file(
        symbol,
        days
    )


    #
    # Step 1:
    # Check local cache
    #

    if os.path.exists(cache_file):

        logger.info(
            f"Loading cached data: {cache_file}"
        )

        print(
            f"Loading cached data: {cache_file}"
        )

        df = pd.read_csv(
            cache_file,
            parse_dates=["Date"]
        )

        return df



    #
    # Step 2:
    # Download from Yahoo
    #

    logger.info(
        f"Downloading {ticker}"
    )


    print(
        f"\nDownloading {ticker} ({days} days)..."
    )


    try:

        df = yf.download(

            ticker,

            period=f"{days}d",

            interval="1d",

            auto_adjust=False,

            progress=False,

            threads=False
        )


    except Exception as ex:

        raise DataLoaderError(
            f"Download failed: {ex}"
        )



    if df.empty:

        raise DataLoaderError(

            f"No data found for {ticker}"

        )



    #
    # Step 3:
    # Fix yfinance columns
    #

    df = _flatten_columns(df)



    required_columns = [

        "Open",
        "High",
        "Low",
        "Close",
        "Volume"

    ]



    for column in required_columns:

        if column not in df.columns:

            raise DataLoaderError(

                f"Missing column: {column}"

            )



    df = df[required_columns].copy()



    #
    # Step 4:
    # Prepare data types
    #

    df.reset_index(
        inplace=True
    )


    df["Open"] = (
        df["Open"]
        .astype(float)
    )


    df["High"] = (
        df["High"]
        .astype(float)
    )


    df["Low"] = (
        df["Low"]
        .astype(float)
    )


    df["Close"] = (
        df["Close"]
        .astype(float)
    )


    df["Volume"] = (
        df["Volume"]
        .astype(int)
    )



    df.sort_values(
        "Date",
        inplace=True
    )


    df.reset_index(
        drop=True,
        inplace=True
    )



    #
    # Step 5:
    # Save cache
    #

    df.to_csv(

        cache_file,

        index=False

    )


    logger.info(

        f"Saved cache: {cache_file}"

    )


    print(
        f"Downloaded {len(df)} trading days."
    )


    return df