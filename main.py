import datetime

from src.broker.mt5_connector import MT5Connector
from src.data.data_service import DataService
from src.signal.signal_service import SignalService
from src.signal.trend import TrendService, higher_tf
from src.ai_review.recommender import Recommender
from src.trade.trade_service import TradeService

APP_NAME = "Trading Assistant AI"
VERSION = "0.0.5"


def main():
    print("=" * 50)
    print(APP_NAME)
    print("Version {}".format(VERSION))
    print("=" * 50)
    print("\nStart Time : {:%Y-%m-%d %H:%M:%S}".format(datetime.datetime.now()))

    connector = MT5Connector()
    print("\nConnecting MetaTrader 5...")
    try:
        if not connector.connect():
            print("[ERROR] Cannot connect to MetaTrader 5")
            return
        print("[OK] MT5 Connected")

        symbol, tf = "XAUUSD", "M15"
        candles = DataService.get_candles(symbol=symbol, timeframe=tf, count=250)
        if candles is None:
            print("[ERROR] Cannot get candle data")
            return
        print("[OK] Loaded {} candles.".format(len(candles)))

        # Trend khung lon (da khung)
        htf = higher_tf(tf)
        htf_candles = DataService.get_candles(symbol=symbol, timeframe=htf, count=250)
        htf_trend = TrendService.direction(htf_candles) if htf_candles else None
        print("HTF {} trend: {}".format(htf, htf_trend))

        signal = SignalService.analyze(candles, htf_trend=htf_trend)
        rec = Recommender.evaluate(signal, candles)
        plan = TradeService.create(signal, candles, symbol=symbol,
                                   confidence=rec.confidence)

        print("\nTrading Signal")
        print("Action    : {}".format(signal.action))
        print("Trend     : {}".format(signal.trend))
        print("Pattern   : {}".format(signal.pattern or "-"))
        print("Reason    : {}".format(signal.reason))
        print("Advice    : {} | Confidence {:.0f}% ({})".format(
            rec.action, rec.confidence, rec.label))

        if plan.action in ("BUY", "SELL"):
            print("\nTrade Plan (SL/TP dong)")
            print("Entry     : {}".format(plan.entry_price))
            print("SL        : {}  ({})".format(plan.stop_loss, plan.sl_source))
            print("TP        : {}  ({})".format(plan.take_profit, plan.tp_source))
            print("R:R       : {}".format(plan.risk_reward))
            print("Trailing  : ~{}".format(plan.trail_distance))
            print("Risk      : {:g}%".format(plan.risk_percent))

        print("\nIndicators: EMA {:.2f}/{:.2f}/{:.2f} ADX {:.2f} ATR {:.2f} RSI {:.2f}".format(
            signal.ema20, signal.ema50, signal.ema200, signal.adx, signal.atr, signal.rsi))
    except Exception as e:
        print("[ERROR] {}".format(e))
    finally:
        connector.disconnect()
        print("\nDisconnected.")


if __name__ == "__main__":
    main()
