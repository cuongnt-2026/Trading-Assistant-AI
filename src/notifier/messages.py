"""
Message builder - soan tieu de & noi dung email tu mot Signal.
"""

from datetime import datetime
from src.signal.constants import BUY, SELL


def _action_label(action):
    if action == BUY:
        return "MUA (BUY)"
    if action == SELL:
        return "BAN (SELL)"
    return action


def build_signal_email(signal, symbol, timeframe, candle,
                       recommendation=None, trade_plan=None):
    action = _action_label(signal.action)
    price = candle.close
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    act = "BUY" if signal.action == BUY else ("SELL" if signal.action == SELL else signal.action)
    conf_txt = "{:.0f}%".format(recommendation.confidence) if recommendation is not None else "-"
    if trade_plan is not None and trade_plan.action in (BUY, SELL):
        subject = "{} {} {} | E:{} SL:{} TP:{} | Tin cay {}".format(
            symbol, timeframe, act, trade_plan.entry_price,
            trade_plan.stop_loss, trade_plan.take_profit, conf_txt)
    else:
        subject = "{} {} {} @ {:.2f} | Tin cay {}".format(
            symbol, timeframe, act, price, conf_txt)

    body = (
        "========================================\n"
        "     TRADING ASSISTANT AI - TIN HIEU\n"
        "========================================\n\n"
        "Symbol      : {}\n"
        "Khung TG    : {}\n"
        "Hanh dong   : {}\n"
        "Xu huong    : {}\n"
        "Gia hien tai: {:.2f}\n"
        "Thoi diem   : {}\n\n"
    ).format(symbol, timeframe, action, signal.trend, price, now)

    if recommendation is not None:
        body += (
            "---------- AI RECOMMENDATION ----------\n"
            "Khuyen nghi : {}\n"
            "Do tin cay  : {:.0f}% ({})\n"
            "Ly do       : {}\n\n"
        ).format(recommendation.action, recommendation.confidence,
                 recommendation.label, ", ".join(recommendation.reasons))

    if trade_plan is not None and trade_plan.action in (BUY, SELL):
        body += (
            "---------- KE HOACH VAO LENH (SL/TP DONG) ----------\n"
            "Loai lenh    : {}\n"
            "Entry        : {}\n"
            "Stop Loss    : {}  ({})\n"
            "Take Profit  : {}  ({})\n"
            "R:R          : {}\n"
            "Trailing SL  : doi theo gia, khoang cach ~{}\n"
            "Risk         : {:g}% (theo do tin cay)\n"
        ).format(("LENH CHO (limit)" if trade_plan.entry_type=='limit' else "vao ngay (market)"), trade_plan.entry_price, trade_plan.stop_loss, trade_plan.sl_source,
                 trade_plan.take_profit, trade_plan.tp_source, trade_plan.risk_reward,
                 trade_plan.trail_distance, trade_plan.risk_percent)
        if trade_plan.lot_size is not None:
            body += "Lot (uoc tinh): {}\nLoi nhuan KV  : {}\n".format(
                trade_plan.lot_size, trade_plan.expected_profit)
        body += ("Ghi chu: TP theo cau truc thi truong; khi gia chay thuan huong,\n"
                 "hay doi SL (trailing) de bao ve loi nhuan thay vi cho cham TP.\n")
        body += "\n"

    body += (
        "---------- CHI BAO ----------\n"
        "EMA20      : {:.2f}\n"
        "EMA50      : {:.2f}\n"
        "EMA200     : {:.2f}\n"
        "ADX        : {:.2f}\n"
        "ATR        : {:.2f}\n"
        "RSI        : {:.2f}\n\n"
        "Ly do      : {}\n\n"
        "========================================\n"
        "Luu y: Day la tin hieu tham khao, khong phai loi khuyen dau tu.\n"
        "-- Trading Assistant AI"
    ).format(signal.ema20, signal.ema50, signal.ema200, signal.adx,
             getattr(signal, "atr", 0.0), getattr(signal, "rsi", 0.0),
             signal.reason)

    return subject, body


