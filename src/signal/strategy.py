"""
Chon chien luoc theo symbol.
  - Nhom XAU (vang) + BTC (crypto): breakout theo trend (danh thuan xu huong).
  - Con lai (forex): trend-following pullback.
Co the ep bang .env: GOLD_STRATEGY / CRYPTO_STRATEGY (trend|meanrev|breakout).
"""
import os


def strategy_for(symbol):
    s = (symbol or "").upper()
    if s.startswith("XAU"):
        return os.getenv("GOLD_STRATEGY", "breakout").strip().lower()
    if s.startswith("BTC"):
        return os.getenv("CRYPTO_STRATEGY", "breakout").strip().lower()
    return "trend"
