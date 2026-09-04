# -*- coding: utf-8 -*-
"""
EmaCrossWatcher - theo doi 2 duong EMA (mac dinh 20/50) tren 1 cap symbol+khung,
PHAT HIEN va tra ve (KHONG tu gui mail, KHONG mutate state - de caller quyet dinh
sau khi gui mail thanh cong, giong het quy uoc _handle_supertrend/_scan_discrete
trong run_cloud.py):

  - 'crossed' : EMA nhanh vua DOI DAU so voi EMA cham so voi nen truoc do (vua cat cheo)
  - 'about'   : 2 duong CHUA cat nhau nhung khoang cach dang hep dan lai, da nho hon
                nguong EMACROSS_NEAR_ATR (theo boi so ATR) -> "sap cat cheo"

Day la mot module CANH BAO KY THUAT DOC LAP - khong dung Signal/TradePlan, khong dung
den trong SignalService/TradeService, nen KHONG anh huong gi den logic vao/thoat lenh
cua bat ky chien luoc dang chay that nao.

Quy uoc "goc" (angle_fast/angle_slow, don vi do):
Goc thay bang mat tren chart phu thuoc ty le zoom truc gia/truc thoi gian nen KHONG the
tinh lai giong het - o day dung mot quy uoc CHUAN HOA THEO ATR de so sanh duoc giua cac
symbol/khung khac nhau (vang bien dong hang chuc USD/nen, EURUSD bien dong vai pip/nen):
    do_doc = (EMA[-1] - EMA[-1-N]) / N          # doi thay trung binh moi nen
    goc    = degrees(atan(do_doc / ATR))        # doc = 1*ATR/nen  ~= 45 do
Goc cang gan 90 do = xu huong doc/dot ngot; cang gan 0 do = di ngang phang. Day CHI la
mot proxy do dung de so sanh tuong doi, khong phai goc nhin thay tren TradingView.
"""
import math

from src.indicators.indicator_service import IndicatorService
from src.signal.constants import (
    EMACROSS_EMA_FAST, EMACROSS_EMA_SLOW, EMACROSS_NEAR_ATR,
    EMACROSS_RESET_ATR, EMACROSS_ANGLE_LOOKBACK,
)


def _ema_series(candles, period, n):
    """EMA(period) tai n diem cuoi cung (diem thu i = EMA tinh tren candles[:end]).
    Tra ve None cho nhung diem chua du du lieu warm-up (end < period)."""
    total = len(candles)
    out = []
    for i in range(n):
        end = total - n + 1 + i
        if end < period:
            out.append(None)
            continue
        out.append(IndicatorService.ema(candles[:end], period))
    return out


def _angle_deg(series, atr):
    vals = [v for v in series if v is not None]
    if len(vals) < 2 or not atr:
        return 0.0
    slope = (vals[-1] - vals[0]) / (len(vals) - 1)
    return round(math.degrees(math.atan(slope / atr)), 1)


class EmaCrossWatcher:
    """State-less ngoai tru phan 'reset' (xem check()). Goi check() moi lan co nen moi,
    truyen vao 1 dict `state` dung chung (vd cloud_state.json) + `key` rieng cho cap
    symbol+khung nay (vd "EMACROSS XAUUSD M15")."""

    @staticmethod
    def check(candles, state, key):
        need = EMACROSS_EMA_SLOW + EMACROSS_ANGLE_LOOKBACK + 2
        if len(candles) < need:
            return None

        atr = IndicatorService.atr(candles)
        if not atr:
            return None

        n = EMACROSS_ANGLE_LOOKBACK + 1
        fast_s = _ema_series(candles, EMACROSS_EMA_FAST, n)
        slow_s = _ema_series(candles, EMACROSS_EMA_SLOW, n)
        if None in (fast_s[-1], slow_s[-1], fast_s[-2], slow_s[-2]):
            return None

        gap = fast_s[-1] - slow_s[-1]
        gap_prev = fast_s[-2] - slow_s[-2]
        last = candles[-1]
        ts = str(last.time)
        st = state.setdefault(key, {})
        gap_ratio = abs(gap) / atr

        # --- VUA cat cheo: dau cua gap doi nguoc so voi nen truoc ---
        if gap_prev != 0 and (gap > 0) != (gap_prev > 0):
            if st.get("crossed_ts") == ts:
                return None
            return {
                "type": "crossed",
                "direction": "up" if gap > 0 else "down",
                "price": last.close,
                "candle_time": ts,
                "gap_atr": round(gap / atr, 3),
                "angle_fast": _angle_deg(fast_s, atr),
                "angle_slow": _angle_deg(slow_s, atr),
                "ema_fast": EMACROSS_EMA_FAST,
                "ema_slow": EMACROSS_EMA_SLOW,
                "_ts": ts,
            }

        # --- SAP cat cheo: khoang cach con nho HON nguong VA dang hep dan (chua doi dau) ---
        if gap_ratio <= EMACROSS_NEAR_ATR and abs(gap) < abs(gap_prev):
            if st.get("about_ts") == ts:
                return None
            d_gap = abs(gap_prev) - abs(gap)
            eta_bars = round(abs(gap) / d_gap, 1) if d_gap > 1e-9 else None
            return {
                "type": "about",
                "direction": "up" if gap < 0 else "down",
                "price": last.close,
                "candle_time": ts,
                "gap_atr": round(gap / atr, 3),
                "angle_fast": _angle_deg(fast_s, atr),
                "angle_slow": _angle_deg(slow_s, atr),
                "ema_fast": EMACROSS_EMA_FAST,
                "ema_slow": EMACROSS_EMA_SLOW,
                "eta_bars": eta_bars,
                "_ts": ts,
            }

        # --- Khoang cach da no rong lai qua nguong reset -> quen lan "sap cheo" cu, cho
        # phep bao lai tu dau khi 2 duong ap sat nhau lan sau. Housekeeping thuan tuy,
        # KHONG lien quan gui mail nen ghi thang vao state, khong can cho ai xac nhan. ---
        if gap_ratio > EMACROSS_RESET_ATR:
            st["about_ts"] = None

        return None
