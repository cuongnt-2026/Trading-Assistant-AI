# -*- coding: utf-8 -*-
"""Gui 1 mail tin hieu MAU (lenh cho) de xem format that."""
from src.core.config import Config
from src.notifier.factory import create_notifier
from src.notifier.messages import build_signal_email
from src.signal.signal import Signal
from src.trade.trade_plan import TradePlan
from src.signal.constants import BUY

class _C:
    close = 1.0850

sig = Signal(action=BUY, trend="UP", strength="STRONG",
             reason="EMA20>50>200 + pullback ve EMA20 + nen Engulfing",
             ema20=1.0855, ema50=1.0840, ema200=1.0790,
             adx=28.4, atr=0.0025, rsi=46.0, pattern="Engulfing")
plan = TradePlan(action=BUY, entry_type="limit",
    entry_price=1.0838, stop_loss=1.0808, take_profit=1.0898,
    risk_reward="1 : 2", reason=sig.reason, rr_ratio=2.0,
    risk_points=0.0030, reward_points=0.0060, risk_percent=1.2,
    sl_source="swing-ATR", tp_source="cau truc thi truong",
    trail_distance=0.0038, risk_amount=120.0, lot_size=0.40,
    expected_profit=240.0)

cfg = Config()
miss = cfg.validate_email()
if miss:
    print("[LOI] Thieu cau hinh mail:", miss); raise SystemExit(1)
subject, body = build_signal_email(sig, "EURUSD", "H1", _C(),
                                   recommendation=None, trade_plan=plan)
subject = "[TEST] " + subject
n = create_notifier(cfg)
ok = n.send(subject, body)
print("Gui toi:", cfg.mail_to, "| Ket qua:", "OK" if ok else "THAT BAI")
