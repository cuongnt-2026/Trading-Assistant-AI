from typing import List

from src.market.candle import Candle
from src.indicators.ema import EMAIndicator
from src.indicators.adx import ADXIndicator
from src.indicators.atr import ATRIndicator
from src.indicators.rsi import RSIIndicator
from src.indicators.bollinger import BollingerBandsIndicator


class IndicatorService:
    """Technical Indicator Service."""

    @staticmethod
    def ema(candles: List[Candle], period: int) -> float:
        return EMAIndicator.calculate(candles, period)

    @staticmethod
    def adx(candles: List[Candle], period: int = 14) -> float:
        return ADXIndicator.calculate(candles, period)

    @staticmethod
    def atr(candles: List[Candle], period: int = 14) -> float:
        return ATRIndicator.calculate(candles, period)

    @staticmethod
    def rsi(candles: List[Candle], period: int = 14) -> float:
        return RSIIndicator.calculate(candles, period)

    @staticmethod
    def bollinger(candles: List[Candle], period: int = 50, mult: float = 2.0):
        """Tra ve (upper, mid, lower)."""
        return BollingerBandsIndicator.calculate(candles, period, mult)
