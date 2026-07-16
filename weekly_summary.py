# -*- coding: utf-8 -*-
"""Tong ket 7 ngay gan nhat tu reports/signals.json (forward-test)."""
import json, os
from datetime import datetime, timedelta

PATH = os.path.join("reports", "signals.json")

def load():
    if not os.path.exists(PATH):
        return []
    try:
        return json.load(open(PATH, encoding="utf-8"))
    except Exception:
        return []

def parse(ts):
    try: return datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
    except Exception: return None

def build_summary(days=7):
    recs = load()
    now = datetime.now()
    since = now - timedelta(days=days)
    week = [r for r in recs
            if r.get("action") in ("BUY", "SELL")
            and (parse(r.get("time", "")) or since) >= since]
    wins  = [r for r in week if r.get("outcome") == "WIN"]
    losses= [r for r in week if r.get("outcome") == "LOSS"]
    opens = [r for r in week if r.get("outcome") == "OPEN"]
    closed = len(wins) + len(losses)
    wr = (len(wins)/closed*100) if closed else 0.0
    total_r = sum((r.get("trade_plan") or {}).get("rr_ratio", 0.0) for r in wins) - len(losses)

    lines = []
    lines.append("========================================")
    lines.append("  TONG KET TUAN - Trading Assistant AI")
    lines.append("  {} -> {}".format(since.strftime("%d/%m"), now.strftime("%d/%m/%Y")))
    lines.append("========================================")
    lines.append("Tin hieu phat ra : {}".format(len(week)))
    lines.append("Da dong          : {}  (Win {} / Loss {})".format(closed, len(wins), len(losses)))
    lines.append("Con mo (OPEN)     : {}".format(len(opens)))
    lines.append("WinRate           : {:.1f}%".format(wr))
    lines.append("Tong R            : {:+.2f}".format(total_r))
    lines.append("")
    # theo tung cap
    by = {}
    for r in week:
        k = "{} {}".format(r.get("symbol"), r.get("timeframe"))
        b = by.setdefault(k, [0,0,0])
        if r.get("outcome")=="WIN": b[0]+=1
        elif r.get("outcome")=="LOSS": b[1]+=1
        else: b[2]+=1
    if by:
        lines.append("---- Theo cap ----")
        for k,(w,l,o) in sorted(by.items()):
            c=w+l; wr2=(w/c*100) if c else 0
            lines.append("{:<12} W{} L{} O{}  WR {:.0f}%".format(k,w,l,o,wr2))
    if not week:
        lines.append("(Tuan nay chua co tin hieu BUY/SELL nao.)")
    lines.append("")
    lines.append("Luu y: forward-test, tin hieu tham khao - khong phai loi khuyen dau tu.")
    return "\n".join(lines)

if __name__ == "__main__":
    print(build_summary())
