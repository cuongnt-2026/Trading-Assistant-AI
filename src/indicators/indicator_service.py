from typing import List

from src.market.candle import Candle
from src.indicators.ema import EMAIndicator
from src.indicators.adx import ADXIndicator


class IndicatorService:
    """
    Technical Indicator Service.
    """

    @staticmethod
    def ema(
        candles: List[Candle],
        period: int,
    ) -> float:
        """
        Calculate EMA.
        """
        return EMAIndicator.calculate(
            candles,
            period,
        )

    @staticmethod
    def adx(
        candles: List[Candle],
        period: int = 14,
    ) -> float:
        """
        Calculate ADX.
        """
        return ADXIndicator.calculate(
            candles,
            period,
        )