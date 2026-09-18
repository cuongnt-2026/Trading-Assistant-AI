# -*- coding: utf-8 -*-
"""
Monthly Review (theo yeu cau CuongNT, 2026-09-18): moi thang, he thong tu
tong hop lai TOAN BO lenh da gui (cloud_signals.json) cua thang vua qua VA
tu truoc den nay, roi TU DONG CHAM DIEM THEO LUAT CO DINH (giong cach
src/ai_review/recommender.py cham diem tin cay tung tin hieu) de viet nhan
xet + khuyen nghi: nen GIU NGUYEN he thong, hay CAN CAI THIEN mot vai cho,
hay NEN CAP NHAT/xem lai gap.

(Ban dau ban nay GOI THAT Claude API - sau khi trao doi voi CuongNT ve chi
phi (can nap tien truoc vao tai khoan Anthropic de co API key, du moi thang
chi ton vai xu), CuongNT chon phuong an MIEN PHI HOAN TOAN nay thay the -
khong can API key, khong can nap tien, khong goi mang ra ngoai.)

Luong chay (xem run_monthly_review.py o thu muc goc):
  1) Doc cloud_signals.json (nhat ky MOI lenh da THUC SU gui mail - khong
     gom NO_TRADE/WAIT) -> loc ra du lieu THANG VUA KET THUC + TOAN BO tu
     truoc den nay.
  2) Tinh thong ke theo tung chien luoc (so lenh, win/loss/open, winrate,
     Profit Factor theo R, tong R, R trung binh, do tin cay trung binh).
  3) Cham diem theo NGUONG CO DINH (giong quy uoc da dung xuyen suot du an:
     PF >= 1.3 voi >= 20 lenh la "tot", PF < 1.0 voi >= 20 lenh la "kem",
     duoi 20 lenh la "chua du du lieu de ket luan") -> sinh van ban nhan
     xet + khuyen nghi bang tieng Viet, CUNG DINH DANG (TAG/NHAN XET/DANH
     GIA/KHUYEN NGHI) nhu ban goi AI truoc day, de dashboard/email khong
     can sua gi them.
  4) Luu ket qua vao dashboard/ai_reviews.js (dashboard doc de hien tab
     "AI Tong ket") + gui 1 email tong ket (xem
     src/notifier/messages.py::build_monthly_review_email).
"""

import json
import os
from datetime import datetime

# Cac chien luoc HIEN DA TAT (hidden khoi dashboard) tinh den 2026-09-18 -
# bo qua khi dua ra khuyen nghi (khong khuyen nghi lai nhung gi da quyet
# dinh roi), nhung van hien so lieu de doi chieu xu huong chung.
DISABLED_STRATEGIES = {"trend", "supertrend"}

# Nguong cham diem (dung lai dung quy uoc da ap dung xuyen suot du an: chi
# bat 1 chien luoc that khi PF > 1.2-1.3 voi it nhat vai chuc lenh - xem
# comment o src/core/config.py::bollinger_pairs/london_pairs/emapullback_*).
MIN_SAMPLE = 20        # duoi nguong nay: chua du du lieu de ket luan chac chan
PF_GOOD = 1.3          # >= muc nay: dang hoat dong tot, giu nguyen
PF_OK = 1.0            # >= muc nay (nhung < PF_GOOD): hoa von/trung binh
PF_BAD_URGENT = 0.8    # < muc nay (VA du mau) -> can xem lai/tam dung gap

MONTH_VN = [
    "", "Tháng 1", "Tháng 2", "Tháng 3", "Tháng 4", "Tháng 5", "Tháng 6",
    "Tháng 7", "Tháng 8", "Tháng 9", "Tháng 10", "Tháng 11", "Tháng 12",
]


def load_signals(path="cloud_signals.json"):
    """Doc nhat ky lenh da gui. Tra ve [] neu chua co file (chay lan dau)."""
    if not os.path.exists(path):
        return []
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print("[WARN] Khong doc duoc {}: {}".format(path, e))
        return []


def _parse_time(s):
    """cloud_signals.json ghi 'time' dang '2026-08-05 15:00 UTC' hoac tuong
    tu - bo hau to UTC roi parse, tra ve None neu khong parse duoc (khong
    lam vo ca script vi 1 dong loi)."""
    if not s:
        return None
    s = s.strip()
    if s.endswith("UTC"):
        s = s[:-3].strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def previous_month(today=None):
    """Thang VUA KET THUC tinh tu 'today' (mac dinh = luc chay, UTC). Job
    chay dung ngay 1 hang thang nen 'today' se la ngay 1 -> tra ve thang
    truoc do (vd chay 2026-09-01 -> tra ve (2026, 8))."""
    today = today or datetime.utcnow()
    y, m = today.year, today.month
    if m == 1:
        return y - 1, 12
    return y, m - 1


