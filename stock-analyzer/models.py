from dataclasses import dataclass


@dataclass
class StockSummary:

    symbol: str

    trading_days: int

    green_days: int

    red_days: int

    probability_up: float

    probability_down: float

    average_gain: float

    average_loss: float

    max_gain: float

    max_loss: float

    volatility: float

    longest_green_streak: int

    longest_red_streak: int
