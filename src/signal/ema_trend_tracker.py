# -*- coding: utf-8 -*-
"""
EmaTrendTracker - theo doi "dung/sai" cho tin hieu EmaTrendWatcher (xem
ema_trend_watcher.py). Theo yeu cau CuongNT (2026-09-15): muon biet cac tin hieu
EMA moi (cross/triple) ban ra co thuc su dung huong hay khong, de co so ma tin
tuong (hoac nghi ngo) khi doc mail.

Tin hieu EMA Trend Watch KHONG phai lenh co san Entry/SL/TP nen khong the cham
Win/Loss/R nhu cac chien luoc khac (Supertrend/Breakout/Trend...). Thay vao do,
module nay do xem SAU khi tin hieu ban ra, gia co thuc su di DUNG huong du doan
(BUY/SELL) hay khong, tai 3 moc thoi gian co dinh (tinh theo so nen M15):

    h1 = 4  nen sau khi tin hieu  (~1 gio)
    h4 = 16 nen sau khi tin hieu  (~4 gio)
    d1 = 96 nen sau khi tin hieu  (~1 ngay)

Quy tac cham diem tai moi moc: so gia luc do voi gia luc ban tin hieu, doi ra
BOI SO ATR (ATR tai thoi diem ban tin hieu, de chuan hoa - khong dung % gia tho
vi XAUUSD bien dong manh yeu hon/manh hon tuy giai doan):

    doi_ATR = (gia_luc_do - gia_luc_tin_hieu) / ATR_luc_tin_hieu
              (dao dau neu tin hieu la "down"/SELL, de "doi_ATR duong" luon
              nghia la "di dung huong du doan")

    doi_ATR >= +EMATREND_EVAL_ATR_MULT  -> "dung"    (gia di dung huong, du xa)
    doi_ATR <= -EMATREND_EVAL_ATR_MULT  -> "sai"      (gia di NGUOC huong, du xa)
    o giua (|doi_ATR| < nguong)          -> "chua_ro" (gia loanh quanh, chua ro
                                             ret dung/sai - KHONG tinh vao ca 2
                                             phia de khoi lam ao ty le)

Vi du cu the (xem huong dan trong lich su chat voi CuongNT):
    Tin hieu "cross" huong up (BUY) luc 10:00, gia luc do = 4270.0, ATR = 3.0.
    Nguong EMATREND_EVAL_ATR_MULT mac dinh = 0.3 -> can gia doi >= 0.3*3.0 = 0.9
    (theo dung huong tang) moi tinh la "dung".
        - Sau 1 gio (10:00 + 4 nen), gia = 4271.5 -> doi_ATR = (4271.5-4270)/3.0
          = +0.5  -> |0.5| < 0.9 (nguong) -> "chua_ro" (chua du ro rang).
        - Sau 4 gio, gia = 4273.2 -> doi_ATR = (4273.2-4270)/3.0 = +1.07
          -> >= +0.9 -> "dung" (gia da tang du ro theo dung huong BUY).
        - Neu thay vi vay gia lai giam con 4267.0 -> doi_ATR = (4267-4270)/3.0
          = -1.0 -> <= -0.9 -> "sai" (gia di NGUOC voi du doan BUY).

Luu vao 1 file JSON rieng (ematrend_history.json, xem run_cloud.py) - KHONG dung
chung voi cloud_signals.json (file danh cho lenh that co Entry/SL/TP/Win-Loss).
Day la module THONG KE THAM KHAO - khong dung de tu dong tat/bat tin hieu, chi
de hien thi ty le tren dashboard cho CuongNT tu danh gia.
"""
from datetime import datetime

from src.signal.constants import EMATREND_EVAL_ATR_MULT

# (ten_moc, so_nen_sau_tin_hieu) - co the them moc khac o day neu can (vd "d3"=288).
HORIZONS = [("h1", 4), ("h4", 16), ("d1", 96)]

PENDING_STATES = ("pending", "khong_du_du_lieu")


def _empty_eval():
    return {hk: {"bars": bars, "result": "pending", "price": None, "atr_mult": None}
            for hk, bars in HORIZONS}


def record_event(history, symbol, timeframe, ev):
    """Tao 1 ban ghi moi cho tin hieu vua ban (ev tu EmaTrendWatcher.check_triple()/
    check_cross(), da duoc _scan_ema_trend gan them ev["atr"] = ATR tai thoi diem do).
    Goi ngay sau khi GUI MAIL THANH CONG (giong quy uoc cap nhat `state` trong
    run_cloud.py) - neu mail loi va tin hieu duoc thu lai o lan chay sau, candle_time
    khong doi nen se bi chan trung boi kiem tra id ben duoi, khong ghi 2 lan.

    Tra ve ban ghi vua tao, hoac None neu da ton tai (trung id).
    """
    records = history.setdefault("records", [])
    rec_id = "{}-{}-{}-{}".format(symbol, timeframe, ev.get("_ts", ev.get("candle_time")),
                                   ev.get("type"))
    if any(r.get("id") == rec_id for r in records):
        return None

    rec = {
        "id": rec_id,
        "symbol": symbol,
        "timeframe": timeframe,
        "kind": "triple" if ev.get("type") == "triple" else "cross",
        "event_type": ev.get("type"),        # "triple" | "about" | "crossed"
        "direction": ev.get("direction"),     # "up" | "down"
        "signal_time": ev.get("candle_time"),
        "signal_price": ev.get("price"),
        "atr": ev.get("atr"),
        "logged_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "eval": _empty_eval(),
    }
    records.append(rec)
    return rec


