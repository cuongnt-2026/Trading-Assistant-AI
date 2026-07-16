# Hướng dẫn: Chạy bot ngầm 24/7 (đi làm vẫn chạy)

Mục tiêu: bạn khóa máy đi làm, để máy ở nhà → MT5 + bot vẫn chạy, có tín hiệu vẫn bắn Gmail. **Chỉ khi bạn Shutdown mới dừng.**

---

## ⚠️ Điều quan trọng nhất phải hiểu trước

| Hành động | MT5 + bot |
|---|---|
| **Khóa màn hình (Win + L)** | ✅ **Vẫn chạy** — dùng cái này khi đi làm |
| Để yên, tắt màn hình | ✅ Vẫn chạy (đã tắt sleep) |
| **Đăng xuất / Sign out** | ❌ **Bị tắt** — Windows đóng hết chương trình |
| Sleep / Hibernate (ngủ) | ❌ Tạm dừng — script sẽ TẮT chế độ này |
| **Shutdown / Restart** | ❌ Tắt (bot tự chạy lại sau khi bật máy + đăng nhập) |

👉 **Đi làm: bấm `Win + L` để KHÓA, tuyệt đối không "Đăng xuất".**

> Vì sao không làm cho survive cả khi Sign out? MT5 là app giao diện, bắt buộc phải có phiên đăng nhập (session) đang mở thì API mới đọc được dữ liệu. Chạy dạng Windows Service khi đã sign out sẽ không ổn định. Cách khóa màn hình là chuẩn và đáng tin nhất cho máy ở nhà.

---

## Cài đặt (làm 1 lần)

### Bước 1 — Tìm đường dẫn MetaTrader 5
Thường là: `C:\Program Files\MetaTrader 5\terminal64.exe`
(Chuột phải icon MT5 → Open file location để xem chính xác.)

### Bước 2 — Chạy script cấu hình (bằng quyền Admin)
Mở **PowerShell (Admin)**: bấm Start → gõ `powershell` → chuột phải → **Run as administrator**. Rồi chạy:

```powershell
cd D:\Projects\Trading-Assistant-AI
powershell -ExecutionPolicy Bypass -File scripts\setup_always_on.ps1 -Mt5Path "C:\Program Files\MetaTrader 5\terminal64.exe"
```

Script sẽ:
1. **Tắt sleep/hibernate** khi cắm điện (máy không tự ngủ).
2. Tạo tác vụ tự chạy **bot** mỗi khi bạn đăng nhập Windows (bot tự bật lại nếu crash).
3. Tạo tác vụ tự mở **MT5** mỗi khi đăng nhập.

> Nếu không muốn tự mở MT5, bỏ phần `-Mt5Path "..."`.

### Bước 3 — Bật đăng nhập tự động cho MT5
Trong MT5: **File → Login to Trade Account** → tick **Save account information**. Để MT5 tự kết nối lại tài khoản sau khi khởi động.

### Bước 4 — Chạy thử ngay
Nháy đúp `run_bot.bat`. Một cửa sổ đen hiện ra và bắt đầu canh tín hiệu. Mở `dashboard\index.html` xem, và kiểm tra `logs\bot.log`.

---

## Kiểm tra & vận hành

**Xem bot có đang chạy?**
- Task Manager (Ctrl+Shift+Esc) → tab Details → tìm `python.exe`.
- Hoặc xem `logs\bot.log` có dòng mới liên tục.

**Kiểm tra tác vụ tự chạy:**
- Mở **Task Scheduler** → tìm `TradingAssistantAI_Bot` và `TradingAssistantAI_MT5`.

**Dừng bot tạm thời:** đóng cửa sổ đen của `run_bot.bat`.

**Dừng hẳn / gỡ tự chạy:**
```powershell
powershell -ExecutionPolicy Bypass -File scripts\setup_always_on.ps1 -Uninstall
```

---

## Vài lưu ý thực tế
- **Mạng:** máy phải có internet để MT5 nhận dữ liệu và bot gửi mail. Mất mạng thì tạm ngưng, có lại thì chạy tiếp.
- **Mất điện:** máy tắt → khi có điện, nếu máy tự bật (hoặc bạn bật) và đăng nhập, mọi thứ tự chạy lại. Muốn chắc hơn có thể dùng bộ lưu điện (UPS).
- **Laptop:** nên cắm sạc liên tục. Đóng nắp laptop có thể làm máy ngủ — vào Control Panel → Power Options → "Khi đóng nắp" chọn **Do nothing** (khi cắm điện).
- **Muốn thật sự không phụ thuộc máy ở nhà** (kể cả cúp điện, tắt máy): thuê **Windows VPS** chạy 24/7 — nhưng cái đó tốn phí hàng tháng.

---
*Tín hiệu chỉ mang tính tham khảo, không phải lời khuyên đầu tư.*
