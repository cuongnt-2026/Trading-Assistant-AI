"""
AI Recommendation Engine (Sprint 8).

Tổng hợp các yếu tố kỹ thuật thành một điểm TIN CẬY (0-100%) + lý do.
Không phải machine learning; đây là hệ thống chấm điểm theo trọng số
(rule-based scoring), minh bạch và dễ kiểm chứng.

Trọng số:
    Trend (EMA alignment) : 25
    ADX (độ mạnh xu hướng): 25
    Pullback về EMA       : 15
    RSI (momentum)        : 15
    Mẫu hình nến          : 20
    --------------------------- Tổng = 100
"""

from src.signal.constants import BUY, SELL, NO_TRADE
from src.ai_review.recommendation import Recommendation


def _clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


class Recommender:

    @staticmethod
    def _direction(signal):
        """Hướng để chấm điểm: theo action; nếu WAIT thì theo trend."""
        if signal.action == BUY:
            return BUY
        if signal.action == SELL:
            return SELL
        if signal.ema20 > signal.ema50 > signal.ema200:
            return BUY
        if signal.ema20 < signal.ema50 < signal.ema200:
            return SELL
        return None

    @staticmethod
    def _trend_score(signal, direction):
        if direction == BUY:
            aligned = (signal.ema20 > signal.ema50) + (signal.ema50 > signal.ema200)
        else:
            aligned = (signal.ema20 < signal.ema50) + (signal.ema50 < signal.ema200)
        return 25.0 * aligned / 2.0

    @staticmethod
    def _adx_score(adx):
        # 20 -> 0đ, 40 -> 25đ
        return _clamp((adx - 20.0) / 20.0) * 25.0

    @staticmethod
    def _pullback_score(signal, candles):
        close = candles[-1].close
        atr = signal.atr if signal.atr else abs(close) * 0.001
        dist = min(abs(close - signal.ema20), abs(close - signal.ema50))
        # 0 ATR = sát EMA = full điểm; >=1.5 ATR = 0 điểm
        return _clamp(1.0 - (dist / atr) / 1.5) * 15.0

    @staticmethod
    def _rsi_score(rsi, direction):
        if direction == BUY:
            if rsi >= 70:
                return 4.0      # quá mua -> rủi ro
            if rsi >= 50:
                return 15.0
            if rsi >= 40:
                return 10.0
            return 5.0
        else:  # SELL
            if rsi <= 30:
                return 4.0      # quá bán -> rủi ro
            if rsi <= 50:
                return 15.0
            if rsi <= 60:
                return 10.0
            return 5.0

    @staticmethod
    def _pattern_score(pattern):
        p = (pattern or "").lower()
        if "engulfing" in p:
            return 20.0
        if "hammer" in p or "star" in p:
            return 14.0
        return 0.0

    @staticmethod
    def evaluate(signal, candles):
        """
        Trả về Recommendation cho tín hiệu.
        """
        direction = Recommender._direction(signal)

        if direction is None:
            return Recommendation(
                action="WAIT",
                confidence=0.0,
                label="LOW",
                reasons=["Không có xu hướng rõ ràng (EMA đan xen)"],
            )

        trend = Recommender._trend_score(signal, direction)
        adx = Recommender._adx_score(signal.adx)
        pull = Recommender._pullback_score(signal, candles)
        rsi = Recommender._rsi_score(signal.rsi, direction)
        patt = Recommender._pattern_score(signal.pattern)

        confidence = round(trend + adx + pull + rsi + patt, 1)

        reasons = []
        if trend >= 20:
            reasons.append("EMA xếp hàng chuẩn xu hướng")
        elif trend > 0:
            reasons.append("EMA xếp hàng một phần")
        if signal.adx > 25:
            reasons.append(f"ADX mạnh ({signal.adx:.1f})")
        else:
            reasons.append(f"ADX yếu ({signal.adx:.1f})")
        if pull >= 10:
            reasons.append("Giá pullback sát EMA")
        if patt > 0:
            reasons.append(f"Nến xác nhận: {signal.pattern}")
        else:
            reasons.append("Chưa có nến xác nhận")
        reasons.append(f"RSI {signal.rsi:.0f}")

        if confidence >= 75:
            label = "STRONG"
        elif confidence >= 55:
            label = "MODERATE"
        else:
            label = "LOW"

        # Action: chỉ khuyến nghị vào lệnh khi tín hiệu thực sự là BUY/SELL
        action = signal.action if signal.action in (BUY, SELL) else "WAIT"

        return Recommendation(
            action=action,
            confidence=confidence,
            label=label,
            reasons=reasons,
        )
