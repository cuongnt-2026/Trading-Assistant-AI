"""
Trend Service - xac dinh xu huong tren mot khung (dung cho loc DA KHUNG).

Chien luoc chong tre: xu huong lon lay tu khung CAO hon (H1/H4),
diem vao lay tu khung thap (M15) -> vao som ma van thuan trend.
"""

from src.indicators.indicator_service import IndicatorService
from src.signal.constants import UPTREND, DOWNTREND, SIDEWAYS

# Anh xa khung -> khung cao hon de lay trend
HIGHER_TF = {
    "M1": "M15", "M5": "M30", "M15": "H1",
    "M30": "H4", "H1": "H4", "H4": "D1",
}


def higher_tf(tf):
    """Tra khung cao hon de xac dinh xu huong."""
    return HIGHER_TF.get((tf or "").upper(), "H4")


class TrendService:
    """Xac dinh huong xu huong tu list nen."""

    @staticmethod
    def direction(candles):
        if not candles:
            return SIDEWAYS
        n = len(candles)
        try:
            if n >= 200:
                fast = IndicatorService.ema(candles, 50)
                slow = IndicatorService.ema(candles, 200)
            elif n >= 50:
                fast = IndicatorService.ema(candles, 20)
                slow = IndicatorService.ema(candles, 50)
            else:
                return SIDEWAYS
        except Exception:
            return SIDEWAYS
        if fast > slow:
            return UPTREND
        if fast < slow:
            return DOWNTREND
        return SIDEWAYS
