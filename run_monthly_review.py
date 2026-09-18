# -*- coding: utf-8 -*-
"""
run_monthly_review.py - chay tren GitHub Actions, 1 lan vao ngay 1 hang thang
(xem .github/workflows/monthly_review.yml), theo yeu cau CuongNT (2026-09-18):
"phai dua AI vao phan tich giup minh va dua ra khuyen nghi cho minh co nen
update hay khong hay giu nguyen".

Chi lam 1 viec: doc cloud_signals.json (nhat ky MOI lenh da gui that tu
truoc den nay) -> tinh thong ke thang vua qua + tong the -> CHAM DIEM THEO
NGUONG CO DINH (mien phi, khong goi API nao - xem
src/ai_review/monthly_report.py de biet ly do doi tu phuong an goi Claude
API sang phuong an nay) de viet nhan xet/khuyen nghi -> luu vao
dashboard/ai_reviews.js (dashboard doc de hien tab "AI Tong ket") -> gui 1
email tong ket.

Co the chay tay de test: python run_monthly_review.py
"""
from src.core.config import Config
from src.notifier.factory import create_notifier
from src.notifier.messages import build_monthly_review_email
from src.ai_review.monthly_report import run as run_monthly_report


def main():
    cfg = Config()

    print("=" * 60)
    print("  TRADING ASSISTANT AI - MONTHLY REVIEW (mien phi, khong goi API)")
    print("=" * 60)

    report = run_monthly_report()

    print("Thang tong ket :", report["month_label"])
    print("Khuyen nghi    :", report["tag"])
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
