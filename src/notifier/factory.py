"""
Notifier factory.

Xây dựng notifier theo cấu hình. Hỗ trợ NHIỀU kênh cùng lúc
(NOTIFIER_CHANNEL = "email,ntfy,telegram").
Kênh thiếu cấu hình sẽ bị bỏ qua kèm cảnh báo, không làm dừng chương trình.
"""

from src.notifier.email_notifier import EmailNotifier
from src.notifier.telegram_notifier import TelegramNotifier
from src.notifier.ntfy_notifier import NtfyNotifier
from src.notifier.multi_notifier import MultiNotifier


def _build_email(config):
    if config.validate_email():
        print("[WARN] Kênh 'email' thiếu cấu hình Gmail -> bỏ qua.")
        return None
    return EmailNotifier(config)


def _build_telegram(config):
    if not config.telegram_bot_token or not config.telegram_chat_id:
        print("[WARN] Kênh 'telegram' thiếu TOKEN/CHAT_ID -> bỏ qua.")
        return None
    return TelegramNotifier(config)


def _build_ntfy(config):
    if not config.ntfy_topic:
        print("[WARN] Kênh 'ntfy' thiếu NTFY_TOPIC -> bỏ qua.")
        return None
    return NtfyNotifier(config)


_BUILDERS = {
    "email": _build_email,
    "telegram": _build_telegram,
    "ntfy": _build_ntfy,
}


def create_notifier(config):
    """Tạo MultiNotifier gồm các kênh đã bật và cấu hình đủ. None nếu không có."""
    active = []
    for channel in config.notifier_channels:
        builder = _BUILDERS.get(channel)
        if builder is None:
            print(f"[WARN] Kênh '{channel}' không hỗ trợ -> bỏ qua.")
            continue
        n = builder(config)
        if n is not None:
            active.append((channel, n))
    if not active:
        return None
    print("Kênh thông báo đang bật:", ", ".join(n for n, _ in active))
    return MultiNotifier(active)
