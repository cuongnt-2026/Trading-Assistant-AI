from src.indicators.indicator_service import IndicatorService
from src.signal.signal_engine import SignalEngine
from src.signal.meanrev_engine import MeanRevEngine
from src.signal.breakout_engine import BreakoutEngine
from src.signal.double_engine import DoubleEngine
from src.signal.flag_engine import FlagEngine
from src.signal.structure_engine import StructureEngine
from src.signal.bollinger_engine import BollingerEngine
from src.signal.london_engine import LondonEngine


class SignalService:
    """Trading Signal Service. strategy = 'trend' (default) hoac 'meanrev'."""

    @staticmethod
    def analyze(candles, htf_trend=None, strategy="trend"):
        ema20 = IndicatorService.ema(candles, 20)
        ema50 = IndicatorService.ema(candles, 50)
        ema200 = IndicatorService.ema(candles, 200)
        adx = IndicatorService.adx(candles)
        atr = IndicatorService.atr(candles)
        rsi = IndicatorService.rsi(candles)

        if strategy == "meanrev":
            return MeanRevEngine.analyze(candles, ema20, ema50, ema200, adx, atr, rsi)
        if strategy == "breakout":
            return BreakoutEngine.analyze(candles, ema20, ema50, ema200, adx, atr, rsi, htf_trend=htf_trend)
        if strategy == "double":
            return DoubleEngine.analyze(candles, ema20, ema50, ema200, adx, atr, rsi, htf_trend=htf_trend)
        if strategy == "flag":
            return FlagEngine.analyze(candles, ema20, ema50, ema200, adx, atr, rsi, htf_trend=htf_trend)
        if strategy == "structure":
            return StructureEngine.analyze(candles, ema20, ema50, ema200, adx, atr, rsi, htf_trend=htf_trend)
        if strategy == "bollinger":
            return BollingerEngine.analyze(candles, ema20, ema50, ema200, adx, atr, rsi, htf_trend=htf_trend)
        if strategy == "london":
            return LondonEngine.analyze(candles, ema20, ema50, ema200, adx, atr, rsi, htf_trend=htf_trend)
        return SignalEngine.analyze(
            candles, ema20, ema50, ema200, adx, atr, rsi, htf_trend=htf_trend)
