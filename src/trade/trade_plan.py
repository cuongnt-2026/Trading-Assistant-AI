from dataclasses import dataclass
from typing import Optional


@dataclass
class TradePlan:
    """Trading Plan Model (SL/TP dong)."""

    action: str

    entry_price: float
    stop_loss: float
    take_profit: float

    risk_reward: str      # chuoi hien thi, vd "1 : 1.8"
    reason: str

    entry_type: str = "market"   # 'market' hoac 'limit' (lenh cho)

    rr_ratio: float = 0.0
    risk_points: float = 0.0
    reward_points: float = 0.0
    risk_percent: float = 0.0

    # SL/TP dong
    sl_source: str = ""        # vd "swing-ATR"
    tp_source: str = ""        # vd "structure" / "atr" / "structure+minRR"
    trail_distance: float = 0.0  # khoang cach trailing stop de nghi

    # Chi co khi biet so du tai khoan (uoc tinh)
    risk_amount: Optional[float] = None
    lot_size: Optional[float] = None
    expected_profit: Optional[float] = None
