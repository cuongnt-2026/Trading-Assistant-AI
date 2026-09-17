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

# ----- RSI Divergence (phan ky gia/RSI) - bat dao chieu SOM HON EMA cross/Supertrend,
# vi khong can doi 2 duong MA (hoac gia vs EMA) cham nhau - chi can gia va RSI
# "khong dong thuan" tai 2 diem swing gan nhat:
#   Bullish (BUY):  gia tao DAY sau THAP hon day truoc (LL), nhung RSI tai day sau
#                   lai CAO hon RSI tai day truoc -> luc ban da yeu di -> de dao chieu tang.
#   Bearish (SELL): gia tao DINH sau CAO hon dinh truoc (HH), nhung RSI tai dinh sau
#                   lai THAP hon RSI tai dinh truoc -> luc mua da yeu di -> de dao chieu giam.
DIV_PIVOT = int(os.getenv("DIV_PIVOT", "3"))            # so nen 2 ben de xac dinh dinh/day swing
DIV_LOOKBACK = int(os.getenv("DIV_LOOKBACK", "60"))     # cua so tim phan ky
DIV_RSI_PERIOD = int(os.getenv("DIV_RSI_PERIOD", "14")) # chu ky RSI dung de so sanh
DIV_MIN_RSI_DIFF = float(os.getenv("DIV_MIN_RSI_DIFF", "3"))  # RSI phai lech >= x diem moi tinh la phan ky that

# ----- Bollinger Squeeze Breakout (NGUOC voi Bollinger Mean Reversion dang co: o day
# TRADE THEO huong pha vo, khong fade lai) - bat cac cu no bien do sau khi bien Bollinger
# "that co lai" (squeeze) - thoi diem thi truong tich luy truoc khi di manh.
SQZ_BB_PERIOD = int(os.getenv("SQZ_BB_PERIOD", "20"))       # chu ky Bollinger (ngan hon ban Mean Reversion)
SQZ_BB_MULT = float(os.getenv("SQZ_BB_MULT", "2.0"))         # so lan do lech chuan cho bien tren/duoi
SQZ_LOOKBACK = int(os.getenv("SQZ_LOOKBACK", "120"))         # so nen lich su dung de xep hang do rong bien
SQZ_PERCENTILE = float(os.getenv("SQZ_PERCENTILE", "20"))    # do rong bien phai thuoc nhom hep nhat x% gan day
SQZ_BREAKOUT_CLOSE = float(os.getenv("SQZ_BREAKOUT_CLOSE", "0.5"))  # nen breakout: than nen >= 50% bien do nen (dong manh)

# ----- EMA Trend Watch (thay the EMA Cross Watch cu - EMA20/50/200 loc theo che do
# EMA200 de giam nhieu, chi ap dung XAUUSD M15 - yeu cau CuongNT 2026-09-14, xem
# src/signal/ema_trend_watcher.py) -----
EMATREND_EMA_FAST = int(os.getenv("EMATREND_EMA_FAST", "20"))
EMATREND_EMA_MID = int(os.getenv("EMATREND_EMA_MID", "50"))
EMATREND_EMA_SLOW = int(os.getenv("EMATREND_EMA_SLOW", "200"))
# Nguong "sap cat cheo" / "reset" cho cap EMA20/50 (giong quy uoc EMACROSS_NEAR_ATR/
# RESET_ATR cu, tach constant rieng de tinh chinh doc lap voi bo EMA Cross cu da tat).
EMATREND_NEAR_ATR = float(os.getenv("EMATREND_NEAR_ATR", "0.3"))
EMATREND_RESET_ATR = float(os.getenv("EMATREND_RESET_ATR", "0.6"))
# Nguong hoi tu cho CA 3 duong (tin hieu "triple") + so nen cho sau khi hoi tu de
# xac nhan thu tu xep hang cuoi cung (mac dinh 3 nen, dung y "3 nen vua cat qua").
EMATREND_TRIPLE_NEAR_ATR = float(os.getenv("EMATREND_TRIPLE_NEAR_ATR", "0.3"))
EMATREND_TRIPLE_CONFIRM_BARS = int(os.getenv("EMATREND_TRIPLE_CONFIRM_BARS", "3"))
# Cham "dung/sai" cho tin hieu EMA Trend Watch (xem src/signal/ema_trend_tracker.py)
# theo kieu "lenh ao" co SL/TP tinh theo CAU TRUC gia + nen gan nhat (swing high/
# low), KHONG dung 1 boi so ATR co dinh cho SL - theo phan hoi CuongNT (2026-09-16,
# cap nhat lan 2): SL/TP phai tinh theo cau truc, dung LAI dung logic
# RiskManager.dynamic_levels() dang dung cho lenh THAT (xem src/trade/risk_manager.py)
# de nhat quan trong toan bo du an:
#   SL_ao = swing high/low gan nhat (EMATREND_EVAL_SWING_LOOKBACK nen) +/- dem ATR
#           (EMATREND_EVAL_SL_ATR_BUFFER), nhung KHONG duoc gan hon
#           EMATREND_EVAL_MIN_RISK_ATR x ATR (san rui ro toi thieu, tranh SL qua sat
#           bi quet rau nen ngay lap tuc).
#   TP_ao = khang cu/ho tro doi dien gan nhat (EMATREND_EVAL_TP_LOOKBACK nen) NEU no
#           cho RR >= EMATREND_EVAL_RR; neu khong (cau truc qua gan hoac khong co) ->
#           ep TP_ao = risk x EMATREND_EVAL_RR (san R:R toi thieu).
# EMATREND_EVAL_RR: luc dau CuongNT muon >= 2 ("dung phai kho hon sai"), sau do
# (2026-09-16, cap nhat lan 3) doi lai ve 1.0 (thang la tinh "dung", khong doi hoi
# "an" nhieu hon "thua" nua), roi CHINH LAI lan cuoi thanh 1.2 (2026-09-16, cap
# nhat lan 4) de bu spread/phi giao dich - "hoa von that" trong thuc te can TP_ao
# xa hon SL_ao mot chut, khong phai dung 1:1, moi tinh la "thang that". SL/TP van
# tinh theo cau truc nhu tren, chi doi muc R:R toi thieu.
EMATREND_EVAL_SWING_LOOKBACK = int(os.getenv("EMATREND_EVAL_SWING_LOOKBACK", "5"))
EMATREND_EVAL_SL_ATR_BUFFER = float(os.getenv("EMATREND_EVAL_SL_ATR_BUFFER", "0.5"))
EMATREND_EVAL_MIN_RISK_ATR = float(os.getenv("EMATREND_EVAL_MIN_RISK_ATR", "1.0"))
EMATREND_EVAL_TP_LOOKBACK = int(os.getenv("EMATREND_EVAL_TP_LOOKBACK", "40"))
EMATREND_EVAL_RR = float(os.getenv("EMATREND_EVAL_RR", "1.2"))
# Qua so nen nay (tren M15) ma van chua cham SL_ao/TP_ao nao -> tinh "het_han" (khong
# ket luan duoc, khong tinh vao ty le dung/sai). Mac dinh 96 nen ~ 1 ngay.
EMATREND_EVAL_MAX_BARS = int(os.getenv("EMATREND_EVAL_MAX_BARS", "96"))

