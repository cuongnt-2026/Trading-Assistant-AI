# -*- coding: utf-8 -*-
"""
EmaTrendTracker - theo doi "dung/sai" cho tin hieu EmaTrendWatcher (xem
ema_trend_watcher.py). Theo yeu cau CuongNT (2026-09-15, cap nhat lai
2026-09-16 sau phan hoi): muon "dung" phai AN NANG hon "sai" theo kieu
R:R that (giong 1 lenh co SL/TP that), KHONG phai nguong doi xung (truoc day
ca 2 phia dung chung 1 nguong = R:R 1:1).

Cach cham diem MOI (gia lap 1 "lenh ao" theo dung huong tin hieu, dung SL/TP
"ao" tinh tu ATR - CHUA tung la lenh that, chi la thuoc do tham khao):

    risk  = EMATREND_EVAL_RISK_ATR  x ATR (luc ban tin hieu)   - vd 0.5 x ATR
    reward= risk x EMATREND_EVAL_RR                            - vd risk x 2 = 1.0 x ATR

    Tin hieu "up" (BUY):  SL_ao = gia_tin_hieu - risk   TP_ao = gia_tin_hieu + reward
    Tin hieu "down"(SELL):SL_ao = gia_tin_hieu + risk   TP_ao = gia_tin_hieu - reward

Sau do quet cac nen KE TIEP (dung high/low tung nen, giong het OutcomeEvaluator
dung cho lenh that o src/trade/outcome.py - de nhat quan quy uoc trong toan bo
du an): nen nao cham TP_ao TRUOC -> "dung"; cham SL_ao TRUOC -> "sai"; 1 nen
cham CA HAI -> tinh "sai" (bao thu, uu tien rui ro - giong OutcomeEvaluator).
Neu qua EMATREND_EVAL_MAX_BARS nen (mac dinh 96 nen ~ 1 ngay tren M15) van
chua cham gi ca -> "het_han" (khong ket luan duoc, KHONG tinh vao ty le).

Vi du cu the (dung so ATR THAT cua XAUUSD M15 luc viet, ~8.1 - xem giai thich
rieng voi CuongNT ve vi sao 0.3/0.09 la TY LE (boi so ATR) chu khong phai gia
USD, thuc te ra gia USD phai NHAN voi ATR):

    Tin hieu "cross" BUY luc 10:00, gia = 4300.0, ATR = 8.1.
    RISK_ATR=0.5 -> risk = 0.5*8.1 = 4.05   -> SL_ao = 4300.0 - 4.05 = 4295.95
    RR=2.0       -> reward = 4.05*2 = 8.10  -> TP_ao = 4300.0 + 8.10 = 4308.10
        - Neu gia cham 4308.10 TRUOC khi cham 4295.95 (theo thu tu nen) -> "dung".
        - Neu gia cham 4295.95 truoc (hoac ca 2 trong cung 1 nen)       -> "sai".
        - Neu sau 96 nen (~1 ngay) van lung lay giua 2 muc do             -> "het_han".

Luu vao 1 file JSON rieng (ematrend_history.json, xem run_cloud.py) - KHONG dung
chung voi cloud_signals.json (file danh cho lenh that co Entry/SL/TP/Win-Loss).
Day la module THONG KE THAM KHAO - khong dung de tu dong tat/bat tin hieu, chi
de hien thi ty le tren dashboard cho CuongNT tu danh gia.
"""
from datetime import datetime

from src.signal.constants import (
    EMATREND_EVAL_RISK_ATR, EMATREND_EVAL_RR, EMATREND_EVAL_MAX_BARS,
)

PENDING = "pending"
DUNG = "dung"
SAI = "sai"
HET_HAN = "het_han"


