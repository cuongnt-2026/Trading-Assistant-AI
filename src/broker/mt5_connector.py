import MetaTrader5 as mt5


class MT5Connector:
    """
    MetaTrader 5 Connector
    """

    def __init__(self):
        self.connected = False

    def connect(self) -> bool:
        """
        Connect to MetaTrader 5 terminal.
        """

        if self.connected:
            return True

        print("Connecting MetaTrader 5...")

        if not mt5.initialize():
            print("[ERROR] MT5 initialize failed")
            print(mt5.last_error())
            return False

        self.connected = True

        print("[OK] MT5 Connected")

        return True

    def disconnect(self) -> None:
        """
        Disconnect from MetaTrader 5 terminal.
        """

        if self.connected:
            print("Disconnecting MT5...")
            mt5.shutdown()
            self.connected = False
            print("[OK] Disconnected")

    def reconnect(self) -> bool:
        """Ngat han roi ket noi lai (chua lanh khi feed bi dut)."""
        try:
            mt5.shutdown()
        except Exception:
            pass
        self.connected = False
        return self.connect()

    def feed_alive(self) -> bool:
        """True neu terminal dang ket noi server broker (co luong gia)."""
        try:
            ti = mt5.terminal_info()
            return bool(ti and getattr(ti, "connected", False))
        except Exception:
            return False

    def is_connected(self) -> bool:
        """
        Check connection status.
        """

        return self.connected

    def terminal_info(self):
        """
        Return terminal information.
        """

        if not self.connected:
            return None

        return mt5.terminal_info()

    def account_info(self):
        """
        Return account information.
        """

        if not self.connected:
            return None

        return mt5.account_info()

    def version(self):
        """
        Return MT5 version.
        """

        if not self.connected:
            return None

        return mt5.version()