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
