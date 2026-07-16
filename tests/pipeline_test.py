"""
Test pipeline KHONG can MT5 (deterministic). Chay: python tests/pipeline_test.py
Sinh dashboard/data.sample.js de xem truoc dashboard.
"""

import os
import sys
import json
import random
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.market.candle import Candle
from src.signal import patterns
from src.signal.trend import TrendService, higher_tf
from src.signal.signal_engine import SignalEngine
from src.signal.signal_service import SignalService
from src.ai_review.recommender import Recommender
from src.trade.trade_service import TradeService
from src.trade.outcome import OutcomeEvaluator, WIN, LOSS, OPEN
from src.backtest.backtester import Backtester

# Khoa cau hinh CO DINH cho test (doc lap voi .env cua nguoi dung)
import src.signal.signal_engine as _SE
_SE.REQUIRE_PATTERN = False
_SE.ADX_MIN = 20.0
_SE.PULLBACK_ATR_MULT = 1.0
import src.trade.risk_manager as _RM
_RM.TP_RR_TARGET = 0.0  # test trend TP theo cau truc (doc lap .env)

PASS = 0


def check(cond, msg):
    global PASS
    assert cond, "FAIL: " + msg
    PASS += 1
    print("  [ok]", msg)


def _c(o, h, l, c, i=0):
    return Candle(time=datetime(2026, 7, 1) + timedelta(minutes=15 * i),
                  open=o, high=h, low=l, close=c, volume=1000)


def buy_candles():
    base = [_c(94, 95, 93.5, 94.8, 0), _c(95, 96, 94.5, 95.6, 1),
            _c(96, 97, 95.5, 96.4, 2), _c(97, 98, 96.5, 97.2, 3)]
    prev = _c(100.0, 100.2, 97.8, 98.0, 4)
    cur = _c(97.5, 101.2, 97.3, 101.0, 5)
    return base + [prev, cur]


def sell_candles():
    base = [_c(106, 106.5, 105, 105.2, 0), _c(105, 105.5, 104, 104.4, 1),
            _c(104, 104.5, 103, 103.6, 2), _c(103, 103.5, 102, 102.8, 3)]
    prev = _c(100.0, 102.2, 99.8, 102.0, 4)
    cur = _c(102.5, 102.7, 98.8, 99.0, 5)
    return base + [prev, cur]


def build_series(base, slope, n=250, seed=1):
    random.seed(seed)
    out = []
    price = base
    for i in range(n):
        o = price
        price += slope + random.uniform(-abs(slope) * 0.5, abs(slope) * 0.5)
        c = price
        out.append(_c(round(o, 3), round(max(o, c) + 0.3, 3),
                      round(min(o, c) - 0.3, 3), round(c, 3), i))
    return out


def to_record(symbol, tf, signal, rec, plan, notified, price, outcome=None):
    r = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "candle_time": "2026-07-01 12:00:00",
        "symbol": symbol, "timeframe": tf,
        "action": signal.action, "trend": signal.trend,
        "strength": signal.strength, "price": price,
        "ema20": signal.ema20, "ema50": signal.ema50, "ema200": signal.ema200,
        "adx": signal.adx, "atr": signal.atr, "rsi": signal.rsi,
        "pattern": signal.pattern, "reason": signal.reason, "notified": notified,
        "recommendation": rec.action, "confidence": rec.confidence,
        "confidence_label": rec.label, "rec_reasons": rec.reasons,
    }
    if outcome:
        r["outcome"] = outcome
    if plan.action in ("BUY", "SELL"):
        r["trade_plan"] = {
            "entry": plan.entry_price, "stop_loss": plan.stop_loss,
            "take_profit": plan.take_profit, "risk_reward": plan.risk_reward,
            "rr_ratio": plan.rr_ratio, "risk_points": plan.risk_points,
            "reward_points": plan.reward_points, "risk_percent": plan.risk_percent,
            "sl_source": plan.sl_source, "tp_source": plan.tp_source,
            "trail_distance": plan.trail_distance,
            "risk_amount": plan.risk_amount, "lot_size": plan.lot_size,
            "expected_profit": plan.expected_profit,
        }
    return r


