# -*- coding: utf-8 -*-
"""
Breakout Engine - danh THEO xu huong bang cu pha vo (nhom XAU + BTC).

Cach dan trend-following/Turtle danh vang & BTC:
  - Xac dinh HUONG bang trend lon (HTF) hoac EMA50 vs EMA200.
  - Vao khi gia PHA VO dinh (BUY) / day (SELL) cua BO_LOOKBACK nen gan nhat,
    va ADX du manh (co xu huong that, khong phai nhieu).
  - SL theo cau truc + ATR; TP dat RR rong de "tha loi chay" (bu cho win rate thap).
Win rate kieu nay thuong ~35-45% nhung thang lon hon thua -> ky vong duong.
"""
from src.signal.constants import (
    BUY, SELL, NO_TRADE, UPTREND, DOWNTREND, SIDEWAYS, STRONG, WEAK,
    BO_LOOKBACK, BO_ADX_MIN, BO_STRONG_CLOSE, BO_SESSION_ONLY,
    BO_SESS_START, BO_SESS_END,
)
from src.signal.signal import Signal


class BreakoutEngine:

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

        prior = candles[-(BO_LOOKBACK + 1):-1] or candles[:-1]
        upper = max(c.high for c in prior)
        lower = min(c.low for c in prior)

        if htf_trend in (UPTREND, DOWNTREND):
            up_regime = htf_trend == UPTREND
            down_regime = htf_trend == DOWNTREND
        else:
            up_regime = ema50 > ema200
            down_regime = ema50 < ema200

        strong = adx >= BO_ADX_MIN
        brk_up = close > upper
        brk_down = close < lower

        last = candles[-1]
        rng = (last.high - last.low) or 1e-9
        strong_up = (last.close - last.low) / rng >= BO_STRONG_CLOSE
        strong_down = (last.high - last.close) / rng >= BO_STRONG_CLOSE
        hr = getattr(last.time, "hour", None)
        in_session = (not BO_SESSION_ONLY) or (hr is None) or (BO_SESS_START <= hr < BO_SESS_END)

        if strong and up_regime and brk_up and close > ema200 and strong_up and in_session:
            return BreakoutEngine._mk(
                BUY, UPTREND, STRONG,
                "Breakout dinh {} nen (ADX {:.1f}) thuan trend tang".format(BO_LOOKBACK, adx),
                ema20, ema50, ema200, adx, atr, rsi, "Breakout")

        if strong and down_regime and brk_down and close < ema200 and strong_down and in_session:
            return BreakoutEngine._mk(
                SELL, DOWNTREND, STRONG,
                "Breakout day {} nen (ADX {:.1f}) thuan trend giam".format(BO_LOOKBACK, adx),
                ema20, ema50, ema200, adx, atr, rsi, "Breakout")

        if not strong:
            reason = "ADX {:.1f} yeu - chua co xu huong de breakout".format(adx)
        elif not (up_regime or down_regime):
            reason = "Trend lon chua ro (sideways) - dung ngoai"
        else:
            reason = "Chua pha vo dinh/day {} nen".format(BO_LOOKBACK)
        return BreakoutEngine._mk(NO_TRADE, SIDEWAYS, WEAK, reason,
                                  ema20, ema50, ema200, adx, atr, rsi, "")
