# -*- coding: utf-8 -*-
"""
EmaTrendWatcher - CANH BAO rieng tren EMA20/50/200 (mac dinh), thay the cho
EmaCrossWatcher cu (EMA20/50 tho, khong loc trend). Theo yeu cau CuongNT
(2026-09-14): chi ap dung XAUUSD khung M15, gom 2 loai tin hieu doc lap:

  1) check_triple() - "Ca 3 EMA cung hoi tu roi tach": khi khoang cach GIUA CA 3 CAP
     duong (20-50, 50-200, 20-200) deu co lai duoi nguong EMATREND_TRIPLE_NEAR_ATR
     (theo boi so ATR) cung mot luc, danh dau "dang hoi tu". Dung EMATREND_TRIPLE_
     CONFIRM_BARS nen SAU do (mac dinh 3), kiem tra lai thu tu xep hang:
        EMA20 > EMA50 > EMA200 (hoan toan thuan tang) -> tin hieu "triple", huong up
        EMA20 < EMA50 < EMA200 (hoan toan thuan giam) -> tin hieu "triple", huong down
        (thu tu khac / con lan lon) -> KHONG co tin hieu, chi don dep trang thai cho.
     Day la tin hieu HIEM (ca 3 duong it khi hoi tu dong thoi tren M15) nhung "nang",
     bao hieu kha nang xac lap/dao chieu mot trend lon hon.

  2) check_cross() - "EMA20/50 cat nhau, LOC theo che do EMA200": chi bao khi EMA200
     da xac nhan dung huong lam "bo loc" (regime), giong het EmaCrossWatcher cu ve
     co che sap/vua cat cheo (nguong EMATREND_NEAR_ATR/RESET_ATR theo ATR) nhung
     THEM dieu kien: ca EMA20 VA EMA50 phai cung nam MOT PHIA cua EMA200 truoc khi
     tinh la tin hieu hop le:
        EMA20 & EMA50 deu DUOI EMA200 (downtrend) + EMA20 sap/vua cat XUONG EMA50
            -> tin hieu "cross", huong down (de xuat SELL)
        EMA20 & EMA50 deu TREN EMA200 (uptrend)   + EMA20 sap/vua cat LEN EMA50
            -> tin hieu "cross", huong up (de xuat BUY)
     Cross xay ra khi che do EMA200 chua ro (lan lon) hoac nguoc huong voi cross thi
     KHONG bao - day chinh la diem khac biet quan trong so voi EmaCrossWatcher cu
     (ban cu bao ca luc thi truong di ngang/ranh cheo gia, gay nhieu).

Ca hai ham deu STATE-LESS ngoai tru phan "pending/reset" luu trong `state[key]`
(dict dung chung, vd cloud_state.json) - KHONG tu gui mail, KHONG mutate state truoc
khi caller xac nhan gui mail thanh cong (giong quy uoc EmaCrossWatcher/_scan_discrete
trong run_cloud.py).

Day la module CANH BAO KY THUAT DOC LAP - khong dung Signal/TradePlan, khong lien
quan SignalService/TradeService, KHONG anh huong gi den logic vao/thoat lenh that.
"""
from src.indicators.indicator_service import IndicatorService
from src.signal.constants import (
    EMATREND_EMA_FAST, EMATREND_EMA_MID, EMATREND_EMA_SLOW,
    EMATREND_NEAR_ATR, EMATREND_RESET_ATR,
    EMATREND_TRIPLE_NEAR_ATR, EMATREND_TRIPLE_CONFIRM_BARS,
)


def _ema_last2(candles, period):
    """EMA(period) tai nen cuoi va nen truoc do. None,None neu chua du du lieu."""
    if len(candles) < period + 1:
        return None, None
    curr = IndicatorService.ema(candles, period)
    prev = IndicatorService.ema(candles[:-1], period)
    return curr, prev


