# -*- coding: utf-8 -*-
"""Tong ket tin hieu cloud tu cloud_signals.json (tin hieu + Win/Loss).

- build_summary(days=7)      : tong ket N ngay gan nhat (mac dinh 1 tuan).
- build_summary_prev_month() : tong ket THANG DUONG LICH truoc do.
"""
import json
import re
from datetime import datetime, timedelta

PATH = "cloud_signals.json"


def load():
    try:
        return json.load(open(PATH, encoding="utf-8"))
    except Exception:
        return []


def parse(ts):
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M UTC"):
        try:
            return datetime.strptime(ts, fmt)
        except Exception:
            continue
    return None


def _rr_of(r):
    """RR (so lan rui ro) cua 1 lenh: uu tien r['rr'] (so thuc), neu thieu/0 thi doc
    chuoi r['risk_reward'] (vd "1 : 2.5" -> 2.5), cuoi cung tinh tu entry/sl/tp.
    (Fix cung logic voi rrOf() da vá trong dashboard/index.html ngay 2026-09-01 -
    truoc day thieu ham nay nen lenh WIN ma thieu/0 "rr" se bi tinh nham thanh 0R.)
    """
    rr = r.get("rr")
    if isinstance(rr, (int, float)) and rr:
        return float(rr)
    rrs = r.get("risk_reward")
    if isinstance(rrs, str):
        m = re.search(r"([\d.]+)\s*$", rrs.strip())
        if m:
            try:
                return float(m.group(1))
            except Exception:
                pass
    try:
        e, sl, tp = float(r.get("entry")), float(r.get("sl")), float(r.get("tp"))
        if abs(e - sl) > 0:
            return abs(tp - e) / abs(e - sl)
    except Exception:
        pass
    return 0.0


def _rval(r):
    if r.get("r_result") is not None:
        return r["r_result"]
    if r.get("outcome") == "WIN":
        return _rr_of(r)
    return -1.0


def _build(since, until, title, range_label):
    """Dung text tong ket cho khoang [since, until)."""
    recs = load()
    rows = []
    for r in recs:
        if r.get("strategy") == "trend":   # Trend da tat -> khong tinh vao tong ket
            continue
        t = parse(r.get("candle_time", ""))
        if t is None:
            continue
        if since <= t < until:
            rows.append(r)

    wins = [r for r in rows if r.get("outcome") == "WIN"]
    losses = [r for r in rows if r.get("outcome") == "LOSS"]
    opens = [r for r in rows if r.get("outcome") == "OPEN"]
    closed = len(wins) + len(losses)
    wr = round(len(wins) / closed * 100, 1) if closed else 0.0
    total_r = round(sum(_rval(r) for r in (wins + losses)), 2)

    L = []
    L.append("========================================")
    L.append("  " + title)
    L.append("  " + range_label)
    L.append("========================================")
    L.append("Tin hieu gui ra : {}".format(len(rows)))
    L.append("Da dong         : {}  (Win {} / Loss {})".format(closed, len(wins), len(losses)))
    L.append("Con mo (OPEN)   : {}".format(len(opens)))
    L.append("WinRate         : {}%".format(wr))
    L.append("Tong R          : {:+.2f}".format(total_r))
    L.append("")
    if rows:
        L.append("---- Chi tiet ----")
        for r in rows:
            L.append("{} {} {} {} @ E:{} SL:{} TP:{} | {} | conf {}".format(
                r.get("candle_time", ""), r.get("symbol"), r.get("timeframe"),
                r.get("action"), r.get("entry"), r.get("sl"), r.get("tp"),
                r.get("outcome"), r.get("confidence")))
    else:
        L.append("(Ky nay chua co tin hieu nao.)")
    L.append("")
    L.append("Luu y: forward-test, tin hieu tham khao - khong phai loi khuyen dau tu.")
    return "\n".join(L)


def build_summary(days=7):
    now = datetime.utcnow()
    since = now - timedelta(days=days)
    return _build(
        since, now,
        "TONG KET TUAN (CLOUD) - Trading Assistant AI",
        "{} -> {} (UTC)".format(since.strftime("%d/%m"), now.strftime("%d/%m/%Y")),
    )


def build_summary_prev_month(ref=None):
    """Tong ket thang duong lich truoc thoi diem ref (mac dinh: bay gio UTC)."""
    now = ref or datetime.utcnow()
    first_this = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    until = first_this
    since = (first_this - timedelta(days=1)).replace(day=1)
    return _build(
        since, until,
        "TONG KET THANG (CLOUD) - Trading Assistant AI",
        "Thang {} ({} -> het {})".format(
            since.strftime("%m/%Y"),
            since.strftime("%d/%m"),
            (until - timedelta(days=1)).strftime("%d/%m")),
    )


if __name__ == "__main__":
    print(build_summary())
