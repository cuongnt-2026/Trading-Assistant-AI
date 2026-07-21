# -*- coding: utf-8 -*-
"""
Flag / Pennant detector (la co / co duoi nheo) - mo hinh TIEP DIEN.

Y tuong: mot cu di manh (CAN CO) -> vai nen di ngang co lai (la co / tam giac nho)
-> gia pha vo vung di ngang theo HUONG cu -> bao tiep dien.
Nguon tin hieu PHU, chay song song.
"""
from src.signal.constants import (
    BUY, SELL, NO_TRADE, UPTREND, DOWNTREND, SIDEWAYS, STRONG, WEAK,
    FLAG_POLE_BARS, FLAG_POLE_ATR, FLAG_CONS_BARS, FLAG_CONS_MAX,
)
from src.signal.signal import Signal


class FlagEngine:

    @staticmethod
    def _mk(action, trend, reason, ema20, ema50, ema200, adx, atr, rsi):
        return Signal(action=action, trend=trend,
                      strength=STRONG if action in (BUY, SELL) else WEAK,
                      reason=reason, ema20=ema20, ema50=ema50, ema200=ema200,
                      adx=adx, atr=round(atr, 5), rsi=round(rsi, 2),
                      pattern="Flag" if action in (BUY, SELL) else "")

    @staticmethod
    def analyze(candles, ema20, ema50, ema200, adx, atr=0.0, rsi=0.0, htf_trend=None):
        close = candles[-1].close
        if not atr or atr <= 0:
            atr = abs(close) * 0.001
        P, C = FLAG_POLE_BARS, FLAG_CONS_BARS
        if len(candles) < P + C + 1:
            return FlagEngine._mk(NO_TRADE, SIDEWAYS, "Chua du nen", ema20, ema50, ema200, adx, atr, rsi)

        pole = candles[-(C + P):-C]        # can co
        cons = candles[-C:-1]              # vung di ngang (khong tinh nen hien tai)
        if not pole or not cons:
            return FlagEngine._mk(NO_TRADE, SIDEWAYS, "Chua du nen", ema20, ema50, ema200, adx, atr, rsi)

        pole_move = pole[-1].close - pole[0].close
        strong_pole = abs(pole_move) >= FLAG_POLE_ATR * atr
        cons_hi = max(c.high for c in cons)
        cons_lo = min(c.low for c in cons)
        tight = (cons_hi - cons_lo) <= abs(pole_move) * FLAG_CONS_MAX

        if strong_pole and tight:
            if pole_move > 0 and close > cons_hi:      # co tang -> pha len
                return FlagEngine._mk(
                    BUY, UPTREND,
                    "Can co tang {:.5g} + di ngang + pha {:.5g}".format(pole_move, cons_hi),
                    ema20, ema50, ema200, adx, atr, rsi)
            if pole_move < 0 and close < cons_lo:      # co giam -> pha xuong
                return FlagEngine._mk(
                    SELL, DOWNTREND,
                    "Can co giam {:.5g} + di ngang + pha {:.5g}".format(pole_move, cons_lo),
                    ema20, ema50, ema200, adx, atr, rsi)

        return FlagEngine._mk(NO_TRADE, SIDEWAYS, "Chua thay mo hinh co/co duoi nheo",
                              ema20, ema50, ema200, adx, atr, rsi)
