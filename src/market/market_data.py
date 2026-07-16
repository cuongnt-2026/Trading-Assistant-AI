import time
from datetime import datetime, timedelta

import MetaTrader5 as mt5

from src.market.candle import Candle
from src.market.timeframe import to_mt5


class MarketData:
    """Market data service for MetaTrader 5."""

    # cache ten symbol da resolve de khoi do lai moi lan
    _resolved = {}

    @staticmethod
    def resolve_symbol(symbol: str) -> str:
        """
        Tra ve ten symbol dung tren broker. Neu 'BTCUSD' khong co,
        thu tim mã bat dau bang 'BTCUSD' (vd BTCUSD.r, BTCUSDm...).
        """
        if symbol in MarketData._resolved:
            return MarketData._resolved[symbol]
        name = symbol
        try:
            if mt5.symbol_info(symbol) is None:
                allsyms = mt5.symbols_get() or []
                up = symbol.upper()
                for s in allsyms:
                    if s.name.upper().startswith(up):
                        name = s.name
                        break
        except Exception:
            name = symbol
        MarketData._resolved[symbol] = name
        return name

    @staticmethod
    def _ensure_selected(symbol: str):
        """Bat symbol vao Market Watch de co the lay du lieu."""
        try:
            mt5.symbol_select(symbol, True)
        except Exception:
            pass

    @staticmethod
    def get_symbol_info(symbol: str):
        return mt5.symbol_info(symbol)

    @staticmethod
    def get_tick(symbol: str):
        return mt5.symbol_info_tick(symbol)

    @staticmethod
    def get_candles(symbol: str, timeframe, count: int):
        """Get OHLC candles."""
        if not symbol:
            raise ValueError("Symbol cannot be empty.")
        if count <= 0:
            raise ValueError("Count must be greater than zero.")

        if isinstance(timeframe, str):
            timeframe = to_mt5(timeframe)
        if timeframe is None:
            raise ValueError("Invalid timeframe.")

        # Resolve ten dung + bat symbol truoc khi lay nen
        real = MarketData.resolve_symbol(symbol)
        MarketData._ensure_selected(real)

        rates = mt5.copy_rates_from_pos(real, timeframe, 0, count)
        if rates is None or len(rates) == 0:
            # thu lai: bat symbol + cho luong gia nap
            MarketData._ensure_selected(real)
            time.sleep(0.3)
            rates = mt5.copy_rates_from_pos(real, timeframe, 0, count)
        if rates is None or len(rates) == 0:
            # fallback: lay theo moc thoi gian
            try:
                rates = mt5.copy_rates_from(real, timeframe, datetime.now(), count)
            except Exception:
                rates = None
        if rates is None or len(rates) == 0:
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
