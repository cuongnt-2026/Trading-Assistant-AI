import MetaTrader5 as mt5
import pandas as pd


def get_candles(symbol="XAUUSD", timeframe=mt5.TIMEFRAME_M15, count=100):

    rates = mt5.copy_rates_from_pos(
        symbol,
        timeframe,
        0,
        count
    )

    if rates is None:
        return None


    df = pd.DataFrame(rates)

    df['time'] = pd.to_datetime(
        df['time'],
        unit='s'
    )

    return df