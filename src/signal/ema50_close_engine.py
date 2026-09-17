# -*- coding: utf-8 -*-
"""
EMA50 Close Engine - chien luoc CHI 1 duong EMA50, theo y tuong CuongNT
(2026-09-17), dung truoc tien de BACKTEST xem gia co "chay dung xu huong
thi truong" theo 1 EMA don gian hay khong, truoc khi ban co vao lenh that.

Luat goc CuongNT:
  Gia dong cua DUT KHOAT tren EMA50 (than nen dong cua o tren EMA50 tro
  len) => BUY.
  Gia dong cua DUT KHOAT duoi EMA50 (than nen dong cua o duoi EMA50 tro
  xuong) => SELL.

Bo sung cua Claude (bat/tat duoc qua EMA50CLOSE_* trong constants.py, dat
ve "0" het la quay lai dung 100% luat goc, khong bo loc gi them):
  1) "Dut khoat" duoc hieu la CA THAN NEN (open VA close) nam gon 1 phia
     EMA50 - khong chi rieng gia dong cua (EMA50CLOSE_REQUIRE_FULL_BODY).
     Ly do: 1 nen mo cua duoi EMA50 nhung dong cua nhinh hon EMA50 vai
     tick la nen do du (indecision), chua phai la 1 cai "dut khoat" dung
     tinh than tu ban dung.
  2) Them 1 khoang dem nho theo ATR (EMA50CLOSE_BUFFER_ATR, mac dinh
     0.15x ATR14) - gia phai vuot EMA50 xa hon khoang dem nay. Ly do: 1
     duong EMA don le rat de bi "nhieu" (whipsaw) o thi truong sideway,
     dac biet khi khong co bo loc xu huong nao khac di kem.

KHONG dung bo loc xu huong khung lon (htf_trend), KHONG dung ADX/RSI de loc
- dung dung y "chi 1 duong EMA50" CuongNT yeu cau. Neu backtest cho thay
qua nhieu nhieu (whipsaw) o thi truong sideway, co the can bo sung bo loc
ADX (xac nhan dang trending) o buoc sau - CHUA lam trong ban dau nay.

SL/TP: dung RiskManager.dynamic_levels() mac dinh (giong ema_pullback) qua
nhanh else cua TradeService.create(), vi day cung se la lenh that neu sau
nay quyet dinh bat len (sau khi qua backtest).
"""
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
    def analyze(candles, ema50, adx=0.0, atr=0.0, rsi=0.0):
        last = candles[-1]
        close = last.close
        open_ = last.open
        if not atr or atr <= 0:
            atr = abs(close) * 0.001
        buf = EMA50CLOSE_BUFFER_ATR * atr

        body_lo, body_hi = (open_, close) if open_ <= close else (close, open_)

        buy_ok = close >= ema50 + buf
        sell_ok = close <= ema50 - buf
        if EMA50CLOSE_REQUIRE_FULL_BODY:
            buy_ok = buy_ok and body_lo > ema50
            sell_ok = sell_ok and body_hi < ema50

        if buy_ok:
            return Ema50CloseEngine._mk(
                BUY, "Dong cua {:.5g} dut khoat TREN EMA50 {:.5g} (dem {:.5g})".format(
                    close, ema50, buf), ema50, adx, atr, rsi)
        if sell_ok:
            return Ema50CloseEngine._mk(
                SELL, "Dong cua {:.5g} dut khoat DUOI EMA50 {:.5g} (dem {:.5g})".format(
                    close, ema50, buf), ema50, adx, atr, rsi)
        return Ema50CloseEngine._mk(
            NO_TRADE, "Gia {:.5g} con qua sat/xen ke EMA50 {:.5g}, chua dut khoat".format(
                close, ema50), ema50, adx, atr, rsi)
