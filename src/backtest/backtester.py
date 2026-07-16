"""
Backtester (Sprint 10) - chay lai chien luoc tren du lieu lich su.

- Trend + entry_mode="limit": dat lenh CHO tai gia tot hon (lui ve EMA).
  Chi tinh la vao lenh neu gia cham limit trong entry_wait nen; neu khong -> bo keo.
- Meanrev / market: vao ngay tai gia dong nen tin hieu.
Sau khi vao: cham TP truoc=WIN, SL truoc=LOSS, het lookahead=dong theo gia.
"""

from src.signal.constants import BUY, SELL, NO_TRADE
from src.signal.signal_service import SignalService
from src.ai_review.recommender import Recommender
from src.trade.trade_service import TradeService

WIN = "WIN"
LOSS = "LOSS"
TIMEOUT = "TIMEOUT"


class Backtester:

    @staticmethod
    def run(candles, symbol="", balance=10000.0,
            risk_min=0.5, risk_max=1.5, min_confidence=0.0, strategy="trend",
            entry_mode="market", entry_wait=6,
            lookahead=250, window=320, warmup=210):
        n = len(candles)
        trades = []
        i = warmup
        while i < n - 1:
            w = candles[max(0, i - window): i + 1]
            if len(w) < warmup:
                i += 1
                continue
            try:
                signal = SignalService.analyze(w, strategy=strategy)
            except Exception:
                i += 1
                continue
            if signal.action not in (BUY, SELL):
                i += 1
                continue

            rec = Recommender.evaluate(signal, w)
            if strategy == "trend" and rec.confidence < min_confidence:
                i += 1
                continue

            plan = TradeService.create(
                signal, w, symbol=symbol, balance=balance,
                confidence=rec.confidence, risk_min=risk_min, risk_max=risk_max,
                strategy=strategy, entry_mode=entry_mode)

            entry = plan.entry_price
            sl = plan.stop_loss
            tp = plan.take_profit
            risk = abs(entry - sl) or 1e-9

            # ----- Khop lenh -----
            if plan.entry_type == "limit":
                fill_idx = None
                for j in range(i + 1, min(n, i + 1 + entry_wait)):
                    c = candles[j]
                    if signal.action == BUY and c.low <= entry:
                        fill_idx = j
                        break
                    if signal.action == SELL and c.high >= entry:
                        fill_idx = j
                        break
                if fill_idx is None:
                    i += 1            # limit khong khop -> bo keo
                    continue
                start = fill_idx
            else:
                start = i             # market: vao ngay

            # ----- Mo phong TP/SL sau khi vao -----
            result = TIMEOUT
            exit_idx = min(n - 1, start + lookahead)
            exit_price = candles[exit_idx].close
            end = min(n, start + 1 + lookahead)
            for j in range(start + 1, end):
                c = candles[j]
                if signal.action == BUY:
                    hit_sl = c.low <= sl
                    hit_tp = c.high >= tp
                else:
                    hit_sl = c.high >= sl
                    hit_tp = c.low <= tp
                if hit_sl and hit_tp:
                    result, exit_idx, exit_price = LOSS, j, sl
                    break
                if hit_sl:
                    result, exit_idx, exit_price = LOSS, j, sl
                    break
                if hit_tp:
                    result, exit_idx, exit_price = WIN, j, tp
                    break

            pnl = (exit_price - entry) if signal.action == BUY else (entry - exit_price)
            if result == WIN:
                r_mult = plan.rr_ratio
            elif result == LOSS:
                r_mult = -1.0
            else:
                r_mult = round(pnl / risk, 3)

            trades.append({
                "symbol": symbol, "action": signal.action,
                "entry_time": str(candles[start].time),
                "exit_time": str(candles[exit_idx].time),
                "entry": entry, "sl": sl, "tp": tp, "rr": plan.rr_ratio,
                "entry_type": plan.entry_type,
                "confidence": rec.confidence, "result": result,
                "r_multiple": r_mult, "risk_percent": plan.risk_percent,
            })
            i = exit_idx + 1

        return Backtester._stats(trades, balance)

    @staticmethod
    def _stats(trades, balance):
        wins = [t for t in trades if t["result"] == WIN]
        losses = [t for t in trades if t["result"] == LOSS]
        closed = len(wins) + len(losses)
        total = len(trades)
        win_rate = round(len(wins) / closed * 100, 1) if closed else 0.0
        gross_win = sum(t["r_multiple"] for t in wins)
        gross_loss = sum(t["r_multiple"] for t in losses)
        profit_factor = round(gross_win / abs(gross_loss), 2) if gross_loss else 0.0
        total_r = round(sum(t["r_multiple"] for t in trades), 2)
        avg_r = round(total_r / total, 3) if total else 0.0

        eq_r = peak_r = max_dd_r = 0.0
        equity_pct = peak_pct = 100.0
        max_dd_pct = 0.0
        curve = []
        for t in trades:
            eq_r += t["r_multiple"]
            peak_r = max(peak_r, eq_r)
            max_dd_r = max(max_dd_r, peak_r - eq_r)
            equity_pct *= (1.0 + t["r_multiple"] * (t["risk_percent"] / 100.0))
            peak_pct = max(peak_pct, equity_pct)
            if peak_pct > 0:
                max_dd_pct = max(max_dd_pct, (peak_pct - equity_pct) / peak_pct * 100.0)
            curve.append(round(equity_pct, 2))

        return {"stats": {
            "trades": total, "wins": len(wins), "losses": len(losses),
            "timeouts": total - closed, "win_rate": win_rate,
            "avg_R": avg_r, "total_R": total_r, "profit_factor": profit_factor,
            "max_drawdown_R": round(max_dd_r, 2),
            "final_equity_pct": round(equity_pct, 2),
            "return_pct": round(equity_pct - 100.0, 2),
            "max_drawdown_pct": round(max_dd_pct, 2),
        }, "trades": trades, "equity_curve": curve}
