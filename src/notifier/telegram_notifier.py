"""
Telegram notifier - báo tín hiệu về điện thoại qua Telegram (MIỄN PHÍ).

Dùng urllib (thư viện chuẩn) nên không cần cài thêm gì.

Cách lấy TELEGRAM_BOT_TOKEN và TELEGRAM_CHAT_ID:
    Xem docs/HUONG_DAN_BAO_DIEN_THOAI.md
"""

import urllib.parse
import urllib.request

from src.notifier.base import Notifier


class TelegramNotifier(Notifier):
    """
    Gửi thông báo qua Telegram Bot API.
    """

    def __init__(self, config):
        self.config = config

    def send(self, subject: str, body: str) -> bool:
        token = self.config.telegram_bot_token
        chat_id = self.config.telegram_chat_id

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        text = f"{subject}\n\n{body}"

        data = urllib.parse.urlencode({
            "chat_id": chat_id,
            "text": text,
        }).encode("utf-8")

        try:
            req = urllib.request.Request(url, data=data, method="POST")
            with urllib.request.urlopen(req, timeout=15) as resp:
                return resp.status == 200
        except Exception as e:
            print(f"[ERROR] Gửi Telegram thất bại: {e}")
            return False

    def send_test(self) -> bool:
        return self.send(
            "[Trading Assistant AI] Test Telegram OK",
            "Neu ban nhan duoc tin nay tren Telegram, cau hinh da OK.",
        )
