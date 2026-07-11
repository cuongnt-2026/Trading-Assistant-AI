import datetime

from src.broker.mt5_connector import MT5Connector
from src.data.data_service import DataService

APP_NAME = "Trading Assistant AI"
VERSION = "0.0.3"


def print_banner():
    print("=" * 50)
    print(APP_NAME)
    print(f"Version {VERSION}")
    print("=" * 50)


def initialize():
    print("\nInitializing...\n")

    print("[OK] Configuration")
    print("[OK] Environment")
    print("[OK] Logger")


def main():

    print_banner()

    initialize()

    print(f"\nStart Time : {datetime.datetime.now():%Y-%m-%d %H:%M:%S}")

    connector = MT5Connector()

    print("\nConnecting MetaTrader 5...")

    try:

        if not connector.connect():
            print("[ERROR] Cannot connect to MetaTrader 5")
            return

        print("[OK] MT5 Connected")

        terminal = connector.terminal_info()

        if terminal:
            print(f"Terminal : {terminal.name}")

        account = connector.account_info()

        if account:
            print(f"Account  : {account.login}")

        print("\nSystem Ready.")

        print("\nLoading candle data...")

        candles = DataService.get_candles(
            symbol="XAUUSD",
            timeframe="M15",
            count=10,
        )

        if candles is None:
            print("[ERROR] Cannot get candle data")
            return

        print(f"[OK] Loaded {len(candles)} candles.\n")

        print("=" * 50)
        print("Last 5 Candles")
        print("=" * 50)

        for candle in candles[-5:]:
            print(
                f"{candle.time} | "
                f"O:{candle.open:.2f} "
                f"H:{candle.high:.2f} "
                f"L:{candle.low:.2f} "
                f"C:{candle.close:.2f} "
                f"V:{candle.volume}"
            )

    except Exception as e:
        print(f"[ERROR] {e}")

    finally:

        connector.disconnect()

        print("\nDisconnected.")


if __name__ == "__main__":
    main()