def record_event(history, symbol, timeframe, ev):
    """Tao 1 ban ghi moi cho tin hieu vua ban (ev tu EmaTrendWatcher.check_triple()/
    check_cross(), da duoc _scan_ema_trend gan them ev["atr"] = ATR tai thoi diem do).
    Goi ngay sau khi GUI MAIL THANH CONG (giong quy uoc cap nhat `state` trong
    run_cloud.py) - neu mail loi va tin hieu duoc thu lai o lan chay sau, candle_time
    khong doi nen se bi chan trung boi kiem tra id ben duoi, khong ghi 2 lan.

    Tra ve ban ghi vua tao, hoac None neu da ton tai (trung id) hoac thieu ATR.
    """
    records = history.setdefault("records", [])
    rec_id = "{}-{}-{}-{}".format(symbol, timeframe, ev.get("_ts", ev.get("candle_time")),
                                   ev.get("type"))
    if any(r.get("id") == rec_id for r in records):
        return None

    atr = ev.get("atr")
    price0 = ev.get("price")
    direction = ev.get("direction")
    if not atr or price0 is None or direction not in ("up", "down"):
        return None  # thieu du lieu goc -> khong the tao SL/TP ao, bo qua

    risk = EMATREND_EVAL_RISK_ATR * atr
    reward = risk * EMATREND_EVAL_RR
    if direction == "up":
        sl, tp = price0 - risk, price0 + reward
    else:
        sl, tp = price0 + risk, price0 - reward

    rec = {
        "id": rec_id,
        "symbol": symbol,
        "timeframe": timeframe,
        "kind": "triple" if ev.get("type") == "triple" else "cross",
        "event_type": ev.get("type"),        # "triple" | "about" | "crossed"
        "direction": direction,               # "up" | "down"
        "signal_time": ev.get("candle_time"),
        "signal_price": price0,
        "atr": atr,
        "risk_atr": EMATREND_EVAL_RISK_ATR,
        "rr": EMATREND_EVAL_RR,
        "sl": round(sl, 5),
        "tp": round(tp, 5),
        "result": PENDING,
        "resolved_time": None,
        "resolved_bars": None,
        "logged_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    }
    records.append(rec)
    return rec


def evaluate_pending(history, candles, symbol, timeframe):
    """Voi moi ban ghi (cung sym/tf) con "pending": tim lai nen tin hieu trong
    `candles` hien tai (danh sach da fetch san trong lan chay nay, KHONG ton them
    request API), quet TUNG NEN KE TIEP (dung high/low - giong OutcomeEvaluator o
    src/trade/outcome.py) xem cham TP_ao hay SL_ao truoc. Neu nen tin hieu da roi
    khoi cua so du lieu (qua cu) ma van chua ket luan -> "het_han" luon (khong con
    du lieu qua khu de quet tiep). Tra ve so ban ghi vua duoc ket luan trong lan
    goi nay (dung/sai/het_han - khong tinh "van dang cho them du lieu")."""
    records = [r for r in history.get("records", [])
               if r.get("symbol") == symbol and r.get("timeframe") == timeframe
               and r.get("result") == PENDING]
    if not records or not candles:
        return 0

    n_done = 0
    for rec in records:
        sig_ts = rec.get("signal_time")
        idx = None
        for i, c in enumerate(candles):
            if str(c.time) == sig_ts:
                idx = i
                break
        if idx is None:
            rec["result"] = HET_HAN
            n_done += 1
            continue

        sl, tp, direction = rec["sl"], rec["tp"], rec["direction"]
        max_bars = EMATREND_EVAL_MAX_BARS
        resolved = False
        for j in range(idx + 1, len(candles)):
            bars = j - idx
            if bars > max_bars:
                rec["result"] = HET_HAN
                resolved = True
                break
            c = candles[j]
            if direction == "up":
                hit_sl = c.low <= sl
                hit_tp = c.high >= tp
            else:
                hit_sl = c.high >= sl
                hit_tp = c.low <= tp
            if hit_sl and hit_tp:
                rec["result"] = SAI          # bao thu: cung 1 nen cham ca 2 -> tinh sai
            elif hit_tp:
                rec["result"] = DUNG
            elif hit_sl:
                rec["result"] = SAI
            else:
                continue
            rec["resolved_time"] = str(c.time)
            rec["resolved_bars"] = bars
            resolved = True
            break
        if resolved:
            n_done += 1
        # Con lai (chua du nen de ket luan, cung chua qua han) -> giu "pending",
        # cho lan chay sau (candles se dai them).
    return n_done


def compute_stats(history, symbol=None, timeframe=None, recent_limit=20):
    """Tong hop ty le dung/sai theo (kind, direction). `accuracy_pct` = dung /
    (dung+sai) * 100 (bo qua "het_han"/"pending" o mau so, vi 2 loai nay chua co
    ket luan). Tra ve dict de ghi vao dashboard (data.js)."""
    records = history.get("records", [])
    if symbol:
        records = [r for r in records if r.get("symbol") == symbol]
    if timeframe:
        records = [r for r in records if r.get("timeframe") == timeframe]

    buckets = {}
    for r in records:
        key = (r.get("kind"), r.get("direction"))
        b = buckets.setdefault(key, {"dung": 0, "sai": 0, "het_han": 0, "pending": 0})
        res = r.get("result", PENDING)
        b[res if res in (DUNG, SAI, HET_HAN) else PENDING] += 1

    by_kind_direction = []
    for (kind, direction), b in sorted(buckets.items(), key=lambda kv: (kv[0][0] or "", kv[0][1] or "")):
        evaluated = b["dung"] + b["sai"]
        acc = round(b["dung"] / evaluated * 100, 1) if evaluated else None
        by_kind_direction.append({
            "kind": kind, "direction": direction,
            "dung": b["dung"], "sai": b["sai"], "het_han": b["het_han"],
            "pending": b["pending"], "accuracy_pct": acc,
        })

    total_dung = sum(b["dung"] for b in buckets.values())
    total_sai = sum(b["sai"] for b in buckets.values())
    total_eval = total_dung + total_sai
    overall_acc = round(total_dung / total_eval * 100, 1) if total_eval else None

    recent = sorted(records, key=lambda r: r.get("signal_time") or "", reverse=True)[:recent_limit]

    return {
        "total_records": len(records),
        "overall_accuracy_pct": overall_acc,
        "overall_dung": total_dung,
        "overall_sai": total_sai,
        "by_kind_direction": by_kind_direction,
        "recent": recent,
        "risk_atr": EMATREND_EVAL_RISK_ATR,
        "rr": EMATREND_EVAL_RR,
        "max_bars": EMATREND_EVAL_MAX_BARS,
    }
