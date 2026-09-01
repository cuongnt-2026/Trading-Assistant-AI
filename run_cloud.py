# -*- coding: utf-8 -*-
"""
run_cloud.py - chay tren GitHub Actions (khong can MT5).
Lay gia tu Twelve Data -> chay dung chien luoc theo symbol
(XAU=breakout, FX=trend pullback) -> gui mail. Chong gui trung bang cloud_state.json.
"""
import os
import json
from datetime import datetime

from src.core.config import Config
from src.data.webdata import WebData
from src.signal.signal_service import SignalService
from src.signal.trend import TrendService, higher_tf
from src.signal.strategy import strategy_for
from src.signal.constants import BUY, SELL
from src.ai_review.recommender import Recommender
from src.trade.trade_service import TradeService
from src.notifier.factory import create_notifier
from src.notifier.messages import build_signal_email, build_supertrend_email
from src.signal.supertrend import supertrend
from src.trade.outcome import OutcomeEvaluator, OPEN

STATE_PATH = "cloud_state.json"


def load_state():
    try:
        return json.load(open(STATE_PATH, encoding="utf-8"))
    except Exception:
        return {}


def save_state(s):
    json.dump(s, open(STATE_PATH, "w", encoding="utf-8"), indent=2, ensure_ascii=False)


SIGNALS_PATH = "cloud_signals.json"


def load_signals():
    try:
        return json.load(open(SIGNALS_PATH, encoding="utf-8"))
    except Exception:
        return []


def save_signals(sig):
    json.dump(sig, open(SIGNALS_PATH, "w", encoding="utf-8"), indent=2, ensure_ascii=False)


def _parse_ct(ts):
    try:
        return datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
    except Exception:
        return None


def _send_test_mail(cfg, notifier):
    from src.signal.signal import Signal
    from src.trade.trade_plan import TradePlan
    class _C:
        close = 1.0850
    sig = Signal(action=BUY, trend="UP", strength="STRONG",
                 reason="MAIL THU - kiem tra he thong cloud",
                 ema20=1.0855, ema50=1.0840, ema200=1.0790,
                 adx=28.0, atr=0.0025, rsi=46.0, pattern="Test")
    plan = TradePlan(action=BUY, entry_type="limit", entry_price=1.0838,
                     stop_loss=1.0808, take_profit=1.0898, risk_reward="1 : 2",
                     reason=sig.reason, rr_ratio=2.0, risk_points=0.003,
                     reward_points=0.006, risk_percent=1.0, sl_source="swing-ATR",
                     tp_source="cau truc", trail_distance=0.0038, risk_amount=100.0,
                     lot_size=0.4, expected_profit=200.0)
    class _Rec:
        action = "BUY"; confidence = 68.0; label = "Kha manh"
        reasons = ["MAIL THU"]
    subject, body = build_signal_email(sig, "EURUSD", "M30", _C(),
                                       recommendation=_Rec(), trade_plan=plan)
    subject = "[CLOUD TEST] " + subject
    ok = notifier.send(subject, body) if notifier else False
    print("MAIL THU -> {}".format("DA GUI OK" if ok else "THAT BAI/khong co notifier"))


def write_dashboard(snapshot, signals_log, path="dashboard/data.js"):
    """Ghi dashboard/data.js: trang thai hien tai + lich su lenh (Win/Loss + ke hoach)."""
    hist = []
    for r in signals_log:
        rr = r.get("rr")
        rr_txt = r.get("risk_reward")
        if not rr_txt:
            rr_txt = "1 : {:g}".format(rr) if isinstance(rr, (int, float)) else "—"
        hist.append({
            "time": r.get("time"), "candle_time": r.get("candle_time"),
            "symbol": r.get("symbol"), "timeframe": r.get("timeframe"),
            "action": r.get("action"), "price": r.get("entry"),
            "strategy": r.get("strategy"),
            "confidence": r.get("confidence"), "notified": True,
            "outcome": r.get("outcome"), "r_result": r.get("r_result"),
            "trade_plan": {
                "entry": r.get("entry"), "stop_loss": r.get("sl"),
                "take_profit": r.get("tp"),
                "risk_reward": rr_txt,
                "risk_percent": r.get("risk_percent", 1),
                "lot_size": r.get("lot_size"), "expected_profit": r.get("expected_profit"),
            },
        })
    data = {
        "updated": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        "symbol": snapshot[0]["symbol"] if snapshot else "XAUUSD",
        "signals": snapshot + hist,
    }
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write("window.TA_DATA = " + json.dumps(data, ensure_ascii=False, indent=2) + ";\n")
    except Exception as e:
        print("[WARN] ghi dashboard loi:", e)


