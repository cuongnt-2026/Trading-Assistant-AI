from typing import List

import pandas as pd
from ta.volatility import AverageTrueRange

from src.market.candle import Candle


class ATRIndicator:
    """
    Average True Range (ATR) Indicator.

    Đo độ biến động (volatility). Dùng để tham chiếu độ rộng SL/TP.
    """

    @staticmethod
    def calculate(
        candles: List[Candle],
        period: int = 14,
    ) -> float:
        """
        Tính giá trị ATR mới nhất.
        """

        if not candles:
            raise ValueError("Candles cannot be empty.")

        if period <= 0:
            raise ValueError("Period must be greater than zero.")

        if len(candles) < period + 1:
            raise ValueError(f"Need at least {period + 1} candles.")

        df = pd.DataFrame({
            "high": [c.high for c in candles],
            "low": [c.low for c in candles],
            "close": [c.close for c in candles],
        })

        atr = AverageTrueRange(
            high=df["high"],
            low=df["low"],
            close=df["close"],
            window=period,
        )

        return float(atr.average_true_range().iloc[-1])
