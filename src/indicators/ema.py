from typing import List

import pandas as pd

from src.market.candle import Candle


class EMAIndicator:
    """
    EMA (Exponential Moving Average) Indicator.
    """

    @staticmethod
    def calculate(
        candles: List[Candle],
        period: int,
    ) -> float:
        """
        Calculate the latest EMA value.

        Args:
            candles: List of Candle objects.
            period: EMA period (e.g. 20, 50, 200).

        Returns:
            Latest EMA value.
        """

        if not candles:
            raise ValueError("Candles cannot be empty.")

        if period <= 0:
            raise ValueError("Period must be greater than zero.")

        if len(candles) < period:
            raise ValueError(
                f"Need at least {period} candles."
            )

        closes = [candle.close for candle in candles]

        df = pd.DataFrame({
            "close": closes,
        })

        ema = df["close"].ewm(
            span=period,
            adjust=False,
        ).mean()

        return float(ema.iloc[-1])