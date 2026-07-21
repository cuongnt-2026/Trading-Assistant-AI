"""
Signal constants (co the tinh chinh qua .env).
"""

import os

# Nap .env truoc khi doc bien (neu khong cac knob trong .env se bi bo qua)
try:
    from src.core.config import load_env_file
    load_env_file()
except Exception:
    pass

BUY = "BUY"
SELL = "SELL"
NO_TRADE = "NO_TRADE"

UPTREND = "UPTREND"
DOWNTREND = "DOWNTREND"
SIDEWAYS = "SIDEWAYS"

STRONG = "STRONG"
WEAK = "WEAK"

# Nguong ADX toi thieu de coi la co xu huong
ADX_MIN = float(os.getenv("ADX_MIN", "20"))

# Do rong pullback tinh theo ATR (cang nho cang chat)
PULLBACK_ATR_MULT = float(os.getenv("PULLBACK_ATR_MULT", "1.0"))

# Bat buoc phai co nen xac nhan (engulfing/pin bar) khong?
REQUIRE_PATTERN = os.getenv("REQUIRE_PATTERN", "0").strip() in ("1", "true", "True")

# ----- Mean-Reversion (danh nguoc ve trung binh) - dung cho nhom XAU -----
MR_STRETCH_ATR = float(os.getenv("MR_STRETCH_ATR", "1.8"))  # gia cach EMA >= x*ATR (sau: chi fade cu keo cang manh)
MR_RSI_OS = float(os.getenv("MR_RSI_OS", "30"))             # RSI qua ban -> BUY
MR_RSI_OB = float(os.getenv("MR_RSI_OB", "70"))             # RSI qua mua -> SELL
MR_ADX_MAX = float(os.getenv("MR_ADX_MAX", "25"))  # CHI danh khi ADX < muc nay (KHONG fade trend manh)

MR_CONFIRM = os.getenv("MR_CONFIRM", "1").strip() not in ("0", "false", "")  # yeu cau nen dao chieu

# ----- Breakout theo trend (nhom XAU + BTC) -----
BO_LOOKBACK = int(os.getenv("BO_LOOKBACK", "20"))   # pha vo dinh/day cua N nen
BO_ADX_MIN = float(os.getenv("BO_ADX_MIN", "18"))   # chi danh khi co xu huong
# Loc chat luong breakout:
BO_STRONG_CLOSE = float(os.getenv("BO_STRONG_CLOSE", "0.6"))  # nen breakout phai dong manh (>=60% bien do theo huong)
BO_SESSION_ONLY = os.getenv("BO_SESSION_ONLY", "1").strip() not in ("0","false","")  # chi danh phien London+NY
BO_SESS_START = int(os.getenv("BO_SESS_START", "7"))   # gio UTC bat dau
BO_SESS_END = int(os.getenv("BO_SESS_END", "20"))     # gio UTC ket thuc
# Loc phien cho FX (trend): chi danh gio London+NY
FX_SESSION_ONLY = os.getenv("FX_SESSION_ONLY", "1").strip() not in ("0","false","")
FX_SESS_START = int(os.getenv("FX_SESS_START", "7"))
FX_SESS_END = int(os.getenv("FX_SESS_END", "20"))
# ----- Hai dinh / hai day (double top/bottom) -----
DBL_PIVOT = int(os.getenv("DBL_PIVOT", "3"))        # so nen 2 ben de xac dinh dinh/day swing
DBL_LOOKBACK = int(os.getenv("DBL_LOOKBACK", "60")) # cua so tim mo hinh
DBL_TOL_ATR = float(os.getenv("DBL_TOL_ATR", "0.6"))# 2 dinh/day lech nhau <= x*ATR moi tinh la bang nhau
DBL_MIN_SEP = int(os.getenv("DBL_MIN_SEP", "4"))    # 2 dinh/day cach nhau it nhat may nen
# ----- La co / co duoi nheo (flag / pennant) - tiep dien -----
FLAG_POLE_BARS = int(os.getenv("FLAG_POLE_BARS", "5"))     # so nen cua "can co" (cu tang/giam manh)
FLAG_POLE_ATR = float(os.getenv("FLAG_POLE_ATR", "3.0"))   # can co phai di >= x*ATR
FLAG_CONS_BARS = int(os.getenv("FLAG_CONS_BARS", "6"))     # so nen di ngang co lai
FLAG_CONS_MAX = float(os.getenv("FLAG_CONS_MAX", "0.6"))   # bien do di ngang <= x lan do dai can co
