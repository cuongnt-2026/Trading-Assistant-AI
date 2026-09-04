# -*- coding: utf-8 -*-
"""
Bollinger Squeeze Breakout Engine - NGUOC lai voi Bollinger Mean Reversion dang co.

BollingerEngine (Mean Reversion) FADE lai khi gia cham bien (danh nguoc trung
binh). Engine nay lam nguoc lai: TRADE THEO huong pha vo, sau khi bien
Bollinger da "that co lai" (squeeze) - dau hieu thi truong dang tich luy/nen
truoc khi bung no manh. Squeeze cang chat thi cu no thuong cang manh.

Luat:
  1) Do rong bien (bandwidth = (upper-lower)/mid) tai NEN TRUOC nen tin hieu
     phai thuoc nhom HEP NHAT (<= percentile SQZ_PERCENTILE) trong SQZ_LOOKBACK
     nen gan day -> xac nhan dang squeeze.
  2) Nen tin hieu (nen hien tai) phai DONG MANH ra ngoai bien:
       BUY:  close > upper VA than nen (close-open) >= SQZ_BREAKOUT_CLOSE * range nen
       SELL: close < lower VA than nen (open-close) >= SQZ_BREAKOUT_CLOSE * range nen
"""
import pandas as pd

from src.signal.constants import (
    BUY, SELL, NO_TRADE, SIDEWAYS, STRONG, WEAK,
    SQZ_BB_PERIOD, SQZ_BB_MULT, SQZ_LOOKBACK, SQZ_PERCENTILE, SQZ_BREAKOUT_CLOSE,
)
from src.signal.signal import Signal


def _bandwidth_series(win, period, mult):
    """Bandwidth = (upper-lower)/mid cho TUNG nen trong win (EMA giua + std cuon)."""
    closes = pd.Series([c.close for c in win])
    mid = closes.ewm(span=period, adjust=False).mean()
    std = closes.rolling(window=period).std(ddof=0)
    upper = mid + mult * std
    lower = mid - mult * std
    mid_safe = mid.replace(0, pd.NA)
    return (upper - lower) / mid_safe, upper, lower, mid


class BollingerSqueezeEngine:

    @staticmethod
    def _mk(action, reason, ema20, ema50, ema200, adx, atr, rsi):
        return Signal(action=action, trend="BREAKOUT" if action in (BUY, SELL) else SIDEWAYS,
                      strength=STRONG if action in (BUY, SELL) else WEAK,
                      reason=reason, ema20=ema20, ema50=ema50, ema200=ema200,
                      adx=adx, atr=round(atr, 5), rsi=round(rsi, 2),
                      pattern="BollingerSqueeze" if action in (BUY, SELL) else "")

    @staticmethod
    def analyze(candles, ema20, ema50, ema200, adx, atr=0.0, rsi=0.0, htf_trend=None):
        last = candles[-1]
        close = last.close
        if not atr or atr <= 0:
            atr = abs(close) * 0.001

        win = candles[-SQZ_LOOKBACK:] if len(candles) >= SQZ_LOOKBACK else candles[:]
        n = len(win)
        if n < SQZ_BB_PERIOD + 5:
            return BollingerSqueezeEngine._mk(NO_TRADE, "Chua du nen de tinh Bollinger Squeeze",
                                              ema20, ema50, ema200, adx, atr, rsi)

        bw, upper, lower, mid = _bandwidth_series(win, SQZ_BB_PERIOD, SQZ_BB_MULT)

        # Bandwidth tai nen TRUOC nen tin hieu (nen hien tai la nen breakout, dang no rong ra
        # nen KHONG tinh no vao tap lich su de xep hang percentile - neu khong se lam sai lech
        # nguong squeeze ngay dung luc can danh gia no nhat).
        prev_bw = bw.iloc[-2] if len(bw) >= 2 else None
        if prev_bw is None or pd.isna(prev_bw):
            return BollingerSqueezeEngine._mk(NO_TRADE, "Khong co du lieu bandwidth nen truoc",
                                              ema20, ema50, ema200, adx, atr, rsi)

        bw_hist = bw.iloc[:-1].dropna()
        if len(bw_hist) < 10:
            return BollingerSqueezeEngine._mk(NO_TRADE, "Chua du du lieu bandwidth de xep hang squeeze",
                                              ema20, ema50, ema200, adx, atr, rsi)

        threshold = bw_hist.quantile(SQZ_PERCENTILE / 100.0)
        is_squeeze = prev_bw <= threshold

        rng = last.high - last.low
        body_up = last.close - last.open
        body_down = last.open - last.close
        upper_now = upper.iloc[-1]
        lower_now = lower.iloc[-1]

        strong_up = rng > 0 and body_up >= SQZ_BREAKOUT_CLOSE * rng
        strong_down = rng > 0 and body_down >= SQZ_BREAKOUT_CLOSE * rng

        if is_squeeze and last.close > upper_now and strong_up:
            return BollingerSqueezeEngine._mk(
                BUY,
                "Squeeze (bandwidth {:.4f} <= nguong {:.4f}) + pha bien tren {:.5g} "
                "voi nen dong manh -> mua theo huong pha vo".format(prev_bw, threshold, upper_now),
                ema20, ema50, ema200, adx, atr, rsi)

        if is_squeeze and last.close < lower_now and strong_down:
            return BollingerSqueezeEngine._mk(
                SELL,
                "Squeeze (bandwidth {:.4f} <= nguong {:.4f}) + pha bien duoi {:.5g} "
                "voi nen dong manh -> ban theo huong pha vo".format(prev_bw, threshold, lower_now),
                ema20, ema50, ema200, adx, atr, rsi)

        if not is_squeeze:
            reason = "Bandwidth ({:.4f}) chua du hep (nguong {:.4f}) - chua phai luc squeeze".format(
                prev_bw, threshold)
        elif not (last.close > upper_now or last.close < lower_now):
            reason = "Dang squeeze nhung gia chua pha bien Bollinger"
        else:
            reason = "Dang squeeze, gia pha bien nhung nen dong chua du manh"
        return BollingerSqueezeEngine._mk(NO_TRADE, reason, ema20, ema50, ema200, adx, atr, rsi)
