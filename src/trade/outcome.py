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
    def evaluate(action, stop_loss, take_profit, future_candles):
        """
        future_candles: cac nen SAU khi vao lenh (theo thu tu thoi gian).
        Tra ve WIN / LOSS / OPEN.
        """
        for c in future_candles:
            if action == BUY:
                hit_sl = c.low <= stop_loss
                hit_tp = c.high >= take_profit
            elif action == SELL:
                hit_sl = c.high >= stop_loss
                hit_tp = c.low <= take_profit
            else:
                return OPEN

            if hit_sl and hit_tp:
                return LOSS          # bao thu: coi nhu dinh SL truoc
            if hit_sl:
                return LOSS
            if hit_tp:
                return WIN
        return OPEN