# EMA Pullback (chien luoc vao lenh THAT - xem src/signal/ema_pullback_engine.py va
# docstring EMAPULLBACK_ trong src/core/config.py):
#   H1 (xu huong): so nen "doc" EMA20 dung sau bao nhieu nen (vd tang thi EMA20 hien
#   tai phai > EMA20 cach day EMAPULLBACK_SLOPE_LOOKBACK nen).
EMAPULLBACK_SLOPE_LOOKBACK = int(os.getenv("EMAPULLBACK_SLOPE_LOOKBACK", "3"))
# Khoang cach toi thieu giua EMA20-EMA50 tren H1 (boi so ATR14 H1) - EMA dinh sat
# nhau du dung thu tu van la dau hieu sap sideway/dao chieu, nen dung ngoai.
EMAPULLBACK_SPACING_ATR_MULT = float(os.getenv("EMAPULLBACK_SPACING_ATR_MULT", "1.0"))
# M15 (diem vao): gia (low cho BUY / high cho SELL) duoc tinh la "da hoi ve" 1 trong
# EMA20/50/100 M15 neu cach EMA do <= boi so ATR14 M15 nay.
EMAPULLBACK_PULLBACK_ATR = float(os.getenv("EMAPULLBACK_PULLBACK_ATR", "0.3"))
# So nen M15 gan nhat (tinh ca nen hien tai) duoc xet la "vua hoi ve" EMA - tranh bo
# lo neu gia cham EMA 1-2 nen truoc roi nen xac nhan moi toi.
EMAPULLBACK_PULLBACK_LOOKBACK = int(os.getenv("EMAPULLBACK_PULLBACK_LOOKBACK", "3"))

# EMA50 Close (chien luoc CHI 1 duong EMA50, y tuong CuongNT 2026-09-17, dung
# de BACKTEST xem gia co "chay dung xu huong thi truong" theo 1 EMA don gian
# hay khong - xem src/signal/ema50_close_engine.py):
#   Luat goc: dong cua DUT KHOAT tren EMA50 => BUY; DUT KHOAT duoi EMA50 => SELL.
# EMA50CLOSE_BUFFER_ATR: gia phai vuot EMA50 xa hon (boi so ATR14) khoang nay
# moi tinh la "dut khoat" - dat "0" de test dung 100% luat goc (chi so sanh
# gia dong cua thuan tuy, khong doi hoi khoang cach toi thieu).
EMA50CLOSE_BUFFER_ATR = float(os.getenv("EMA50CLOSE_BUFFER_ATR", "0.15"))
# EMA50CLOSE_REQUIRE_FULL_BODY: "1" = doi hoi CA than nen (open VA close) nam
# gon 1 phia EMA50 (dung tinh than "than nen dong cua tren/duoi EMA50" CuongNT
# noi), khong chi rieng gia dong cua - tranh nhan 1 nen do du (mo cua duoi EMA,
# dong cua nhinh hon EMA50 mot chut) la "dut khoat". Dat "0" de chi xet gia
# dong cua nhu luat goc.
EMA50CLOSE_REQUIRE_FULL_BODY = os.getenv("EMA50CLOSE_REQUIRE_FULL_BODY", "1").strip() not in ("0", "false", "")
# EMA50CLOSE_ADX_MIN: chi nhan tin hieu khi ADX14 >= muc nay (thi truong dang
# THUC SU trending, khong phai sideway) - bo sung SAU KHI backtest mau lon
# (20000 nen) cho thay ca 3 khung deu PF ~1.0-1.13 (qua thap, nhieu whipsaw
# luc sideway). Dat "0" de tat han bo loc nay (giu dung ban dau, khong loc
# ADX). Muc 20 giong ADX_MIN chung cua he thong (xem SignalEngine).
EMA50CLOSE_ADX_MIN = float(os.getenv("EMA50CLOSE_ADX_MIN", "20"))