def month_label(year, month):
    return "{} {}".format(MONTH_VN[month], year)


def filter_by_month(signals, year, month):
    out = []
    for r in signals:
        t = _parse_time(r.get("time"))
        if t and t.year == year and t.month == month:
            out.append(r)
    return out


def _pf(gross_win, gross_loss):
    if gross_loss <= 0:
        return None if gross_win <= 0 else "vo cuc (chua thua lenh nao)"
    return round(gross_win / gross_loss, 2)


def _bucket_stats(rows):
    wins = [r for r in rows if r.get("outcome") == "WIN"]
    losses = [r for r in rows if r.get("outcome") == "LOSS"]
    opens = [r for r in rows if r.get("outcome") == "OPEN"]
    closed_n = len(wins) + len(losses)
    gross_win = sum((r.get("r_result") or 0) for r in wins)
    gross_loss = abs(sum((r.get("r_result") or 0) for r in losses))
    total_r = sum((r.get("r_result") or 0) for r in wins + losses)
    confs = [r["confidence"] for r in rows if isinstance(r.get("confidence"), (int, float))]
    return {
        "total": len(rows),
        "wins": len(wins),
        "losses": len(losses),
        "open": len(opens),
        "winrate_pct": round(len(wins) / closed_n * 100, 1) if closed_n else None,
        "profit_factor": _pf(gross_win, gross_loss),
        "total_r": round(total_r, 2),
        "avg_r": round(total_r / closed_n, 2) if closed_n else None,
        "avg_confidence": round(sum(confs) / len(confs), 1) if confs else None,
    }


def compute_stats(signals):
    """Tra ve {'overall': {...}, 'by_strategy': {ten_chien_luoc: {...}}}."""
    strategies = sorted(set((r.get("strategy") or "?") for r in signals))
    by_strategy = {
        s: _bucket_stats([r for r in signals if (r.get("strategy") or "?") == s])
        for s in strategies
    }
    return {"overall": _bucket_stats(signals), "by_strategy": by_strategy}


def _fmt_stats_block(stats):
    lines = []
    o = stats["overall"]
    lines.append(
        "TONG: {} lenh | Win {} - Loss {} - Open {} | Winrate {}% | "
        "PF {} | Tong R {} | R trung binh {} | Tin cay TB {}%".format(
            o["total"], o["wins"], o["losses"], o["open"],
            o["winrate_pct"], o["profit_factor"], o["total_r"], o["avg_r"],
            o["avg_confidence"]))
    for name, s in sorted(stats["by_strategy"].items()):
        lines.append(
            "  - {}: {} lenh | Win {} - Loss {} - Open {} | Winrate {}% | "
            "PF {} | Tong R {} | R trung binh {} | Tin cay TB {}%".format(
                name, s["total"], s["wins"], s["losses"], s["open"],
                s["winrate_pct"], s["profit_factor"], s["total_r"], s["avg_r"],
                s["avg_confidence"]))
    return "\n".join(lines)


def _judge(s):
    """Xep loai 1 bucket thong ke (tong the hoac 1 chien luoc) theo nguong
    co dinh. Tra ve 1 trong: 'THIEU_DU_LIEU', 'TOT', 'TRUNG_BINH', 'KEM'."""
    if s["total"] < MIN_SAMPLE:
        return "THIEU_DU_LIEU"
    pf = s["profit_factor"]
    if isinstance(pf, str):  # "vo cuc (chua thua lenh nao)" -> toan thang
        return "TOT"
    if pf is None:  # chua co lenh nao thang/thua (toan OPEN) du >= MIN_SAMPLE
        return "THIEU_DU_LIEU"
    if pf >= PF_GOOD:
        return "TOT"
    if pf >= PF_OK:
        return "TRUNG_BINH"
    return "KEM"


