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
# ----- Market Structure (HH/HL - mua day trend tang / ban dinh trend giam) -----
STRUCT_PIVOT = int(os.getenv("STRUCT_PIVOT", "3"))       # so nen 2 ben de xac dinh dinh/day
STRUCT_LOOKBACK = int(os.getenv("STRUCT_LOOKBACK", "90"))# cua so danh gia cau truc
STRUCT_SR_TOL = float(os.getenv("STRUCT_SR_TOL", "0.8")) # gom vung S/R: cach nhau <= x*ATR
STRUCT_ADX_MIN = float(os.getenv("STRUCT_ADX_MIN", "22"))# chi vao khi ADX >= (trend that, khong nhieu)

# ----- Bollinger Band Mean Reversion (bien EMA + RSI cuc doan, theo Babypips) -----
BOLL_PERIOD = int(os.getenv("BOLL_PERIOD", "50"))       # chu ky EMA giua + do lech chuan
BOLL_MULT = float(os.getenv("BOLL_MULT", "2.0"))         # so lan do lech chuan cho bien tren/duoi
BOLL_RSI_PERIOD = int(os.getenv("BOLL_RSI_PERIOD", "9")) # RSI ngan de bat cuc doan
BOLL_RSI_OB = float(os.getenv("BOLL_RSI_OB", "75"))       # RSI qua mua -> SELL
BOLL_RSI_OS = float(os.getenv("BOLL_RSI_OS", "25"))       # RSI qua ban -> BUY
BOLL_SL_ATR = float(os.getenv("BOLL_SL_ATR", "0.5"))      # dem SL ngoai dinh/day nen tin hieu

# ----- London Breakout (pha bien do phien A khi London mo cua) -----
LB_ASIA_START = int(os.getenv("LB_ASIA_START", "0"))       # gio bat dau do bien do phien A
LB_ASIA_END = int(os.getenv("LB_ASIA_END", "8"))            # gio ket thuc phien A / London mo cua
LB_ENTRY_END = int(os.getenv("LB_ENTRY_END", "11"))         # chi vao lenh truoc gio nay
LB_BUFFER_ATR = float(os.getenv("LB_BUFFER_ATR", "0.1"))    # dem ngoai bien do (thay "3-5 pip" goc)
LB_MIN_RANGE_ATR = float(os.getenv("LB_MIN_RANGE_ATR", "0.5"))  # bo qua neu bien do qua hep
LB_MAX_RANGE_ATR = float(os.getenv("LB_MAX_RANGE_ATR", "4.0"))  # bo qua neu bien do qua rong

# ----- EMA Cross Watch (CANH BAO rieng, KHONG phai chien luoc vao lenh - chi theo doi
# EMA nhanh/cham tren nhieu cap/khung, bao mail khi SAP hoac VUA cat cheo nhau)
# Da doi 100 -> 50 cho EMA_SLOW (2025-09): voi 20/100, EMA100 qua "nang", khi gia giat
# manh (vd XAUUSD M15) thi luc bao "sap/vua cat cheo" gia da di qua rat xa diem cat that
# tren chart - mail toi thi da tre, khong con kip lam gi. 20/50 phan ung nhanh hon nhieu,
# gia luc bao gan voi diem cat that hon han (test thuc te tren chart: 20/100 bao tre ~vai
# chuc USD, 20/50 bat duoc ngay tai diem cat). Danh doi: se co nhieu mail hon (kem "chac
# chan" hon 20/100) trong luc gia di ngang/rung lac - chap nhan duoc vi day chi la canh
# bao tham khao, khong phai lenh tu dong. -----
EMACROSS_EMA_FAST = int(os.getenv("EMACROSS_EMA_FAST", "20"))
EMACROSS_EMA_SLOW = int(os.getenv("EMACROSS_EMA_SLOW", "50"))
# Khoang cach |EMA_fast - EMA_slow| <= x*ATR VA dang hep dan lai -> coi la "SAP cat cheo"
EMACROSS_NEAR_ATR = float(os.getenv("EMACROSS_NEAR_ATR", "0.3"))
# Khoang cach no rong lai vuot muc nay -> "quen" lan sap-cheo cu, cho phep bao lai tu dau
# lan sau ap sat nhau (tranh bao 1 lan roi im re neu gia chi lang vang gan nguong mai).
EMACROSS_RESET_ATR = float(os.getenv("EMACROSS_RESET_ATR", "0.6"))
# So nen dung de do do doc (goc) cua duong EMA, chuan hoa theo ATR (xem ema_cross_watcher.py)
EMACROSS_ANGLE_LOOKBACK = int(os.getenv("EMACROSS_ANGLE_LOOKBACK", "5"))
