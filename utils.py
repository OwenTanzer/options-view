"""
Calendar utilities for NYSE trading days and QQQ expiration targeting.
Extracted from fetch_historical.py — no API dependency.
"""

from datetime import date, timedelta

import pandas_market_calendars as mcal

_NYSE = mcal.get_calendar("NYSE")
_valid_days: set[date] = set()
_loaded_range: tuple[date, date] | None = None


def _ensure_calendar_loaded(start: date, end: date) -> None:
    global _loaded_range
    if _loaded_range and _loaded_range[0] <= start and end <= _loaded_range[1]:
        return
    days = _NYSE.valid_days(start_date=start.isoformat(), end_date=end.isoformat())
    _valid_days.update(d.date() for d in days)
    _loaded_range = (start, end)


def is_trading_day(d: date) -> bool:
    return d in _valid_days


def next_trading_day(d: date) -> date:
    nd = d + timedelta(days=1)
    while not is_trading_day(nd):
        nd += timedelta(days=1)
    return nd


def prior_trading_day(d: date) -> date:
    nd = d
    while not is_trading_day(nd):
        nd -= timedelta(days=1)
    return nd


def nominal_friday(d: date) -> date:
    return d + timedelta(days=(4 - d.weekday()) % 7)


def last_calendar_day_of_month(year: int, month: int) -> date:
    if month == 12:
        return date(year + 1, 1, 1) - timedelta(days=1)
    return date(year, month + 1, 1) - timedelta(days=1)


def target_expirations(as_of: date) -> list[tuple[str, date]]:
    """Return the 6 tiered expiration targets as they would have applied on as_of."""
    _ensure_calendar_loaded(as_of - timedelta(days=10), as_of + timedelta(days=120))

    this_fri = prior_trading_day(nominal_friday(as_of))
    next_fri = prior_trading_day(nominal_friday(as_of) + timedelta(days=7))

    nm = as_of.month % 12 + 1
    ny = as_of.year + (1 if as_of.month == 12 else 0)

    candidates = [
        ("0DTE", as_of),
        ("+1D",  next_trading_day(as_of)),
        ("EoW",  this_fri),
        ("EoNW", next_fri),
        ("EoM",  prior_trading_day(last_calendar_day_of_month(as_of.year, as_of.month))),
        ("EoNM", prior_trading_day(last_calendar_day_of_month(ny, nm))),
    ]

    seen: set[date] = set()
    result = []
    for label, d in candidates:
        if d not in seen:
            seen.add(d)
            result.append((label, d))
    return result
