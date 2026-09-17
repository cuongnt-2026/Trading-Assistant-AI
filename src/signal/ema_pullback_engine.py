# -*- coding: utf-8 -*-
"""
EMA Pullback Engine - chien luoc VAO LENH THAT (co Entry/SL/TP), theo y tuong
CuongNT (2026-09-17):

  H1 la khung XU HUONG:
    20 > 50 > 100 > 200  => xu huong TANG => CHI canh BUY, khong canh SELL.
    20 < 50 < 100 < 200  => xu huong GIAM => CHI canh SELL, khong canh BUY.
    Sai thu tu (ke ca H1 dang sideway/dang chuyen giao) => KHONG giao dich.

  M15 la khung DIEM VAO:
    Cho gia HOI VE 1 trong 3 duong EMA20/50/100 (M15), roi cho THEM 1 nen xac
    nhan dao chieu (Bullish/Bearish Engulfing, Hammer/Shooting Star - xem
    src/signal/patterns.py) truoc khi vao - KHONG vao ngay khi vua cham EMA,
    vi gia hay xuyen qua EMA roi bat lai that, cham thoi chua chac an.

Ngoai 2 dieu kien goc cua CuongNT, them 2 lop loc H1 (khong doi y tuong goc,
chi giup tranh vao lenh luc xu huong H1 sap can da/sap sideway - van la 1
diem yeu pho bien cua he thong kieu "thu tu EMA" don thuan):
  (1) EMA20 H1 phai dang DOC dung huong (so voi EMAPULLBACK_SLOPE_LOOKBACK nen
      truoc) - neu EMA20 dang di ngang/be gay du dung thu tu van coi la chua
      du tin cay.
  (2) Khoang cach EMA20-EMA50 H1 phai >= EMAPULLBACK_SPACING_ATR_MULT x ATR14
      H1 - EMA dinh sat nhau (du dung thu tu) thuong bao hieu sap sideway.

SL/TP: KHONG tu tinh rieng, dung LAI CHINH XAC RiskManager.dynamic_levels()
(swing high/low + cau truc khang cu/ho tro + san R:R, xem src/trade/
risk_manager.py) - day la chien luoc vao lenh THAT nen phai nhat quan voi
breakout/bollinger/london, khong bia cong thuc rieng. TradeService.create()
tu dong dung nhanh else (RiskManager.dynamic_levels) cho strategy nay vi
khong nam trong danh sach cac strategy co cong thuc rieng.

Khac voi EmaTrendWatcher/EmaCrossWatcher (chi la CANH BAO tham khao, khong
Entry/SL/TP that): day la chien luoc VAO LENH THAT, quet DOC LAP qua ham
_scan_ema_pullback() trong run_cloud.py (giong bollinger/london), ghi vao
CHUNG cloud_signals.json (KHONG dung ematrend_history.json rieng).
"""
from src.indicators.indicator_service import IndicatorService
from src.signal.constants import (
    BUY, SELL, NO_TRADE, UPTREND, DOWNTREND, SIDEWAYS, STRONG, WEAK,
    EMAPULLBACK_SLOPE_LOOKBACK, EMAPULLBACK_SPACING_ATR_MULT,
    EMAPULLBACK_PULLBACK_ATR, EMAPULLBACK_PULLBACK_LOOKBACK,
)
from src.signal.signal import Signal
from src.signal.patterns import bullish_pattern, bearish_pattern

# So nen H1 toi thieu can co de tinh EMA200 + doc EMA20 lui EMAPULLBACK_SLOPE_LOOKBACK nen.
_MIN_H1_CANDLES = 200 + EMAPULLBACK_SLOPE_LOOKBACK


