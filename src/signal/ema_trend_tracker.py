# -*- coding: utf-8 -*-
"""
EmaTrendTracker - theo doi "dung/sai" cho tin hieu EmaTrendWatcher (xem
ema_trend_watcher.py). Lich su thay doi cach cham diem (theo phan hoi CuongNT):

  v1 (2026-09-15): "chua_ro" trong 1 khoang ATR doi xung quanh gia tin hieu, kiem
      tra tai 3 moc thoi gian co dinh (1h/4h/1 ngay).
  v2 (2026-09-16): doi sang "lenh ao" co SL/TP, nhung SL/TP la MOT BOI SO ATR CO
      DINH (vd luon 0.5xATR) - CuongNT phan hoi dung the la chua on: "sl dat sao
      cho ko duoc, phai tinh duoc quy luat dat sl/tp, khong phai co dinh luc nao
      cung chung do, ma tuy thi truong/nen".
  v3 (hien tai): SL/TP AO tinh THEO CAU TRUC GIA THAT (swing high/low + khang cu/
      ho tro gan nhat), dung LAI CHINH XAC logic RiskManager.dynamic_levels() dang
      dung cho lenh THAT trong he thong (xem src/trade/risk_manager.py) - de nhat
      quan va vi day la cach dat SL/TP da duoc kiem chung, khong phai bia moi:

        SL_ao = swing high/low gan nhat trong EMATREND_EVAL_SWING_LOOKBACK nen
                truoc tin hieu, +/- dem EMATREND_EVAL_SL_ATR_BUFFER x ATR (dem
                chong "quet rau nen"). Khong duoc gan hon
                EMATREND_EVAL_MIN_RISK_ATR x ATR (san rui ro toi thieu - neu swing
                gan sat gia thi ep SL ra xa hon, tranh bi quet ngay tuc khac).
                -> SL_ao BIEN DOI theo tung tin hieu, KHONG con la 1 con so co
                   dinh nhu ban truoc.

        TP_ao = khang cu (BUY) / ho tro (SELL) gan nhat trong
                EMATREND_EVAL_TP_LOOKBACK nen truoc tin hieu, NEU muc do cho ty
                le R:R >= EMATREND_EVAL_RR; neu khong (cau truc qua gan hoac
                khong ro) -> ep TP_ao = risk x EMATREND_EVAL_RR (san R:R toi
                thieu).

  v4 (2026-09-16): EMATREND_EVAL_RR (san R:R toi thieu de tinh "dung") doi tu 2.0
      -> 1.0 -> 1.2 theo phan hoi CuongNT: luc dau muon "dung phai kho hon sai"
      (RR>=2), sau do doi lai chi can thang la tinh dung (RR=1.0), roi chot lai
      RR=1.2 de bu spread/phi giao dich (hoa von that ngoai doi can TP xa hon SL
      mot chut). SL/TP van tinh theo cau truc y het v3, chi doi con so nguong RR.

Sau do quet cac nen KE TIEP (dung high/low tung nen, giong het OutcomeEvaluator
dung cho lenh that o src/trade/outcome.py - de nhat quan quy uoc trong toan bo
du an): nen nao cham TP_ao TRUOC -> "dung"; cham SL_ao TRUOC -> "sai"; 1 nen
cham CA HAI -> tinh "sai" (bao thu, uu tien rui ro - giong OutcomeEvaluator).
Neu qua EMATREND_EVAL_MAX_BARS nen (mac dinh 96 nen ~ 1 ngay tren M15) van
chua cham gi ca -> "het_han" (khong ket luan duoc, KHONG tinh vao ty le).

QUAN TRONG (tranh nhin-truoc-tuong-lai/lookahead bias): SL/TP ao CHI duoc tinh
tu cac nen CO SAN TAI THOI DIEM ban tin hieu (candles[:idx_tin_hieu+1], KHONG
dung bat ky nen nao SAU do) - dung y nghia "neu la lenh that thi luc do minh chi
biet duoc bay nhieu thong tin nay thoi".

Luu vao 1 file JSON rieng (ematrend_history.json, xem run_cloud.py) - KHONG dung
chung voi cloud_signals.json (file danh cho lenh that co Entry/SL/TP/Win-Loss).
Day la module THONG KE THAM KHAO - khong dung de tu dong tat/bat tin hieu, chi
de hien thi ty le tren dashboard cho CuongNT tu danh gia.
"""
from datetime import datetime

from src.signal.constants import (
    EMATREND_EVAL_SWING_LOOKBACK, EMATREND_EVAL_SL_ATR_BUFFER,
    EMATREND_EVAL_MIN_RISK_ATR, EMATREND_EVAL_TP_LOOKBACK, EMATREND_EVAL_RR,
    EMATREND_EVAL_MAX_BARS,
)

PENDING = "pending"
DUNG = "dung"
SAI = "sai"
HET_HAN = "het_han"


