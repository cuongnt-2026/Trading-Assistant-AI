"""
Chon chien luoc theo symbol.
  - Nhom XAU (vang & cac cap cheo vang): mean-reversion (danh nguoc ve trung binh)
  - Con lai: trend-following (thuan xu huong)
Co the ep bang .env: GOLD_STRATEGY=trend|meanrev
"""
import os


def strategy_for(symbol):
    s = (symbol or "").upper()
    if s.startswith("XAU"):
        return os.getenv("GOLD_STRATEGY", "meanrev").strip().lower()
    return "trend"
