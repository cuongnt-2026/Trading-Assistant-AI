# -*- coding: utf-8 -*-
"""Tong ket 7 ngay tu cloud_signals.json (tin hieu cloud + Win/Loss)."""
import json
import os
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


def build_summary(days=7):
    recs = load()
    now = datetime.utcnow()
    since = now - timedelta(days=days)
    week = [r for r in recs if (parse(r.get("candle_time", "")) or since) >= since]

    wins = [r for r in week if r.get("outcome") == "WIN"]
    losses = [r for r in week if r.get("outcome") == "LOSS"]
    opens = [r for r in week if r.get("outcome") == "OPEN"]
    closed = len(wins) + len(losses)
    wr = round(len(wins) / closed * 100, 1) if closed else 0.0
    def _rval(r):
        if r.get("r_result") is not None:
            return r["r_result"]
        if r.get("outcome") == "WIN":
            return r.get("rr") or 0.0
        return -1.0
    total_r = round(sum(_rval(r) for r in (wins + losses)), 2)

    L = []
    L.append("========================================")
    L.append("  TONG KET TUAN (CLOUD) - Trading Assistant AI")
    L.append("  {} -> {} (UTC)".format(since.strftime("%d/%m"), now.strftime("%d/%m/%Y")))
    L.append("========================================")
    L.append("Tin hieu gui ra : {}".format(len(week)))
    L.append("Da dong         : {}  (Win {} / Loss {})".format(closed, len(wins), len(losses)))
    L.append("Con mo (OPEN)   : {}".format(len(opens)))
    L.append("WinRate         : {}%".format(wr))
    L.append("Tong R          : {:+.2f}".format(total_r))
    L.append("")
    if week:
        L.append("---- Chi tiet ----")
        for r in week:
            L.append("{} {} {} {} @ E:{} SL:{} TP:{} | {} | conf {}".format(
                r.get("candle_time", ""), r.get("symbol"), r.get("timeframe"),
                r.get("action"), r.get("entry"), r.get("sl"), r.get("tp"),
                r.get("outcome"), r.get("confidence")))
    else:
        L.append("(Tuan nay chua co tin hieu nao.)")
    L.append("")
    L.append("Luu y: forward-test, tin hieu tham khao - khong phai loi khuyen dau tu.")
    return "\n".join(L)


if __name__ == "__main__":
    print(build_summary())
