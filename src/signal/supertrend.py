# -*- coding: utf-8 -*-
"""Supertrend indicator (mac dinh 10, 3). Tra ve (direction[], st_line[])."""


def supertrend(candles, period=10, mult=3.0):
    n = len(candles)
    if n == 0:
        return [], []
    tr = [0.0] * n
    for i in range(n):
        if i == 0:
            tr[i] = candles[i].high - candles[i].low
        else:
            h, l, pc = candles[i].high, candles[i].low, candles[i - 1].close
            tr[i] = max(h - l, abs(h - pc), abs(l - pc))
    atr = [0.0] * n
    atr[0] = tr[0]
    for i in range(1, n):
        atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period   # Wilder ATR

    direction = [1] * n
    st_line = [0.0] * n
    fu = [0.0] * n
    fl = [0.0] * n
    for i in range(n):
        hl2 = (candles[i].high + candles[i].low) / 2.0
        bu = hl2 + mult * atr[i]
        bl = hl2 - mult * atr[i]
        if i == 0:
            fu[i], fl[i] = bu, bl
            st_line[i] = bl
            continue
        fu[i] = bu if (bu < fu[i - 1] or candles[i - 1].close > fu[i - 1]) else fu[i - 1]
        fl[i] = bl if (bl > fl[i - 1] or candles[i - 1].close < fl[i - 1]) else fl[i - 1]
        if candles[i].close > fu[i - 1]:
            direction[i] = 1
        elif candles[i].close < fl[i - 1]:
            direction[i] = -1
        else:
            direction[i] = direction[i - 1]
        st_line[i] = fl[i] if direction[i] == 1 else fu[i]
    return direction, st_line
