from src.signal.constants import BUY, SELL
from src.trade.constants import (
    ATR_SL_BUFFER, TP_STRUCT_LOOKBACK, TP_ATR_FALLBACK, MIN_RR,
    TRAIL_ATR_MULT, SWING_LOOKBACK, TP_RR_TARGET, point_value_per_lot,
)


def _clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


class RiskManager:
    """SL/TP DONG theo cau truc + ATR, va sizing co gian theo do tin cay."""

    @staticmethod
    def dynamic_levels(action, entry, candles, atr,
                       swing_lookback=SWING_LOOKBACK,
                       atr_buffer=ATR_SL_BUFFER,
                       tp_lookback=TP_STRUCT_LOOKBACK,
                       tp_atr_fallback=TP_ATR_FALLBACK,
                       min_rr=MIN_RR):
        """
        Tinh SL/TP dong (gia tri tho, chua lam tron).

        SL = swing gan nhat -/+ dem ATR.
        TP = khang cu/ho tro gan nhat (cau truc); neu khong co -> boi so ATR.
        Ap RR toi thieu de khong nhan setup qua xau.
        """
        if atr is None or atr <= 0:
            atr = abs(entry) * 0.001

        recent = candles[-swing_lookback:]
        wide = candles[-tp_lookback:] if len(candles) >= tp_lookback else candles

        if action == BUY:
            swing_low = min(c.low for c in recent)
            sl = swing_low - atr_buffer * atr
            sl = min(sl, entry - atr)                 # dam bao SL < entry
            sl_source = "swing-ATR"

            resistance = max(c.high for c in wide)
            if resistance > entry + 0.1 * atr:
                tp = resistance
                tp_source = "structure"
            else:
                tp = entry + tp_atr_fallback * atr
                tp_source = "atr"

            risk = entry - sl
            if TP_RR_TARGET > 0:                       # ep TP theo RR co dinh
                tp = entry + TP_RR_TARGET * risk
                tp_source = "rr{:g}".format(TP_RR_TARGET)
            elif tp - entry < min_rr * risk:           # ep RR toi thieu
                tp = entry + min_rr * risk
                tp_source += "+minRR"

        else:  # SELL
            swing_high = max(c.high for c in recent)
            sl = swing_high + atr_buffer * atr
            sl = max(sl, entry + atr)
            sl_source = "swing-ATR"

            support = min(c.low for c in wide)
            if support < entry - 0.1 * atr:
                tp = support
                tp_source = "structure"
            else:
                tp = entry - tp_atr_fallback * atr
                tp_source = "atr"

            risk = sl - entry
            if TP_RR_TARGET > 0:
                tp = entry - TP_RR_TARGET * risk
                tp_source = "rr{:g}".format(TP_RR_TARGET)
            elif entry - tp < min_rr * risk:
                tp = entry - min_rr * risk
                tp_source += "+minRR"

        return {
            "stop_loss": sl,
            "take_profit": tp,
            "sl_source": sl_source,
            "tp_source": tp_source,
            "trail_distance": TRAIL_ATR_MULT * atr,
        }

    @staticmethod
    def sizing(symbol, risk_points, rr_ratio, balance, confidence,
               risk_min, risk_max):
        """
        Risk % noi suy theo confidence (50%..100% -> risk_min..risk_max).
        Tra (risk_percent, risk_amount, lot_size, expected_profit).
        lot/$ = None neu chua biet balance.
        """
        t = _clamp((confidence - 50.0) / 50.0)
        risk_percent = round(risk_min + t * (risk_max - risk_min), 3)

        risk_amount = lot_size = expected_profit = None
        if balance and balance > 0 and risk_points > 0:
            risk_amount = round(balance * risk_percent / 100.0, 2)
            value_per_point = point_value_per_lot(symbol)
            raw_lot = risk_amount / (risk_points * value_per_point)
            lot_size = max(round(raw_lot, 2), 0.01)
            expected_profit = round(risk_amount * rr_ratio, 2)

        return risk_percent, risk_amount, lot_size, expected_profit
