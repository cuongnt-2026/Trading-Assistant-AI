# -*- coding: utf-8 -*-
"""
Bollinger Engine - Bollinger Band Mean Reversion + RSI cuc doan.

Nguon: "Short-Term Bollinger Reversion Strategy" (Babypips), dieu chinh cho
khop ha tang du an (dung EMA lam bien giua, RSI/ATR co san).

Luat:
  SELL: nen tin hieu co HIGH >= bien tren, nhung CLOSE dong lai DUOI bien tren
        (rau tren tu choi bien) VA RSI(9) >= BOLL_RSI_OB (qua mua manh).
  BUY:  nen tin hieu co LOW <= bien duoi, nhung CLOSE dong lai TREN bien duoi
        (rau duoi tu choi bien) VA RSI(9) <= BOLL_RSI_OS (qua ban manh).

SL dat ngoai dinh/day nen tin hieu (+ dem ATR). TP = bien doi dien (muc tieu
day du theo tai lieu goc; ban goc con co chot 1 nua som tai EMA giua bien -
o day don gian hoa thanh 1 TP duy nhat cho khop co che backtest hien tai,
giong cach Fibonacci engine da lam voi TP1/TP2).

Ghi chu ky thuat: tam dung lai 2 truong Signal.swing_low / Signal.swing_high
(von dat ten cho Fibonacci) de mang muc SL-tham-chieu/TP-tham-chieu sang
TradeService, tranh phai mo rong them schema.
"""
from src.signal.constants import (
    BUY, SELL, NO_TRADE, SIDEWAYS, STRONG, WEAK,
    BOLL_PERIOD, BOLL_MULT, BOLL_RSI_PERIOD, BOLL_RSI_OB, BOLL_RSI_OS,
)
from src.signal.signal import Signal
from src.indicators.indicator_service import IndicatorService


class BollingerEngine:

    @staticmethod
    def _mk(action, reason, ema20, ema50, ema200, adx, atr, rsi, swing_low=0.0, swing_high=0.0):
        return Signal(action=action, trend="MEANREV" if action in (BUY, SELL) else SIDEWAYS,
                      strength=STRONG if action in (BUY, SELL) else WEAK,
                      reason=reason, ema20=ema20, ema50=ema50, ema200=ema200,
                      adx=adx, atr=round(atr, 5), rsi=round(rsi, 2),
                      pattern="BollingerReversion" if action in (BUY, SELL) else "",
                      swing_low=swing_low, swing_high=swing_high)

    @staticmethod
    def analyze(candles, ema20, ema50, ema200, adx, atr=0.0, rsi=0.0, htf_trend=None):
        last = candles[-1]
        close = last.close
        if not atr or atr <= 0:
            atr = abs(close) * 0.001
        if len(candles) < BOLL_PERIOD:
            return BollingerEngine._mk(NO_TRADE, "Chua du nen de tinh Bollinger Band",
                                       ema20, ema50, ema200, adx, atr, rsi)

        upper, mid, lower = IndicatorService.bollinger(candles, BOLL_PERIOD, BOLL_MULT)
        rsi9 = IndicatorService.rsi(candles, BOLL_RSI_PERIOD)

        touch_upper = last.high >= upper
        reject_upper = last.close < upper
        touch_lower = last.low <= lower
        reject_lower = last.close > lower

        if touch_lower and reject_lower and rsi9 <= BOLL_RSI_OS:
            return BollingerEngine._mk(
                BUY,
                "Cham bien duoi Bollinger ({:.5g}) + tu choi + RSI9 {:.1f} qua ban".format(lower, rsi9),
                ema20, ema50, ema200, adx, atr, rsi9,
                swing_low=last.low, swing_high=upper)

        if touch_upper and reject_upper and rsi9 >= BOLL_RSI_OB:
            return BollingerEngine._mk(
                SELL,
                "Cham bien tren Bollinger ({:.5g}) + tu choi + RSI9 {:.1f} qua mua".format(upper, rsi9),
                ema20, ema50, ema200, adx, atr, rsi9,
                swing_low=lower, swing_high=last.high)

        if touch_upper or touch_lower:
            reason = "Da cham bien nhung RSI9 ({:.1f}) chua du cuc doan".format(rsi9)
        else:
            reason = "Gia chua cham bien Bollinger (tren {:.5g} / duoi {:.5g})".format(upper, lower)
        return BollingerEngine._mk(NO_TRADE, reason, ema20, ema50, ema200, adx, atr, rsi9)
