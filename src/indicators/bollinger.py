from typing import List

import pandas as pd

from src.market.candle import Candle


class BollingerBandsIndicator:
    """
    Bollinger Bands (bien EMA): mid = EMA(period), bien = mid +/- mult * do lech chuan(period).
    Tra ve (upper, mid, lower) tai nen cuoi cung.
    """

    @staticmethod
    def calculate(candles: List[Candle], period: int = 50, mult: float = 2.0):
        if not candles:
            raise ValueError("Candles cannot be empty.")
        if period <= 0:
            raise ValueError("Period must be greater than zero.")
        if len(candles) < period:
            raise ValueError(f"Need at least {period} candles.")

        closes = pd.Series([c.close for c in candles])
        mid = closes.ewm(span=period, adjust=False).mean()
        std = closes.rolling(window=period).std(ddof=0)
        upper = mid + mult * std
        lower = mid - mult * std

        return float(upper.iloc[-1]), float(mid.iloc[-1]), float(lower.iloc[-1])