def evaluate_pending(history, candles, symbol, timeframe):
    """Voi moi ban ghi (cung sym/tf) con moc "pending": tim lai nen tin hieu trong
    `candles` hien tai (danh sach da fetch san trong lan chay nay, KHONG ton them
    request API); neu da du so nen tinh tu do (theo HORIZONS) -> cham diem "dung/
    sai/chua_ro". Neu nen tin hieu da roi khoi cua so du lieu (qua cu, ATR/gia luc do
    khong con trong `candles`) -> danh dau "khong_du_du_lieu" de khoi thu cham lai
    vo han lan moi lan chay. Tra ve so moc vua cham xong trong lan goi nay."""
    records = [r for r in history.get("records", [])
               if r.get("symbol") == symbol and r.get("timeframe") == timeframe]
    if not records or not candles:
        return 0

    n_done = 0
    for rec in records:
        pending_keys = [k for k, v in rec["eval"].items() if v["result"] == "pending"]
        if not pending_keys:
            continue

        sig_ts = rec.get("signal_time")
        idx = None
        for i, c in enumerate(candles):
            if str(c.time) == sig_ts:
                idx = i
                break
        if idx is None:
            for k in pending_keys:
                rec["eval"][k] = {**rec["eval"][k], "result": "khong_du_du_lieu"}
            continue

        atr = rec.get("atr") or 0
        price0 = rec.get("signal_price")
        direction = rec.get("direction")
        if not atr or price0 is None:
            continue  # thieu du lieu goc (khong nen xay ra) -> bo qua, thu lai sau

        for k in pending_keys:
            bars = rec["eval"][k]["bars"]
            target_idx = idx + bars
            if target_idx >= len(candles):
                continue  # chua toi luc, cho lan chay sau
            price_then = candles[target_idx].close
            atr_mult = (price_then - price0) / atr
            if direction == "down":
                atr_mult = -atr_mult
            if atr_mult >= EMATREND_EVAL_ATR_MULT:
                result = "dung"
            elif atr_mult <= -EMATREND_EVAL_ATR_MULT:
                result = "sai"
            else:
                result = "chua_ro"
            rec["eval"][k] = {"bars": bars, "result": result,
                               "price": round(price_then, 5),
                               "atr_mult": round(atr_mult, 3)}
            n_done += 1
    return n_done


def compute_stats(history, symbol=None, timeframe=None, recent_limit=20):
    """Tong hop ty le dung/sai theo (kind, direction) x moc thoi gian (h1/h4/d1).
    `accuracy_pct` = dung / (dung+sai) * 100 (bo qua "chua_ro"/"pending" o mau so,
    vi 2 loai nay chua co ket luan). Tra ve dict de ghi vao dashboard (data.js)."""
    records = history.get("records", [])
    if symbol:
        records = [r for r in records if r.get("symbol") == symbol]
    if timeframe:
        records = [r for r in records if r.get("timeframe") == timeframe]

    buckets = {}
    for r in records:
        key = (r.get("kind"), r.get("direction"))
        b = buckets.setdefault(key, {hk: {"dung": 0, "sai": 0, "chua_ro": 0, "pending": 0}
                                      for hk, _ in HORIZONS})
        for hk, _ in HORIZONS:
            res = r.get("eval", {}).get(hk, {}).get("result", "pending")
            if res in PENDING_STATES:
                b[hk]["pending"] += 1
            else:
                b[hk][res] += 1

    by_kind_direction = []
    for (kind, direction), b in sorted(buckets.items(), key=lambda kv: (kv[0][0] or "", kv[0][1] or "")):
        row = {"kind": kind, "direction": direction, "horizons": {}}
        for hk, _ in HORIZONS:
            d = b[hk]
            evaluated = d["dung"] + d["sai"]
            acc = round(d["dung"] / evaluated * 100, 1) if evaluated else None
            row["horizons"][hk] = {
                "dung": d["dung"], "sai": d["sai"], "chua_ro": d["chua_ro"],
                "pending": d["pending"], "accuracy_pct": acc,
            }
        by_kind_direction.append(row)

    recent = sorted(records, key=lambda r: r.get("signal_time") or "", reverse=True)[:recent_limit]

    return {
        "total_records": len(records),
        "by_kind_direction": by_kind_direction,
        "recent": recent,
        "eval_atr_mult": EMATREND_EVAL_ATR_MULT,
        "horizons": [{"key": hk, "bars": bars} for hk, bars in HORIZONS],
    }
