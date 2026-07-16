from typing import List

import pandas as pd
from ta.momentum import RSIIndicator as TaRSIIndicator

from src.market.candle import Candle


class RSIIndicator:
    """
    Relative Strength Index (RSI) Indicator.

    Đo động lượng (momentum), thang 0-100.
    > 70 quá mua, < 30 quá bán.
    """

    @staticmethod
    def calculate(
        candles: List[Candle],
        period: int = 14,
    ) -> float:
        """
        Tính giá trị RSI mới nhất.
        """

        if not candles:
            raise ValueError("Candles cannot be empty.")

        if period <= 0:
            raise ValueError("Period must be greater than zero.")

        if len(candles) < period + 1:
            raise ValueError(f"Need at least {period + 1} candles.")

        df = pd.DataFrame({
            "close": [c.close for c in candles],
        })

        rsi = TaRSIIndicator(
            close=df["close"],
            window=period,
        )

        return float(rsi.rsi().iloc[-1])