def decide_tag(alltime_stats):
    """Quyet dinh khuyen nghi tong the dua tren so lieu TU TRUOC DEN NAY
    (khong dung so lieu 1 thang le - de tranh ket luan voi theo 1 thang xau
    ngau nhien). Chi xet cac chien luoc DANG BAT (bo qua trend/supertrend
    da tat)."""
    by = {k: s for k, s in alltime_stats["by_strategy"].items()
          if k not in DISABLED_STRATEGIES}
    urgent = [k for k, s in by.items()
              if s["total"] >= MIN_SAMPLE and isinstance(s["profit_factor"], (int, float))
              and s["profit_factor"] < PF_BAD_URGENT]
    weak = [k for k, s in by.items()
            if s["total"] >= MIN_SAMPLE and isinstance(s["profit_factor"], (int, float))
            and s["profit_factor"] < PF_OK]
    overall_pf = alltime_stats["overall"]["profit_factor"]
    overall_n = alltime_stats["overall"]["total"]
    overall_urgent = (overall_n >= MIN_SAMPLE and isinstance(overall_pf, (int, float))
                       and overall_pf < PF_BAD_URGENT)
    overall_weak = (overall_n >= MIN_SAMPLE and isinstance(overall_pf, (int, float))
                     and overall_pf < PF_OK)
    if urgent or overall_urgent:
        return "CAP_NHAT_NGAY"
    if weak or overall_weak:
        return "CAI_THIEN"
    return "GIU_NGUYEN"


def _strategy_comment(name, s):
    j = _judge(s)
    pf_txt = s["profit_factor"] if s["profit_factor"] is not None else "—"
    if j == "THIEU_DU_LIEU":
        return "{}: mới {} lệnh (dưới ngưỡng {} lệnh để kết luận chắc chắn), cần theo dõi thêm".format(
            name, s["total"], MIN_SAMPLE)
    if j == "TOT":
        return "{}: đang hoạt động TỐT - {} lệnh, PF {}, winrate {}%, tổng {} R".format(
            name, s["total"], pf_txt, s["winrate_pct"], s["total_r"])
    if j == "TRUNG_BINH":
        return "{}: ở mức TRUNG BÌNH - {} lệnh, PF {}, winrate {}%, tổng {} R (chưa lỗ nhưng chưa đạt ngưỡng {})".format(
            name, s["total"], pf_txt, s["winrate_pct"], s["total_r"], PF_GOOD)
    return "{}: đang KÉM - {} lệnh, PF {}, winrate {}%, tổng {} R (dưới ngưỡng hòa vốn {})".format(
        name, s["total"], pf_txt, s["winrate_pct"], s["total_r"], PF_OK)


def _recommendation_lines(alltime_stats):
    by = {k: s for k, s in alltime_stats["by_strategy"].items()
          if k not in DISABLED_STRATEGIES}
    lines = []
    for name, s in sorted(by.items()):
        j = _judge(s)
        if j == "KEM":
            lines.append("- Nên xem lại/cân nhắc tạm dừng {}: PF {} trên {} lệnh, đang dưới "
                          "ngưỡng hòa vốn {}.".format(name, s["profit_factor"], s["total"], PF_OK))
        elif j == "TRUNG_BINH":
            lines.append("- Theo dõi thêm {}: PF {} trên {} lệnh, chưa lỗ nhưng chưa đạt "
                          "ngưỡng {} để yên tâm.".format(name, s["profit_factor"], s["total"], PF_GOOD))
        elif j == "THIEU_DU_LIEU":
            lines.append("- {} mới có {} lệnh, cần thêm dữ liệu (ít nhất {} lệnh) trước khi "
                          "kết luận, chưa nên vội thay đổi.".format(name, s["total"], MIN_SAMPLE))
        else:
            lines.append("- Giữ nguyên {}, đang hoạt động tốt (PF {}, {} lệnh).".format(
                name, s["profit_factor"], s["total"]))
    if not lines:
        lines.append("- Chưa có chiến lược nào đang bật có đủ dữ liệu để đánh giá.")
    return lines


