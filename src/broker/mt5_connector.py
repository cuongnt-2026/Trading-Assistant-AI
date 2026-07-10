import MetaTrader5 as mt5


class MT5Connector:
    """
    MetaTrader 5 Connector
    """

    def __init__(self):
        self.connected = False

    def connect(self):

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

    def disconnect(self):
        """
        Disconnect from MetaTrader 5 terminal.
        """

        if self.connected:
            print("Disconnecting MT5...")
            mt5.shutdown()
            print("[OK] Disconnected")
            self.connected = False

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
        
    def connect(self) -> bool:
    def disconnect(self) -> None:

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
