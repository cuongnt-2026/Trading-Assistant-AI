"""
Chan doan vi sao mot symbol khong lay duoc du lieu (vd cac cap BTC).
Chay:  python diag_symbols.py   (hoac bam DIAG.bat)
"""

import sys
import traceback


def main():
    try:
        import MetaTrader5 as mt5
    except Exception as e:
        print("[ERROR] Thieu thu vien MetaTrader5:", e)
        return

    from src.core.config import Config
    from src.broker.mt5_connector import MT5Connector

    config = Config()
    conn = MT5Connector()
    print("Ket noi MT5...")
    if not conn.connect():
        print("[ERROR] Khong ket noi duoc MT5. Hay mo MT5 va dang nhap.")
        return

    try:
        total = mt5.symbols_total()
        print("Tong so symbol broker cung cap:", total)

        # Liet ke tat ca symbol co chua 'BTC'
        allsyms = mt5.symbols_get() or []
        btc = [s.name for s in allsyms if "BTC" in s.name.upper()]
        print("\n=== Cac ma co chu 'BTC' tren broker cua ban ({}) ===".format(len(btc)))
        if btc:
            for name in btc:
                print("   ", name)
        else:
            print("   (KHONG co ma nao chua 'BTC' -> broker khong cung cap Bitcoin)")

        # Kiem tra tung ma trong config
        print("\n=== Kiem tra tung ma trong watchlist ===")
        checked = set()
        for sym, tf in config.watchlist:
            if sym in checked:
                continue
            checked.add(sym)
            info = mt5.symbol_info(sym)
            if info is None:
                print("{:<10} : KHONG ton tai tren broker (sai ten hoac khong cung cap)".format(sym))
                continue
            # thu bat va lay nen
            mt5.symbol_select(sym, True)
            rates = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_M15, 0, 300)
            nbar = 0 if rates is None else len(rates)
            vis = getattr(info, "visible", None)
            print("{:<10} : ton tai | visible={} | lay duoc {} nen M15".format(
                sym, vis, nbar))
    finally:
        conn.disconnect()
        print("\nXong. Neu BTC 'KHONG ton tai' -> dien dung ten o phan ma 'BTC' ben tren vao .env,")
        print("hoac broker khong co Bitcoin (bo BTC khoi .env cho gon).")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("[FATAL]", e)
        traceback.print_exc()
