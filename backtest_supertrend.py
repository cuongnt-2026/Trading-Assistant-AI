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


def run(candles, rr_target):
    """
    Mo phong dung LUAT MOI, di tung nen (cai nao toi truoc):
      - Cham +rr_target*R  -> WIN, +rr_target
      - Cham SL (duong Supertrend luc vao) -> LOSS, -1R
      - Dao chieu truoc khi cham TP/SL -> dong tai nen flip:
          con duong  -> WIN = R that (cap +rr_target)
          <=0 (ve/qua entry) -> LOSS, -1R
    """
    direction, st_line = supertrend(candles, ST_PERIOD, ST_MULT)
    n = len(candles)
    warmup = max(ST_PERIOD * 3, 30)
    flips = []   # (idx, dir)  dir=1 BUY, -1 SELL
    for i in range(warmup, n):
        if direction[i] != direction[i - 1]:
            flips.append((i, direction[i]))

    trades = []   # moi phan tu = R cua 1 lenh
    for k in range(len(flips) - 1):
        idx, d = flips[k]
        nxt = flips[k + 1][0]
        entry = candles[idx].close
        sl = st_line[idx]
        risk = abs(entry - sl) or 1e-9
        tp = entry + rr_target * risk if d == 1 else entry - rr_target * risk
        r = None
        for j in range(idx + 1, nxt + 1):     # di tung nen toi khi flip nguoc
            c = candles[j]
            if d == 1:
                hit_sl = c.low <= sl
                hit_tp = c.high >= tp
            else:
                hit_sl = c.high >= sl
                hit_tp = c.low <= tp
            if hit_sl and hit_tp:
                r = -1.0; break              # cung nen cham ca 2 -> bao thu LOSS
            if hit_sl:
                r = -1.0; break
            if hit_tp:
                r = float(rr_target); break
        if r is None:                        # khong cham TP/SL -> dong tai flip nguoc
            exit_p = candles[nxt].close
            pnl = (exit_p - entry) if d == 1 else (entry - exit_p)
            rr = pnl / risk
            r = min(rr, rr_target) if rr > 0 else -1.0
        trades.append(r)

    n_t = len(trades)
    wins = [x for x in trades if x > 0]
    losses = [x for x in trades if x <= 0]
    total_r = sum(trades)
    gw = sum(wins)
    gl = abs(sum(losses))
    pf = round(gw / gl, 2) if gl else 0.0
    return {
        "trades": n_t, "wins": len(wins), "losses": len(losses),
        "win_rate": round(len(wins) / n_t * 100, 1) if n_t else 0.0,
        "avg_R": round(total_r / n_t, 3) if n_t else 0.0,
        "total_R": round(total_r, 2),
        "profit_factor": pf,
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

    # Cac moc R muon so sanh (mac dinh 2R va 3R). Sua qua env RR_TARGETS="2,3,4"
    targets = [float(x) for x in os.getenv("RR_TARGETS", "2,3").split(",") if x.strip()]

    conn = MT5Connector()
    print("Ket noi MT5...")
    if not conn.connect():
        print("[ERROR] Khong ket noi MT5. Mo MT5 va dang nhap truoc.")
        return
    print("Backtest SUPERTREND ({},{}) | LUAT MOI: TP theo moc R + SL -1R + dao chieu".format(ST_PERIOD, ST_MULT))
    print("=" * 72)
    print("{:<8} {:<5} {:<5} {:>7} {:>5} {:>6} {:>8} {:>7} {:>8}".format(
        "SYMBOL", "TF", "MOC", "Trades", "Win", "Loss", "WinRate", "AvgR", "TotalR"))
    print("-" * 72)
    grand = {t: 0.0 for t in targets}
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
                for ti, t in enumerate(targets):
                    s = run(candles, t)
                    grand[t] += s["total_R"]
                    print("{:<8} {:<5} {:<5} {:>7} {:>5} {:>6} {:>7}% {:>8} {:>+8.2f}".format(
                        symbol if ti == 0 else "", tf if ti == 0 else "",
                        "{:g}R".format(t), s["trades"], s["wins"], s["losses"],
                        s["win_rate"], s["avg_R"], s["total_R"]))
            print("-" * 72)
    finally:
        conn.disconnect()
    print("TONG TotalR tat ca cac cap-khung:")
    for t in targets:
        print("   Moc {:g}R : {:+.2f} R".format(t, grand[t]))
    print()
    print("Luat: cham +NR->WIN +N | cham SL->LOSS -1 | dao chieu: con duong=WIN R that (cap N), am=LOSS -1.")
    print("He dao chieu luon co lenh, chua tru spread/phi. Ket qua chi tham khao.")


if __name__ == "__main__":
    main()
