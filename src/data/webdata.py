# -*- coding: utf-8 -*-
"""
WebData - lay nen OHLC tu Twelve Data (API free) thay cho MT5.
Dung cho ban chay tren cloud (GitHub Actions), khong can MT5/Windows.
"""
import os
import time
import json
import urllib.request
import urllib.parse
from datetime import datetime

from src.market.candle import Candle

_TF_MAP = {"M1": "1min", "M5": "5min", "M15": "15min", "M30": "30min",
           "H1": "1h", "H2": "2h", "H4": "4h", "D1": "1day"}

_API = "https://api.twelvedata.com/time_series"
_MIN_INTERVAL_SEC = float(os.getenv("WEBDATA_THROTTLE", "8"))  # 8 req/phut (free)
_last_call = [0.0]


def _fx_symbol(sym):
    """EURUSD -> EUR/USD ; giu nguyen neu da co '/'."""
    s = sym.upper()
    if "/" in s:
        return s
    if len(s) == 6:
        return s[:3] + "/" + s[3:]
    return s


class WebData:

    @staticmethod
    def get_candles(symbol, timeframe, count=250):
        interval = _TF_MAP.get(str(timeframe).upper())
        if interval is None:
            raise ValueError("Khung khong ho tro: %s" % timeframe)
        key = os.getenv("TWELVEDATA_API_KEY", "").strip()
        if not key:
            raise RuntimeError("Thieu TWELVEDATA_API_KEY")

        # throttle de khong vuot 8 req/phut
        wait = _MIN_INTERVAL_SEC - (time.time() - _last_call[0])
        if wait > 0:
            time.sleep(wait)

        q = urllib.parse.urlencode({
            "symbol": _fx_symbol(symbol), "interval": interval,
            "outputsize": count, "apikey": key, "format": "JSON",
            "timezone": "UTC",
        })
        url = _API + "?" + q
        req = urllib.request.Request(url, headers={"User-Agent": "trading-assistant-ai"})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read().decode("utf-8"))
        _last_call[0] = time.time()

        if data.get("status") != "ok" or "values" not in data:
            raise RuntimeError("API loi: %s" % data.get("message", data))

        rows = list(reversed(data["values"]))  # dao ve cu -> moi
        candles = []
        for v in rows:
            ts = v["datetime"]
            try:
                t = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                t = datetime.strptime(ts, "%Y-%m-%d")
            candles.append(Candle(
                time=t, open=float(v["open"]), high=float(v["high"]),
                low=float(v["low"]), close=float(v["close"]),
                volume=int(float(v.get("volume", 0) or 0)),
            ))
        return candles