def build_supertrend_email(symbol, timeframe, action, entry, st_line):
    """Email cho tin hieu Supertrend (he dao chieu). Co Entry + SL, khong co TP co dinh."""
    act = "MUA (BUY)" if action == BUY else "BAN (SELL)"
    short = "BUY" if action == BUY else "SELL"
    risk = abs(entry - st_line)
    tp_ref = round(entry + 2 * risk, 2) if action == BUY else round(entry - 2 * risk, 2)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    subject = "{} {} SUPERTREND {} | Entry:{} SL:{} | dao chieu".format(
        symbol, timeframe, short, entry, st_line)
    body = (
        "========================================\n"
        "  TRADING ASSISTANT AI - SUPERTREND\n"
        "========================================\n\n"
        "Symbol      : {}\n"
        "Khung TG    : {}\n"
        "Tin hieu    : {}  (Supertrend vua DAO CHIEU)\n"
        "Thoi diem   : {}\n\n"
        "---------- KE HOACH ----------\n"
        "Entry       : {}\n"
        "Stop Loss   : {}  (= duong Supertrend, trailing)\n"
        "Take Profit : KHONG co dinh - THOAT khi co tin hieu Supertrend NGUOC\n"
        "TP tham khao: {}  (neu muon chot o 2R)\n\n"
        "*** CACH QUAN LY (he dao chieu) ***\n"
        "- Neu dang giu lenh NGUOC lai -> DONG lenh cu truoc, roi mo lenh nay.\n"
        "- Giu lenh nay toi khi nhan mail Supertrend huong nguoc.\n"
        "- SL doi theo duong Supertrend (trailing).\n\n"
        "========================================\n"
        "Luu y: tin hieu tham khao, khong phai loi khuyen dau tu.\n"
        "-- Trading Assistant AI (Supertrend)"
    ).format(symbol, timeframe, act, now, entry, st_line, tp_ref)
    return subject, body


