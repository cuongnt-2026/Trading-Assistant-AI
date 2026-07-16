"""
Notifier base class.

Định nghĩa interface chung cho mọi kênh thông báo.
Nhờ lớp trừu tượng này, sau này thêm Telegram / Zalo / SMS
chỉ cần tạo class mới kế thừa Notifier, không phải sửa Monitor.
"""

from abc import ABC, abstractmethod


class Notifier(ABC):
    """
    Kênh thông báo trừu tượng.
    """

    @abstractmethod
    def send(self, subject: str, body: str) -> bool:
        """
        Gửi một thông báo.

        Returns:
            True nếu gửi thành công, False nếu lỗi.
        """
        raise NotImplementedError
