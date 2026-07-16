# Hướng dẫn: Cảnh báo tín hiệu qua Gmail

Tính năng mới cho **Trading Assistant AI**: chương trình tự canh thị trường, khi có tín hiệu **BUY/SELL** thì gửi email cho bạn. Hỗ trợ **nhiều cặp cùng lúc** (vàng, ngoại tệ chính, và BTC — chạy cả cuối tuần).

---

## Chạy nhanh 5 bước

### Bước 1 — Bật xác minh 2 bước cho Gmail
App Password chỉ tạo được khi tài khoản đã bật 2FA.
Vào https://myaccount.google.com/security → bật **Xác minh 2 bước**.

### Bước 2 — Tạo App Password (16 ký tự)
Vào https://myaccount.google.com/apppasswords → đặt tên (vd `TradingAI`) → **Tạo**.
Google trả về chuỗi 16 ký tự dạng `abcd efgh ijkl mnop`. **Copy lại** (bỏ khoảng trắng khi dán cũng được).
> Đây KHÔNG phải mật khẩu đăng nhập Gmail. Đừng dùng mật khẩu Gmail thường.

### Bước 3 — Tạo file cấu hình `.env`
Trong thư mục dự án, copy `.env.example` thành `.env` rồi điền:
```
GMAIL_USER=cuongnt2023@gmail.com
GMAIL_APP_PASSWORD=abcdefghijklmnop      # 16 ký tự App Password ở Bước 2
MAIL_TO=cuongnt2023@gmail.com
SYMBOLS=XAUUSD,EURUSD,GBPUSD,USDJPY,AUDUSD,USDCAD,USDCHF,NZDUSD,BTCUSD,BTCJPY,BTCEUR,BTCGBP
TIMEFRAME=M15
NOTIFY_ON=change
```
> File `.env` đã được `.gitignore` nên **không bị đẩy lên git** — an toàn.

### Bước 4 — Cài thư viện & gửi mail thử
```powershell
pip install -r requirements.txt
python run_monitor.py --test-mail
```
Nếu nhận được email `[Trading Assistant AI] Test email OK` là cấu hình đúng.

### Bước 5 — Chạy bot canh tín hiệu
```powershell
python run_monitor.py            # chạy nền liên tục (Ctrl+C để dừng)
python run_monitor.py --once     # kiểm tra 1 lần rồi thoát
```
Bot cần **MetaTrader 5 đang mở và đã đăng nhập** trên cùng máy.

---

## Xem dashboard thống kê
Mở `dashboard/index.html` bằng trình duyệt (nháy đúp là được).
Trang này đọc `dashboard/data.js` — file được bot tự cập nhật mỗi khi có tín hiệu.
Hiển thị: tổng tín hiệu, số BUY/SELL, số mail đã gửi, bảng lịch sử, biểu đồ phân bổ và theo từng cặp.
> Sau khi bot ghi tín hiệu mới, bấm **F5** để làm mới dashboard.

---

## Lưu ý quan trọng về tên symbol
Tên cặp tiền phải **trùng đúng** với tên trong MT5 của broker bạn.
Nhiều broker thêm hậu tố, ví dụ `EURUSD.m`, `XAUUSD.s`, `BTCUSD.raw`...
Mở MT5 → **Market Watch** (Ctrl+M) để xem tên chính xác, rồi sửa lại `SYMBOLS` trong `.env`.
Nếu một symbol không tồn tại, bot chỉ báo cảnh báo cho symbol đó và vẫn chạy tiếp các symbol khác.

## Cách chống spam mail
- `NOTIFY_ON=change` (khuyến nghị): chỉ gửi khi tín hiệu **đổi** (vd NO_TRADE → BUY).
- `NOTIFY_ON=every`: gửi mỗi cây nến có BUY/SELL.

## "Không cần bật máy" thì sao?
MT5 bắt buộc một máy Windows luôn bật. Muốn chạy 24/7 mà tắt laptop:
- **Miễn phí:** để chương trình chạy trên chính máy bạn (khi máy bật + có mạng).
- **24/7 thật sự (tốn phí):** thuê **Windows VPS** (~5–15$/tháng), cài MT5 + bot lên đó. Code y nguyên, chỉ khác nơi chạy.

---

## Roadmap nâng cấp (mở rộng sau này)
Kiến trúc đã tách sẵn để dễ mở rộng:

- ✅ **Sprint 8 — Notification:** cảnh báo email khi có tín hiệu (đã xong).
- **Telegram / Zalo push:** báo về điện thoại **miễn phí**. Chỉ cần thêm 1 class kế thừa `Notifier` trong `src/notifier/` rồi khai báo `NOTIFIER_CHANNEL=telegram`. (SMS vào số điện thoại tốn phí nên không khuyến nghị.)
- **Sprint 9 — Backtest:** dữ liệu tín hiệu đã được lưu ở `reports/signals.json`, dùng để đo tỉ lệ thắng (win rate) trong quá khứ.
- **Sprint 7/10 — AI Recommendation:** thêm gợi ý SL/TP, quản lý rủi ro, xác suất thắng vào nội dung cảnh báo.
- **Dashboard nâng cao:** thêm biểu đồ nến + đường EMA, lọc theo symbol, thống kê theo ngày/tuần.

---
*Tín hiệu chỉ mang tính tham khảo từ hệ thống, không phải lời khuyên đầu tư. Luôn tự quản lý rủi ro.*
