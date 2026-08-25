from src.signal.constants import BUY, SELL, NO_TRADE, BOLL_PERIOD, BOLL_MULT
from src.indicators.indicator_service import IndicatorService
from src.trade.trade_plan import TradePlan
from src.trade.risk_manager import RiskManager
from src.trade.constants import (RISK_MIN_PERCENT, RISK_MAX_PERCENT, ATR_SL_BUFFER,
                                 SWING_LOOKBACK, ENTRY_PULLBACK_ATR, BO_RR, TRAIL_ATR_MULT, DBL_RR, FLAG_RR, STRUCT_RR,
                                 BOLL_TP_MODE, LB_TP_MULT)


class TradeService:
    """Build Trade Plan (SL/TP dong) tu Trading Signal."""

    @staticmethod
    def _decimals(price):
        return 2 if price >= 10 else 5

    @staticmethod
    def create(signal, candles, symbol="", balance=None, confidence=0.0,
               risk_min=RISK_MIN_PERCENT, risk_max=RISK_MAX_PERCENT, strategy="trend",
               entry_mode="market"):
        """
        Dung TradePlan. SL/TP dong theo cau truc + ATR; sizing theo confidence.
        """
        if signal.action not in (BUY, SELL):
            return TradePlan(
                action=NO_TRADE, entry_price=0.0, stop_loss=0.0,
                take_profit=0.0, risk_reward="-", reason=signal.reason,
            )

        last = candles[-1]
        nd = TradeService._decimals(last.close)
        close = round(last.close, nd)
        atr = getattr(signal, "atr", 0.0) or abs(close) * 0.001

        # Trend + lenh cho: lui gia ve phia EMA de vao dep hon
        if strategy == "trend" and entry_mode == "limit":
            if signal.action == BUY:
                entry = round(close - ENTRY_PULLBACK_ATR * atr, nd)
            else:
                entry = round(close + ENTRY_PULLBACK_ATR * atr, nd)
            entry_type = "limit"
        else:
            entry = close
            entry_type = "market"

        if strategy == "meanrev":
            # SL vuot qua diem cuc doan gan nhat, TP nham ve EMA20 (trung binh)
            recent = candles[-SWING_LOOKBACK:]
            if signal.action == BUY:
                sl_raw = min(c.low for c in recent) - ATR_SL_BUFFER * atr
                tp_raw = signal.ema20
            else:
                sl_raw = max(c.high for c in recent) + ATR_SL_BUFFER * atr
                tp_raw = signal.ema20
            lv = {"stop_loss": sl_raw, "take_profit": tp_raw,
                  "sl_source": "swing-ATR", "tp_source": "mean-EMA20",
                  "trail_distance": 1.5 * atr}
        elif strategy in ("breakout", "double", "flag", "structure"):
            _rr = {"breakout": BO_RR, "double": DBL_RR, "flag": FLAG_RR, "structure": STRUCT_RR}[strategy]
            recent = candles[-SWING_LOOKBACK:]
            if signal.action == BUY:
                sl_raw = min(c.low for c in recent) - ATR_SL_BUFFER * atr
                risk = abs(entry - sl_raw) or atr
                tp_raw = entry + _rr * risk
            else:
                sl_raw = max(c.high for c in recent) + ATR_SL_BUFFER * atr
                risk = abs(sl_raw - entry) or atr
                tp_raw = entry - _rr * risk
            lv = {"stop_loss": sl_raw, "take_profit": tp_raw,
                  "sl_source": strategy + "-swing",
                  "tp_source": "RR {:g}x".format(_rr),
                  "trail_distance": TRAIL_ATR_MULT * atr}
        elif strategy == "bollinger":
            # Tai su dung swing_low/swing_high lam SL-ref/gia bien doi dien (xem docstring BollingerEngine).
            lo = getattr(signal, "swing_low", 0.0)
            hi = getattr(signal, "swing_high", 0.0)
            far_buy_tp, far_sell_tp = hi, lo
            near_tp = 0.0
            if BOLL_TP_MODE != "opposite":
                try:
                    _, near_tp, _ = IndicatorService.bollinger(candles, BOLL_PERIOD, BOLL_MULT)
                except Exception:
                    near_tp = (lo + hi) / 2 if (lo and hi) else 0.0
            if signal.action == BUY:
                sl_raw = (lo - ATR_SL_BUFFER * atr) if lo else (entry - 2 * atr)
                tp_raw = near_tp if (near_tp and BOLL_TP_MODE != "opposite") else (far_buy_tp or entry + 2 * atr)
            else:
                sl_raw = (hi + ATR_SL_BUFFER * atr) if hi else (entry + 2 * atr)
                tp_raw = near_tp if (near_tp and BOLL_TP_MODE != "opposite") else (far_sell_tp or entry - 2 * atr)
            lv = {"stop_loss": sl_raw, "take_profit": tp_raw,
                  "sl_source": "bollinger-signal-candle",
                  "tp_source": ("Duong giua bien (TP gan)" if BOLL_TP_MODE != "opposite"
                                else "Bien doi dien (TP xa)"),
                  "trail_distance": TRAIL_ATR_MULT * atr}
        elif strategy == "london":
            # Tai su dung swing_low/swing_high = day/dinh bien do phien A (xem LondonEngine).
            lo = getattr(signal, "swing_low", 0.0)
            hi = getattr(signal, "swing_high", 0.0)
            rng = (hi - lo) if (hi and lo and hi > lo) else 2 * atr
            if signal.action == BUY:
                sl_raw = lo if lo else (entry - 2 * atr)
                tp_raw = entry + LB_TP_MULT * rng
            else:
                sl_raw = hi if hi else (entry + 2 * atr)
                tp_raw = entry - LB_TP_MULT * rng
            lv = {"stop_loss": sl_raw, "take_profit": tp_raw,
                  "sl_source": "london-asia-range",
                  "tp_source": "TP {:g}x bien do phien A".format(LB_TP_MULT),
                  "trail_distance": TRAIL_ATR_MULT * atr}
        else:
            lv = RiskManager.dynamic_levels(signal.action, entry, candles, atr)

        sl = round(lv["stop_loss"], nd)
        tp = round(lv["take_profit"], nd)
        trail = round(lv["trail_distance"], nd)

        risk_points = round(abs(entry - sl), nd)
        reward_points = round(abs(tp - entry), nd)
        rr_ratio = round(reward_points / risk_points, 2) if risk_points else 0.0

        risk_percent, risk_amount, lot_size, expected_profit = RiskManager.sizing(
            symbol, risk_points, rr_ratio, balance, confidence, risk_min, risk_max,
        )

        return TradePlan(
            action=signal.action,
            entry_type=entry_type,
            entry_price=entry,
            stop_loss=sl,
            take_profit=tp,
            risk_reward="1 : {:g}".format(rr_ratio),
            reason=signal.reason,
            rr_ratio=rr_ratio,
            risk_points=risk_points,
            reward_points=reward_points,
            risk_percent=risk_percent,
            sl_source=lv["sl_source"],
            tp_source=lv["tp_source"],
            trail_distance=trail,
            risk_amount=risk_amount,
            lot_size=lot_size,
            expected_profit=expected_profit,
        )
