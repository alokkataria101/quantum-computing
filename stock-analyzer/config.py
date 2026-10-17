"""
config.py

Central configuration for the
Quantum Portfolio Intelligence Platform (QPIP).

Version : 11.0.1
"""

import os
from pathlib import Path

# ==========================================================
# Application Version & Branding
# ==========================================================

APP_VERSION    = "11.0.1"
APP_NAME       = "Quantum Portfolio Intelligence Platform"
APP_SHORT_NAME = "QPIP"
APP_TAGLINE    = "Quantum-powered portfolio insights for faster risk analysis and better investment decisions."

# ==========================================================
# 5-Level Signal Thresholds  (Track 1 — Intraday Assistant)
# ==========================================================

# P(Up) ≥ STRONG_BUY_P_UP AND confidence ≥ STRONG_SIGNAL_CONF → STRONG BUY
STRONG_BUY_P_UP    = 0.65
# P(Up) ≥ BUY_P_UP → BUY
BUY_P_UP           = 0.55
# P(Up) ≤ SELL_P_UP → SELL
SELL_P_UP          = 0.45
# P(Up) ≤ STRONG_SELL_P_UP AND confidence ≥ STRONG_SIGNAL_CONF → STRONG SELL
STRONG_SELL_P_UP   = 0.35
# Minimum confidence required for STRONG labels
STRONG_SIGNAL_CONF = 0.55

# ==========================================================
# Project Directories
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parent

OUTPUT_DIR = PROJECT_ROOT / "output"

OUTPUT_CHART_DIR = OUTPUT_DIR / "charts"

OUTPUT_REPORT_DIR = OUTPUT_DIR / "reports"

CACHE_DIR = PROJECT_ROOT / "data"

LOG_DIR = PROJECT_ROOT / "logs"

# ==========================================================
# Output Files
# ==========================================================

CSV_SUFFIX = "_report.csv"

JSON_SUFFIX = "_summary.json"

PRICE_CHART_SUFFIX = "_price.png"

RETURN_CHART_SUFFIX = "_returns.png"

VOLUME_CHART_SUFFIX = "_volume.png"

PORTFOLIO_JSON = "portfolio_complete.json"

PORTFOLIO_MARKDOWN = "Portfolio_Report.md"

AI_REPORT_MARKDOWN = "AI_Report.md"

AI_REPORT_JSON = "AI_Report.json"

AI_PROMPT_FILE = "watsonx_prompt.txt"

# ==========================================================
# Analysis Settings
# ==========================================================

DEFAULT_ANALYSIS_DAYS = 365

PRICE_MOVING_AVERAGES = [

    20,

    50,

    100

]

# ==========================================================
# Chart Settings
# ==========================================================

FIGURE_SIZE = (

    14,

    7

)

DPI = 120

# ==========================================================
# Yahoo Finance Settings
# ==========================================================

YFINANCE_INTERVAL = "1d"

AUTO_ADJUST = False

DOWNLOAD_THREADS = False

# ==========================================================
# Logging
# ==========================================================

LOG_FILE = LOG_DIR / "stock_analyzer.log"

LOG_LEVEL = "INFO"

# ==========================================================
# Cache
# ==========================================================

ENABLE_CACHE = True

CACHE_EXPIRY_HOURS = 24

# ==========================================================
# Report Formatting
# ==========================================================

PERCENT_PRECISION = 2

PRICE_PRECISION = 2

VOLUME_PRECISION = 0

# ==========================================================
# IBM watsonx Configuration
# ==========================================================

#
# Credentials can be supplied either
# 1. Environment Variables (recommended)
# 2. Directly below
#

WATSONX_API_KEY = os.getenv(
    "WATSONX_API_KEY",
    ""
)

WATSONX_URL = os.getenv(
    "WATSONX_URL",
    "https://us-south.ml.cloud.ibm.com"
)

WATSONX_PROJECT_ID = os.getenv(
    "WATSONX_PROJECT_ID",
    ""
)

#
# Granite Model
#

WATSONX_MODEL = os.getenv(
    "WATSONX_MODEL",
    "ibm/granite-3-8b-instruct"
)

#
# Generation Parameters
#

WATSONX_MAX_NEW_TOKENS = 1200

WATSONX_TEMPERATURE = 0.20

WATSONX_TOP_P = 0.90

WATSONX_REPETITION_PENALTY = 1.05

# ==========================================================
# AI Prompt Settings
# ==========================================================

AI_REPORT_TITLE = "AI Portfolio Investment Report"

AI_MAX_PORTFOLIO_STOCKS = 20

# ==========================================================
# Quantum Module
# ==========================================================

DEFAULT_QUBITS = 8

DEFAULT_SHOTS = 4096

# ----------------------------------------------------------
# Rich Quantum Encoding — normalisation constants
#
# These cap the raw feature values before mapping onto
# rotation angles.  Adjust if your universe of stocks
# routinely exceeds these ranges.
# ----------------------------------------------------------

# Maximum expected annualised-style daily volatility (%)
QUANTUM_MAX_VOLATILITY = 5.0

# Maximum expected average gain per green day (%)
QUANTUM_MAX_AVG_GAIN = 5.0

# Maximum expected winning/losing streak length (days)
QUANTUM_MAX_STREAK = 20

# Maximum expected trend slope (% per day)
QUANTUM_MAX_TREND = 0.5

# Maximum expected average daily volume (millions of shares)
QUANTUM_MAX_VOLUME = 50.0

# ==========================================================
# Automatically Create Directories
# ==========================================================

for directory in (

    OUTPUT_DIR,

    OUTPUT_CHART_DIR,

    OUTPUT_REPORT_DIR,

    CACHE_DIR,

    LOG_DIR,

):

    directory.mkdir(

        parents=True,

        exist_ok=True

    )