def build_ema_cross_email(symbol, timeframe, ev):
    """Email CANH BAO 2 duong EMA (vd EMA20/EMA100) SAP hoac VUA cat cheo nhau.
    KHONG phai tin hieu vao lenh (khong co Entry/SL/TP) - chi de theo doi thu cong.
    `ev` la dict tra ve tu EmaCrossWatcher.check() (co ema_fast/ema_slow = chu ky
    THAT cua 2 duong, de hien thi ro rang thay vi noi chung chung "nhanh/cham")."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ef, es = ev["ema_fast"], ev["ema_slow"]
    up = ev["direction"] == "up"
    dir_txt = ("TANG (EMA{} cat LEN TREN EMA{})".format(ef, es) if up
               else "GIAM (EMA{} cat XUONG DUOI EMA{})".format(ef, es))
    dir_short = "TANG" if up else "GIAM"
    # Goc "dai dien" hien ngay tren tieu de = do doc cua duong EMA vua di dong (EMA nhanh) -
    # de nguoi doc nhin 1 cai la hinh dung duoc muc do "dut khoat" cua cu cheo, khong can
    # mo mail ra doc chi tiet. Lay tri tuyet doi vi chieu (TANG/GIAM) da noi rieng roi -
    # "goc -12 do" doc la nhung "goc 12 do" thi tu nhien hon.
    goc_dai_dien = abs(ev["angle_fast"])

    if ev["type"] == "crossed":
        headline = "VUA CAT CHEO"
        eta_line = ""
    else:
        headline = "SAP CAT CHEO"
        eta_txt = "~{:g} nen nua".format(ev["eta_bars"]) if ev.get("eta_bars") else "chua uoc tinh duoc"
        eta_line = "Du kien       : con {} se cham nhau (ngoai suy tuyen tinh tu toc do hep\n                lai hien tai - CHI tham khao, gia co the doi chieu bat ky luc nao)\n".format(eta_txt)

    subject = "{} {} EMA{}/{} {} {} | goc {:g} do".format(
        symbol, timeframe, ef, es, headline, dir_short, goc_dai_dien)

    body = (
        "========================================\n"
        "   TRADING ASSISTANT AI - EMA CROSS WATCH (EMA{}/EMA{})\n"
        "========================================\n\n"
        "Symbol        : {}\n"
        "Khung TG      : {}\n"
        "Tin hieu      : {} - {}\n"
        "Gia hien tai  : {}\n"
        "Thoi diem     : {}\n"
        "Nen tin hieu  : {}\n\n"
        "---------- CHI TIET ----------\n"
        "Goc doc EMA{} (duong vua di dong, 5 nen gan nhat): {} do  <- goc tren tieu de\n"
        "Goc doc EMA{} (duong con lai,     5 nen gan nhat): {} do\n"
        "{}"
        "Khoang cach 2 duong EMA hien tai: {} x ATR (chi so ky thuat tham khao them)\n\n"
        "  (Goc cang gan 90 do = xu huong dang manh/dot ngot, cang gan 0 do = di ngang\n"
        "   phang. Chenh lech giua 2 goc EMA{}/EMA{} CANG LON -> cu cat cheo cang 'dut\n"
        "   khoat' (dang tin cay hon); chenh lech nho/2 duong gan nhu song song -> de bi\n"
        "   nhieu/fake. Quy uoc: doc ~1*ATR/nen ~= 45 do, de so sanh duoc giua cac\n"
        "   symbol/khung khac nhau - khong phai goc nhin thay tren TradingView.)\n\n"
        "========================================\n"
        "Luu y QUAN TRONG: day CHI la canh bao ky thuat (EMA giao nhau), KHONG phai tin\n"
        "hieu vao lenh co san Entry/SL/TP - ban tu quyet dinh dua tren cac yeu to khac\n"
        "(xu huong khung lon hon, tin tuc, khoi luong, v.v).\n"
        "-- Trading Assistant AI (EMA Cross Watch)"
    ).format(ef, es, symbol, timeframe, headline, dir_txt, ev["price"], now, ev["candle_time"],
             ef, ev["angle_fast"], es, ev["angle_slow"], eta_line, ev["gap_atr"], ef, es)
    return subject, body


def build_ema_trend_email(symbol, timeframe, ev):
    """Email cho EmaTrendWatcher (EMA20/50/200 loc theo che do EMA200, thay EMA Cross
    Watch cu). `ev` la dict tra ve tu EmaTrendWatcher.check_triple()/check_cross().
    KHONG phai tin hieu vao lenh (khong co Entry/SL/TP co san) - chi la nhan dinh/de
    xuat de nguoi dung tu quyet dinh vao lenh tay."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ef, em, es = ev["ef"], ev["em"], ev["es"]
    up = ev["direction"] == "up"
    de_xuat = "BUY (MUA)" if up else "SELL (BAN)"

    if ev["type"] == "triple":
        headline = "CA 3 EMA VUA HOI TU ROI TACH RA - {}".format("THUAN TANG" if up else "THUAN GIAM")
        nhan_dinh = (
            "Ca 3 duong EMA{}/EMA{}/EMA{} vua hoi tu sat nhau ({} nen truoc), sau {} nen\n"
            "da tach ra va xep lai HOAN TOAN theo thu tu {} - day la tin hieu HIEM nhung\n"
            "MANH, thuong bao hieu kha nang xac lap hoac dao chieu mot xu huong lon hon\n"
            "(khong chi la mot nhip dao dong ngan). Nen cao trach nhiem xem xet vao lenh\n"
            "theo huong {} tu day, VOI dieu kien cho gia xac nhan them (vd nen dong manh\n"
            "cung huong, khong chi dua vao mot minh tin hieu nay)."
        ).format(ef, em, es, ev["confirm_bars"], ev["confirm_bars"],
                 "EMA{}>EMA{}>EMA{}".format(ef, em, es) if up else "EMA{}<EMA{}<EMA{}".format(ef, em, es),
                 "TANG" if up else "GIAM")
        chi_tiet = (
            "EMA{:<4}: {}\n"
            "EMA{:<4}: {}\n"
            "EMA{:<4}: {}\n"
        ).format(ef, ev["ema_fast"], em, ev["ema_mid"], es, ev["ema_slow"])
        subject = "{} {} EMA{}/{}/{} TRIPLE {} | {}".format(
            symbol, timeframe, ef, em, es, "TANG" if up else "GIAM", de_xuat)

    else:
        headline = "VUA CAT CHEO" if ev["type"] == "crossed" else "SAP CAT CHEO"
        che_do = "DUOI EMA{} (downtrend)".format(es) if not up else "TREN EMA{} (uptrend)".format(es)
        if ev["type"] == "crossed":
            eta_line = ""
            dong_luc = "vua cat"
        else:
            eta_txt = "~{:g} nen nua".format(ev["eta_bars"]) if ev.get("eta_bars") else "chua uoc tinh duoc"
            eta_line = "Du kien       : con {} se cham nhau (ngoai suy tuyen tinh - CHI tham\n                khao, gia co the doi chieu bat ky luc nao)\n".format(eta_txt)
            dong_luc = "sap"
        nhan_dinh = (
            "EMA{} va EMA{} deu dang nam {} - xac nhan xu huong {} da on dinh o khung\n"
            "lon hon. Trong boi canh do, EMA{} {} cat {} EMA{} - dong luc ngan han dang\n"
            "{} theo dung huong trend, cung co kha nang gia se tiep tuc di theo huong nay.\n"
            "De xuat: canh nhap {} theo trend, dat SL qua dinh/day gan nhat, KHONG vao\n"
            "nguoc huong trend lon (EMA{}/EMA{} so voi EMA{})."
        ).format(ef, em, che_do, "GIAM" if not up else "TANG",
                 ef, dong_luc, "XUONG DUOI" if not up else "LEN TREN", em,
                 "manh len" if not up else "manh len",
                 de_xuat, ef, em, es)
        chi_tiet = (
            "EMA{:<4}: {}\n"
            "EMA{:<4}: {}\n"
            "EMA{:<4}: {}\n"
            "Khoang cach EMA{}/EMA{}: {} x ATR\n"
            "{}"
        ).format(ef, ev["ema_fast"], em, ev["ema_mid"], es, ev["ema_slow"],
                 ef, em, ev["gap_atr"], eta_line)
        subject = "{} {} EMA{}/{} {} ({}) | {}".format(
            symbol, timeframe, ef, em, headline, "GIAM" if not up else "TANG", de_xuat)

    body = (
        "========================================\n"
        "   TRADING ASSISTANT AI - EMA TREND WATCH\n"
        "========================================\n\n"
        "Symbol        : {}\n"
        "Khung TG      : {}\n"
        "Tin hieu      : {}\n"
        "De xuat       : {}\n"
        "Gia hien tai  : {}\n"
        "Thoi diem     : {}\n"
        "Nen tin hieu  : {}\n\n"
        "---------- NHAN DINH THI TRUONG ----------\n"
        "{}\n\n"
        "---------- CHI TIET CHI BAO ----------\n"
        "{}\n"
        "========================================\n"
        "Luu y QUAN TRONG: day CHI la canh bao/nhan dinh ky thuat dua tren EMA{}/{}/{},\n"
        "KHONG phai tin hieu vao lenh co san Entry/SL/TP tu dong - ban tu quyet dinh va\n"
        "tu quan ly rui ro (SL/khoi luong) khi vao lenh tay.\n"
        "-- Trading Assistant AI (EMA Trend Watch)"
    ).format(symbol, timeframe, headline, de_xuat, ev["price"], now, ev["candle_time"],
             nhan_dinh, chi_tiet, ef, em, es)
    return subject, body
