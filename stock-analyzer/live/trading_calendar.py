"""
trading_calendar.py

NSE trading calendar utilities.

Converts "N trading days before date D" into an actual start date,
skipping weekends and NSE public holidays.

Version : 5.3.0
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import List

# NSE public holidays 2024–2026 (approximate)
_NSE_HOLIDAYS: set[date] = {
    # 2024
    date(2024,  1, 26), date(2024,  3, 25), date(2024,  3, 29),
    date(2024,  4, 14), date(2024,  4, 17), date(2024,  4, 21),
    date(2024,  5,  1), date(2024,  6, 17), date(2024,  7, 17),
    date(2024,  8, 15), date(2024, 10,  2), date(2024, 10, 13),
    date(2024, 11,  1), date(2024, 11, 15), date(2024, 12, 25),
    # 2025
    date(2025,  1, 26), date(2025,  2, 26), date(2025,  3, 14),
    date(2025,  3, 31), date(2025,  4, 10), date(2025,  4, 14),
    date(2025,  4, 18), date(2025,  5,  1), date(2025,  6,  7),
    date(2025,  8, 15), date(2025,  8, 27), date(2025, 10,  2),
    date(2025, 10, 20), date(2025, 10, 21), date(2025, 11,  5),
    date(2025, 12, 25),
    # 2026
    date(2026,  1, 26), date(2026,  3,  3), date(2026,  3, 20),
    date(2026,  4,  3), date(2026,  4, 14), date(2026,  5,  1),
    date(2026,  8, 15), date(2026, 10,  2), date(2026, 11, 25),
    date(2026, 12, 25),
}


def is_trading_day(d: date) -> bool:
    """True if d is Mon–Fri and not an NSE holiday."""
    return d.weekday() < 5 and d not in _NSE_HOLIDAYS


def previous_trading_days(
    reference        : date,
    n                : int,
    include_reference: bool = False,
) -> List[date]:
    """
    Return the n most recent trading days before `reference`,
    ordered oldest → newest.
    """
    days   : List[date] = []
    cursor : date = reference if include_reference else reference - timedelta(days=1)
    while len(days) < n:
        if is_trading_day(cursor):
            days.append(cursor)
        cursor -= timedelta(days=1)
        if cursor < date(2000, 1, 1):
            break
    days.reverse()
    return days


def trading_days_in_range(start: date, end: date) -> List[date]:
    """All trading days in [start, end] inclusive, oldest first."""
    days : List[date] = []
    cur  : date       = start
    while cur <= end:
        if is_trading_day(cur):
            days.append(cur)
        cur += timedelta(days=1)
    return days


def next_trading_day(d: date) -> date:
    """First trading day strictly after d."""
    cur = d + timedelta(days=1)
    while not is_trading_day(cur):
        cur += timedelta(days=1)
    return cur


def date_n_trading_days_before(reference: date, n: int) -> date:
    """Date that is exactly n trading days before reference."""
    days = previous_trading_days(reference, n)
    return days[0] if days else reference - timedelta(days=n * 2)
