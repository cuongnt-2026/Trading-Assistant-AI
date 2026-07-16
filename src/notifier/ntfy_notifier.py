"""
ntfy.sh notifier - báo tín hiệu về điện thoại qua app ntfy (MIỄN PHÍ).

Không cần tài khoản. Chỉ cần cài app "ntfy" và đăng ký 1 topic.
Dùng urllib (thư viện chuẩn) nên không cần cài thêm gì.

Cách dùng:
    1. Cài app "ntfy" (Android/iOS) hoặc mở https://ntfy.sh
    2. Đăng ký (subscribe) 1 topic tên khó đoán, ví dụ: cuong-trading-ai-9x7k
    3. Điền tên topic đó vào NTFY_TOPIC trong .env
"""

import urllib.request

from src.notifier.base import Notifier


def _ascii(s: str) -> str:
    """Loại ký tự không phải ASCII cho HTTP header (Title)."""
    return s.encode("ascii", "ignore").decode("ascii")


class NtfyNotifier(Notifier):
    """
    Gửi thông báo qua ntfy.sh.
    """

    def __init__(self, config):
        self.config = config

    def send(self, subject: str, body: str) -> bool:
        server = self.config.ntfy_server.rstrip("/")
        topic = self.config.ntfy_topic
        url = f"{server}/{topic}"

        try:
            req = urllib.request.Request(
                url,
                data=body.encode("utf-8"),
                method="POST",
            )
            # Header chi nhan ASCII
            req.add_header("Title", _ascii(subject))
            req.add_header("Priority", "high")
            req.add_header("Tags", "chart_with_upwards_trend")

            with urllib.request.urlopen(req, timeout=15) as resp:
                return resp.status == 200
        except Exception as e:
            print(f"[ERROR] Gửi ntfy thất bại: {e}")
            return False

    def send_test(self) -> bool:
        return self.send(
            "[Trading Assistant AI] Test ntfy OK",
            "Neu ban nhan duoc thong bao nay tren dien thoai, cau hinh da OK.",
        )
