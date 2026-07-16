from dataclasses import dataclass, field
from typing import List


@dataclass
class Recommendation:
    """
    Khuyến nghị của AI cho một tín hiệu.
    """

    action: str            # BUY / SELL / WAIT
    confidence: float      # 0 - 100 (%)
    label: str             # STRONG / MODERATE / LOW
    reasons: List[str] = field(default_factory=list)
