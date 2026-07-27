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
from src.notifier.messages import build_signal_email
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


def main():
    cfg = Config()
    notifier = create_notifier(cfg)
    state = load_state()
    signals_log = load_signals()

    if os.getenv("FORCE_TEST_MAIL", "").strip().lower() in ("1", "true"):
        _send_test_mail(cfg, notifier)
        return

    min_conf = cfg.min_confidence
    print("Cloud run {} | watchlist={} | MIN_CONF={}".format(
        datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"), len(cfg.watchlist), min_conf))

    htf_cache = {}
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
                st = _parse_ct(r.get("candle_time", ""))
                fut = [c for c in candles if st and c.time > st]
                if fut:
                    res = OutcomeEvaluator.evaluate(r["action"], r["sl"], r["tp"], fut)
                    if res != OPEN:
                        r["outcome"] = res

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

        signal = SignalService.analyze(candles, htf_trend=htf_trend, strategy=strat)
        last = candles[-1]
        ts = str(last.time)
        print("  {} {} [{}] | {} | close={:.5g} | ADX={:.1f}".format(
            sym, tf, strat, signal.action, last.close, signal.adx))

        if signal.action not in (BUY, SELL):
            continue

        rec = Recommender.evaluate(signal, candles)
        # Loc do tin cay chi ap cho trend (breakout khong dung nguong nay)
        if strat == "trend" and rec.confidence < min_conf:
            print("     -> conf {:.0f} < {} -> bo qua".format(rec.confidence, min_conf))
            continue

        skey = "{} {}".format(sym, tf)
        if state.get(skey) == ts:
            print("     -> da bao cho nen nay -> bo qua")
            continue

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
                "rr": plan.rr_ratio, "confidence": round(rec.confidence, 1),
                "outcome": "OPEN",
            })

    save_state(state)
    save_signals(signals_log)
    print("Xong. Da gui {} tin hieu.".format(sent))


if __name__ == "__main__":
    main()
