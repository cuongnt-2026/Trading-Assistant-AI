# -*- coding: utf-8 -*-
"""
Double Top / Double Bottom detector (hai dinh / hai day).

- Hai DAY gan bang nhau + gia PHA VO neckline (dinh giua 2 day) -> BUY (dao chieu tang).
- Hai DINH gan bang nhau + gia PHA VO neckline (day giua 2 dinh) -> SELL (dao chieu giam).
Dua tren cac diem swing (pivot) trong DBL_LOOKBACK nen gan nhat.
Day la NGUON TIN HIEU PHU, chay song song voi phuong phap chinh.
"""
from src.signal.constants import (
    BUY, SELL, NO_TRADE, UPTREND, DOWNTREND, SIDEWAYS, STRONG, WEAK,
    DBL_PIVOT, DBL_LOOKBACK, DBL_TOL_ATR, DBL_MIN_SEP,
)
from src.signal.signal import Signal


def _pivot_lows(cs, k):
    out = []
    for i in range(k, len(cs) - k):
        seg = cs[i - k:i + k + 1]
        if cs[i].low == min(c.low for c in seg):
            out.append((i, cs[i].low))
    return out


def _pivot_highs(cs, k):
    out = []
    for i in range(k, len(cs) - k):
        seg = cs[i - k:i + k + 1]
        if cs[i].high == max(c.high for c in seg):
            out.append((i, cs[i].high))
    return out


class DoubleEngine:

    @staticmethod
    def _mk(action, trend, reason, ema20, ema50, ema200, adx, atr, rsi):
        return Signal(action=action, trend=trend,
                      strength=STRONG if action in (BUY, SELL) else WEAK,
                      reason=reason, ema20=ema20, ema50=ema50, ema200=ema200,
                      adx=adx, atr=round(atr, 5), rsi=round(rsi, 2),
                      pattern="Double" if action in (BUY, SELL) else "")

    @staticmethod
    def analyze(candles, ema20, ema50, ema200, adx, atr=0.0, rsi=0.0, htf_trend=None):
        close = candles[-1].close
        if not atr or atr <= 0:
            atr = abs(close) * 0.001
        win = candles[-DBL_LOOKBACK:] if len(candles) >= DBL_LOOKBACK else candles[:]
        k = DBL_PIVOT
        tol = DBL_TOL_ATR * atr

        # ----- DOUBLE BOTTOM -> BUY -----
        lows = _pivot_lows(win, k)
        if len(lows) >= 2:
            i2, l2 = lows[-1]
            for i1, l1 in reversed(lows[:-1]):
                if (i2 - i1) >= DBL_MIN_SEP and abs(l1 - l2) <= tol:
                    neckline = max(c.high for c in win[i1:i2 + 1])
                    if close > neckline:   # pha vo neckline len tren
                        return DoubleEngine._mk(
                            BUY, UPTREND,
                            "Hai day (~{:.5g}) + pha neckline {:.5g}".format((l1 + l2) / 2, neckline),
                            ema20, ema50, ema200, adx, atr, rsi)
                    break

        # ----- DOUBLE TOP -> SELL -----
        highs = _pivot_highs(win, k)
        if len(highs) >= 2:
            i2, h2 = highs[-1]
            for i1, h1 in reversed(highs[:-1]):
                if (i2 - i1) >= DBL_MIN_SEP and abs(h1 - h2) <= tol:
                    neckline = min(c.low for c in win[i1:i2 + 1])
                    if close < neckline:   # pha vo neckline xuong duoi
                        return DoubleEngine._mk(
                            SELL, DOWNTREND,
                            "Hai dinh (~{:.5g}) + pha neckline {:.5g}".format((h1 + h2) / 2, neckline),
                            ema20, ema50, ema200, adx, atr, rsi)
                    break

        return DoubleEngine._mk(NO_TRADE, SIDEWAYS,
                                "Chua thay mo hinh hai dinh/hai day",
                                ema20, ema50, ema200, adx, atr, rsi)