def generate_review_text(month_stats, alltime_stats):
    """Sinh van ban nhan xet + khuyen nghi THEO NGUONG CO DINH (khong goi
    API/AI nao), CUNG dinh dang voi ban goi Claude truoc day (TAG/NHAN
    XET/DANH GIA/KHUYEN NGHI) de parse_tag() va dashboard/email khong doi."""
    tag = decide_tag(alltime_stats)

    month_by = {k: s for k, s in month_stats["by_strategy"].items()
                if k not in DISABLED_STRATEGIES}
    nhan_xet = ([_strategy_comment(stratlabel, s) for stratlabel, s in sorted(month_by.items())]
                or ["Tháng này chưa có lệnh nào ở các chiến lược đang bật."])

    o_m, o_a = month_stats["overall"], alltime_stats["overall"]
    xu_huong = ""
    if isinstance(o_m["profit_factor"], (int, float)) and isinstance(o_a["profit_factor"], (int, float)):
        if o_m["profit_factor"] > o_a["profit_factor"]:
            xu_huong = " Tháng này (PF {}) đang TỐT HƠN mặt bằng chung từ trước đến nay (PF {}).".format(
                o_m["profit_factor"], o_a["profit_factor"])
        elif o_m["profit_factor"] < o_a["profit_factor"]:
            xu_huong = " Tháng này (PF {}) đang KÉM HƠN mặt bằng chung từ trước đến nay (PF {}).".format(
                o_m["profit_factor"], o_a["profit_factor"])
    danh_gia = (
        "Tổng thể từ trước đến nay: {} lệnh, winrate {}%, PF {}, tổng {} R.{}".format(
            o_a["total"], o_a["winrate_pct"], o_a["profit_factor"], o_a["total_r"], xu_huong))

    lines = [
        "TAG: {}".format(tag),
        "",
        "NHAN XET THANG NAY:",
    ] + nhan_xet + [
        "",
        "DANH GIA TONG THE TU TRUOC DEN NAY:",
        danh_gia,
        "",
        "KHUYEN NGHI CU THE:",
    ] + _recommendation_lines(alltime_stats) + [
        "",
        "(Nhan xet nay duoc sinh tu dong theo nguong co dinh - PF >= {} la tot, "
        "duoi {} la can xem lai, duoi {} lenh la chua du du lieu - khong phai do "
        "AI doc va viet tu do; ban co the doi lai nguong nay trong "
        "src/ai_review/monthly_report.py neu thay chua phu hop.)".format(
            PF_GOOD, PF_OK, MIN_SAMPLE),
    ]
    return "\n".join(lines)


def parse_tag(review_text):
    """Lay dong 'TAG: ...' o dau van ban de hien badge mau tren dashboard.
    Tra ve 'KHONG_RO' neu khong dung dinh dang mong doi."""
    for line in review_text.splitlines():
        line = line.strip()
        if line.upper().startswith("TAG:"):
            val = line.split(":", 1)[1].strip().upper()
            if val in ("GIU_NGUYEN", "CAI_THIEN", "CAP_NHAT_NGAY"):
                return val
    return "KHONG_RO"


def load_history(path="dashboard/ai_reviews.js"):
    if not os.path.exists(path):
        return []
    try:
        with open(path, encoding="utf-8") as f:
            raw = f.read()
        start = raw.index("[")
        end = raw.rindex("]") + 1
        return json.loads(raw[start:end])
    except Exception as e:
        print("[WARN] Khong doc duoc lich su {}: {}".format(path, e))
        return []


def save_history(history, path="dashboard/ai_reviews.js", keep_last=24):
    history = history[-keep_last:]
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("window.TA_REVIEWS = " + json.dumps(history, ensure_ascii=False, indent=2) + ";\n")


def run(signals_path="cloud_signals.json", history_path="dashboard/ai_reviews.js", now=None):
    """Chay tron 1 chu ky tong ket thang (mien phi, khong goi API nao). Tra
    ve dict report vua tao (da them vao history va ghi file) de
    run_monthly_review.py dung gui mail."""
    signals = load_signals(signals_path)
    y, m = previous_month(now)
    m_label = month_label(y, m)
    month_signals = filter_by_month(signals, y, m)
    month_stats = compute_stats(month_signals)
    alltime_stats = compute_stats(signals)
    times = [_parse_time(r.get("time")) for r in signals]
    times = [t for t in times if t]
    alltime_range_txt = (
        "{} -> {}".format(min(times).strftime("%d/%m/%Y"), max(times).strftime("%d/%m/%Y"))
        if times else "chua co du lieu")

    review_text = generate_review_text(month_stats, alltime_stats)
    tag = parse_tag(review_text)

    report = {
        "month_label": m_label,
        "generated_at": (now or datetime.utcnow()).strftime("%Y-%m-%d %H:%M UTC"),
        "tag": tag,
        "month_stats": month_stats,
        "alltime_stats": alltime_stats,
        "alltime_range": alltime_range_txt,
        "ai_text": review_text,
    }

    history = load_history(history_path)
    history.append(report)
    save_history(history, history_path)
    return report
