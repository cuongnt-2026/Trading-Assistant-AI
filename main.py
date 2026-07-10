import datetime

from src.broker.mt5_connector import MT5Connector
from src.services.data_service import get_candles

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

        candles = get_candles(
            symbol="XAUUSD",
            count=10
        )

        if candles is not None:
            print(candles.tail())
        else:
            print("[ERROR] Cannot get candle data")

    finally:

        connector.disconnect()

        print("Disconnected.")


if __name__ == "__main__":
    main()