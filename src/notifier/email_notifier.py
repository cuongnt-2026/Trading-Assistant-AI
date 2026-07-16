"""
Email notifier - gửi thông báo qua Gmail SMTP (App Password).

Dùng thư viện chuẩn của Python (smtplib, ssl, email) nên không cần
cài thêm gì. Chạy độc lập trên máy bạn hoặc trên VPS đều được.
"""

import smtplib
import ssl
from email.message import EmailMessage

from src.notifier.base import Notifier


class EmailNotifier(Notifier):
    """
    Gửi email qua Gmail SMTP.
    """

    def __init__(self, config):
        self.config = config

    def send(self, subject: str, body: str) -> bool:
        """
        Gửi email.

        Returns:
            True nếu gửi thành công, False nếu lỗi.
        """

        msg = EmailMessage()
        msg["From"] = self.config.gmail_user
        msg["To"] = self.config.mail_to
        msg["Subject"] = subject
        msg.set_content(body)

        context = ssl.create_default_context()

        try:
            with smtplib.SMTP_SSL(
                self.config.smtp_host,
                self.config.smtp_port,
                context=context,
                timeout=30,
            ) as server:
                server.login(
                    self.config.gmail_user,
                    self.config.gmail_app_password,
                )
                server.send_message(msg)

            return True

        except smtplib.SMTPAuthenticationError:
            print(
                "[ERROR] Gmail đăng nhập thất bại. "
                "Kiểm tra GMAIL_USER và GMAIL_APP_PASSWORD "
                "(phải là App Password 16 ký tự, không phải mật khẩu Gmail)."
            )
            return False

        except Exception as e:
            print(f"[ERROR] Gửi email thất bại: {e}")
            return False

    def send_test(self) -> bool:
        """
        Gửi 1 email test để kiểm tra cấu hình.
        """

        return self.send(
            subject="[Trading Assistant AI] Test email OK",
            body=(
                "Xin chào,\n\n"
                "Nếu bạn nhận được email này nghĩa là cấu hình Gmail "
                "đã hoạt động.\n"
                "Từ giờ khi có tín hiệu vào lệnh, bạn sẽ nhận được thông báo "
                "tại đây.\n\n"
                "-- Trading Assistant AI"
            ),
        )