def main():
    print("== 1. TrendService (khung lon) ==")
    check(TrendService.direction(build_series(100, 1.0)) == "UPTREND", "uptrend detected")
    check(TrendService.direction(build_series(300, -1.0)) == "DOWNTREND", "downtrend detected")
    check(higher_tf("M15") == "H1" and higher_tf("M30") == "H4", "timeframe mapping")

    print("== 2. Da khung: HTF loc vao lenh ==")
    bc = buy_candles()
    # HTF UPTREND + ema20>ema50 -> BUY (khong can EMA200)
    s_buy = SignalEngine.analyze(bc, 100.8, 100.0, 98.0, 30.0, 1.0, 58.0, htf_trend="UPTREND")
    check(s_buy.action == "BUY", "HTF up + fast EMA -> BUY (got {})".format(s_buy.action))
    # HTF DOWNTREND chan BUY
    s_blk = SignalEngine.analyze(bc, 100.8, 100.0, 98.0, 30.0, 1.0, 58.0, htf_trend="DOWNTREND")
    check(s_blk.action == "NO_TRADE", "HTF down chan BUY -> NO_TRADE")
    # ADX floor moi = 20 (truoc la 25): ADX 22 van cho tin hieu
    s_adx = SignalEngine.analyze(bc, 100.8, 100.0, 98.0, 22.0, 1.0, 58.0, htf_trend="UPTREND")
    check(s_adx.action == "BUY", "ADX 22 (>20) van BUY - bot tre hon")

    sc = sell_candles()
    s_sell = SignalEngine.analyze(sc, 99.2, 100.0, 101.0, 30.0, 1.0, 42.0, htf_trend="DOWNTREND")
    check(s_sell.action == "SELL", "HTF down + fast EMA -> SELL")

    print("== 3. SL/TP DONG ==")
    plan = TradeService.create(s_buy, bc, symbol="XAUUSD", balance=10000, confidence=80)
    swing_low = min(c.low for c in bc[-5:])
    check(plan.stop_loss < swing_low, "SL nam DUOI swing low (dem ATR): {} < {}".format(
        plan.stop_loss, swing_low))
    check(plan.sl_source == "swing-ATR", "SL source = swing-ATR")
    check(plan.rr_ratio >= 1.2, "RR >= min 1.2 (dong, khong ep 2.0): {}".format(plan.rr_ratio))
    check(plan.trail_distance > 0, "co trailing distance ({})".format(plan.trail_distance))
    check("structure" in plan.tp_source or "atr" in plan.tp_source, "TP source: {}".format(plan.tp_source))

    print("== 4. Sizing co gian theo confidence ==")
    p60 = TradeService.create(s_buy, bc, symbol="XAUUSD", balance=10000, confidence=60)
    p90 = TradeService.create(s_buy, bc, symbol="XAUUSD", balance=10000, confidence=90)
    check(p90.risk_percent > p60.risk_percent, "conf cao -> risk% cao ({} > {})".format(
        p90.risk_percent, p60.risk_percent))
    check(p90.lot_size >= p60.lot_size, "conf cao -> lot >= ({} >= {})".format(
        p90.lot_size, p60.lot_size))
    check(0.5 <= p60.risk_percent <= 1.5, "risk% trong tran 0.5-1.5")

    print("== 4b. Lenh CHO (limit entry) ==")
    p_lim = TradeService.create(s_buy, bc, symbol="XAUUSD", balance=10000,
                                confidence=80, strategy="trend", entry_mode="limit")
    check(p_lim.entry_type == "limit", "trend + limit -> entry_type=limit")
    check(p_lim.entry_price < bc[-1].close, "BUY limit thap hon gia dong nen ({} < {})".format(
        p_lim.entry_price, bc[-1].close))
    p_mkt = TradeService.create(s_buy, bc, symbol="XAUUSD", balance=10000,
                                confidence=80, strategy="trend", entry_mode="market")
    check(p_mkt.entry_type == "market", "market -> entry_type=market")

    print("== 5. SignalService end-to-end + fallback (htf=None) ==")
    sig = SignalService.analyze(build_series(4000, 1.2, seed=3))
    check(sig.action in ("BUY", "SELL", "NO_TRADE"), "valid action")
    check(sig.atr > 0 and 0 <= sig.rsi <= 100, "ATR/RSI ok")

    print("== 5b. OutcomeEvaluator (WIN/LOSS theo thi truong) ==")
    # BUY entry ~101, gia chay len cham TP -> WIN
    up = [_c(101, 120, 100.5, 119, i) for i in range(6, 12)]
    check(OutcomeEvaluator.evaluate("BUY", 94.0, 110.0, up) == WIN, "BUY cham TP -> WIN")
    dn = [_c(101, 101.5, 90, 92, i) for i in range(6, 12)]
    check(OutcomeEvaluator.evaluate("BUY", 94.0, 110.0, dn) == LOSS, "BUY cham SL -> LOSS")
    flat = [_c(101, 102, 100, 101, i) for i in range(6, 12)]
    check(OutcomeEvaluator.evaluate("BUY", 94.0, 110.0, flat) == OPEN, "chua cham -> OPEN")

    print("== 5c. Backtester (nen gia song sin) ==")
    import math
    from datetime import datetime as _dt, timedelta as _td
    wav = []
    base = 2000.0
    for i in range(600):
        o = base + i * 1.5 + 25.0 * math.sin(i / 9.0)
        c = base + i * 1.5 + 25.0 * math.sin((i + 1) / 9.0)
        wav.append(Candle(time=_dt(2026, 1, 1) + _td(hours=i),
                          open=round(o, 2), high=round(max(o, c) + 3, 2),
                          low=round(min(o, c) - 3, 2), close=round(c, 2), volume=1000))
    res = Backtester.run(wav, symbol="XAUUSD", balance=10000,
                         lookahead=60, window=300, warmup=210)
    st = res["stats"]
    print("   ", st)
    check(st["trades"] >= 1, "backtest sinh >=1 lenh ({})".format(st["trades"]))
    check(st["wins"] + st["losses"] + st["timeouts"] == st["trades"], "phan loai khop tong")
    check(0 <= st["win_rate"] <= 100, "win_rate hop le ({})".format(st["win_rate"]))
    check(len(res["equity_curve"]) == st["trades"], "equity_curve dung so lenh")
    res_hi = Backtester.run(wav, symbol="XAUUSD", balance=10000,
                            min_confidence=999, lookahead=60, window=300, warmup=210)
    check(res_hi["stats"]["trades"] == 0, "MIN_CONFIDENCE=999 loc het lenh (0)")
    check(res_hi["stats"]["trades"] <= st["trades"], "loc lam giam so lenh")

    print("== 5d. Mean-Reversion (nhom XAU) ==")
    from src.signal.meanrev_engine import MeanRevEngine
    import src.signal.meanrev_engine as _MRE
    _MRE.MR_ADX_MAX = 25.0   # khoa config co dinh cho test (doc lap .env)
    _MRE.MR_STRETCH_ATR = 1.5
    _MRE.MR_RSI_OS = 30.0
    _MRE.MR_RSI_OB = 70.0
    _MRE.MR_CONFIRM = True
    mrc = [_c(101, 101.5, 100.5, 101, 0), _c(100, 100.5, 99, 99.5, 1),
           _c(99, 99.5, 98, 98.5, 2), _c(99, 99.2, 97.5, 98.0, 3),
           _c(98.5, 98.7, 97.0, 97.5, 4), _c(98, 98.2, 97.3, 98.0, 5)]
    s_mr = MeanRevEngine.analyze(mrc, 100.0, 100.5, 101.0, 15.0, 1.0, 25.0)
    check(s_mr.action == "BUY", "meanrev: gia duoi EMA + RSI25 + ADX15 -> BUY (got {})".format(s_mr.action))
    s_mr2 = MeanRevEngine.analyze(mrc, 100.0, 100.5, 101.0, 40.0, 1.0, 25.0)
    check(s_mr2.action == "NO_TRADE", "meanrev: ADX40 (trend manh) -> NO_TRADE")
    plan_mr = TradeService.create(s_mr, mrc, symbol="XAUUSD", balance=10000, confidence=70, strategy="meanrev")
    check(plan_mr.tp_source == "mean-EMA20", "meanrev TP nham ve EMA20 (got {})".format(plan_mr.tp_source))
    check(abs(plan_mr.take_profit - 100.0) < 0.05, "meanrev TP ~ EMA20 (got {})".format(plan_mr.take_profit))
    check(plan_mr.stop_loss < min(c.low for c in mrc[-5:]), "meanrev SL duoi day gan nhat")

    print("== 6. Sinh data.sample.js ==")
    rec_b = Recommender.evaluate(s_buy, bc)
    rec_s = Recommender.evaluate(s_sell, sc)
    s_wait = SignalEngine.analyze(bc, 100.8, 100.0, 98.0, 30.0, 1.0, 58.0, htf_trend="DOWNTREND")
    rec_w = Recommender.evaluate(s_wait, bc)
    records = [
        to_record("XAUUSD", "M15", s_buy, rec_b, plan, True, 101.0, outcome="WIN"),
        to_record("XAUUSD", "M30", s_sell,
                  rec_s, TradeService.create(s_sell, sc, symbol="XAUUSD", balance=10000,
                                             confidence=rec_s.confidence), True, 99.0, outcome="LOSS"),
        to_record("EURUSD", "H1", s_wait, rec_w,
                  TradeService.create(s_wait, bc, symbol="EURUSD"), False, 100.5),
    ]
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "dashboard", "data.sample.js")
    payload = {"updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
               "symbol": "XAUUSD", "timeframe": "", "signals": records}
    with open(out, "w", encoding="utf-8") as f:
        f.write("window.TA_DATA = ")
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write(";\n")
    check(os.path.exists(out), "data.sample.js written")

    print("\n[OK] {} checks PASS.".format(PASS))


if __name__ == "__main__":
    main()
