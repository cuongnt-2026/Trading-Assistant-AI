# -*- coding: utf-8 -*-
"""
Monthly AI Review (theo yeu cau CuongNT, 2026-09-18): moi thang, he thong tu
tong hop lai TOAN BO lenh da gui (cloud_signals.json) cua thang vua qua VA
tu truoc den nay, roi GOI THAT Claude API (khong phai cham diem theo luat co
dinh nhu src/ai_review/recommender.py) de doc so lieu va viet nhan xet +
khuyen nghi bang van tu nhien: nen GIU NGUYEN he thong, hay CAN CAI THIEN
mot vai cho, hay NEN CAP NHAT/xem lai gap.

Luong chay (xem run_monthly_review.py o thu muc goc):
  1) Doc cloud_signals.json (nhat ky MOI lenh da THUC SU gui mail - khong
     gom NO_TRADE/WAIT) -> loc ra du lieu THANG VUA KET THUC + TOAN BO tu
     truoc den nay.
  2) Tinh thong ke theo tung chien luoc (so lenh, win/loss/open, winrate,
     Profit Factor theo R, tong R, R trung binh, do tin cay trung binh).
  3) Dung so lieu do de dung 1 prompt tieng Viet, goi that Claude API
     (Anthropic Messages API, qua urllib - khong can them thu vien ngoai).
  4) Luu ket qua vao dashboard/ai_reviews.js (dashboard doc de hien tab
     "AI Tong ket") + gui 1 email tong ket (xem
     src/notifier/messages.py::build_monthly_review_email).

CAN bien moi truong ANTHROPIC_API_KEY (secret rieng, xem
.github/workflows/monthly_review.yml) - neu thieu, script se dung lai va
bao loi ro rang thay vi tu bia mot ban "AI gia" khong dung y muon that su
dung AI (CuongNT da chon phuong an "goi AI that" thay vi cham diem luat
co dinh).
"""

import json
import os
import urllib.error
import urllib.request
from datetime import datetime

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = "claude-sonnet-4-5"

# Cac chien luoc HIEN DA TAT (hidden khoi dashboard) tinh den 2026-09-18 -
# dua vao prompt de AI khong khuyen nghi lai nhung gi da quyet dinh roi.
DISABLED_STRATEGIES_NOTE = (
    "trend (TREND_ENABLED=0, da bo han watchlist), "
    "supertrend (SUPERTREND_ENABLED=0, da an khoi dashboard tu 2026-09 vi "
    "nhieu lenh nhung khong loi nhuan ro ret)"
)

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


def build_prompt(m_label, month_stats, alltime_stats, alltime_range_txt):
    return (
        "Ban la co van rui ro/dinh luong cho mot he thong GUI TIN HIEU giao dich "
        "tu dong (Trading Assistant AI) cua toi, chay tren GitHub Actions, gui "
        "tin hieu BUY/SELL qua email theo nhieu \"chien luoc\" khac nhau (moi "
        "chien luoc = 1 bo luat ky thuat rieng, da qua backtest truoc khi bat "
        "len that). Moi thang toi muon ban DOC LAI so lieu that va NHAN XET + "
        "KHUYEN NGHI giup toi, giong nhu mot chuyen gia dang review hieu suat "
        "thuc te cua he thong.\n\n"
        "Boi canh: cac chien luoc {} da bi TAT/an di roi (khong con chay nua) "
        "vi hieu suat kem trong qua khu - KHONG can khuyen nghi ve 2 chien "
        "luoc nay nua, chi de ban doi chieu xu huong chung.\n\n"
        "===== SO LIEU THANG VUA QUA ({}) =====\n{}\n\n"
        "===== SO LIEU TU TRUOC DEN NAY ({}) =====\n{}\n\n"
        "Hay tra loi bang TIENG VIET, theo dung cau truc sau (giu nguyen tieu "
        "de cac dong, khong dung markdown/bang bieu phuc tap):\n\n"
        "TAG: <chon dung 1 trong 3: GIU_NGUYEN | CAI_THIEN | CAP_NHAT_NGAY>\n\n"
        "NHAN XET THANG NAY:\n<2-4 cau, chien luoc nao tot/xau, co gi bat "
        "thuong khong>\n\n"
        "DANH GIA TONG THE TU TRUOC DEN NAY:\n<3-5 cau, he thong dang on dinh, "
        "tien bo hay xau di, chien luoc nao dang la tru cot, chien luoc nao "
        "dang keo tut hieu suat chung>\n\n"
        "KHUYEN NGHI CU THE:\n<liet ke gach dau dong cac hanh dong cu the toi "
        "nen lam - vi du: tat/giam risk 1 chien luoc cu the, backtest them "
        "mot bien the, giu nguyen khong doi gi vi so lieu con qua it, v.v. "
        "Neu so lenh cua 1 chien luoc con qua it (duoi ~20-30 lenh) de ket "
        "luan chac chan, hay noi ro la CAN CHO THEM DU LIEU thay vi vo doan.>\n"
    ).format(DISABLED_STRATEGIES_NOTE, m_label,
             _fmt_stats_block(month_stats), alltime_range_txt,
             _fmt_stats_block(alltime_stats))


