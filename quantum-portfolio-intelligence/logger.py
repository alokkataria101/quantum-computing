"""
Logging utility
"""

import logging
import os


def get_logger():

    os.makedirs(
        "logs",
        exist_ok=True
    )


    logging.basicConfig(

        filename="logs/stock_analyzer.log",

        level=logging.INFO,

        format=
        "%(asctime)s %(levelname)s %(message)s"

    )


    return logging.getLogger(
        "stock-analyzer"
    )