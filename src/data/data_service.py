import MetaTrader5 as mt5

from src.market.market_data import MarketData


class DataService:

    @staticmethod
    def get_candles(
        symbol: str,
        timeframe=mt5.TIMEFRAME_M15,
        count: int = 100,
    ):
        """
        Get candle data from market.
        """

        return MarketData.get_candles(
            symbol=symbol,
            timeframe=timeframe,
            count=count,
        )