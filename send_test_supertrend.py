# -*- coding: utf-8 -*-
"""Gui 1 mail MAU tin hieu Supertrend de xem format."""
from src.core.config import Config
from src.notifier.factory import create_notifier
from src.notifier.messages import build_supertrend_email
from src.signal.constants import BUY

cfg = Config()
miss = cfg.validate_email()
if miss:
    print("[LOI] Thieu cau hinh mail:", miss); raise SystemExit(1)
subject, body = build_supertrend_email("XAUUSD", "M30", BUY, 4034.30, 4008.50)
subject = "[TEST] " + subject
n = create_notifier(cfg)
ok = n.send(subject, body) if n else False
print("Gui toi:", cfg.mail_to, "| Ket qua:", "OK" if ok else "THAT BAI")
