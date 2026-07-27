# -*- coding: utf-8 -*-
"""
backtest_hedge.py - Backtest chien luoc HEDGE tai khang cu manh (chi XAUUSD).

Luat:
  - Xu huong tang = HH (dinh sau cao hon) + HL (day sau cao hon).
  - Khang cu = vung gia co >= 3 lan dinh swing cham ma dong cua KHONG vuot len.
  - Lan cham thu 4 -> mo HEDGE: dong thoi BUY va SELL tai muc khang cu.
  - TP Sell = +10 USD (gia giam 10) ; SL Sell = -20 (gia tang 20).
  - TP Buy  = +20 USD (gia tang 20) ; SL Buy  = -20 (gia giam 20).
  - Ket qua moi HEDGE = pnl_buy + pnl_sell (USD tren 1 don vi gia).
"""
import os
import sys

RES_PIVOT = int(os.getenv("RES_PIVOT", "3"))       # nen 2 ben de la dinh swing
RES_TOL_PCT = float(os.getenv("RES_TOL_PCT", "0.1"))  # dung sai "cham" = % gia (~4 diem @4000)
TP_BUY = float(os.getenv("HEDGE_TP_BUY", "20"))
TP_SELL = float(os.getenv("HEDGE_TP_SELL", "10"))
SL_USD = float(os.getenv("HEDGE_SL", "20"))
LOOKAHEAD = int(os.getenv("HEDGE_LOOKAHEAD", "400"))
MIN_TOUCH = int(os.getenv("HEDGE_MIN_TOUCH", "4"))


def _pivot_highs(cs, k):
    raw = []
    for i in range(k, len(cs) - k):
        if cs[i].high == max(c.high for c in cs[i - k:i + k + 1]):
            raw.append((i, cs[i].high))
    out = []                       # gop pivot sat nhau (giu dinh cao hon)
    for (i, p) in raw:
        if out and i - out[-1][0] <= k:
            if p >= out[-1][1]:
                out[-1] = (i, p)
        else:
            out.append((i, p))
    return out


def _pivot_lows(cs, k):
    raw = []
    for i in range(k, len(cs) - k):
        if cs[i].low == min(c.low for c in cs[i - k:i + k + 1]):
            raw.append((i, cs[i].low))
    out = []                       # gop pivot sat nhau (giu day thap hon)
    for (i, p) in raw:
        if out and i - out[-1][0] <= k:
            if p <= out[-1][1]:
                out[-1] = (i, p)
        else:
            out.append((i, p))
    return out


def _uptrend(highs, lows, idx):
    h = [p for (i, p) in highs if i <= idx]
    l = [p for (i, p) in lows if i <= idx]
    if len(l) < 2:
        return False
    # Tai khang cu, cac DINH bang nhau (tran phang) nen chi doi DAY sau cao hon (HL)
    return l[-1] > l[-2]   # higher low = gia dang ep len khang cu


def find_hedges(candles):
    k = RES_PIVOT
    highs = _pivot_highs(candles, k)
    lows = _pivot_lows(candles, k)
    levels = []   # {price, count, triggered}
    signals = []  # (idx, entry_price)
    for (idx, p) in highs:
        tol = p * RES_TOL_PCT / 100.0
        # xac nhan dong cua KHONG vuot len (dinh swing thi close thuong <= high)
        matched = None
        for lv in levels:
            if abs(p - lv["price"]) <= tol:
                matched = lv
                break
        if matched:
            matched["count"] += 1
            matched["price"] = (matched["price"] * (matched["count"] - 1) + p) / matched["count"]
            if matched["count"] >= MIN_TOUCH and not matched["triggered"] and _uptrend(highs, lows, idx):
                signals.append((idx, matched["price"]))
                matched["triggered"] = True
        else:
            levels.append({"price": p, "count": 1, "triggered": False})
    return signals