class EmaTrendWatcher:

    @staticmethod
    def check_triple(candles, state, key):
        need = EMATREND_EMA_SLOW + 2
        if len(candles) < need:
            return None
        atr = IndicatorService.atr(candles)
        if not atr:
            return None

        fast = IndicatorService.ema(candles, EMATREND_EMA_FAST)
        mid = IndicatorService.ema(candles, EMATREND_EMA_MID)
        slow = IndicatorService.ema(candles, EMATREND_EMA_SLOW)

        last = candles[-1]
        ts = str(last.time)
        st = state.setdefault(key, {})

        gap_fm = abs(fast - mid) / atr
        gap_ms = abs(mid - slow) / atr
        gap_fs = abs(fast - slow) / atr
        converged = (gap_fm <= EMATREND_TRIPLE_NEAR_ATR
                     and gap_ms <= EMATREND_TRIPLE_NEAR_ATR
                     and gap_fs <= EMATREND_TRIPLE_NEAR_ATR)

        pending_ts = st.get("triple_pending_ts")
        if pending_ts:
            # Tim lai nen bat dau hoi tu trong cua so candles hien tai de dem so nen
            # da troi qua - KHONG phu thuoc so lan check() duoc goi (co the goi nhieu
            # lan hon 1 lan/nen trong thuc te).
            idx = None
            for i, c in enumerate(candles):
                if str(c.time) == pending_ts:
                    idx = i
                    break
            if idx is None:
                # Nen hoi tu da roi khoi cua so du lieu (qua cu) -> bo cuoc, don dep.
                st["triple_pending_ts"] = None
            else:
                elapsed = (len(candles) - 1) - idx
                if elapsed >= EMATREND_TRIPLE_CONFIRM_BARS:
                    st["triple_pending_ts"] = None  # luon reset, tranh bao lai lien tuc
                    if fast > mid > slow:
                        return {
                            "type": "triple", "direction": "up",
                            "price": last.close, "candle_time": ts,
                            "ema_fast": fast, "ema_mid": mid, "ema_slow": slow,
                            "confirm_bars": elapsed,
                            "ef": EMATREND_EMA_FAST, "em": EMATREND_EMA_MID, "es": EMATREND_EMA_SLOW,
                            "_ts": ts,
                        }
                    if fast < mid < slow:
                        return {
                            "type": "triple", "direction": "down",
                            "price": last.close, "candle_time": ts,
                            "ema_fast": fast, "ema_mid": mid, "ema_slow": slow,
                            "confirm_bars": elapsed,
                            "ef": EMATREND_EMA_FAST, "em": EMATREND_EMA_MID, "es": EMATREND_EMA_SLOW,
                            "_ts": ts,
                        }
                    return None  # het han dem nhung thu tu con lan lon -> khong tin hieu
                return None  # dang cho, chua du so nen
        elif converged:
            st["triple_pending_ts"] = ts

        return None

    @staticmethod
    def check_cross(candles, state, key):
        need = EMATREND_EMA_SLOW + 2
        if len(candles) < need:
            return None
        atr = IndicatorService.atr(candles)
        if not atr:
            return None

        fast, fast_prev = _ema_last2(candles, EMATREND_EMA_FAST)
        mid, mid_prev = _ema_last2(candles, EMATREND_EMA_MID)
        slow = IndicatorService.ema(candles, EMATREND_EMA_SLOW)
        if None in (fast, fast_prev, mid, mid_prev):
            return None

        regime_down = fast < slow and mid < slow
        regime_up = fast > slow and mid > slow
        st = state.setdefault(key, {})
        if not (regime_down or regime_up):
            # Che do EMA200 chua ro rang (EMA20/EMA50 khac phia nhau) -> khong tinh la
            # tin hieu hop le theo dung yeu cau (loc nhieu luc thi truong dang gianh
            # giat quanh EMA200). Van cho reset "about" o duoi neu can.
            need_direction = None
        else:
            need_direction = "down" if regime_down else "up"

        gap = fast - mid
        gap_prev = fast_prev - mid_prev
        gap_ratio = abs(gap) / atr
        last = candles[-1]
        ts = str(last.time)

        if need_direction is not None:
            # --- VUA cat cheo: dau cua gap doi nguoc so voi nen truoc ---
            if gap_prev != 0 and (gap > 0) != (gap_prev > 0):
                actual_dir = "up" if gap > 0 else "down"
                if actual_dir == need_direction:
                    if st.get("crossed_ts") != ts:
                        return {
                            "type": "crossed", "direction": actual_dir,
                            "price": last.close, "candle_time": ts,
                            "gap_atr": round(gap / atr, 3),
                            "ema_fast": fast, "ema_mid": mid, "ema_slow": slow,
                            "ef": EMATREND_EMA_FAST, "em": EMATREND_EMA_MID, "es": EMATREND_EMA_SLOW,
                            "_ts": ts,
                        }
                return None

            # --- SAP cat cheo: khoang cach nho hon nguong VA dang hep dan (chua doi dau) ---
            if gap_ratio <= EMATREND_NEAR_ATR and abs(gap) < abs(gap_prev):
                about_dir = "up" if gap < 0 else "down"
                if about_dir == need_direction:
                    if st.get("about_ts") != ts:
                        d_gap = abs(gap_prev) - abs(gap)
                        eta_bars = round(abs(gap) / d_gap, 1) if d_gap > 1e-9 else None
                        return {
                            "type": "about", "direction": about_dir,
                            "price": last.close, "candle_time": ts,
                            "gap_atr": round(gap / atr, 3), "eta_bars": eta_bars,
                            "ema_fast": fast, "ema_mid": mid, "ema_slow": slow,
                            "ef": EMATREND_EMA_FAST, "em": EMATREND_EMA_MID, "es": EMATREND_EMA_SLOW,
                            "_ts": ts,
                        }

        if gap_ratio > EMATREND_RESET_ATR:
            st["about_ts"] = None

        return None
