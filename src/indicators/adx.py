from typing import List

import pandas as pd
from ta.trend import ADXIndicator as TaADXIndicator

from src.market.candle import Candle


class ADXIndicator:
    """
    Average Directional Index (ADX) Indicator.
    """

    @staticmethod
    def calculate(
        candles: List[Candle],
        period: int = 14,
    ) -> float:
        """
        Calculate the latest ADX value.

        Args:
            candles: List of Candle objects.
            period: ADX period.

        Returns:
            Latest ADX value.
        """

        if not candles:
            raise ValueError("Candles cannot be empty.")

        if period <= 0:
            raise ValueError("Period must be greater than zero.")

        if len(candles) < period * 2:
            raise ValueError(
                f"Need at least {period * 2} candles."
            )

        df = pd.DataFrame({
            "high": [c.high for c in candles],
            "low": [c.low for c in candles],
            "close": [c.close for c in candles],
        })

        adx = TaADXIndicator(
            high=df["high"],
            low=df["low"],
            close=df["close"],
            window=period,
        )

        return float(adx.adx().iloc[-1])