def _handle_supertrend(sym, tf, candles, cfg, state, signals_log, notifier):
    """Supertrend flip -> gui mail dao chieu, dong lenh cu (stop-and-reverse)."""
    direction, st_line = supertrend(candles, cfg.supertrend_period, cfg.supertrend_mult)
    if len(direction) < 5 or direction[-1] == direction[-2]:
        return 0
    last = candles[-1]
    ts = str(last.time)
    key = "ST {} {}".format(sym, tf)
    if state.get(key) == ts:
        return 0
    action = BUY if direction[-1] == 1 else SELL
    entry = round(last.close, 2)
    sl = round(st_line[-1], 2)
    # Chong lenh rac: neu da co lenh Supertrend CUNG CHIEU dang mo -> khong phai dao chieu that
    # (do Supertrend repaint gan diem lat) -> bo qua, khong ban trung.
    if any(r.get("strategy") == "supertrend" and r.get("symbol") == sym
           and r.get("timeframe") == tf and r.get("outcome") == "OPEN"
           and r.get("action") == action for r in signals_log):
        state[key] = ts
        print("  {} {} [supertrend] {} da mo san -> bo qua (chong ban trung)".format(sym, tf, action))
        return 0
    # dong lenh Supertrend cu (dao chieu that - nguoc huong)
    # Luat: con duong khi dao -> WIN R that (cap +NR); ve/qua entry -> LOSS -1R (SL da chan)
    for r in signals_log:
        if (r.get("strategy") == "supertrend" and r.get("symbol") == sym
                and r.get("timeframe") == tf and r.get("outcome") == "OPEN"):
            pnl = (entry - r["entry"]) if r["action"] == BUY else (r["entry"] - entry)
            risk = abs(r["entry"] - r.get("sl", entry)) or 1e-9
            if pnl > 0:
                r["outcome"] = "WIN"
                r["r_result"] = round(min(pnl / risk, cfg.supertrend_rr), 3)
            else:
                r["outcome"] = "LOSS"
                r["r_result"] = -1.0
            r["exit"] = entry
    subject, body = build_supertrend_email(sym, tf, action, entry, sl)
    subject = "[CLOUD] " + subject
    ok = notifier.send(subject, body) if notifier else False
    print("  {} {} [supertrend] FLIP {} -> GUI MAIL: {}".format(sym, tf, action, "OK" if ok else "FAIL"))
    if ok:
        state[key] = ts
        risk = abs(entry - sl) or 1e-9
        n = cfg.supertrend_rr
        tp = round(entry + n * risk, 2) if action == BUY else round(entry - n * risk, 2)
        signals_log.append({
            "time": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
            "candle_time": ts, "symbol": sym, "timeframe": tf,
            "action": action, "strategy": "supertrend",
            "entry": entry, "sl": sl, "tp": tp, "rr": n, "risk_reward": "1 : {:g}".format(n),
            "confidence": None, "outcome": "OPEN",
        })
        return 1
    return 0


