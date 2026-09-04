# -*- coding: utf-8 -*-
"""
backtest_supertrend.py - Backtest chi bao Supertrend (mac dinh 10, 3).

He DAO CHIEU (stop-and-reverse): Supertrend chuyen xanh -> BUY,
giu toi khi chuyen do -> dong + SELL, va nguoc lai.
Moi lenh: vao tai gia dong nen "flip", dong tai nen "flip" nguoc lai.
R = lai/lo chia cho khoang cach tu gia vao toi duong Supertrend (stop ban dau).

MOI (phan tich nguyen nhan thua): ngoai bang tong hop nhu cu, script con ghi
lai CHI TIET tung lenh (gio, thu, phien giao dich, symbol, khung, thang/thua,
so R) o 1 muc R "dai dien" (mac dinh = SUPERTREND_RR dang chay that, hoac moc
dau tien trong --tf neu khong set), roi gom nhom thong ke theo gio/phien/thu/
symbol/khung de xem lo co tap trung vao dieu kien nao khong. Ket qua chi tiet
duoc xuat ra reports/backtest_supertrend_detail.json + .csv.

LUU Y VE GIO: candle.time la GIO SERVER cua broker MT5 (KHONG chac la UTC -
da so broker dung UTC+2/+3 tuy DST). Neu muon cot "Gio(UTC)/Phien" chinh xac,
chinh bien MT5_UTC_OFFSET_HOURS = so gio server dang lech so voi UTC (vd
broker dang la UTC+3 -> dat MT5_UTC_OFFSET_HOURS=3). Mac dinh = 0 (coi server
= UTC) - neu khong chac broker lech may gio thi cu de mac dinh, chi can hieu
la "gio tuong doi", so sanh giua cac khung gio VOI NHAU van dung, chi la nhan
"UTC" tren cot co the lech vai gio so voi UTC that.
"""
import csv
import json
import os
import sys
from datetime import timedelta

ST_PERIOD = int(os.getenv("ST_PERIOD", "10"))
ST_MULT = float(os.getenv("ST_MULT", "3"))
MT5_UTC_OFFSET_HOURS = float(os.getenv("MT5_UTC_OFFSET_HOURS", "0"))

# Phien giao dich (theo gio UTC da quy doi qua MT5_UTC_OFFSET_HOURS). Dung
# chung quy uoc voi BO_SESS_START/END, FX_SESS_START/END trong constants.py
# (London+NY ~ 7h-20h UTC) nhung tach chi tiet hon de de doi chieu.
SESSION_BOUNDS = [
    (0, 7, "Chau A (00-07h)"),
    (7, 13, "London (07-13h)"),
    (13, 16, "Chong phien London+NY (13-16h)"),
    (16, 21, "New York (16-21h)"),
    (21, 24, "Ngoai phien - thanh khoan thap (21-24h)"),
]
WEEKDAY_VN = ["Thu 2", "Thu 3", "Thu 4", "Thu 5", "Thu 6", "Thu 7", "CN"]


def session_of(hour_utc):
    for start, end, name in SESSION_BOUNDS:
        if start <= hour_utc < end:
            return name
    return "?"


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


def run(candles, rr_target, symbol=None, tf=None, want_detail=False):
    """
    Mo phong dung LUAT MOI, di tung nen (cai nao toi truoc):
      - Cham +rr_target*R  -> WIN, +rr_target
      - Cham SL (duong Supertrend luc vao) -> LOSS, -1R
      - Dao chieu truoc khi cham TP/SL -> dong tai nen flip:
          con duong  -> WIN = R that (cap +rr_target)
          <=0 (ve/qua entry) -> LOSS, -1R

    Neu want_detail=True, tra ve them list chi tiet tung lenh (gio/thu/phien/
    symbol/khung/direction/R) de gom nhom phan tich - xem ham breakdown().
    """
    direction, st_line = supertrend(candles, ST_PERIOD, ST_MULT)
    n = len(candles)
    warmup = max(ST_PERIOD * 3, 30)
    flips = []   # (idx, dir)  dir=1 BUY, -1 SELL
    for i in range(warmup, n):
        if direction[i] != direction[i - 1]:
            flips.append((i, direction[i]))

    trades = []    # moi phan tu = R cua 1 lenh
    details = []   # chi tiet tung lenh (chi dien khi want_detail=True)
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
            # thang: R that (cap +NR); thua: R that luc dao, san -1R (SL da chan neu tut sau)
            r = min(rr, rr_target) if rr > 0 else max(rr, -1.0)
        trades.append(r)

        if want_detail:
            entry_time = candles[idx].time
            utc_dt = entry_time - timedelta(hours=MT5_UTC_OFFSET_HOURS)
            details.append({
                "symbol": symbol, "tf": tf, "rr_target": rr_target,
                "entry_time_server": entry_time.strftime("%Y-%m-%d %H:%M"),
                "entry_time_utc_est": utc_dt.strftime("%Y-%m-%d %H:%M"),
                "hour_utc_est": utc_dt.hour,
                "weekday": WEEKDAY_VN[utc_dt.weekday()],
                "session": session_of(utc_dt.hour),
                "direction": "BUY" if d == 1 else "SELL",
                "r": round(r, 3),
                "result": "WIN" if r > 0 else "LOSS",
            })

    n_t = len(trades)
    wins = [x for x in trades if x > 0]
    losses = [x for x in trades if x <= 0]
    total_r = sum(trades)
    gw = sum(wins)
    gl = abs(sum(losses))
    pf = round(gw / gl, 2) if gl else 0.0
    summary = {
        "trades": n_t, "wins": len(wins), "losses": len(losses),
        "win_rate": round(len(wins) / n_t * 100, 1) if n_t else 0.0,
        "avg_R": round(total_r / n_t, 3) if n_t else 0.0,
        "total_R": round(total_r, 2),
        "profit_factor": pf,
    }
    return (summary, details) if want_detail else summary