class EmaPullbackEngine:

    @staticmethod
    def _mk(action, trend, strength, reason, ema20, ema50, ema200, adx, atr, rsi, pattern=""):
        return Signal(action=action, trend=trend, strength=strength, reason=reason,
                      ema20=ema20, ema50=ema50, ema200=ema200, adx=adx,
                      atr=round(atr, 5), rsi=round(rsi, 2), pattern=pattern)

    @staticmethod
    def h1_trend(h1_candles):
        """Xac dinh xu huong H1 theo thu tu chat 4 EMA + loc doc EMA20 + loc
        khoang cach EMA20-EMA50 (xem docstring module). Tra ve (trend, ly_do)
        voi trend la UPTREND|DOWNTREND|SIDEWAYS."""
        if not h1_candles or len(h1_candles) < _MIN_H1_CANDLES:
            return SIDEWAYS, "H1 chua du nen (can >= {})".format(_MIN_H1_CANDLES)

        e20 = IndicatorService.ema(h1_candles, 20)
        e50 = IndicatorService.ema(h1_candles, 50)
        e100 = IndicatorService.ema(h1_candles, 100)
        e200 = IndicatorService.ema(h1_candles, 200)
        atr_h1 = IndicatorService.atr(h1_candles, 14)
        e20_prev = IndicatorService.ema(h1_candles[:-EMAPULLBACK_SLOPE_LOOKBACK], 20)

        spacing_ok = atr_h1 > 0 and abs(e20 - e50) >= EMAPULLBACK_SPACING_ATR_MULT * atr_h1

        if e20 > e50 > e100 > e200:
            if e20 <= e20_prev:
                return SIDEWAYS, "H1 dung thu tu tang nhung EMA20 chua doc len (sap sideway/dao chieu)"
            if not spacing_ok:
                return SIDEWAYS, "H1 dung thu tu tang nhung EMA20/50 qua sat nhau (< {:g}x ATR14 H1)".format(
                    EMAPULLBACK_SPACING_ATR_MULT)
            return UPTREND, "H1: EMA20>50>100>200, EMA20 dang doc len, du rong (>= {:g}x ATR)".format(
                EMAPULLBACK_SPACING_ATR_MULT)

        if e20 < e50 < e100 < e200:
            if e20 >= e20_prev:
                return SIDEWAYS, "H1 dung thu tu giam nhung EMA20 chua doc xuong (sap sideway/dao chieu)"
            if not spacing_ok:
                return SIDEWAYS, "H1 dung thu tu giam nhung EMA20/50 qua sat nhau (< {:g}x ATR14 H1)".format(
                    EMAPULLBACK_SPACING_ATR_MULT)
            return DOWNTREND, "H1: EMA20<50<100<200, EMA20 dang doc xuong, du rong (>= {:g}x ATR)".format(
                EMAPULLBACK_SPACING_ATR_MULT)

        return SIDEWAYS, "H1: thu tu 4 EMA chua ro xu huong (sideway/dang chuyen giao)"

    @staticmethod
    def analyze(candles_m15, h1_candles, ema20, ema50, ema200, adx, atr=0.0, rsi=0.0):
        """candles_m15: nen M15 (khung vao lenh). h1_candles: nen H1 (khung xu
        huong, fetch qua cache chung trong run_cloud.py - KHONG ton them
        request rieng vi XAUUSD H1 da duoc quet san cho breakout).
        ema20/ema50/ema200/adx/atr/rsi: chi bao tren M15 (candles_m15), giu
        dong bo chu ky voi cac engine khac (SignalEngine/BreakoutEngine)."""
        close = candles_m15[-1].close
        if not atr or atr <= 0:
            atr = abs(close) * 0.001

        trend, why = EmaPullbackEngine.h1_trend(h1_candles)
        if trend not in (UPTREND, DOWNTREND):
            return EmaPullbackEngine._mk(NO_TRADE, SIDEWAYS, WEAK, why,
                                         ema20, ema50, ema200, adx, atr, rsi)

        ema100_m15 = IndicatorService.ema(candles_m15, 100)
        zones = (("EMA20", ema20), ("EMA50", ema50), ("EMA100", ema100_m15))
        recent = candles_m15[-EMAPULLBACK_PULLBACK_LOOKBACK:]

        touched = None
        for name, lvl in zones:
            for c in recent:
                dist = (c.low - lvl) if trend == UPTREND else (lvl - c.high)
                # Hoi ve = gia (low cho BUY / high cho SELL) toi gan hoac xuyen
                # qua EMA mot chut (dist co the am neu xuyen qua that, van tinh
                # la da hoi ve), nhung khong qua xa (gioi han duoi boi
                # -EMAPULLBACK_PULLBACK_ATR*atr de tranh nhan lam gia da vuot
                # qua xa EMA ve phia nguoc trend).
                if -EMAPULLBACK_PULLBACK_ATR * atr <= dist <= EMAPULLBACK_PULLBACK_ATR * atr:
                    touched = name
                    break
            if touched:
                break

        if not touched:
            return EmaPullbackEngine._mk(NO_TRADE, trend, WEAK,
                "{} - nhung gia M15 chua hoi ve vung EMA20/50/100".format(why),
                ema20, ema50, ema200, adx, atr, rsi)

        if trend == UPTREND:
            pat = bullish_pattern(candles_m15)
            if not pat:
                return EmaPullbackEngine._mk(NO_TRADE, trend, WEAK,
                    "Da hoi ve {} (M15) nhung chua co nen xac nhan dao chieu tang".format(touched),
                    ema20, ema50, ema200, adx, atr, rsi)
            return EmaPullbackEngine._mk(BUY, trend, STRONG,
                "{}. M15 hoi ve {} + xac nhan {}".format(why, touched, pat),
                ema20, ema50, ema200, adx, atr, rsi, pat)

        pat = bearish_pattern(candles_m15)
        if not pat:
            return EmaPullbackEngine._mk(NO_TRADE, trend, WEAK,
                "Da hoi ve {} (M15) nhung chua co nen xac nhan dao chieu giam".format(touched),
                ema20, ema50, ema200, adx, atr, rsi)
        return EmaPullbackEngine._mk(SELL, trend, STRONG,
            "{}. M15 hoi ve {} + xac nhan {}".format(why, touched, pat),
            ema20, ema50, ema200, adx, atr, rsi, pat)
