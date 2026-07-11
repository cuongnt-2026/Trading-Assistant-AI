from datetime import datetime

import MetaTrader5 as mt5

from src.market.candle import Candle
from src.market.timeframe import to_mt5


class MarketData:
    """
    Market data service for MetaTrader 5.
    """

    @staticmethod
    def get_symbol_info(symbol: str):
        """
        Get symbol information.
        """
        info = mt5.symbol_info(symbol)

        if info is None:
            return None

        return info

    @staticmethod
    def get_tick(symbol: str):
        """
        Get latest tick.
        """
        tick = mt5.symbol_info_tick(symbol)

        if tick is None:
            return None

        return tick

    @staticmethod
    def get_candles(
        symbol: str,
        timeframe,
        count: int,
    ):
        """
        Get OHLC candles.
        """

        # Validate symbol
        if not symbol:
            raise ValueError("Symbol cannot be empty.")

        # Validate count
        if count <= 0:
            raise ValueError("Count must be greater than zero.")

        # Convert timeframe string -> MT5 timeframe
        if isinstance(timeframe, str):
            timeframe = to_mt5(timeframe)

        if timeframe is None:
            raise ValueError("Invalid timeframe.")

        rates = mt5.copy_rates_from_pos(
            symbol,
            timeframe,
            0,
            count,
        )

        if rates is None:
            return None

        candles = []

        for rate in rates:
            candles.append(
                Candle(
                    time=datetime.fromtimestamp(rate["time"]),
                    open=float(rate["open"]),
                    high=float(rate["high"]),
                    low=float(rate["low"]),
                    close=float(rate["close"]),
                    volume=int(rate["tick_volume"]),
                )
            )

        return candles