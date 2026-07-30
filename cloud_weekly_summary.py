# -*- coding: utf-8 -*-
"""
cloud_weekly_summary.py - chay tren GitHub Actions moi sang thu 7.
Doc cloud_signals.json -> dung build_summary() (tai dung weekly_summary.py)
-> gui 1 mail "Tong ket tuan" qua Gmail (dung secrets nhu bot tin hieu).
Khong quet tin hieu, khong sua state.
"""
import sys
from datetime import datetime

from src.core.config import Config
from src.notifier.email_notifier import EmailNotifier
from weekly_summary import build_summary


def main():
    body = build_summary(days=7)

    cfg = Config()
    if not cfg.gmail_user or not cfg.gmail_app_password or not cfg.mail_to:
        print("[SKIP] Thieu cau hinh Gmail (GMAIL_USER / GMAIL_APP_PASSWORD / MAIL_TO).")
        print(body)
        return 1

    subject = "[Trading AI] Tong ket tuan " + datetime.utcnow().strftime("%d/%m/%Y")
    ok = EmailNotifier(cfg).send(subject, body)
    if ok:
        print("[OK] Da gui mail tong ket tuan toi", cfg.mail_to)
        return 0
    print("[FAIL] Gui mail tong ket that bai.")
    print(body)
    return 1


if __name__ == "__main__":
    sys.exit(main())
