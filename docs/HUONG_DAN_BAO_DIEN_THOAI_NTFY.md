# Hướng dẫn: Báo tín hiệu về điện thoại qua ntfy.sh (MIỄN PHÍ)

ntfy.sh đẩy thông báo về điện thoại như tin nhắn — miễn phí, không cần tài khoản.

## Topic của bạn đã được tạo sẵn
Trong file `.env`, dòng:
```
NTFY_TOPIC=cuong-trading-ai-890235
```
Đây là "kênh riêng" của bạn. Chỉ cần đăng ký đúng tên này trên điện thoại là nhận được tín hiệu.
> Giữ tên topic kín (đừng chia sẻ) vì ai biết tên cũng đọc được thông báo.

## 3 bước cài trên điện thoại
1. Cài app **ntfy**:
   - Android: Google Play → tìm "ntfy"
   - iPhone: App Store → tìm "ntfy"
   (Hoặc mở web https://ntfy.sh trên trình duyệt điện thoại.)
2. Mở app → bấm **+ (Subscribe to topic)**.
3. Nhập đúng tên topic: **cuong-trading-ai-890235** → **Subscribe**.

Xong. Máy tính chạy bot, có tín hiệu là điện thoại kêu ngay.

## Test thử
Trên máy tính (đã có MT5 + .env):
```powershell
python run_monitor.py --test
```
Điện thoại sẽ nhận thông báo `[Trading Assistant AI] Test OK` qua cả Gmail và ntfy.

## Đổi topic (nếu muốn)
Sửa `NTFY_TOPIC` trong `.env` thành tên khác (đặt khó đoán), rồi subscribe tên mới trên app.

## Lưu ý
- Máy tính chạy bot cần có internet để gửi lên ntfy.
- Điện thoại cần bật thông báo cho app ntfy.
- ntfy.sh miễn phí, dùng chung máy chủ công cộng; muốn riêng tư tuyệt đối có thể tự dựng server ntfy (nâng cao, không bắt buộc).

---
*Tín hiệu chỉ mang tính tham khảo, không phải lời khuyên đầu tư.*
