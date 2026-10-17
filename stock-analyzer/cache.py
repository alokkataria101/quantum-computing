import os


CACHE_DIR="data"


def cache_file(symbol,days):

    os.makedirs(
        CACHE_DIR,
        exist_ok=True
    )

    return (
        f"{CACHE_DIR}/"
        f"{symbol}_{days}.csv"
    )
