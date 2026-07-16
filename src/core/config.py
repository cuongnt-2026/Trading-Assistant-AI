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
        # Vao lenh: "limit" (cho gia hoi) hoac "market" (vao ngay)
        self.entry_mode = os.getenv("ENTRY_MODE", "limit").strip().lower()
        self.entry_wait_bars = int(os.getenv("ENTRY_WAIT_BARS", "6"))

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
