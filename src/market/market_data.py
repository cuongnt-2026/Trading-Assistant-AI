import MetaTrader5 as mt5


class MarketData:

    @staticmethod
    def get_symbol_info(symbol: str):

        info = mt5.symbol_info(symbol)

        if info is None:
            return None

        return info


    @staticmethod
    def get_tick(symbol: str):

        tick = mt5.symbol_info_tick(symbol)

        if tick is None:
            return None

        return tick