def _sim_leg(candles, start, entry, tp, sl, is_buy):
    """Tra ve pnl USD cua 1 chan (buy hoac sell)."""
    end = min(len(candles), start + 1 + LOOKAHEAD)
    for j in range(start + 1, end):
        c = candles[j]
        if is_buy:
            hit_sl = c.low <= entry - sl
            hit_tp = c.high >= entry + tp
        else:
            hit_sl = c.high >= entry + sl
            hit_tp = c.low <= entry - tp
        if hit_sl and hit_tp:
            return -sl            # cung nen cham ca 2 -> tinh thua (than trong)
        if hit_sl:
            return -sl
        if hit_tp:
            return tp
    # het lookahead: dong theo gia cuoi
    last = candles[min(len(candles) - 1, end - 1)].close
    return (last - entry) if is_buy else (entry - last)


def run(candles):
    signals = find_hedges(candles)
    results = []
    for (idx, entry) in signals:
        pnl_buy = _sim_leg(candles, idx, entry, TP_BUY, SL_USD, True)
        pnl_sell = _sim_leg(candles, idx, entry, TP_SELL, SL_USD, False)
        results.append(pnl_buy + pnl_sell)
    n = len(results)
    total = sum(results)
    wins = sum(1 for r in results if r > 0)
    losses = sum(1 for r in results if r < 0)
    flat = n - wins - losses
    return {
        "hedges": n, "net_win": wins, "net_loss": losses, "net_flat": flat,
        "win_rate": round(wins / n * 100, 1) if n else 0.0,
        "total_usd": round(total, 1),
        "avg_usd": round(total / n, 2) if n else 0.0,
    }


def main():
    args = sys.argv[1:]
    bars = 3000
    if "--bars" in args:
        bars = int(args[args.index("--bars") + 1])
    tfs = ["M5", "M15", "M30", "H1"]
    if "--tf" in args:
        tfs = [x.strip() for x in args[args.index("--tf") + 1].split(",") if x.strip()]
    symbol = "XAUUSD"
    if "--symbol" in args:
        symbol = args[args.index("--symbol") + 1].upper()

    from src.broker.mt5_connector import MT5Connector
    from src.data.data_service import DataService

    conn = MT5Connector()
    print("Ket noi MT5...")
    if not conn.connect():
        print("[ERROR] Khong ket noi MT5. Mo MT5 va dang nhap truoc.")
        return
    print("Backtest HEDGE khang cu | {} | TP_Buy={} TP_Sell={} SL={} | cham thu {}".format(
        symbol, TP_BUY, TP_SELL, SL_USD, MIN_TOUCH))
    print("=" * 70)
    print("{:<8} {:<5} {:>7} {:>7} {:>7} {:>9} {:>10} {:>9}".format(
        "SYMBOL", "TF", "Hedges", "NetWin", "NetLoss", "WinRate", "Total$", "Avg$/hg"))
    print("-" * 70)
    grand = 0.0
    hg = 0
    try:
        for tf in tfs:
            try:
                candles = DataService.get_candles(symbol=symbol, timeframe=tf, count=bars)
            except Exception as e:
                print("{:<8} {:<5} loi lay du lieu: {}".format(symbol, tf, e))
                continue
            if not candles or len(candles) < 250:
                print("{:<8} {:<5} khong du du lieu".format(symbol, tf))
                continue
            s = run(candles)
            print("{:<8} {:<5} {:>7} {:>7} {:>7} {:>8}% {:>10} {:>9}".format(
                symbol, tf, s["hedges"], s["net_win"], s["net_loss"],
                s["win_rate"], s["total_usd"], s["avg_usd"]))
            grand += s["total_usd"]
            hg += s["hedges"]
    finally:
        conn.disconnect()
    print("-" * 70)
    print("TONG: {} hedge | Tong loi/lo: {:+.1f} USD (tren 1 don vi gia)".format(hg, grand))
    print("Luu y: chua tinh spread/phi. Ket qua chi tham khao, KHONG phai loi khuyen dau tu.")


if __name__ == "__main__":
    main()
