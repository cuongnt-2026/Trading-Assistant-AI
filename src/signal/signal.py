from dataclasses import dataclass


@dataclass
class Signal:
    """Trading signal result."""

    action: str
    trend: str
    strength: str
    reason: str

    ema20: float
    ema50: float
    ema200: float

    adx: float

    # ----- Chi bao mo rong (Sprint 5) -----
    atr: float = 0.0
    rsi: float = 0.0

    # ----- Mau hinh nen (Sprint 6) -----
    pattern: str = ""