def breakdown(rows, key_fn, key_label):
    """Gom nhom `rows` (list dict co 'r') theo key_fn, in bang thong ke,
    sap xep theo AvgR TANG DAN (te nhat len dau) de de thay ngay diem yeu."""
    groups = {}
    for row in rows:
        k = key_fn(row)
        groups.setdefault(k, []).append(row["r"])

    items = []
    for k, rs in groups.items():
        n = len(rs)
        wins = [x for x in rs if x > 0]
        total = sum(rs)
        items.append({
            "key": k, "trades": n,
            "win_rate": round(len(wins) / n * 100, 1) if n else 0.0,
            "avg_R": round(total / n, 3) if n else 0.0,
            "total_R": round(total, 2),
        })
    items.sort(key=lambda x: x["avg_R"])

    print()
    print("--- Gom nhom theo {} (sap xep AvgR tang dan - te nhat o TREN) ---".format(key_label))
    print("{:<32} {:>7} {:>8} {:>8} {:>8}".format(key_label, "Trades", "WinRate", "AvgR", "TotalR"))
    for it in items:
        print("{:<32} {:>7} {:>7}% {:>8} {:>+8.2f}".format(
            str(it["key"])[:32], it["trades"], it["win_rate"], it["avg_R"], it["total_R"]))
    return items


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
    # Moc R dung de PHAN TICH CHI TIET (gio/phien/thu) - mac dinh lay dung
    # SUPERTREND_RR dang chay that tren cloud (env), de ket qua phan tich
    # phan anh dung he thong dang song, khong phai 1 moc R tuy chon.
    detail_rr = float(os.getenv("SUPERTREND_RR", str(targets[0])))
    if detail_rr not in targets:
        targets = targets + [detail_rr]

    conn = MT5Connector()
    print("Ket noi MT5...")
    if not conn.connect():
        print("[ERROR] Khong ket noi MT5. Mo MT5 va dang nhap truoc.")
        return
    print("Backtest SUPERTREND ({},{}) | LUAT MOI: TP theo moc R + SL -1R + dao chieu".format(ST_PERIOD, ST_MULT))
    print("Moc R dung de phan tich chi tiet gio/phien/thu: {:g}R (= SUPERTREND_RR dang chay that)".format(detail_rr))
    print("=" * 72)
    print("{:<8} {:<5} {:<5} {:>7} {:>5} {:>6} {:>8} {:>7} {:>8}".format(
        "SYMBOL", "TF", "MOC", "Trades", "Win", "Loss", "WinRate", "AvgR", "TotalR"))
    print("-" * 72)
    grand = {t: 0.0 for t in targets}
    all_details = []
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
                    want_detail = (t == detail_rr)
                    result = run(candles, t, symbol=symbol, tf=tf, want_detail=want_detail)
                    s, det = result if want_detail else (result, [])
                    if want_detail:
                        all_details.extend(det)
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

    # ----- Phan tich chi tiet: gio / phien / thu / symbol / khung -----
    if all_details:
        print()
        print("#" * 72)
        print("PHAN TICH CHI TIET ({} lenh, o moc {:g}R)".format(len(all_details), detail_rr))
        print("LUU Y: cot gio la GIO SERVER MT5 da tru MT5_UTC_OFFSET_HOURS (dang = {:g}).".format(
            MT5_UTC_OFFSET_HOURS))
        print("Neu chua chac broker lech UTC bao nhieu gio, dat lai bien nay cho dung roi chay lai.")
        print("#" * 72)

        breakdown(all_details, lambda r: r["session"], "Phien giao dich")
        breakdown(all_details, lambda r: r["hour_utc_est"], "Gio (UTC uoc tinh)")
        breakdown(all_details, lambda r: r["weekday"], "Thu trong tuan")
        breakdown(all_details, lambda r: r["symbol"], "Symbol")
        breakdown(all_details, lambda r: r["tf"], "Khung thoi gian")
        breakdown(all_details, lambda r: (r["symbol"], r["tf"]), "Symbol+Khung")

        os.makedirs("reports", exist_ok=True)
        json_path = os.path.join("reports", "backtest_supertrend_detail.json")
        csv_path = os.path.join("reports", "backtest_supertrend_detail.csv")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(all_details, f, ensure_ascii=False, indent=2)
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(all_details[0].keys()))
            w.writeheader()
            w.writerows(all_details)
        print()
        print("Da xuat chi tiet {} lenh ra:".format(len(all_details)))
        print("  - {}".format(json_path))
        print("  - {}".format(csv_path))
        print("Gui 2 file nay cho Claude de phan tich sau/de xuat bo loc cu the.")


if __name__ == "__main__":
    main()
