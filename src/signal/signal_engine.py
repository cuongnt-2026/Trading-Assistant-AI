from src.signal.constants import (
    BUY, SELL, NO_TRADE, UPTREND, DOWNTREND, SIDEWAYS, STRONG, WEAK,
    ADX_MIN, PULLBACK_ATR_MULT, REQUIRE_PATTERN,
)
from src.signal.signal import Signal
from src.signal import patterns


class SignalEngine:
    """
    Trading Signal Engine (da khung).

    Setup vao lenh:
      - Trend lon (HTF H1/H4) + EMA20>EMA50 tren khung vao lenh
      - ADX > ADX_MIN
      - Pullback ve EMA (dung sai = PULLBACK_ATR_MULT * ATR)
      - Nen xac nhan: BAT BUOC neu REQUIRE_PATTERN=1, nguoc lai chi la diem cong.
    """

    @staticmethod
    def _strong(adx):
        return adx > ADX_MIN

    @staticmethod
    def _tolerance(close_price, atr):
        if atr and atr > 0:
            return atr * PULLBACK_ATR_MULT
        return abs(close_price) * 0.001

    @staticmethod
    def _is_pullback(close_price, ema20, ema50, atr):
        tol = SignalEngine._tolerance(close_price, atr)
        return (abs(close_price - ema20) <= tol) or (abs(close_price - ema50) <= tol)

    @staticmethod
    def _make(action, trend, strength, reason,
              ema20, ema50, ema200, adx, atr, rsi, pattern=""):
        return Signal(
            action=action, trend=trend, strength=strength, reason=reason,
            ema20=ema20, ema50=ema50, ema200=ema200, adx=adx,
            atr=round(atr, 5), rsi=round(rsi, 2), pattern=pattern,
        )

    @staticmethod
    def analyze(candles, ema20, ema50, ema200, adx, atr=0.0, rsi=0.0,
                htf_trend=None):
        close_price = candles[-1].close
        strong = SignalEngine._strong(adx)
        pullback = SignalEngine._is_pullback(close_price, ema20, ema50, atr)
        bull = patterns.bullish_pattern(candles)
        bear = patterns.bearish_pattern(candles)

        up_fast = ema20 > ema50
        down_fast = ema20 < ema50

        if htf_trend in (UPTREND, DOWNTREND):
            buy_trend = (htf_trend == UPTREND) and up_fast
            sell_trend = (htf_trend == DOWNTREND) and down_fast
            trend_label = htf_trend
            mode = "HTF {}".format(htf_trend)
        else:
            buy_trend = ema20 > ema50 > ema200
            sell_trend = ema20 < ema50 < ema200
            trend_label = (UPTREND if buy_trend else
                           DOWNTREND if sell_trend else SIDEWAYS)
            mode = "EMA align"

        # Nen xac nhan: bat buoc hay khong
        buy_conf = bool(bull) if REQUIRE_PATTERN else True
        sell_conf = bool(bear) if REQUIRE_PATTERN else True

        # ---------- BUY ----------
        if buy_trend and strong and pullback and buy_conf:
            note = bull if bull else "no-pattern"
            return SignalEngine._make(
                BUY, UPTREND, STRONG,
                "{} + EMA20>EMA50 + ADX {:.1f} + Pullback + {}".format(mode, adx, note),
                ema20, ema50, ema200, adx, atr, rsi, bull,
            )

        # ---------- SELL ----------
        if sell_trend and strong and pullback and sell_conf:
            note = bear if bear else "no-pattern"
            return SignalEngine._make(
                SELL, DOWNTREND, STRONG,
                "{} + EMA20<EMA50 + ADX {:.1f} + Pullback + {}".format(mode, adx, note),
                ema20, ema50, ema200, adx, atr, rsi, bear,
            )

        # ---------- NO TRADE ----------
        if htf_trend == SIDEWAYS:
            reason = "Khung lon di ngang (HTF SIDEWAYS)"
        elif not (buy_trend or sell_trend):
            reason = "Chua thuan trend lon / EMA20-50 chua xep hang"
        elif not strong:
            reason = "ADX yeu ({:.2f} <= {:g})".format(adx, ADX_MIN)
        elif not pullback:
            reason = "Gia chua pullback ve EMA (Close={:.2f})".format(close_price)
        else:
            reason = "Thieu nen xac nhan (REQUIRE_PATTERN=1)"

        return SignalEngine._make(
            NO_TRADE, trend_label, WEAK, reason,
            ema20, ema50, ema200, adx, atr, rsi, bull or bear,
        )
