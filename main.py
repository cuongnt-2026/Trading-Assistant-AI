import datetime


APP_NAME = "Trading Assistant AI"
VERSION = "0.0.1"


def print_banner():
    print("=" * 50)
    print(f"{APP_NAME}")
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

    print("\nSystem Ready.")
    print("Waiting for next development step...")


if __name__ == "__main__":
    main()