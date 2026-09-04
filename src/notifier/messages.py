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
    """Email CANH BAO EMA nhanh/cham (mac dinh 20/100) SAP hoac VUA cat cheo nhau.
    KHONG phai tin hieu vao lenh (khong co Entry/SL/TP) - chi de theo doi thu cong.
    `ev` la dict tra ve tu EmaCrossWatcher.check()."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    up = ev["direction"] == "up"
    dir_txt = "TANG (EMA nhanh cat LEN TREN EMA cham)" if up else "GIAM (EMA nhanh cat XUONG DUOI EMA cham)"
    dir_short = "TANG" if up else "GIAM"

    if ev["type"] == "crossed":
        headline = "VUA CAT CHEO"
        eta_line = ""
    else:
        headline = "SAP CAT CHEO"
        eta_txt = "~{:g} nen nua".format(ev["eta_bars"]) if ev.get("eta_bars") else "chua uoc tinh duoc"
        eta_line = "Du kien       : con {} se cham nhau (ngoai suy tuyen tinh tu toc do hep\n                lai hien tai - CHI tham khao, gia co the doi chieu bat ky luc nao)\n".format(eta_txt)

    subject = "{} {} EMA {} {} | gap {}xATR".format(
        symbol, timeframe, headline, dir_short, ev["gap_atr"])

    body = (
        "========================================\n"
        "   TRADING ASSISTANT AI - EMA CROSS WATCH\n"
        "========================================\n\n"
        "Symbol        : {}\n"
        "Khung TG      : {}\n"
        "Tin hieu      : {} - {}\n"
        "Gia hien tai  : {}\n"
        "Thoi diem     : {}\n"
        "Nen tin hieu  : {}\n\n"
        "---------- CHI TIET ----------\n"
        "Khoang cach EMA hien tai : {} x ATR\n"
        "{}"
        "Do doc EMA nhanh (5 nen gan nhat): {} do\n"
        "Do doc EMA cham  (5 nen gan nhat): {} do\n"
        "  (Quy uoc do de so sanh giua cac symbol/khung: doc ~1*ATR/nen ~= 45 do; cang\n"
        "   gan 90 do = xu huong dang manh/dot ngot, cang gan 0 do = di ngang phang.\n"
        "   Chenh lech giua 2 goc nay CANG LON -> cu cat cheo cang 'dut khoat' (dang tin\n"
        "   cay hon); chenh lech nho/2 duong gan nhu song song -> de bi nhieu/fake.)\n\n"
        "========================================\n"
        "Luu y QUAN TRONG: day CHI la canh bao ky thuat (EMA giao nhau), KHONG phai tin\n"
        "hieu vao lenh co san Entry/SL/TP - ban tu quyet dinh dua tren cac yeu to khac\n"
        "(xu huong khung lon hon, tin tuc, khoi luong, v.v).\n"
        "-- Trading Assistant AI (EMA Cross Watch)"
    ).format(symbol, timeframe, headline, dir_txt, ev["price"], now, ev["candle_time"],
             ev["gap_atr"], eta_line, ev["angle_fast"], ev["angle_slow"])
    return subject, body