def _virtual_levels(direction, price0, atr, candles_upto_signal):
    """Tinh SL_ao/TP_ao theo CAU TRUC (swing + khang cu/ho tro), y het
    RiskManager.dynamic_levels() dung cho lenh that - xem docstring module.
    `candles_upto_signal` PHAI la danh sach nen tinh DEN VA BAO GOM nen tin hieu
    (khong duoc chua nen nao sau do, tranh lookahead bias)."""
    recent = candles_upto_signal[-EMATREND_EVAL_SWING_LOOKBACK:]
    wide = (candles_upto_signal[-EMATREND_EVAL_TP_LOOKBACK:]
            if len(candles_upto_signal) >= EMATREND_EVAL_TP_LOOKBACK else candles_upto_signal)

    if direction == "up":
        swing_low = min(c.low for c in recent)
        sl = swing_low - EMATREND_EVAL_SL_ATR_BUFFER * atr
        sl = min(sl, price0 - EMATREND_EVAL_MIN_RISK_ATR * atr)   # san rui ro toi thieu
        sl_source = "swing-ATR"
        risk = price0 - sl

        resistance = max(c.high for c in wide)
        if resistance > price0 + 0.1 * atr and (resistance - price0) >= EMATREND_EVAL_RR * risk:
            tp, tp_source = resistance, "structure"
        else:
            tp, tp_source = price0 + EMATREND_EVAL_RR * risk, "rr{:g}".format(EMATREND_EVAL_RR)
    else:
        swing_high = max(c.high for c in recent)
        sl = swing_high + EMATREND_EVAL_SL_ATR_BUFFER * atr
        sl = max(sl, price0 + EMATREND_EVAL_MIN_RISK_ATR * atr)
        sl_source = "swing-ATR"
        risk = sl - price0

        support = min(c.low for c in wide)
        if support < price0 - 0.1 * atr and (price0 - support) >= EMATREND_EVAL_RR * risk:
            tp, tp_source = support, "structure"
        else:
            tp, tp_source = price0 - EMATREND_EVAL_RR * risk, "rr{:g}".format(EMATREND_EVAL_RR)

    rr_actual = round(abs(tp - price0) / risk, 2) if risk else None
    return sl, tp, sl_source, tp_source, risk, rr_actual


def record_event(history, symbol, timeframe, ev, candles):
    """Tao 1 ban ghi moi cho tin hieu vua ban (ev tu EmaTrendWatcher.check_triple()/
    check_cross(), da duoc _scan_ema_trend gan them ev["atr"] = ATR tai thoi diem
    do). `candles` la danh sach nen dung de PHAT HIEN tin hieu nay (nen cuoi cung =
    nen tin hieu, KHONG chua nen nao sau do) - dung de tinh SL/TP ao theo cau truc.

    Goi ngay sau khi GUI MAIL THANH CONG (giong quy uoc cap nhat `state` trong
    run_cloud.py) - neu mail loi va tin hieu duoc thu lai o lan chay sau, candle_time
    khong doi nen se bi chan trung boi kiem tra id ben duoi, khong ghi 2 lan.

    Tra ve ban ghi vua tao, hoac None neu da ton tai (trung id) hoac thieu du lieu.
    """
    records = history.setdefault("records", [])
    rec_id = "{}-{}-{}-{}".format(symbol, timeframe, ev.get("_ts", ev.get("candle_time")),
                                   ev.get("type"))
    if any(r.get("id") == rec_id for r in records):
        return None

    atr = ev.get("atr")
    price0 = ev.get("price")
    direction = ev.get("direction")
    if not atr or price0 is None or direction not in ("up", "down") or not candles:
        return None  # thieu du lieu goc -> khong the tao SL/TP ao, bo qua

    sl, tp, sl_source, tp_source, risk, rr_actual = _virtual_levels(direction, price0, atr, candles)

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
        "sl": round(sl, 5),
        "tp": round(tp, 5),
        "sl_source": sl_source,
        "tp_source": tp_source,
        "risk": round(risk, 5),
        "rr": rr_actual,
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

    rr_vals = [r["rr"] for r in records if isinstance(r.get("rr"), (int, float))]
    avg_rr = round(sum(rr_vals) / len(rr_vals), 2) if rr_vals else None

    recent = sorted(records, key=lambda r: r.get("signal_time") or "", reverse=True)[:recent_limit]

    return {
        "total_records": len(records),
        "overall_accuracy_pct": overall_acc,
        "overall_dung": total_dung,
        "overall_sai": total_sai,
        "by_kind_direction": by_kind_direction,
        "recent": recent,
        "rr_target": EMATREND_EVAL_RR,     # R:R toi thieu ap dung (san), xem docstring
        "avg_rr_actual": avg_rr,           # R:R thuc te trung binh (co the > target neu TP theo cau truc xa hon)
        "max_bars": EMATREND_EVAL_MAX_BARS,
    }