def _scan_discrete(sym, tf, strategy, cfg, state, signals_log, snapshot, notifier):
    """Tin hieu roi rac (Bollinger/London): quet DOC LAP, khong thuoc watchlist chinh.
    Gui mail dung kieu Trend/Breakout (Entry/SL/TP/RR qua build_signal_email), KHONG loc
    them MIN_CONFIDENCE/ADX vi cap/khung da duoc chon loc san qua backtest (chi giu to hop
    co Profit Factor > 1)."""
    try:
        candles = WebData.get_candles(sym, tf, cfg.candle_count)
    except Exception as e:
        print("[WARN] {} {} [{}] fetch loi: {}".format(sym, tf, strategy, e))
        return 0
    if not candles or len(candles) < 200:
        print("[WARN] {} {} [{}] khong du nen ({})".format(
            sym, tf, strategy, len(candles) if candles else 0))
        return 0

    # Cham WIN/LOSS cho tin hieu OPEN cua chinh strategy + cap-khung nay
    for r in signals_log:
        if (r.get("outcome") == "OPEN" and r.get("symbol") == sym
                and r.get("timeframe") == tf and r.get("strategy") == strategy):
            try:
                st = _parse_ct(r.get("candle_time", ""))
                fut = [c for c in candles if st and c.time > st]
                if fut:
                    res = OutcomeEvaluator.evaluate(r["action"], r.get("sl"), r.get("tp"), fut)
                    if res != OPEN:
                        r["outcome"] = res
            except Exception as e:
                print("[WARN] cham outcome {} {} [{}] loi: {}".format(sym, tf, strategy, e))

    try:
        signal = SignalService.analyze(candles, htf_trend=None, strategy=strategy)
    except Exception as e:
        print("[WARN] {} {} [{}] analyze loi: {}".format(sym, tf, strategy, e))
        return 0
    last = candles[-1]
    ts = str(last.time)
    print("  {} {} [{}] | {} | close={:.5g} | ADX={:.1f}".format(
        sym, tf, strategy, signal.action, last.close, signal.adx))

    snapshot.append({
        "time": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "symbol": sym, "timeframe": tf, "action": signal.action,
        "strategy": strategy,
        "trend": signal.trend, "strength": signal.strength,
        "price": round(last.close, 5),
        "ema20": round(signal.ema20, 5), "ema50": round(signal.ema50, 5),
        "ema200": round(signal.ema200, 5), "adx": round(signal.adx, 2),
        "atr": round(getattr(signal, "atr", 0.0), 5),
        "rsi": round(getattr(signal, "rsi", 0.0), 2),
        "pattern": getattr(signal, "pattern", ""), "reason": signal.reason,
        "notified": False,
    })

    if signal.action not in (BUY, SELL):
        return 0

    skey = "{} {} {}".format(strategy, sym, tf)
    if state.get(skey) == ts:
        print("     -> [{}] da bao cho nen nay -> bo qua".format(strategy))
        return 0

    # Chong ban trung: da co lenh CUNG CHIEU dang mo o cap-khung-strategy nay -> bo qua
    if any(r.get("outcome") == "OPEN" and r.get("symbol") == sym
           and r.get("timeframe") == tf and r.get("strategy") == strategy
           and r.get("action") == signal.action for r in signals_log):
        print("     -> [{}] da co lenh {} dang mo o {} {} -> bo qua (chong ban trung)".format(
            strategy, signal.action, sym, tf))
        return 0

    try:
        rec = Recommender.evaluate(signal, candles)
    except Exception as e:
        print("[WARN] {} {} [{}] recommender loi: {}".format(sym, tf, strategy, e))
        return 0

    try:
        plan = TradeService.create(
            signal, candles, symbol=sym, balance=cfg.account_balance or None,
            confidence=rec.confidence, risk_min=cfg.risk_min_percent,
            risk_max=cfg.risk_max_percent, strategy=strategy, entry_mode=cfg.entry_mode)
        subject, body = build_signal_email(signal, sym, tf, last,
                                           recommendation=rec, trade_plan=plan)
        subject = "[CLOUD][{}] ".format(strategy.upper()) + subject
        ok = notifier.send(subject, body) if notifier else False
        print("     -> [{}] GUI MAIL: {} (conf {:.0f})".format(
            strategy, "OK" if ok else "FAIL/none", rec.confidence))
        if ok:
            state[skey] = ts
            signals_log.append({
                "time": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
                "candle_time": ts, "symbol": sym, "timeframe": tf,
                "action": signal.action, "strategy": strategy,
                "entry": plan.entry_price, "sl": plan.stop_loss, "tp": plan.take_profit,
                "rr": plan.rr_ratio, "risk_reward": plan.risk_reward,
                "risk_percent": plan.risk_percent, "lot_size": plan.lot_size,
                "expected_profit": plan.expected_profit,
                "confidence": round(rec.confidence, 1), "outcome": "OPEN",
            })
            return 1
    except Exception as e:
        print("[WARN] {} {} [{}] tao/gui lenh loi: {}".format(sym, tf, strategy, e))
    return 0


