"""
Monitor - vong lap theo doi thi truong va ban thong bao khi co tin hieu.
Loc DA KHUNG (H1/H4) + cham WIN/LOSS cho tin hieu theo thi truong chay.
"""

import time
from datetime import datetime

from src.broker.mt5_connector import MT5Connector
from src.data.data_service import DataService
from src.signal.signal_service import SignalService
from src.signal.trend import TrendService, higher_tf
from src.signal.strategy import strategy_for
from src.signal.constants import NO_TRADE
from src.trade.trade_service import TradeService
from src.trade.outcome import OutcomeEvaluator, OPEN
from src.ai_review.recommender import Recommender
from src.notifier.factory import create_notifier
from src.notifier.messages import build_signal_email
from src.scheduler.signal_logger import SignalLogger


def _parse_time(ts):
    try:
        return datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
    except Exception:
        return None


class Monitor:
    """Bo theo doi tin hieu giao dich (da symbol, da khung)."""

    def __init__(self, config, once: bool = False, notifier=None):
        self.config = config
        self.once = once
        self.connector = MT5Connector()
        self.notifier = notifier if notifier is not None else create_notifier(config)
        self.logger = SignalLogger(config)
        self.last_action = {}
        self.last_candle_time = {}
        self.balance = config.account_balance or None

    def _htf_trend(self, symbol, timeframe):
        if not self.config.use_mtf:
            return None
        htf = higher_tf(timeframe)
        try:
            cs = DataService.get_candles(
                symbol=symbol, timeframe=htf, count=self.config.candle_count)
        except Exception:
            return None
        if not cs or len(cs) < 60:
            return None
        return TrendService.direction(cs)

    def _analyze(self, symbol, timeframe):
        candles = DataService.get_candles(
            symbol=symbol, timeframe=timeframe, count=self.config.candle_count)
        if candles is None or len(candles) < 200:
            print("[WARN] {} {}: khong du du lieu nen.".format(symbol, timeframe))
            return None, None
        htf = self._htf_trend(symbol, timeframe)
        signal = SignalService.analyze(candles, htf_trend=htf, strategy=strategy_for(symbol))
        return signal, candles

    def _should_notify(self, key, signal) -> bool:
        if signal.action == NO_TRADE:
            return False
        if self.config.notify_on == "every":
            return True
        return signal.action != self.last_action.get(key)

    def _handle(self, symbol, timeframe, signal, candles):
        key = (symbol, timeframe)
        candle = candles[-1]
        ts = datetime.now().strftime("%H:%M:%S")
        print("[{}] {} {} | {} | trend={} | close={:.5g} | ADX={:.2f}".format(
            ts, symbol, timeframe, signal.action, signal.trend, candle.close, signal.adx))

        recommendation = Recommender.evaluate(signal, candles)
        trade_plan = TradeService.create(
            signal, candles, symbol=symbol, balance=self.balance,
            confidence=recommendation.confidence,
            risk_min=self.config.risk_min_percent,
            risk_max=self.config.risk_max_percent,
            strategy=strategy_for(symbol),
            entry_mode=self.config.entry_mode)
        if signal.action != NO_TRADE:
            print("       -> Conf {:.0f}% ({}) | Entry {} SL {} TP {} RR {} trail {}".format(
                recommendation.confidence, recommendation.label,
                trade_plan.entry_price, trade_plan.stop_loss,
                trade_plan.take_profit, trade_plan.risk_reward, trade_plan.trail_distance))

        notified = False
        conf_ok = (strategy_for(symbol) != "trend") or (recommendation.confidence >= self.config.min_confidence)
        if self.notifier and conf_ok and self._should_notify(key, signal):
            subject, body = build_signal_email(
                signal, symbol, timeframe, candle,
                recommendation=recommendation, trade_plan=trade_plan)
            print("       -> Tin hieu {}, dang gui thong bao...".format(signal.action))
            notified = self.notifier.send(subject, body)
            if notified:
                print("       -> [OK] Da gui.")

        self.logger.add(
            signal, candle, notified, symbol=symbol, timeframe=timeframe,
            recommendation=recommendation, trade_plan=trade_plan)
        self.last_action[key] = signal.action

    def _update_outcomes(self):
        """Cham WIN/LOSS cho cac tin hieu OPEN dua theo nen SAU khi vao lenh."""
        changed = False
        cache = {}
        for rec in self.logger.records:
            if rec.get("outcome") != OPEN:
                continue
            tp = rec.get("trade_plan")
            if not tp:
                continue
            sym = rec.get("symbol")
            tf = rec.get("timeframe") or ""
            ck = (sym, tf)
            if ck not in cache:
                try:
                    cache[ck] = DataService.get_candles(
                        symbol=sym, timeframe=tf,
                        count=self.config.candle_count) or []
                except Exception:
                    cache[ck] = []
            entry_time = _parse_time(rec.get("candle_time", ""))
            if entry_time is None:
                continue
            future = [c for c in cache[ck] if c.time > entry_time]
            if not future:
                continue
            res = OutcomeEvaluator.evaluate(
                rec["action"], tp["stop_loss"], tp["take_profit"], future)
            if res != OPEN:
                rec["outcome"] = res
                changed = True
                print("       -> Ket qua {} {}: {}".format(sym, tf, res))
        if changed:
            self.logger.save()

    def _scan_all(self, force: bool = False):
        ok_count = 0
        for symbol, timeframe in self.config.watchlist:
            key = (symbol, timeframe)
            try:
                signal, candles = self._analyze(symbol, timeframe)
                if signal is None:
                    continue
                ok_count += 1
                candle = candles[-1]
                is_new = candle.time != self.last_candle_time.get(key)
                if force or is_new:
                    self.last_candle_time[key] = candle.time
                    self._handle(symbol, timeframe, signal, candles)
            except Exception as e:
                print("[ERROR] {} {}: {}".format(symbol, timeframe, e))
        # Neu CA loat cap deu khong co du lieu -> luong gia co the da dut, tu lanh
        if self.config.watchlist and ok_count == 0:
            alive = self.connector.feed_alive()
            print("[WARN] 0/{} cap co du lieu (feed_alive={}). Dang tu ket noi lai MT5...".format(
                len(self.config.watchlist), alive))
            if self.connector.reconnect():
                try:
                    acc = self.connector.account_info()
                    if acc is not None and getattr(acc, "balance", 0):
                        self.balance = float(acc.balance)
                except Exception:
                    pass
                print("[OK] Da ket noi lai MT5.")
        # Sau moi vong quet: cap nhat ket qua WIN/LOSS
        try:
            self._update_outcomes()
        except Exception as e:
            print("[ERROR] update_outcomes: {}".format(e))
        # Nhip "con song" de biet bot van dang chay
        hb = datetime.now().strftime("%H:%M:%S")
        print("[{}] Da quet {} cap-khung. Dang cho nen moi...".format(
            hb, len(self.config.watchlist)))

    def run(self):
        print("=" * 60)
        print("TRADING ASSISTANT AI - SIGNAL MONITOR")
        print("=" * 60)
        print(self.config.summary())
        print("=" * 60)

        if not self.connector.connect():
            print("[ERROR] Khong ket noi duoc MetaTrader 5. "
                  "Hay mo MT5 va dang nhap.")
            if self.once:
                return
            # Chay lien tuc: doi va thu ket noi lai thay vi thoat
            while not self.connector.connect():
                print("   ... doi MT5 (thu lai sau {}s)".format(self.config.poll_interval))
                time.sleep(self.config.poll_interval)
            print("[OK] Da ket noi MT5.")

        try:
            account = self.connector.account_info()
            if account is not None and getattr(account, "balance", 0):
                self.balance = float(account.balance)
                print("[OK] Balance: {:.2f}".format(self.balance))
        except Exception:
            pass

        try:
            if self.once:
                self._scan_all(force=True)
                return
            print("Dang theo doi... (Ctrl+C de dung)\n")
            while True:
                self._scan_all()
                time.sleep(self.config.poll_interval)
        except KeyboardInterrupt:
            print("\n[STOP] Dung theo doi theo yeu cau.")
        finally:
            self.connector.disconnect()
            print("Disconnected.")
