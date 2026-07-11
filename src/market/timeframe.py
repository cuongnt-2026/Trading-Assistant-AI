import MetaTrader5 as mt5


TIMEFRAME_MAP = {
    "M1": mt5.TIMEFRAME_M1,
    "M5": mt5.TIMEFRAME_M5,
    "M15": mt5.TIMEFRAME_M15,
    "M30": mt5.TIMEFRAME_M30,
    "H1": mt5.TIMEFRAME_H1,
    "H4": mt5.TIMEFRAME_H4,
    "D1": mt5.TIMEFRAME_D1,
}


def to_mt5(timeframe: str):
    """
    Convert timeframe string to MT5 timeframe.
    """
    return TIMEFRAME_MAP.get(timeframe.upper())


def is_valid(timeframe: str) -> bool:
    """
    Check timeframe is supported.
    """
    return timeframe.upper() in TIMEFRAME_MAP


def all_timeframes():
    """
    Return supported timeframes.
    """
    return list(TIMEFRAME_MAP.keys())