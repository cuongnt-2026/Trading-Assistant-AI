# -*- coding: utf-8 -*-
"""
cloud_monthly_summary.py - chay tren GitHub Actions moi sang ngay 1 hang thang.
Doc cloud_signals.json -> tong ket THANG DUONG LICH truoc do -> gui 1 mail qua Gmail.
Vi du: chay 01/08 -> tong ket thang 7. Khong quet tin hieu, khong sua state.
"""
import sys
from datetime import datetime, timedelta

from src.core.config import Config
from src.notifier.email_notifier import EmailNotifier
from weekly_summary import build_summary_prev_month


def main():
    body = build_summary_prev_month()

    cfg = Config()
    if not cfg.gmail_user or not cfg.gmail_app_password or not cfg.mail_to:
        print("[SKIP] Thieu cau hinh Gmail (GMAIL_USER / GMAIL_APP_PASSWORD / MAIL_TO).")
        print(body)
        return 1

    # Thang truoc = thang cua (ngay 1 thang nay - 1 ngay)
    prev = (datetime.utcnow().replace(day=1) - timedelta(days=1))
    subject = "[Trading AI] Tong ket thang " + prev.strftime("%m/%Y")
    ok = EmailNotifier(cfg).send(subject, body)
    if ok:
        print("[OK] Da gui mail tong ket thang toi", cfg.mail_to)
        return 0
    print("[FAIL] Gui mail tong ket thang that bai.")
    print(body)
    return 1


if __name__ == "__main__":
    sys.exit(main())
