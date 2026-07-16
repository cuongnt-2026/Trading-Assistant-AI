"""
Mean-Reversion Engine - danh NGUOC ve trung binh (cho nhom XAU trong bien do).

Vao lenh khi:
  - Thi truong KHONG trend manh (ADX < MR_ADX_MAX)
  - Gia bi keo xa EMA20 >= MR_STRETCH_ATR * ATR
  - RSI cham vung cuc doan (<= MR_RSI_OS de BUY, >= MR_RSI_OB de SELL)
TP nham ve lai EMA20 (trung binh) -> win rate co xu huong cao, RR nho.
"""

from src.signal.constants import (
    BUY, SELL, NO_TRADE, SIDEWAYS, STRONG, WEAK,
    MR_STRETCH_ATR, MR_RSI_OS, MR_RSI_OB, MR_ADX_MAX, MR_CONFIRM,
)
from src.signal.signal import Signal


class MeanRevEngine:

    @staticmethod
    def _mk(action, trend, strength, reason, ema20, ema50, ema200, adx, atr, rsi, pattern=""):
        return Signal(action=action, trend=trend, strength=strength, reason=reason,
                      ema20=ema20, ema50=ema50, ema200=ema200, adx=adx,
                      atr=round(atr, 5), rsi=round(rsi, 2), pattern=pattern)

    @staticmethod
    def analyze(candles, ema20, ema50, ema200, adx, atr=0.0, rsi=0.0, htf_trend=None):
        close = candles[-1].close
        if not atr or atr <= 0:
            atr = abs(close) * 0.001
        dist = close - ema20
        ranging = adx < MR_ADX_MAX
        stretched_up = dist > MR_STRETCH_ATR * atr
        stretched_down = dist < -MR_STRETCH_ATR * atr
        # Xac nhan da bat dau dao chieu (khong bat dao roi):
        prev_close = candles[-2].close if len(candles) >= 2 else close
        turn_up = (not MR_CONFIRM) or (close > prev_close)
        turn_down = (not MR_CONFIRM) or (close < prev_close)

        if ranging and stretched_down and rsi <= MR_RSI_OS and turn_up:
            return MeanRevEngine._mk(
                BUY, "MEANREV", STRONG,
                "Range(ADX {:.1f}) + gia duoi EMA {:.1f}xATR + RSI {:.0f} qua ban".format(
                    adx, MR_STRETCH_ATR, rsi),
                ema20, ema50, ema200, adx, atr, rsi, "MeanRev")

        if ranging and stretched_up and rsi >= MR_RSI_OB and turn_down:
            return MeanRevEngine._mk(
                SELL, "MEANREV", STRONG,
                "Range(ADX {:.1f}) + gia tren EMA {:.1f}xATR + RSI {:.0f} qua mua".format(
                    adx, MR_STRETCH_ATR, rsi),
                ema20, ema50, ema200, adx, atr, rsi, "MeanRev")

        if not ranging:
            reason = "ADX {:.1f} qua manh - khong danh mean-reversion".format(adx)
        elif not (stretched_up or stretched_down):
            reason = "Gia chua cach xa EMA du {:.1f}xATR".format(MR_STRETCH_ATR)
        else:
            reason = "RSI chua cuc doan (RSI {:.0f})".format(rsi)
        return MeanRevEngine._mk(NO_TRADE, SIDEWAYS, WEAK, reason,
                                 ema20, ema50, ema200, adx, atr, rsi, "")
