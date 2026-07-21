"""
Backtest chien luoc tren du lieu lich su tu MT5.

Cach dung:
    python run_backtest.py                # backtest toan bo watchlist, 3000 bar
    python run_backtest.py --bars 5000     # so bar lich su moi cap
Ket qua in ra man hinh + luu reports/backtest.json + logs/backtest.log
"""

import os
import sys
import json
import traceback
from datetime import datetime


class _Tee:
    def __init__(self, path):
        self.t = sys.__stdout__
        self.f = open(path, "a", encoding="utf-8")
        self.f.write("\n===== BACKTEST {} =====\n".format(
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    def write(self, m):
        try:
            self.t.write(m)
        except Exception:
            pass
        self.f.write(m); self.f.flush()

    def flush(self):
        self.f.flush()


def main():
    os.makedirs("logs", exist_ok=True)
    sys.stdout = sys.stderr = _Tee(os.path.join("logs", "backtest.log"))

    args = sys.argv[1:]
    bars = 3000
    if "--bars" in args:
        try:
            bars = int(args[args.index("--bars") + 1])
        except Exception:
            pass
    minconf_override = None
    if "--minconf" in args:
        try:
            minconf_override = float(args[args.index("--minconf") + 1])
        except Exception:
            pass
    only_symbol = None
    if "--symbol" in args:
        try:
            only_symbol = args[args.index("--symbol") + 1].upper()
        except Exception:
            pass
    strategy_override = None
    if "--strategy" in args:
        try:
            strategy_override = args[args.index("--strategy") + 1].strip().lower()
        except Exception:
            pass
    tf_override = None
    if "--tf" in args:
        try:
            tf_override = [x.strip() for x in args[args.index("--tf") + 1].split(",") if x.strip()]
        except Exception:
            pass

    from src.core.config import Config
    try:
        from src.broker.mt5_connector import MT5Connector
        from src.data.data_service import DataService
        from src.backtest.backtester import Backtester
        from src.signal.strategy import strategy_for
    except Exception as e:
        print("[ERROR] Thieu thu vien:", e)
        print("Hay chay SETUP.bat truoc.")
        traceback.print_exc()
        return

    config = Config()
    if minconf_override is not None:
        config.min_confidence = minconf_override
    connector = MT5Connector()
    print("Ket noi MT5...")
    if not connector.connect():
        print("[ERROR] Khong ket noi duoc MT5. Hay mo MT5 va dang nhap.")
        return

    balance = config.account_balance or 10000.0
    try:
        acc = connector.account_info()
        if acc is not None and getattr(acc, "balance", 0):
            balance = float(acc.balance)
    except Exception:
        pass

    print("Balance dung de backtest: {:.2f} | So bar/cap: {}".format(balance, bars))
    print("=" * 78)
    print("{:<10} {:<5} {:>6} {:>6} {:>6} {:>8} {:>7} {:>7} {:>9} {:>9}".format(
        "SYMBOL", "TF", "Trades", "Win", "Loss", "WinRate", "AvgR", "PF", "Return%", "MaxDD%"))
    print("-" * 78)

    report = {"generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
              "balance": balance, "bars": bars, "results": []}
    agg_trades = agg_R = 0.0
    agg_wins = agg_losses = 0

    if tf_override:
        scan_list = [(sym, tf) for sym in config.symbols for tf in tf_override]
    else:
        scan_list = list(config.watchlist)

    try:
        for symbol, tf in scan_list:
            if only_symbol and only_symbol not in symbol.upper():
                continue
            try:
                candles = DataService.get_candles(symbol=symbol, timeframe=tf, count=bars)
            except Exception as e:
                print("{:<10} {:<5} loi lay du lieu: {}".format(symbol, tf, e))
                continue
            if not candles or len(candles) < 250:
                print("{:<10} {:<5} khong du du lieu".format(symbol, tf))
                continue

            res = Backtester.run(candles, symbol=symbol, balance=balance,
                                 risk_min=config.risk_min_percent,
                                 risk_max=config.risk_max_percent,
                                 min_confidence=config.min_confidence,
                                 strategy=(strategy_override or strategy_for(symbol)),
                                 entry_mode=config.entry_mode,
                                 entry_wait=config.entry_wait_bars)
            s = res["stats"]
            print("{:<10} {:<5} {:>6} {:>6} {:>6} {:>7}% {:>7} {:>7} {:>8}% {:>8}%".format(
                symbol, tf, s["trades"], s["wins"], s["losses"], s["win_rate"],
                s["avg_R"], s["profit_factor"], s["return_pct"], s["max_drawdown_pct"]))
            report["results"].append({"symbol": symbol, "timeframe": tf, **s})
            agg_trades += s["trades"]; agg_R += s["total_R"]
            agg_wins += s["wins"]; agg_losses += s["losses"]
    finally:
        connector.disconnect()

    closed = agg_wins + agg_losses
    agg_wr = round(agg_wins / closed * 100, 1) if closed else 0.0
    print("-" * 78)
    print("TONG: {} lenh | Win {} / Loss {} | WinRate {}% | Tong R {:.2f}".format(
        int(agg_trades), agg_wins, agg_losses, agg_wr, agg_R))
    report["summary"] = {"trades": int(agg_trades), "wins": agg_wins,
                         "losses": agg_losses, "win_rate": agg_wr,
                         "total_R": round(agg_R, 2)}

    os.makedirs("reports", exist_ok=True)
    with open(os.path.join("reports", "backtest.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print("\nDa luu reports/backtest.json")
    print("Luu y: ket qua chi tham khao (khong tinh spread/phi/truot gia).")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("[FATAL]", e)
        traceback.print_exc()
