# -*- coding: utf-8 -*-
"""
run_cloud.py - chay tren GitHub Actions (khong can MT5).
Lay gia tu Twelve Data -> chay dung bo loc trend + lenh cho -> gui mail.
Chong gui trung bang cloud_state.json (nho nen da bao cho moi cap).
"""
import os
import sys
import json
import time
from datetime import datetime

from src.core.config import Config
from src.data.webdata import WebData
from src.signal.signal_service import SignalService
from src.signal.trend import TrendService, higher_tf
from src.signal.constants import BUY, SELL
from src.ai_review.recommender import Recommender
from src.trade.trade_service import TradeService
from src.notifier.factory import create_notifier
from src.notifier.messages import build_signal_email

STATE_PATH = "cloud_state.json"


def load_state():
    try:
        return json.load(open(STATE_PATH, encoding="utf-8"))
    except Exception:
        return {}


def save_state(s):
    json.dump(s, open(STATE_PATH, "w", encoding="utf-8"), indent=2, ensure_ascii=False)


def main():
    cfg = Config()
    notifier = create_notifier(cfg)
    state = load_state()

    fx = cfg.groups.get("FOREX", {})
    symbols = fx.get("symbols", [])
    tfs = fx.get("timeframes", [])
    min_conf = cfg.min_confidence
    print("Cloud run {} | FX={} | TF={} | MIN_CONF={} | entry={}".format(
        datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        ",".join(symbols), ",".join(tfs), min_conf, cfg.entry_mode))

    htf_cache = {}
    sent = 0
    for sym in symbols:
        for tf in tfs:
            try:
                candles = WebData.get_candles(sym, tf, cfg.candle_count)
            except Exception as e:
                print("[WARN] {} {} fetch loi: {}".format(sym, tf, e))
                continue
            if not candles or len(candles) < 200:
                print("[WARN] {} {} khong du nen ({})".format(
                    sym, tf, len(candles) if candles else 0))
                continue

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

            signal = SignalService.analyze(candles, htf_trend=htf_trend, strategy="trend")
            last = candles[-1]
            ts = str(last.time)
            print("  {} {} | {} | trend={} | close={:.5g} | ADX={:.1f}".format(
                sym, tf, signal.action, signal.trend, last.close, signal.adx))

            if signal.action not in (BUY, SELL):
                continue

            rec = Recommender.evaluate(signal, candles)
            if rec.confidence < min_conf:
                print("     -> conf {:.0f} < {} -> bo qua".format(rec.confidence, min_conf))
                continue

            skey = "{} {}".format(sym, tf)
            if state.get(skey) == ts:
                print("     -> da bao cho nen nay -> bo qua")
                continue

            plan = TradeService.create(
                signal, candles, symbol=sym, balance=cfg.account_balance or None,
                confidence=rec.confidence, risk_min=cfg.risk_min_percent,
                risk_max=cfg.risk_max_percent, strategy="trend",
                entry_mode=cfg.entry_mode)
            subject, body = build_signal_email(
                signal, sym, tf, last, recommendation=rec, trade_plan=plan)
            subject = "[CLOUD] " + subject
            ok = notifier.send(subject, body) if notifier else False
            print("     -> GUI MAIL: {} (conf {:.0f})".format(
                "OK" if ok else "FAIL/none", rec.confidence))
            if ok:
                state[skey] = ts
                sent += 1

    save_state(state)
    print("Xong. Da gui {} tin hieu.".format(sent))


if __name__ == "__main__":
    main()
