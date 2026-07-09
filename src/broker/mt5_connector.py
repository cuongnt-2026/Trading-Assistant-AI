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

        if not mt5.initialize():
            print("MT5 initialize failed")
            print(mt5.last_error())
            return False

        self.connected = True
        return True

    def disconnect(self):
        """
        Disconnect from MetaTrader 5 terminal.
        """

        if self.connected:
            mt5.shutdown()
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

        return mt5.terminal_info()

    def account_info(self):
        """
        Return account information.
        """

        return mt5.account_info()

    def version(self):
        """
        Return MT5 version.
        """

        return mt5.version()