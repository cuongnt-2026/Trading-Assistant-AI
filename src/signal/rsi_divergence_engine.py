# -*- coding: utf-8 -*-
"""
RSI Divergence Engine - phan ky gia/RSI, bat dao chieu SOM HON EMA cross/Supertrend.

Y tuong: EMA cross / Supertrend chi bao dao chieu SAU KHI 2 duong (hoac gia vs
duong) da thuc su cham nhau - luon co do tre. Phan ky RSI thi khac: no phat
hien luc DONG LUC (momentum) da yeu di truoc khi gia kip dao chieu, bang cach
so sanh 2 diem swing GAN NHAT cua gia voi 2 diem swing tuong ung cua RSI:

  Bullish (BUY):  gia tao DAY sau THAP hon day truoc (Lower Low) NHUNG RSI tai
                  day sau lai CAO hon RSI tai day truoc (Higher Low tren RSI)
                  -> luc ban da yeu dan, de dao chieu tang.
  Bearish (SELL): gia tao DINH sau CAO hon dinh truoc (Higher High) NHUNG RSI
                  tai dinh sau lai THAP hon RSI tai dinh truoc (Lower High tren
                  RSI) -> luc mua da yeu dan, de dao chieu giam.

Chi bao tin hieu khi pivot gia lien quan VUA duoc xac nhan tai nen hien tai
(tranh bao lai nhieu lan cho cung 1 phan ky cu).
"""
import pandas as pd
from ta.momentum import RSIIndicator as TaRSIIndicator

from src.signal.constants import (
    BUY, SELL, NO_TRADE, SIDEWAYS, STRONG, WEAK,
    DIV_PIVOT, DIV_LOOKBACK, DIV_RSI_PERIOD, DIV_MIN_RSI_DIFF,
)
from src.signal.signal import Signal


def _pivots(win, k):
    """Giong structure_engine._pivots: tim dinh/day can k nen 2 ben xac nhan."""
    highs, lows = [], []
    for i in range(k, len(win) - k):
        seg = win[i - k:i + k + 1]
        if win[i].high == max(c.high for c in seg):
            highs.append((i, win[i].high))
        if win[i].low == min(c.low for c in seg):
            lows.append((i, win[i].low))
    return highs, lows


def _rsi_series(win, period):
    """RSI cho TUNG nen trong win (khac IndicatorService.rsi - chi tra 1 gia tri cuoi)."""
    closes = pd.Series([c.close for c in win])
    return TaRSIIndicator(close=closes, window=period).rsi()


class RSIDivergenceEngine:

    @staticmethod
    def _mk(action, reason, ema20, ema50, ema200, adx, atr, rsi):
        return Signal(action=action, trend="MEANREV" if action in (BUY, SELL) else SIDEWAYS,
                      strength=STRONG if action in (BUY, SELL) else WEAK,
                      reason=reason, ema20=ema20, ema50=ema50, ema200=ema200,
                      adx=adx, atr=round(atr, 5), rsi=round(rsi, 2),
                      pattern="RSIDivergence" if action in (BUY, SELL) else "")

    @staticmethod
    def analyze(candles, ema20, ema50, ema200, adx, atr=0.0, rsi=0.0, htf_trend=None):
        close = candles[-1].close
        if not atr or atr <= 0:
            atr = abs(close) * 0.001

        k = DIV_PIVOT
        win = candles[-DIV_LOOKBACK:] if len(candles) >= DIV_LOOKBACK else candles[:]
        n = len(win)
        # RSI can du nen "am" (khoi dong) truoc DIV_LOOKBACK, neu khong RSI dau cua so se khong chinh xac
        min_needed = 2 * k + 5
        if n < min_needed or n < DIV_RSI_PERIOD + 2:
            return RSIDivergenceEngine._mk(NO_TRADE, "Chua du nen de tim phan ky RSI",
                                           ema20, ema50, ema200, adx, atr, rsi)

        highs, lows = _pivots(win, k)
        if len(highs) < 2 or len(lows) < 2:
            return RSIDivergenceEngine._mk(NO_TRADE, "Chua du dinh/day swing de so sanh phan ky",
                                           ema20, ema50, ema200, adx, atr, rsi)

        rsi_series = _rsi_series(win, DIV_RSI_PERIOD)
        confirm_pos = n - 1 - k  # pivot vua duoc xac nhan tai nen hien tai

        # ----- Bullish divergence: day gia thap hon, day RSI cao hon -----
        (i2, low2) = lows[-1]
        (i1, low1) = lows[-2]
        fresh_low = i2 == confirm_pos
        if fresh_low and low2 < low1:
            rsi_low2 = rsi_series.iloc[i2]
            rsi_low1 = rsi_series.iloc[i1]
            if pd.notna(rsi_low1) and pd.notna(rsi_low2) and (rsi_low2 - rsi_low1) >= DIV_MIN_RSI_DIFF:
                return RSIDivergenceEngine._mk(
                    BUY,
                    "Phan ky tang: gia day {:.5g}->{:.5g} (thap hon) nhung RSI {:.1f}->{:.1f} "
                    "(cao hon) - luc ban yeu di".format(low1, low2, rsi_low1, rsi_low2),
                    ema20, ema50, ema200, adx, atr, float(rsi_low2))

        # ----- Bearish divergence: dinh gia cao hon, dinh RSI thap hon -----
        (j2, high2) = highs[-1]
        (j1, high1) = highs[-2]
        fresh_high = j2 == confirm_pos
        if fresh_high and high2 > high1:
            rsi_high2 = rsi_series.iloc[j2]
            rsi_high1 = rsi_series.iloc[j1]
            if pd.notna(rsi_high1) and pd.notna(rsi_high2) and (rsi_high1 - rsi_high2) >= DIV_MIN_RSI_DIFF:
                return RSIDivergenceEngine._mk(
                    SELL,
                    "Phan ky giam: gia dinh {:.5g}->{:.5g} (cao hon) nhung RSI {:.1f}->{:.1f} "
                    "(thap hon) - luc mua yeu di".format(high1, high2, rsi_high1, rsi_high2),
                    ema20, ema50, ema200, adx, atr, float(rsi_high2))

        if not (fresh_low or fresh_high):
            reason = "Chua co pivot gia moi duoc xac nhan"
        else:
            reason = "Co pivot moi nhung khong lech huong gia/RSI (khong phan ky)"
        return RSIDivergenceEngine._mk(NO_TRADE, reason, ema20, ema50, ema200, adx, atr, rsi)
