"""
price_level_forecaster.py

Track 1 — Expected OHLC Price Level Forecaster.

Derives expected Open, High, Low, Close levels for the next bar from:
    • exp_return  — expected % move from NextStatePredictorV2
    • atr_w4      — Average True Range from MultiWindowFeatures (w4 window)
    • current price

Formulas
--------
    exp_close = price * (1 + exp_return / 100)
    exp_open  = price                      # intraday: next bar opens at current close
    exp_high  = exp_close + atr_w4 * ATR_MULT
    exp_low   = exp_close - atr_w4 * ATR_MULT
    atr_range = exp_high - exp_low

All levels are clipped to price +/- MAX_DEVIATION_PCT % to prevent
runaway predictions when exp_return is extreme.

Version : 11.0.1
"""

from __future__ import annotations

# ATR multiplier for the High/Low band around the expected close
_ATR_MULT          = 0.60

# Maximum allowed deviation from current price (20%)
_MAX_DEVIATION_PCT = 20.0


class PriceLevelForecaster:
    """
    Derives expected OHLC levels for the next bar.

    Parameters
    ----------
    fv     : dict   feature vector from MultiWindowFeatures.compute()
                    Required keys: ``price``, ``atr_w4`` (fallback: ``atr``)
    signal : dict   signal dict from ConfidenceScore.compute() or
                    NextStatePredictorV2.predict()
                    Required key: ``exp_return``
    """

    def __init__(self, fv: dict, signal: dict):
        self._price   = float(fv.get("price",  0.0))
        self._atr     = float(fv.get("atr_w4", fv.get("atr", 0.0)))
        self._exp_ret = float(signal.get("exp_return", 0.0))

    # ------------------------------------------------------------------

    def forecast(self) -> dict:
        """
        Compute the OHLC forecast.

        Returns
        -------
        dict:
            exp_open   float  expected open price (₹)
            exp_high   float  expected high price (₹)
            exp_low    float  expected low price  (₹)
            exp_close  float  expected close price (₹)
            exp_pct    float  expected % move
            atr_range  float  expected high-minus-low range (₹)
        """
        price = self._price
        if price <= 0:
            zero = {"exp_open": 0.0, "exp_high": 0.0, "exp_low": 0.0,
                    "exp_close": 0.0, "exp_pct": 0.0, "atr_range": 0.0}
            return zero

        max_dev = price * _MAX_DEVIATION_PCT / 100.0

        # Expected close — clipped to max deviation
        raw_close = price * (1.0 + self._exp_ret / 100.0)
        exp_close = float(max(price - max_dev, min(price + max_dev, raw_close)))

        # Expected open = current close (intraday: next bar opens here)
        exp_open = price

        # Expected high / low from ATR band
        half_band = self._atr * _ATR_MULT
        exp_high  = min(exp_close + half_band, price + max_dev)
        exp_low   = max(exp_close - half_band, price - max_dev)

        if exp_high < exp_low:
            exp_high, exp_low = exp_low, exp_high

        return {
            "exp_open" : round(exp_open,        2),
            "exp_high" : round(exp_high,        2),
            "exp_low"  : round(exp_low,         2),
            "exp_close": round(exp_close,       2),
            "exp_pct"  : round(self._exp_ret,   3),
            "atr_range": round(exp_high - exp_low, 2),
        }
