"""
Nhận diện mẫu hình nến (candlestick patterns) - Sprint 6.

Hàm nhận list Candle, xét 1-2 nến cuối. Trả về True/False.
"""


def _body(c):
    return abs(c.close - c.open)


def _range(c):
    return (c.high - c.low) or 1e-9


def _upper_wick(c):
    return c.high - max(c.open, c.close)


def _lower_wick(c):
    return min(c.open, c.close) - c.low


def is_bullish(c):
    return c.close > c.open


def is_bearish(c):
    return c.close < c.open


def is_bullish_engulfing(candles):
    """Nến xanh hiện tại 'nuốt' trọn thân nến đỏ trước đó."""
    if len(candles) < 2:
        return False
    prev, cur = candles[-2], candles[-1]
    return (
        is_bearish(prev)
        and is_bullish(cur)
        and cur.close >= prev.open
        and cur.open <= prev.close
        and _body(cur) > _body(prev)
    )


def is_bearish_engulfing(candles):
    """Nến đỏ hiện tại 'nuốt' trọn thân nến xanh trước đó."""
    if len(candles) < 2:
        return False
    prev, cur = candles[-2], candles[-1]
    return (
        is_bullish(prev)
        and is_bearish(cur)
        and cur.open >= prev.close
        and cur.close <= prev.open
        and _body(cur) > _body(prev)
    )


def is_hammer(candles):
    """Pin bar tăng (búa): râu dưới dài >= 2x thân, râu trên ngắn."""
    c = candles[-1]
    body = _body(c)
    if body <= 0:
        return False
    return (
        _lower_wick(c) >= 2 * body
        and _upper_wick(c) <= body
        and body <= 0.4 * _range(c)
    )


def is_shooting_star(candles):
    """Pin bar giảm (sao băng): râu trên dài >= 2x thân, râu dưới ngắn."""
    c = candles[-1]
    body = _body(c)
    if body <= 0:
        return False
    return (
        _upper_wick(c) >= 2 * body
        and _lower_wick(c) <= body
        and body <= 0.4 * _range(c)
    )


def bullish_pattern(candles):
    """Trả tên mẫu hình tăng nếu có, ngược lại ''. """
    if is_bullish_engulfing(candles):
        return "Bullish Engulfing"
    if is_hammer(candles):
        return "Hammer"
    return ""


def bearish_pattern(candles):
    """Trả tên mẫu hình giảm nếu có, ngược lại ''. """
    if is_bearish_engulfing(candles):
        return "Bearish Engulfing"
    if is_shooting_star(candles):
        return "Shooting Star"
    return ""
