"""
Application configuration.
Doc cau hinh tu file .env (neu co) + bien moi truong.
"""

import os


def load_env_file(path: str = ".env") -> None:
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


def _split(raw):
    return [x.strip() for x in raw.split(",") if x.strip()]


def _parse_pairs(raw):
    """'EURUSD:H4,USDJPY:H4' -> [(EURUSD,H4), (USDJPY,H4)] (bo qua muc sai dinh dang)."""
    out = []
    for item in _split(raw):
        if ":" in item:
            s, t = item.split(":", 1)
            s, t = s.strip(), t.strip()
            if s and t:
                out.append((s, t))
    return out


class Config:
    """Cau hinh toan cuc cho Trading Assistant AI."""

    def __init__(self, env_path: str = ".env"):
        load_env_file(env_path)

        # ----- Gmail / SMTP -----
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "465"))
        self.gmail_user = os.getenv("GMAIL_USER", "").strip()
        self.gmail_app_password = os.getenv("GMAIL_APP_PASSWORD", "").strip()
        self.mail_to = os.getenv("MAIL_TO", self.gmail_user).strip()

        # ----- Kenh thong bao -----
        raw_channels = os.getenv("NOTIFIER_CHANNEL", "email").lower()
        self.notifier_channels = _split(raw_channels)
        self.notifier_channel = self.notifier_channels[0]

        # ----- Telegram / ntfy -----
        self.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
        self.ntfy_server = os.getenv("NTFY_SERVER", "https://ntfy.sh").strip()
        self.ntfy_topic = os.getenv("NTFY_TOPIC", "").strip()

        # ----- Nhom tai san + khung thoi gian -----
        gc_syms = os.getenv("SYMBOLS_GOLD_CRYPTO",
                            "XAUUSD,BTCUSD,BTCJPY,BTCEUR,BTCGBP")
        gc_tfs = os.getenv("TIMEFRAMES_GOLD_CRYPTO", "M15,M30")
        fx_syms = os.getenv("SYMBOLS_FOREX",
                            "EURUSD,GBPUSD,USDJPY,AUDUSD,USDCAD,USDCHF,NZDUSD")
        fx_tfs = os.getenv("TIMEFRAMES_FOREX", "M30,H1")

        self.groups = {
            "GOLD_CRYPTO": {"symbols": _split(gc_syms), "timeframes": _split(gc_tfs)},
            "FOREX": {"symbols": _split(fx_syms), "timeframes": _split(fx_tfs)},
        }

        self.watchlist = []
        for g in self.groups.values():
            for sym in g["symbols"]:
                for tf in g["timeframes"]:
                    self.watchlist.append((sym, tf))

        self.symbols = list(dict.fromkeys(s for s, _ in self.watchlist))
        self.symbol = self.symbols[0] if self.symbols else "XAUUSD"

        # ----- Monitor -----
        self.candle_count = int(os.getenv("CANDLE_COUNT", "250"))
        self.poll_interval = int(os.getenv("POLL_INTERVAL_SECONDS", "30"))
        self.notify_on = os.getenv("NOTIFY_ON", "change").lower()

        # ----- Loc da khung (chong tre) -----
        self.use_mtf = os.getenv("USE_MTF", "1").strip() not in ("0", "false", "")

        # ----- Quan tri rui ro (SL/TP dong + sizing theo confidence) -----
        self.risk_percent = float(os.getenv("RISK_PERCENT", "1.0"))
        self.risk_min_percent = float(os.getenv("RISK_MIN_PERCENT", "0.5"))
        self.risk_max_percent = float(os.getenv("RISK_MAX_PERCENT", "1.5"))
        self.account_balance = float(os.getenv("ACCOUNT_BALANCE", "0") or "0")
        # Chi vao lenh khi do tin cay >= nguong nay (0 = tat loc)
        self.min_confidence = float(os.getenv("MIN_CONFIDENCE", "0"))
        # Nguong tin cay rieng cho breakout (breakout cham diem thap hon trend)
        self.breakout_min_confidence = float(os.getenv("BREAKOUT_MIN_CONFIDENCE", "45"))
        # Breakout can momentum: bo qua neu ADX < nguong nay (0 = tat)
        self.breakout_min_adx = float(os.getenv("BREAKOUT_MIN_ADX", "22"))
        # Cong tac bat/tat chien luoc trend (pullback). TREND_ENABLED=0 de tat han.
        self.trend_enabled = os.getenv("TREND_ENABLED", "1").strip() not in ("0", "false", "")
        # Vao lenh: "limit" (cho gia hoi) hoac "market" (vao ngay)
        self.entry_mode = os.getenv("ENTRY_MODE", "limit").strip().lower()
        self.entry_wait_bars = int(os.getenv("ENTRY_WAIT_BARS", "6"))

        # ----- Supertrend (he dao chieu; sau backtest: chi XAU M30, TP 3R) -----
        self.supertrend_enabled = os.getenv("SUPERTREND_ENABLED", "1").strip() not in ("0", "false", "")
        self.supertrend_symbols = _split(os.getenv("SUPERTREND_SYMBOLS", "XAUUSD"))
        self.supertrend_tfs = _split(os.getenv("SUPERTREND_TFS", "M30"))
        self.supertrend_period = int(os.getenv("SUPERTREND_PERIOD", "10"))
        self.supertrend_mult = float(os.getenv("SUPERTREND_MULT", "3"))
        # Moc chot lai (R). Cham +NR -> WIN cap +N; cham SL -> LOSS -1R; dao chieu con duong -> WIN R that.
        self.supertrend_rr = float(os.getenv("SUPERTREND_RR", "3"))

        # ----- Bollinger Mean Reversion (tin hieu roi rac, quet doc lap ngoai watchlist chinh) -----
        # Danh sach cap/khung da chot qua backtest (PF > 1.8): EURUSD H4, USDJPY H4, EURUSD M15.
        self.bollinger_enabled = os.getenv("BOLLINGER_ENABLED", "1").strip() not in ("0", "false", "")
        self.bollinger_pairs = _parse_pairs(os.getenv(
            "BOLLINGER_PAIRS", "EURUSD:H4,USDJPY:H4,EURUSD:M15"))

        # ----- London Breakout (tin hieu roi rac, quet doc lap ngoai watchlist chinh) -----
        # Danh sach cap/khung da chot qua backtest: EURUSD M30+H1, USDJPY H1, NZDUSD M30.
        self.london_enabled = os.getenv("LONDON_ENABLED", "1").strip() not in ("0", "false", "")
        self.london_pairs = _parse_pairs(os.getenv(
            "LONDON_PAIRS", "EURUSD:M30,EURUSD:H1,USDJPY:H1"))

        # ----- EMA Cross Watch (CANH BAO rieng, KHONG phai chien luoc vao lenh: chi
        # theo doi EMA20/EMA100 tren nhieu cap/khung, bao qua mail khi sap/vua cat cheo).
        # Da CAT GIAM tu 33 cap xuong 9 cap de vua quota mien phi Twelve Data (800
        # request/ngay) - xem tinh toan trong lich su chat. XAUUSD mien phi (dung lai
        # nen da tai san cho tin hieu breakout chinh); EURUSD/GBPUSD/USDJPY moi cap chi
        # con M30+H1 (bo M15) VA chi thuc su quet moi 30 phut (xem emacross_slow_symbols
        # + gate trong run_cloud.py) de khong vuot quota. -----
        self.emacross_enabled = os.getenv("EMACROSS_ENABLED", "1").strip() not in ("0", "false", "")
        self.emacross_pairs = _parse_pairs(os.getenv(
            "EMACROSS_PAIRS",
            "XAUUSD:M15,XAUUSD:M30,XAUUSD:H1,"
            "EURUSD:M30,EURUSD:H1,"
            "GBPUSD:M30,GBPUSD:H1,"
            "USDJPY:M30,USDJPY:H1"))
        # Cac symbol trong danh sach nay CHI duoc quet khi phut UTC hien tai la :00 hoac
        # :30 (~moi 30 phut thay vi moi 15 phut) - tiet kiem quota. Symbol KHONG nam
        # trong danh sach nay (vd XAUUSD) van quet moi lan chay (moi 15 phut) nhu binh
        # thuong vi da mien phi (dung chung nen voi tin hieu chinh).
        self.emacross_slow_symbols = set(_split(os.getenv(
            "EMACROSS_SLOW_SYMBOLS", "EURUSD,GBPUSD,USDJPY")))

        # ----- Duong dan output -----
        self.reports_dir = os.getenv("REPORTS_DIR", "reports")
        self.dashboard_data = os.getenv("DASHBOARD_DATA", "dashboard/data.js")

    def validate_email(self) -> list:
        missing = []
        if not self.gmail_user:
            missing.append("GMAIL_USER")
        if not self.gmail_app_password:
            missing.append("GMAIL_APP_PASSWORD")
        if not self.mail_to:
            missing.append("MAIL_TO")
        return missing

    def summary(self) -> str:
        pwd = "***set***" if self.gmail_app_password else "(missing)"
        gc = self.groups["GOLD_CRYPTO"]
        fx = self.groups["FOREX"]
        return (
            "Watchlist={} | Gold/BTC={} Forex={} | MTF={} | "
            "Poll={}s NotifyOn={} Risk={}-{}% | Channels={} Gmail={} AppPwd={} Ntfy={}"
        ).format(
            len(self.watchlist), ",".join(gc["timeframes"]),
            ",".join(fx["timeframes"]), "on" if self.use_mtf else "off",
            self.poll_interval, self.notify_on,
            self.risk_min_percent, self.risk_max_percent,
            ",".join(self.notifier_channels),
            self.gmail_user or "(missing)", pwd, self.ntfy_topic or "(missing)",
        )
