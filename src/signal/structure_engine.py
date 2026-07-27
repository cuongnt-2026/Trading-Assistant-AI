# -*- coding: utf-8 -*-
"""
Structure Engine - giao dich theo CAU TRUC THI TRUONG.

Quy tac:
  - Trend TANG neu: dinh sau > dinh truoc (HH) VA day sau > day truoc (HL).
  - Trend GIAM neu: dinh sau < dinh truoc (LH) VA day sau < day truoc (LL).
  - Trend tang + vua hinh thanh 1 DAY swing moi  -> BUY (mua tai day).
  - Trend giam + vua hinh thanh 1 DINH swing moi -> SELL (ban tai dinh).
Day/dinh swing xac dinh bang pivot (STRUCT_PIVOT nen moi ben).
"""
from src.signal.constants import (
    BUY, SELL, NO_TRADE, UPTREND, DOWNTREND, SIDEWAYS, STRONG, WEAK,
    STRUCT_PIVOT, STRUCT_LOOKBACK, STRUCT_ADX_MIN,
)
from src.signal.signal import Signal


def _pivots(win, k):
    highs, lows = [], []
    for i in range(k, len(win) - k):
        seg = win[i - k:i + k + 1]
        if win[i].high == max(c.high for c in seg):
            highs.append((i, win[i].high))
        if win[i].low == min(c.low for c in seg):
            lows.append((i, win[i].low))
    return highs, lows


class StructureEngine:

    @staticmethod
    def _mk(action, trend, reason, ema20, ema50, ema200, adx, atr, rsi):
        return Signal(action=action, trend=trend,
                      strength=STRONG if action in (BUY, SELL) else WEAK,
                      reason=reason, ema20=ema20, ema50=ema50, ema200=ema200,
                      adx=adx, atr=round(atr, 5), rsi=round(rsi, 2),
                      pattern="Structure" if action in (BUY, SELL) else "")

    @staticmethod
    def analyze(candles, ema20, ema50, ema200, adx, atr=0.0, rsi=0.0, htf_trend=None):
        close = candles[-1].close
        if not atr or atr <= 0:
            atr = abs(close) * 0.001
        k = STRUCT_PIVOT
        win = candles[-STRUCT_LOOKBACK:] if len(candles) >= STRUCT_LOOKBACK else candles[:]
        n = len(win)
        if n < 2 * k + 5:
            return StructureEngine._mk(NO_TRADE, SIDEWAYS, "Chua du nen",
                                       ema20, ema50, ema200, adx, atr, rsi)

        highs, lows = _pivots(win, k)
        if len(highs) < 2 or len(lows) < 2:
            return StructureEngine._mk(NO_TRADE, SIDEWAYS, "Chua du dinh/day de doc cau truc",
                                       ema20, ema50, ema200, adx, atr, rsi)

        hh = highs[-1][1] > highs[-2][1]   # dinh sau cao hon
        hl = lows[-1][1] > lows[-2][1]     # day sau cao hon
        lh = highs[-1][1] < highs[-2][1]   # dinh sau thap hon
        ll = lows[-1][1] < lows[-2][1]     # day sau thap hon
        up = hh and hl
        down = lh and ll

        confirm_pos = n - 1 - k            # pivot vua duoc xac nhan tai nen hien tai
        fresh_low = lows[-1][0] == confirm_pos
        fresh_high = highs[-1][0] == confirm_pos

        strong = adx >= STRUCT_ADX_MIN          # trend du manh
        up_ema = ema50 > ema200                 # EMA xac nhan uptrend
        down_ema = ema50 < ema200               # EMA xac nhan downtrend

        if up and fresh_low and strong and up_ema:
            return StructureEngine._mk(
                BUY, UPTREND,
                "Trend tang (HH+HL) + vua tao day swing {:.5g} -> mua tai day".format(lows[-1][1]),
                ema20, ema50, ema200, adx, atr, rsi)

        if down and fresh_high and strong and down_ema:
            return StructureEngine._mk(
                SELL, DOWNTREND,
                "Trend giam (LH+LL) + vua tao dinh swing {:.5g} -> ban tai dinh".format(highs[-1][1]),
                ema20, ema50, ema200, adx, atr, rsi)

        if not (up or down):
            reason = "Cau truc chua ro trend (khong HH+HL / LH+LL)"
        elif adx < STRUCT_ADX_MIN:
            reason = "ADX yeu ({:.1f}) - trend chua du manh".format(adx)
        else:
            reason = "Dung trend nhung chua tao day/dinh swing moi / EMA chua thuan"
        return StructureEngine._mk(NO_TRADE, SIDEWAYS, reason,
                                   ema20, ema50, ema200, adx, atr, rsi)
