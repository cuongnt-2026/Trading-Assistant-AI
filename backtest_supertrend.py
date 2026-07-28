# -*- coding: utf-8 -*-
"""
backtest_supertrend.py - Backtest chi bao Supertrend (mac dinh 10, 3).

He DAO CHIEU (stop-and-reverse): Supertrend chuyen xanh -> BUY,
giu toi khi chuyen do -> dong + SELL, va nguoc lai.
Moi lenh: vao tai gia dong nen "flip", dong tai nen "flip" nguoc lai.
R = lai/lo chia cho khoang cach tu gia vao toi duong Supertrend (stop ban dau).
"""
import os
import sys

ST_PERIOD = int(os.getenv("ST_PERIOD", "10"))
ST_MULT = float(os.getenv("ST_MULT", "3"))


def supertrend(candles, period, mult):
    n = len(candles)
    tr = [0.0] * n
    for i in range(n):
        if i == 0:
            tr[i] = candles[i].high - candles[i].low
        else:
            h, l, pc = candles[i].high, candles[i].low, candles[i - 1].close
            tr[i] = max(h - l, abs(h - pc), abs(l - pc))
    atr = [0.0] * n
    atr[0] = tr[0]
    for i in range(1, n):
        atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period   # Wilder ATR

    direction = [1] * n
    st_line = [0.0] * n
    fu = [0.0] * n
    fl = [0.0] * n
    for i in range(n):
        hl2 = (candles[i].high + candles[i].low) / 2.0
        bu = hl2 + mult * atr[i]
        bl = hl2 - mult * atr[i]
        if i == 0:
            fu[i], fl[i] = bu, bl
            direction[i] = 1
            st_line[i] = bl
            continue
        fu[i] = bu if (bu < fu[i - 1] or candles[i - 1].close > fu[i - 1]) else fu[i - 1]
        fl[i] = bl if (bl > fl[i - 1] or candles[i - 1].close < fl[i - 1]) else fl[i - 1]
        if candles[i].close > fu[i - 1]:
            direction[i] = 1
        elif candles[i].close < fl[i - 1]:
            direction[i] = -1
        else:
            direction[i] = direction[i - 1]
        st_line[i] = fl[i] if direction[i] == 1 else fu[i]
    return direction, st_line


def run(candles):
    direction, st_line = supertrend(candles, ST_PERIOD, ST_MULT)
    n = len(candles)
    warmup = max(ST_PERIOD * 3, 30)
    # tim cac diem flip
    flips = []   # (idx, dir)  dir=1 BUY, -1 SELL
    for i in range(warmup, n):
        if direction[i] != direction[i - 1]:
            flips.append((i, direction[i]))

    trades = []
    for k in range(len(flips) - 1):
        idx, d = flips[k]
        nxt = flips[k + 1][0]
        entry = candles[idx].close
        exit_p = candles[nxt].close
        pnl = (exit_p - entry) if d == 1 else (entry - exit_p)
        risk = abs(entry - st_line[idx]) or 1e-9
        trades.append({"dir": d, "entry": entry, "exit": exit_p,
                       "pnl": pnl, "r": pnl / risk})
    n_t = len(trades)
    wins = [t for t in trades if t["pnl"] > 0]
    losses = [t for t in trades if t["pnl"] <= 0]
    total_usd = sum(t["pnl"] for t in trades)
    total_r = sum(t["r"] for t in trades)
    gw = sum(t["pnl"] for t in wins)
    gl = sum(t["pnl"] for t in losses)
    pf = round(gw / abs(gl), 2) if gl else 0.0
    return {
        "trades": n_t, "wins": len(wins), "losses": len(losses),
        "win_rate": round(len(wins) / n_t * 100, 1) if n_t else 0.0,
        "avg_R": round(total_r / n_t, 3) if n_t else 0.0,
        "total_R": round(total_r, 2),
        "profit_factor": pf,
        "total_usd": round(total_usd, 1),
        "avg_usd": round(total_usd / n_t, 2) if n_t else 0.0,
    }


def main():
    args = sys.argv[1:]
    bars = 3000
    if "--bars" in args:
        bars = int(args[args.index("--bars") + 1])
    tfs = ["M5", "M15", "M30", "H1"]
    if "--tf" in args:
        tfs = [x.strip() for x in args[args.index("--tf") + 1].split(",") if x.strip()]
    symbols = ["XAUUSD"]
    if "--symbol" in args:
        symbols = [args[args.index("--symbol") + 1].upper()]
    if "--symbols" in args:
        symbols = [x.strip().upper() for x in args[args.index("--symbols") + 1].split(",") if x.strip()]

    from src.broker.mt5_connector import MT5Connector
    from src.data.data_service import DataService

    conn = MT5Connector()
    print("Ket noi MT5...")
    if not conn.connect():
        print("[ERROR] Khong ket noi MT5. Mo MT5 va dang nhap truoc.")
        return
    print("Backtest SUPERTREND ({},{}) | he dao chieu (BUY<->SELL)".format(ST_PERIOD, ST_MULT))
    print("=" * 74)
    print("{:<8} {:<5} {:>7} {:>5} {:>6} {:>8} {:>8} {:>7} {:>9} {:>9}".format(
        "SYMBOL", "TF", "Trades", "Win", "Loss", "WinRate", "AvgR", "PF", "Total$", "TotalR"))
    print("-" * 74)
    grand_r = 0.0
    try:
        for symbol in symbols:
            for tf in tfs:
                try:
                    candles = DataService.get_candles(symbol=symbol, timeframe=tf, count=bars)
                except Exception as e:
                    print("{:<8} {:<5} loi lay du lieu: {}".format(symbol, tf, e))
                    continue
                if not candles or len(candles) < 100:
                    print("{:<8} {:<5} khong du du lieu".format(symbol, tf))
                    continue
                s = run(candles)
                grand_r += s["total_R"]
                print("{:<8} {:<5} {:>7} {:>5} {:>6} {:>7}% {:>8} {:>7} {:>9} {:>9}".format(
                    symbol, tf, s["trades"], s["wins"], s["losses"], s["win_rate"],
                    s["avg_R"], s["profit_factor"], s["total_usd"], s["total_R"]))
            print("-" * 74)
    finally:
        conn.disconnect()
    print("TONG TotalR tat ca: {:+.2f}".format(grand_r))
    print("Luu y: he dao chieu (luon co lenh), chua tinh spread/phi.")
    print("Nhin AvgR/PF/TotalR: duong = co edge. Ket qua chi tham khao.")


if __name__ == "__main__":
    main()
