"""
Signal logger - luu lich su tin hieu ra file.
- reports/signals.json : du lieu tho.
- dashboard/data.js     : du lieu cho dashboard.
"""

import os
import json
from datetime import datetime

from src.signal.constants import BUY, SELL


class SignalLogger:
    def __init__(self, config, max_records: int = 800):
        self.config = config
        self.max_records = max_records
        self.records = []
        self.json_path = os.path.join(config.reports_dir, "signals.json")
        self.dashboard_path = config.dashboard_data
        self._ensure_dirs()
        self._load()

    def _ensure_dirs(self):
        os.makedirs(os.path.dirname(self.json_path) or ".", exist_ok=True)
        os.makedirs(os.path.dirname(self.dashboard_path) or ".", exist_ok=True)

    def _load(self):
        if os.path.exists(self.json_path):
            try:
                with open(self.json_path, encoding="utf-8") as f:
                    self.records = json.load(f)
            except Exception:
                self.records = []

    def add(self, signal, candle, notified, symbol=None, timeframe=None,
            recommendation=None, trade_plan=None):
        record = {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "candle_time": str(candle.time),
            "symbol": symbol or self.config.symbol,
            "timeframe": timeframe or "",
            "action": signal.action,
            "trend": signal.trend,
            "strength": signal.strength,
            "price": round(candle.close, 5),
            "ema20": round(signal.ema20, 5),
            "ema50": round(signal.ema50, 5),
            "ema200": round(signal.ema200, 5),
            "adx": round(signal.adx, 2),
            "atr": round(getattr(signal, "atr", 0.0), 5),
            "rsi": round(getattr(signal, "rsi", 0.0), 2),
            "pattern": getattr(signal, "pattern", ""),
            "reason": signal.reason,
            "notified": notified,
        }

        if recommendation is not None:
            record["recommendation"] = recommendation.action
            record["confidence"] = recommendation.confidence
            record["confidence_label"] = recommendation.label
            record["rec_reasons"] = recommendation.reasons

        if trade_plan is not None:
            record["trade_plan"] = {
                "entry": trade_plan.entry_price,
                "stop_loss": trade_plan.stop_loss,
                "take_profit": trade_plan.take_profit,
                "risk_reward": trade_plan.risk_reward,
                "rr_ratio": trade_plan.rr_ratio,
                "risk_points": trade_plan.risk_points,
                "reward_points": trade_plan.reward_points,
                "risk_percent": trade_plan.risk_percent,
                "sl_source": trade_plan.sl_source,
                "tp_source": trade_plan.tp_source,
                "trail_distance": trade_plan.trail_distance,
                "risk_amount": trade_plan.risk_amount,
                "lot_size": trade_plan.lot_size,
                "expected_profit": trade_plan.expected_profit,
            }

        # Trang thai ket qua (cham theo thi truong chay): OPEN khi moi tao
        if signal.action in (BUY, SELL) and trade_plan is not None:
            record["outcome"] = "OPEN"

        self.records.append(record)
        if len(self.records) > self.max_records:
            self.records = self.records[-self.max_records:]
        self.save()

    def save(self):
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(self.records, f, ensure_ascii=False, indent=2)
        payload = {
            "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "symbol": self.config.symbol,
            "signals": self.records,
        }
        with open(self.dashboard_path, "w", encoding="utf-8") as f:
            f.write("window.TA_DATA = ")
            json.dump(payload, f, ensure_ascii=False, indent=2)
            f.write(";\n")
