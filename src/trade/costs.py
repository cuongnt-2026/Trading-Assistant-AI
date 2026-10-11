"""
Chi phi giao dich (spread) de tinh R THAT thay vi R "tren giay".

Truoc 2026-10-11, r_result = +rr (WIN) / -1 (LOSS) - CHUA tru spread. Voi lenh SL
rat ngan (vd Bollinger EURUSD M15, SL ~3 pip, spread ~1.2 pip) spread an ~0.3R
moi lenh, nen Tong R tren dashboard dep hon thuc te rat nhieu.

Mo hinh (bao thu, don gian): moi lenh ton 1 lan spread (mua o Ask / ban o Bid),
tinh ra R bang spread / risk (risk = |entry - sl|):
    WIN  -> rr - spread/risk
    LOSS -> -1 - spread/risk
Gia tri spread (don vi GIA, khong phai pip) chinh qua bien moi truong SPREADS,
vd SPREADS="XAUUSD:0.35,EURUSD:0.00012". Symbol khong co trong bang -> 0.
"""
import os

_DEFAULT_SPREADS = ("XAUUSD:0.35,EURUSD:0.00012,GBPUSD:0.00015,USDJPY:0.015,"
                    "USDCHF:0.00015,AUDUSD:0.00015,USDCAD:0.0002,NZDUSD:0.00018")


def _parse(raw):
    out = {}
    for part in (raw or "").split(","):
        if ":" in part:
            k, v = part.split(":", 1)
            try:
                out[k.strip().upper()] = float(v)
            except ValueError:
                pass
    return out


SPREADS = _parse(os.getenv("SPREADS", _DEFAULT_SPREADS))


def spread_of(symbol):
    return SPREADS.get((symbol or "").upper(), 0.0)


def spread_r(symbol, entry, sl):
    """Spread quy ra R cho 1 lenh (0 neu thieu du lieu)."""
    try:
        risk = abs(float(entry) - float(sl))
    except (TypeError, ValueError):
        return 0.0
    return spread_of(symbol) / risk if risk > 0 else 0.0
