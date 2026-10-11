"""
Outcome Evaluator - cham WIN/LOSS cho tin hieu dua theo THI TRUONG CHAY.

Sau khi phat tin hieu, cac nen tiep theo se cho biet gia cham TP truoc (WIN)
hay cham SL truoc (LOSS). Neu chua cham gi -> OPEN (chua ket thuc).
Neu 1 nen cham CA SL va TP -> coi la LOSS (bao thu, uu tien rui ro).
"""

from src.signal.constants import BUY, SELL

WIN = "WIN"
LOSS = "LOSS"
OPEN = "OPEN"


class OutcomeEvaluator:

    @staticmethod
    def evaluate(action, stop_loss, take_profit, future_candles, spread=0.0):
        """
        future_candles: cac nen SAU khi vao lenh (theo thu tu thoi gian).
        Tra ve WIN / LOSS / OPEN.

        spread: nen la gia Bid -> lenh SELL thoat o gia Ask (= Bid + spread), nen
        SL cua SELL bi cham SOM hon va TP can gia xuong SAU hon `spread`. Lenh BUY
        thoat o Bid nen khong doi (chi phi spread cua BUY nam o luc vao, da tinh
        vao R qua src/trade/costs.py).
        """
        for c in future_candles:
            hit_sl = False
            hit_tp = False
            if action == BUY:
                if stop_loss is not None:
                    hit_sl = c.low <= stop_loss
                if take_profit is not None:
                    hit_tp = c.high >= take_profit
            elif action == SELL:
                if stop_loss is not None:
                    hit_sl = c.high + spread >= stop_loss
                if take_profit is not None:
                    hit_tp = c.low + spread <= take_profit
            else:
                return OPEN

            if hit_sl and hit_tp:
                return LOSS          # bao thu: coi nhu dinh SL truoc
            if hit_sl:
                return LOSS
            if hit_tp:
                return WIN
        return OPEN
