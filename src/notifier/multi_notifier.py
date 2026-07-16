"""
MultiNotifier - gửi thông báo qua NHIỀU kênh cùng lúc (email + telegram + ntfy).
"""

from src.notifier.base import Notifier


class MultiNotifier(Notifier):
    """
    Bọc nhiều notifier, gửi tới tất cả.
    """

    def __init__(self, notifiers):
        # notifiers: list các tuple (tên_kênh, notifier)
        self.notifiers = notifiers

    def send(self, subject: str, body: str) -> bool:
        any_ok = False
        for name, n in self.notifiers:
            ok = n.send(subject, body)
            if ok:
                any_ok = True
            else:
                print(f"       -> [WARN] Kênh '{name}' gửi thất bại.")
        return any_ok

    def channel_names(self):
        return [name for name, _ in self.notifiers]
