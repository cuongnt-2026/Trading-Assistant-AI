# -*- coding: utf-8 -*-
"""
EMA50 Close Engine - chien luoc CHI 1 duong EMA50, theo y tuong CuongNT
(2026-09-17), dung truoc tien de BACKTEST xem gia co "chay dung xu huong
thi truong" theo 1 EMA don gian hay khong, truoc khi ban co vao lenh that.

Luat CuongNT (cap nhat lan 2, 2026-09-17 - CHI TINH LUC VUA CAT QUA, khong
phai cu dang o tren/duoi la tinh):
  Nen tu DUOI EMA50 CAT LEN TREN EMA50 (nen truoc dong cua duoi EMA50, nen
  nay cat dut khoat, than nen dong cua tren EMA50) => BUY.
  Nen tu TREN EMA50 CAT XUONG DUOI EMA50 (nen truoc dong cua tren EMA50,
  nen nay cat dut khoat, than nen dong cua duoi EMA50) => SELL.
(Ban dau CuongNT mo ta la "dong cua dut khoat tren/duoi EMA50 => BUY/SELL",
tuc la CU DANG o 1 phia la tinh - nhung sau khi test thay PF thap deu ca 3
khung (nhieu tin hieu lien tuc lien tiep khi gia duy tri 1 phia), CuongNT
doi lai chi tinh o candle VUA CAT QUA - moi nen tiep theo van dang o cung
phia se KHONG con tinh la tin hieu moi nua, tranh lap/spam tin hieu cung
1 huong nhieu lan lien tiep khi thi truong dang trending on dinh.)

Da THU bo loc ADX (theo yeu cau CuongNT) - khong con dung ADX de loc nua,
quay lai dung 2 bo sung ban dau:
  1) "Dut khoat" duoc hieu la CA THAN NEN (open VA close) nam gon 1 phia
     EMA50 - khong chi rieng gia dong cua (EMA50CLOSE_REQUIRE_FULL_BODY).
  2) Them 1 khoang dem nho theo ATR (EMA50CLOSE_BUFFER_ATR, mac dinh
     0.15x ATR14) - gia phai vuot EMA50 xa hon khoang dem nay.
Ca 2 ap dung cho CA nen hien tai (xac nhan cat dut khoat) LAN nen truoc do
(xac nhan nen truoc THUC SU dang o phia doi dien, khong phai cung dang
"lung lung" gan EMA50).

KHONG dung bo loc xu huong khung lon (htf_trend), KHONG dung ADX/RSI - dung
dung y "chi 1 duong EMA50" CuongNT yeu cau.

SL/TP: dung RiskManager.dynamic_levels() mac dinh (giong ema_pullback) qua
nhanh else cua TradeService.create(), vi day cung se la lenh that neu sau
nay quyet dinh bat len (sau khi qua backtest).
"""
from src.indicators.indicator_service import IndicatorService
from src.signal.constants import (
    BUY, SELL, NO_TRADE, UPTREND, DOWNTREND, SIDEWAYS, STRONG, WEAK,
    EMA50CLOSE_BUFFER_ATR, EMA50CLOSE_REQUIRE_FULL_BODY,
)
from src.signal.signal import Signal


class Ema50CloseEngine:

    @staticmethod
    def _mk(action, reason, ema50, adx, atr, rsi):
        trend = UPTREND if action == BUY else DOWNTREND if action == SELL else SIDEWAYS
        return Signal(action=action, trend=trend,
                      strength=STRONG if action in (BUY, SELL) else WEAK,
                      reason=reason,
                      # Chi co 1 duong EMA50 - dung lai truong ema20/ema200
                      # (=ema50) de khong phai mo rong schema Signal.
                      ema20=ema50, ema50=ema50, ema200=ema50,
                      adx=adx, atr=round(atr, 5), rsi=round(rsi, 2),
                      pattern="EMA50Close" if action in (BUY, SELL) else "")

    @staticmethod
    def _decisive_side(close, open_, ema, buf):
        """Tra ve 'above' neu nen (theo dung nghia 'dut khoat' - xem module
        docstring) nam gon tren ema, 'below' neu nam gon duoi, None neu con
        lung lung/khong du dut khoat."""
        body_lo, body_hi = (open_, close) if open_ <= close else (close, open_)
        if close >= ema + buf and (not EMA50CLOSE_REQUIRE_FULL_BODY or body_lo > ema):
            return "above"
        if close <= ema - buf and (not EMA50CLOSE_REQUIRE_FULL_BODY or body_hi < ema):
            return "below"
        return None

    @staticmethod
    def analyze(candles, ema50, adx=0.0, atr=0.0, rsi=0.0):
        last = candles[-1]
        close = last.close
        open_ = last.open
        if not atr or atr <= 0:
            atr = abs(close) * 0.001
        buf = EMA50CLOSE_BUFFER_ATR * atr

        if len(candles) < 51:
            return Ema50CloseEngine._mk(
                NO_TRADE, "Chua du nen de xac dinh EMA50 nen truoc do (can >= 51 nen)",
                ema50, adx, atr, rsi)

        prev = candles[-2]
        prev_ema50 = IndicatorService.ema(candles[:-1], 50)

        cur_side = Ema50CloseEngine._decisive_side(close, open_, ema50, buf)
        prev_side = Ema50CloseEngine._decisive_side(prev.close, prev.open, prev_ema50, buf)

        if cur_side == "above" and prev_side != "above":
            return Ema50CloseEngine._mk(
                BUY, "Nen truoc chua o han tren EMA50 ({:.5g}), nen nay dut khoat "
                     "CAT LEN TREN EMA50 {:.5g} (dong cua {:.5g})".format(
                         prev_ema50, ema50, close),
                ema50, adx, atr, rsi)
        if cur_side == "below" and prev_side != "below":
            return Ema50CloseEngine._mk(
                SELL, "Nen truoc chua o han duoi EMA50 ({:.5g}), nen nay dut khoat "
                      "CAT XUONG DUOI EMA50 {:.5g} (dong cua {:.5g})".format(
                          prev_ema50, ema50, close),
                ema50, adx, atr, rsi)
        if cur_side is not None:
            return Ema50CloseEngine._mk(
                NO_TRADE, "Van dang o han {} EMA50 nhung KHONG phai lan cat moi (nen "
                          "truoc da o cung phia roi) - bo qua de tranh lap tin hieu".format(
                              "tren" if cur_side == "above" else "duoi"),
                ema50, adx, atr, rsi)
        return Ema50CloseEngine._mk(
            NO_TRADE, "Gia {:.5g} con qua sat/xen ke EMA50 {:.5g}, chua dut khoat".format(
                close, ema50), ema50, adx, atr, rsi)
