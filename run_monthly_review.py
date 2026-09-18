# -*- coding: utf-8 -*-
"""
run_monthly_review.py - chay tren GitHub Actions, 1 lan vao ngay 1 hang thang
(xem .github/workflows/monthly_review.yml), theo yeu cau CuongNT (2026-09-18):
"phai dua AI vao phan tich giup minh va dua ra khuyen nghi cho minh co nen
update hay khong hay giu nguyen".

Chi lam 1 viec: doc cloud_signals.json (nhat ky MOI lenh da gui that tu
truoc den nay) -> tinh thong ke thang vua qua + tong the -> goi THAT Claude
API de viet nhan xet/khuyen nghi -> luu vao dashboard/ai_reviews.js (dashboard
doc de hien tab "AI Tong ket") -> gui 1 email tong ket.

Co the chay tay de test: python run_monthly_review.py
(doc ANTHROPIC_API_KEY/GMAIL_* tu .env neu co, giong run_cloud.py).
"""
import sys

from src.core.config import Config
from src.notifier.factory import create_notifier
from src.notifier.messages import build_monthly_review_email
from src.ai_review.monthly_report import run as run_monthly_report


def main():
    cfg = Config()

    print("=" * 60)
    print("  TRADING ASSISTANT AI - AI MONTHLY REVIEW")
    print("=" * 60)

    if not cfg.anthropic_api_key:
        print("[LOI] Thieu ANTHROPIC_API_KEY (.env hoac GitHub Secrets).")
        print("      Vao Settings > Secrets and variables > Actions cua repo")
        print("      GitHub de them secret ANTHROPIC_API_KEY roi chay lai.")
        sys.exit(1)

    try:
        report = run_monthly_report(api_key=cfg.anthropic_api_key,
                                     model=cfg.anthropic_model)
    except Exception as e:
        print("[LOI] Khong tao duoc bao cao AI:", e)
        sys.exit(1)

    print("Thang tong ket :", report["month_label"])
    print("Khuyen nghi AI :", report["tag"])
    print("Da luu vao     : dashboard/ai_reviews.js")

    notifier = create_notifier(cfg)
    if notifier is None:
        print("[WARN] Khong co kenh thong bao nao duoc cau hinh - bo qua gui mail")
        print("       (bao cao van da duoc luu vao dashboard).")
        return

    subject, body = build_monthly_review_email(report)
    ok = notifier.send(subject, body)
    print("Gui mail tong ket thang ->", "OK" if ok else "THAT BAI")


if __name__ == "__main__":
    main()