def call_claude(prompt, api_key, model=None, max_tokens=2000, timeout=90):
    """Goi that Anthropic Messages API bang urllib (khong can them thu vien
    ngoai vao requirements-cloud.txt). Nem loi ro rang neu that bai - KHONG
    tu bia noi dung thay the, vi CuongNT chon ro la muon AI THAT phan tich."""
    if not api_key:
        raise RuntimeError(
            "Thieu ANTHROPIC_API_KEY - vao Settings > Secrets and variables > "
            "Actions cua repo GitHub de them secret nay truoc khi chay lai.")
    model = model or os.getenv("ANTHROPIC_MODEL", DEFAULT_MODEL)
    body = json.dumps({
        "model": model,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")
    req = urllib.request.Request(
        ANTHROPIC_API_URL, data=body, method="POST",
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            "Anthropic API tra loi loi HTTP {} (model='{}'): {}\n"
            "-> Neu loi 'not_found_error'/model khong ton tai, kiem tra model "
            "hien hanh tai https://docs.claude.com/en/docs/about-claude/models "
            "roi dat secret/bien ANTHROPIC_MODEL cho dung.".format(
                e.code, model, detail))
    except urllib.error.URLError as e:
        raise RuntimeError("Khong ket noi duoc toi Anthropic API: {}".format(e))
    parts = data.get("content", [])
    text = "".join(p.get("text", "") for p in parts if p.get("type") == "text")
    return text.strip()


def parse_tag(ai_text):
    """Lay dong 'TAG: ...' o dau van ban de hien badge mau tren dashboard.
    Tra ve 'KHONG_RO' neu AI tra loi khong dung dinh dang mong doi."""
    for line in ai_text.splitlines():
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


def run(signals_path="cloud_signals.json", history_path="dashboard/ai_reviews.js",
        api_key=None, model=None, now=None):
    """Chay tron 1 chu ky tong ket thang. Tra ve dict report vua tao (da
    them vao history va ghi file) de run_monthly_review.py dung gui mail."""
    api_key = api_key if api_key is not None else os.getenv("ANTHROPIC_API_KEY", "").strip()
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

    prompt = build_prompt(m_label, month_stats, alltime_stats, alltime_range_txt)
    ai_text = call_claude(prompt, api_key, model=model)
    tag = parse_tag(ai_text)

    report = {
        "month_label": m_label,
        "generated_at": (now or datetime.utcnow()).strftime("%Y-%m-%d %H:%M UTC"),
        "tag": tag,
        "month_stats": month_stats,
        "alltime_stats": alltime_stats,
        "alltime_range": alltime_range_txt,
        "ai_text": ai_text,
    }

    history = load_history(history_path)
    history.append(report)
    save_history(history, history_path)
    return report
