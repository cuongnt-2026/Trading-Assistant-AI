# -*- coding: utf-8 -*-
"""
Minh hoa Entry/SL/TP THAT cho Bollinger + London: quet nguoc ve qua khu gan nhat
de tim 1 nen ĐA THUC SU co tin hieu that (khong fake ep BUY/SELL len 1 nen
NO_TRADE - vi Bollinger chi hop le khi gia dang o sat bien tren/duoi that su,
ep tin hieu len 1 nen trung tinh se cho SL/TP vo nghia, khong phan anh dung code that).
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")
from src.core.config import Config
from src.broker.mt5_connector import MT5Connector
from src.data.data_service import DataService
from src.signal.signal_service import SignalService
from src.trade.trade_service import TradeService
from src.ai_review.recommender import Recommender
from src.signal.constants import BUY, SELL, NO_TRADE

cfg = Config()
conn = MT5Connector()
print("Ket noi MT5...")
if not conn.connect():
    print("[ERROR] Khong ket noi duoc MT5. Hay mo MT5 va dang nhap.")
    sys.exit(1)

balance = cfg.account_balance or 10000.0
try:
    acc = conn.account_info()
    if acc is not None and getattr(acc, "balance", 0):
        balance = float(acc.balance)
except Exception:
    pass

COMBOS = [
    ("bollinger", "EURUSD", "H4"),
    ("bollinger", "USDJPY", "H4"),
    ("bollinger", "EURUSD", "M15"),
    ("london", "EURUSD", "M30"),
    ("london", "EURUSD", "H1"),
    ("london", "USDJPY", "H1"),
    ("london", "NZDUSD", "M30"),
]

print("=" * 100)
print("{:<10} {:<10} {:<5} {:<8} {:>10} {:>10} {:>10} {:>7}  {}".format(
    "STRATEGY", "SYMBOL", "TF", "ACTION", "ENTRY", "SL", "TP", "RR", "KHI NAO"))
print("-" * 100)

for strat, sym, tf in COMBOS:
    try:
        candles = DataService.get_candles(symbol=sym, timeframe=tf, count=1500)
    except Exception as e:
        print("{:<10} {:<10} {:<5} loi lay du lieu: {}".format(strat, sym, tf, e))
        continue
    if not candles or len(candles) < 250:
        print("{:<10} {:<10} {:<5} khong du du lieu".format(strat, sym, tf))
        continue

    found = False
    n = len(candles)
    # Quet nguoc: nen cuoi cung truoc, lui dan, tim nen GAN NHAT co tin hieu that
    for cut in range(n, 220, -1):
        window = candles[:cut]
        try:
            signal = SignalService.analyze(window, htf_trend=None, strategy=strat)
        except Exception:
            continue
        if signal.action in (BUY, SELL):
            ago = n - cut
            try:
                rec = Recommender.evaluate(signal, window)
                plan = TradeService.create(signal, window, symbol=sym, balance=balance,
                                            confidence=rec.confidence, strategy=strat,
                                            entry_mode=cfg.entry_mode)
                when = "nen hien tai" if ago == 0 else "{} nen truoc".format(ago)
                tag = "TIN HIEU THAT NGAY BAY GIO" if ago == 0 else "vi du that gan nhat"
                print("{:<10} {:<10} {:<5} {:<8} {:>10} {:>10} {:>10} {:>7}  {} ({})".format(
                    strat, sym, tf, signal.action, plan.entry_price, plan.stop_loss,
                    plan.take_profit, plan.risk_reward, when, tag))
            except Exception as e:
                print("{:<10} {:<10} {:<5} loi tinh plan: {}".format(strat, sym, tf, e))
            found = True
            break
    if not found:
        print("{:<10} {:<10} {:<5} khong tim thay tin hieu that nao trong {} nen gan day".format(
            strat, sym, tf, n - 220))

conn.disconnect()
print("=" * 100)
print("Xong.")
