# -*- coding: utf-8 -*-
"""
London Engine - London Breakout (pha bien do phien A khi London mo cua).

Nguon: "London Breakout Strategy" (pho bien trong tai lieu Forex, vd
newyorkcityservers.com/blog/london-breakout-strategy). Luat:
  1. Do bien do CAO/THAP cua phien A trong ngay (LB_ASIA_START-LB_ASIA_END, gio
     theo candle.time.hour - cung quy uoc "gio UTC" ma cac bo loc phien khac
     trong du an nay dang dung, vd FX_SESS_START/END).
  2. Bo qua neu bien do qua hep (< LB_MIN_RANGE_ATR*ATR, khong du bien dong)
     hoac qua rong (> LB_MAX_RANGE_ATR*ATR, rui ro qua lon).
  3. Chi vao lenh trong khung gio LB_ASIA_END - LB_ENTRY_END (ngay sau London
     mo cua). Gia dong cua VUOT dinh/day phien A + dem LB_BUFFER_ATR (thay cho
     "3-5 pip" cua tai lieu goc - quy theo ATR de dung duoc tren nhieu symbol)
     -> vao lenh. Chi bat tin hieu O NEN VUA PHA VO (nen truoc do chua vuot),
     tranh vao lai nhieu lan khi gia da vuot san.
  4. SL = phia doi dien bien do phien A (day cho BUY / dinh cho SELL).
  5. TP = LB_TP_MULT lan do rong bien do phien A (mac dinh 1.5x, theo tai lieu goc).
"""
from src.signal.constants import (
    BUY, SELL, NO_TRADE, UPTREND, DOWNTREND, SIDEWAYS, STRONG, WEAK,
    LB_ASIA_START, LB_ASIA_END, LB_ENTRY_END, LB_BUFFER_ATR,
    LB_MIN_RANGE_ATR, LB_MAX_RANGE_ATR,
)
from src.signal.signal import Signal


def _asia_range(candles, start_h, end_h):
    """Tra ve (high, low) cua phien A CUNG NGAY voi nen cuoi cung."""
    last_date = candles[-1].time.date()
    highs, lows = [], []
    for c in reversed(candles[:-1]):
        d = c.time.date()
        if d != last_date:
            if d < last_date:
                break
            continue
        h = getattr(c.time, "hour", None)
        if h is not None and start_h <= h < end_h:
            highs.append(c.high)
            lows.append(c.low)
    if not highs:
        return None, None
    return max(highs), min(lows)


class LondonEngine:

    @staticmethod
    def _mk(action, trend, reason, ema20, ema50, ema200, adx, atr, rsi,
            swing_low=0.0, swing_high=0.0):
        return Signal(action=action, trend=trend,
                      strength=STRONG if action in (BUY, SELL) else WEAK,
                      reason=reason, ema20=ema20, ema50=ema50, ema200=ema200,
                      adx=adx, atr=round(atr, 5), rsi=round(rsi, 2),
                      pattern="LondonBreakout" if action in (BUY, SELL) else "",
                      swing_low=swing_low, swing_high=swing_high)

    @staticmethod
    def analyze(candles, ema20, ema50, ema200, adx, atr=0.0, rsi=0.0, htf_trend=None):
        last = candles[-1]
        close = last.close
        if not atr or atr <= 0:
            atr = abs(close) * 0.001

        hr = getattr(last.time, "hour", None)
        if hr is None or not (LB_ASIA_END <= hr < LB_ENTRY_END):
            return LondonEngine._mk(
                NO_TRADE, SIDEWAYS,
                "Ngoai khung gio vao lenh ({:02d}h-{:02d}h)".format(LB_ASIA_END, LB_ENTRY_END),
                ema20, ema50, ema200, adx, atr, rsi)

        asia_high, asia_low = _asia_range(candles, LB_ASIA_START, LB_ASIA_END)
        if asia_high is None:
            return LondonEngine._mk(NO_TRADE, SIDEWAYS, "Chua du du lieu phien A trong ngay",
                                    ema20, ema50, ema200, adx, atr, rsi)

        rng = asia_high - asia_low
        if rng < LB_MIN_RANGE_ATR * atr:
            return LondonEngine._mk(NO_TRADE, SIDEWAYS,
                                    "Bien do phien A qua hep ({:.5g})".format(rng),
                                    ema20, ema50, ema200, adx, atr, rsi)
        if rng > LB_MAX_RANGE_ATR * atr:
            return LondonEngine._mk(NO_TRADE, SIDEWAYS,
                                    "Bien do phien A qua rong ({:.5g}) - rui ro lon".format(rng),
                                    ema20, ema50, ema200, adx, atr, rsi)

        buf = LB_BUFFER_ATR * atr
        prev_close = candles[-2].close if len(candles) >= 2 else close
        broke_up_now = close > asia_high + buf
        broke_up_before = prev_close > asia_high + buf
        broke_down_now = close < asia_low - buf
        broke_down_before = prev_close < asia_low - buf

        if broke_up_now and not broke_up_before:
            return LondonEngine._mk(
                BUY, UPTREND,
                "Pha dinh phien A ({:.5g}) khi London mo cua".format(asia_high),
                ema20, ema50, ema200, adx, atr, rsi, swing_low=asia_low, swing_high=asia_high)

        if broke_down_now and not broke_down_before:
            return LondonEngine._mk(
                SELL, DOWNTREND,
                "Pha day phien A ({:.5g}) khi London mo cua".format(asia_low),
                ema20, ema50, ema200, adx, atr, rsi, swing_low=asia_low, swing_high=asia_high)

        return LondonEngine._mk(
            NO_TRADE, SIDEWAYS,
            "Gia trong bien do phien A ({:.5g}-{:.5g}) hoac da pha tu truoc".format(asia_low, asia_high),
            ema20, ema50, ema200, adx, atr, rsi)
