# -*- coding: utf-8 -*-
"""
Chay 1 lan (2026-10-11): tru spread vao r_result cua cac lenh DA DONG ghi truoc khi
bot biet tinh spread (xem src/trade/costs.py). Lenh da tru roi co co "r_net": true
-> bo qua, nen chay lai nhieu lan van an toan.

Chi tru CHI PHI (spread/risk); KHONG cham lai WIN/LOSS (khong con nen cu). Vai lenh
SELL sat SL/TP co the doi ket qua neu cham lai co spread -> so lieu nay van hoi lac quan.

Chay: python scripts/recalc_net_r.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.trade.costs import spread_r  # noqa: E402

PATH = "cloud_signals.json"


def main():
    with open(PATH, encoding="utf-8") as f:
        log = json.load(f)
    changed = before = after = 0.0
    n = 0
    for r in log:
        if r.get("outcome") not in ("WIN", "LOSS") or r.get("r_net"):
            continue
        if not isinstance(r.get("r_result"), (int, float)):
            continue
        cost = spread_r(r.get("symbol"), r.get("entry"), r.get("sl"))
        before += r["r_result"]
        r["r_result"] = round(r["r_result"] - cost, 3)
        r["r_net"] = True
        after += r["r_result"]
        n += 1
    with open(PATH, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)
    print("Da tru spread cho {} lenh: Tong R {:+.2f} -> {:+.2f}".format(n, before, after))


if __name__ == "__main__":
    main()