def main():
    cfg = Config()
    notifier = create_notifier(cfg)
    state = load_state()
    signals_log = load_signals()

    # Reset 1 lan (do chinh cloud thuc hien -> khong bi race/merge de len):
    # neu co file RESET_SIGNALS.flag -> xoa sach lich su + trang thai, roi xoa co.
    if os.path.exists("RESET_SIGNALS.flag"):
        signals_log = []
        state = {}
        try:
            os.remove("RESET_SIGNALS.flag")
        except Exception:
            pass
        print(">>> RESET_SIGNALS.flag: da xoa sach toan bo lich su tin hieu + trang thai <<<")

    if os.getenv("FORCE_TEST_MAIL", "").strip().lower() in ("1", "true"):
        _send_test_mail(cfg, notifier)
        return

    min_conf = cfg.min_confidence
    print("Cloud run {} | watchlist={} | +bollinger={} +london={} | MIN_CONF={}".format(
        datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"), len(cfg.watchlist),
        len(cfg.bollinger_pairs) if cfg.bollinger_enabled else 0,
        len(cfg.london_pairs) if cfg.london_enabled else 0, min_conf))

    htf_cache = {}
    snapshot = []
    sent = 0
    for sym, tf in cfg.watchlist:
        strat = strategy_for(sym)
        try:
            candles = WebData.get_candles(sym, tf, cfg.candle_count)
        except Exception as e:
            print("[WARN] {} {} fetch loi: {}".format(sym, tf, e))
            continue
        if not candles or len(candles) < 200:
            print("[WARN] {} {} khong du nen ({})".format(sym, tf, len(candles) if candles else 0))
            continue

        # Cham WIN/LOSS cho tin hieu OPEN cua cap-khung nay
        for r in signals_log:
            if r.get("outcome") == "OPEN" and r.get("symbol") == sym and r.get("timeframe") == tf:
                try:
                    st = _parse_ct(r.get("candle_time", ""))
                    fut = [c for c in candles if st and c.time > st]
                    if fut:
                        res = OutcomeEvaluator.evaluate(r["action"], r.get("sl"), r.get("tp"), fut)
                        if res != OPEN:
                            r["outcome"] = res
                except Exception as e:
                    print("[WARN] cham outcome {} {} loi: {}".format(sym, tf, e))

        htf_trend = None
        if cfg.use_mtf:
            htf = higher_tf(tf)
            ck = (sym, htf)
            if ck not in htf_cache:
                try:
                    hc = WebData.get_candles(sym, htf, cfg.candle_count)
                    htf_cache[ck] = (TrendService.direction(hc)
                                     if hc and len(hc) >= 60 else None)
                except Exception:
                    htf_cache[ck] = None
            htf_trend = htf_cache[ck]

        try:
            signal = SignalService.analyze(candles, htf_trend=htf_trend, strategy=strat)
        except Exception as e:
            print("[WARN] {} {} analyze loi: {}".format(sym, tf, e))
            continue
        last = candles[-1]
        ts = str(last.time)
        print("  {} {} [{}] | {} | close={:.5g} | ADX={:.1f}".format(
            sym, tf, strat, signal.action, last.close, signal.adx))

        snapshot.append({
            "time": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "symbol": sym, "timeframe": tf, "action": signal.action,
            "strategy": strat,
            "trend": signal.trend, "strength": signal.strength,
            "price": round(last.close, 5),
            "ema20": round(signal.ema20, 5), "ema50": round(signal.ema50, 5),
            "ema200": round(signal.ema200, 5), "adx": round(signal.adx, 2),
            "atr": round(getattr(signal, "atr", 0.0), 5),
            "rsi": round(getattr(signal, "rsi", 0.0), 2),
            "pattern": getattr(signal, "pattern", ""), "reason": signal.reason,
            "notified": False,
        })

        # Supertrend (he dao chieu) cho XAU M30/H1 - chay song song
        if (cfg.supertrend_enabled and sym in cfg.supertrend_symbols
                and tf in cfg.supertrend_tfs):
            try:
                sent += _handle_supertrend(sym, tf, candles, cfg, state, signals_log, notifier)
            except Exception as e:
                print("[WARN] supertrend {} {}: {}".format(sym, tf, e))

        if signal.action not in (BUY, SELL):
            continue

        # Trend da tat -> khong gui/khong ghi (van quet de hien snapshot)
        if strat == "trend" and not cfg.trend_enabled:
            print("     -> [trend] da TAT (TREND_ENABLED=0) -> bo qua")
            continue

        try:
            rec = Recommender.evaluate(signal, candles)
        except Exception as e:
            print("[WARN] {} {} recommender loi: {}".format(sym, tf, e))
            continue
        # Loc chat luong: trend dung MIN_CONFIDENCE; breakout dung nguong rieng + ADX
        if strat == "trend" and rec.confidence < min_conf:
            print("     -> [trend] conf {:.0f} < {} -> bo qua".format(rec.confidence, min_conf))
            continue
        if strat == "breakout":
            if rec.confidence < cfg.breakout_min_confidence:
                print("     -> [breakout] conf {:.0f} < {} -> bo qua".format(
                    rec.confidence, cfg.breakout_min_confidence))
                continue
            if cfg.breakout_min_adx and signal.adx < cfg.breakout_min_adx:
                print("     -> [breakout] ADX {:.1f} < {} (thi truong yeu/sideways) -> bo qua".format(
                    signal.adx, cfg.breakout_min_adx))
                continue

        skey = "{} {}".format(sym, tf)
        if state.get(skey) == ts:
            print("     -> da bao cho nen nay -> bo qua")
            continue

        # Chong ban trung: da co lenh CUNG CHIEU dang mo o cap-khung nay -> bo qua
        if any(r.get("outcome") == "OPEN" and r.get("symbol") == sym
               and r.get("timeframe") == tf and r.get("action") == signal.action
               for r in signals_log):
            print("     -> da co lenh {} dang mo o {} {} -> bo qua (chong ban trung)".format(
                signal.action, sym, tf))
            continue

        try:
            plan = TradeService.create(
                signal, candles, symbol=sym, balance=cfg.account_balance or None,
                confidence=rec.confidence, risk_min=cfg.risk_min_percent,
                risk_max=cfg.risk_max_percent, strategy=strat, entry_mode=cfg.entry_mode)
            subject, body = build_signal_email(signal, sym, tf, last,
                                               recommendation=rec, trade_plan=plan)
            subject = "[CLOUD] " + subject
            ok = notifier.send(subject, body) if notifier else False
            print("     -> GUI MAIL: {} (conf {:.0f})".format("OK" if ok else "FAIL/none", rec.confidence))
            if ok:
                state[skey] = ts
                sent += 1
                signals_log.append({
                    "time": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
                    "candle_time": ts, "symbol": sym, "timeframe": tf,
                    "action": signal.action, "strategy": strat,
                    "entry": plan.entry_price, "sl": plan.stop_loss, "tp": plan.take_profit,
                    "rr": plan.rr_ratio, "risk_reward": plan.risk_reward,
                    "risk_percent": plan.risk_percent, "lot_size": plan.lot_size,
                    "expected_profit": plan.expected_profit,
                    "confidence": round(rec.confidence, 1), "outcome": "OPEN",
                })
        except Exception as e:
            print("[WARN] {} {} tao/gui lenh loi: {}".format(sym, tf, e))
            continue

    # ----- Bollinger + London: tin hieu roi rac, quet DOC LAP ngoai watchlist chinh -----
    if cfg.bollinger_enabled:
        for sym, tf in cfg.bollinger_pairs:
            try:
                sent += _scan_discrete(sym, tf, "bollinger", cfg, state, signals_log, snapshot, notifier)
            except Exception as e:
                print("[WARN] bollinger {} {}: {}".format(sym, tf, e))
    if cfg.london_enabled:
        for sym, tf in cfg.london_pairs:
            try:
                sent += _scan_discrete(sym, tf, "london", cfg, state, signals_log, snapshot, notifier)
            except Exception as e:
                print("[WARN] london {} {}: {}".format(sym, tf, e))

    try:
        save_state(state)
        save_signals(signals_log)
    except Exception as e:
        print("[WARN] luu state/signals loi:", e)
    try:
        write_dashboard(snapshot, signals_log, cfg.dashboard_data)
    except Exception as e:
        print("[WARN] ghi dashboard loi:", e)
    print("Xong. Da gui {} tin hieu.".format(sent))


if __name__ == "__main__":
    main()
