"""
Backtester (Sprint 10) - chay lai chien luoc tren du lieu lich su.

- Trend + entry_mode="limit": dat lenh CHO tai gia tot hon (lui ve EMA).
  Chi tinh la vao lenh neu gia cham limit trong entry_wait nen; neu khong -> bo keo.
- Meanrev / market: vao ngay tai gia dong nen tin hieu.
Sau khi vao: cham TP truoc=WIN, SL truoc=LOSS, het lookahead=dong theo gia.

- htf_candles (tuy chon): du lieu KHUNG LON that (VD H4/D1) de tinh htf_trend
  dung THOI DIEM cho cac chien luoc da khung (VD "mtf_structure"). Dung bisect
  de CHI lay cac nen khung lon da dong HOAN TOAN truoc thoi diem nen hien tai
  (khong de lo du lieu tuong lai). Cac chien luoc khac khong truyen tham so
  nay -> hanh vi khong doi (htf_trend luon None nhu truoc).
"""

import bisect

from src.signal.constants import BUY, SELL, NO_TRADE
from src.signal.signal_service import SignalService
from src.signal.trend import TrendService
from src.indicators.indicator_service import IndicatorService
from src.signal.ema_pullback_engine import EmaPullbackEngine
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
            lookahead=250, window=320, warmup=210, htf_candles=None):
        n = len(candles)
        trades = []
        htf_times = [c.time for c in htf_candles] if htf_candles else None
        i = warmup
        while i < n - 1:
            w = candles[max(0, i - window): i + 1]
            if len(w) < warmup:
                i += 1
                continue
            htf_trend_val = None
            htf_win = None
            if htf_times:
                cur_time = candles[i].time
                idx = bisect.bisect_left(htf_times, cur_time) - 1
                if idx >= 0:
                    # Cua so nen khung lon (H1...) DA DONG HOAN TOAN truoc thoi
                    # diem nen hien tai - dung chung cho ca TrendService.direction()
                    # (cac chien luoc mtf_trend cu) lan EmaPullbackEngine.h1_trend()
                    # (can toi thieu ~203 nen H1, tu xu ly SIDEWAYS neu thieu).
                    htf_win = htf_candles[max(0, idx - 260):idx + 1]
                if idx >= 60:
                    htf_trend_val = TrendService.direction(htf_win)

            # ----- EMA Pullback: can CA hai khung (M15 = w, H1 = htf_win that,
            # khong phai chi 1 gia tri huong nhu htf_trend_val) - bypass
            # SignalService.analyze() vi engine nay doc lap, khong nam trong
            # dispatch cua SignalService (xem src/signal/ema_pullback_engine.py). -----
            if strategy == "ema_pullback":
                if not htf_win:
                    i += 1
                    continue
                try:
                    ema20 = IndicatorService.ema(w, 20)
                    ema50 = IndicatorService.ema(w, 50)
                    ema200 = IndicatorService.ema(w, 200)
                    adx_w = IndicatorService.adx(w)
                    atr_w = IndicatorService.atr(w)
                    rsi_w = IndicatorService.rsi(w)
                    signal = EmaPullbackEngine.analyze(
                        w, htf_win, ema20, ema50, ema200, adx_w, atr_w, rsi_w)
                except Exception:
                    i += 1
                    continue
            else:
                try:
                    signal = SignalService.analyze(w, strategy=strategy, htf_trend=htf_trend_val)
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
