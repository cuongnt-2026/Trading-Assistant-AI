"""
Trade Constants
"""

import os
try:
    from src.core.config import load_env_file
    load_env_file()
except Exception:
    pass


# (Cu) Risk Reward - khong con ep cung, chi dung lam RR toi thieu ben duoi.
RISK_REWARD = 2.0

# So nen de do Swing High / Swing Low khi dat SL
SWING_LOOKBACK = 5

# ----- SL/TP DONG (Sprint 7 nang cap) -----
ATR_SL_BUFFER = 0.5        # SL = swing -/+ 0.5*ATR (dem chong quet rau nen)
TP_STRUCT_LOOKBACK = 40    # so nen do khang cu/ho tro gan nhat lam TP
TP_ATR_FALLBACK = 3.0      # neu khong co cau truc -> TP = entry +/- 3*ATR
MIN_RR = 1.2               # RR toi thieu (khong nhan lenh RR qua thap)
TRAIL_ATR_MULT = 1.5       # khoang cach trailing stop de nghi = 1.5*ATR

# ----- Position sizing co gian theo do tin cay -----
DEFAULT_RISK_PERCENT = 1.0
RISK_MIN_PERCENT = 0.5     # confidence thap -> risk it
RISK_MAX_PERCENT = 1.5     # confidence cao -> risk nhieu (trong tran)

# ---------------------------------------------------------------------------
# Gia tri 1 diem gia (1.0 price move) cho MOI 1.0 lot (uoc tinh, tuy broker)
# ---------------------------------------------------------------------------
POINT_VALUE_PER_LOT = {
    "XAUUSD": 100.0,
    "BTCUSD": 1.0,
    "BTCJPY": 1.0,
    "BTCEUR": 1.0,
    "BTCGBP": 1.0,
}
DEFAULT_POINT_VALUE_PER_LOT = 100000.0


def point_value_per_lot(symbol):
    return POINT_VALUE_PER_LOT.get(symbol, DEFAULT_POINT_VALUE_PER_LOT)

# TP theo boi so RR co dinh (0 = giu TP dong theo cau truc).
# TP_RR_TARGET nho (0.8-1.2) -> win rate CAO hon nhung an it hon moi lenh.
TP_RR_TARGET = float(os.getenv("TP_RR_TARGET", "0"))

# Vao lenh CHO (limit): lui ve phia EMA bao nhieu ATR de co gia tot hon
ENTRY_PULLBACK_ATR = float(os.getenv("ENTRY_PULLBACK_ATR", "0.5"))

# Breakout: chot loi = BO_RR lan rui ro (tha loi chay, bu win rate thap)
BO_RR = float(os.getenv("BO_RR", "2.5"))
