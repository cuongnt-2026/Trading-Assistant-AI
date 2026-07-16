# Chạy bot trên GitHub Actions (miễn phí, chạy cả khi TẮT máy)

Bot sẽ chạy trên máy chủ của GitHub, tự lấy giá từ API free (Twelve Data),
chạy đúng bộ lọc trend + lệnh chờ như bản ở máy, và gửi mail khi có tín hiệu.
**Không cần MT5, không cần máy bạn bật.**

Chỉ làm 1 lần, khoảng 10 phút.

---

## Bước 1 — Lấy API key Twelve Data (free)

1. Vào https://twelvedata.com → **Sign up** (đăng ký free bằng email).
2. Sau khi đăng nhập, vào mục **API Key** → copy dãy key (khoảng 32 ký tự).
3. Giữ lại để dán ở Bước 3.

Gói free: 800 lượt gọi/ngày, 8 lượt/phút — đủ cho 5 cặp FX chạy mỗi giờ.

---

## Bước 2 — Đẩy code lên GitHub

Double-click **`PUSH-CLOUD.bat`** trong thư mục dự án.
- Lần đầu có thể mở trình duyệt để đăng nhập GitHub — cứ đăng nhập.
- Chạy xong, vào https://github.com/cuongnt-2026/Trading-Assistant-AI
  kiểm tra thấy các file mới (`run_cloud.py`, thư mục `.github/workflows`) là được.

---

## Bước 3 — Thêm "Secrets" (thông tin bí mật) vào GitHub

Vào repo trên GitHub → **Settings** → menu trái **Secrets and variables** →
**Actions** → nút **New repository secret**. Thêm lần lượt **4 cái**:

| Name | Value (giá trị) |
|------|-----------------|
| `TWELVEDATA_API_KEY` | API key ở Bước 1 |
| `GMAIL_USER` | email Gmail dùng để gửi (vd cuongnt2023@gmail.com) |
| `GMAIL_APP_PASSWORD` | App Password 16 ký tự của Gmail (giống trong .env) |
| `MAIL_TO` | email nhận thông báo |

> Secrets được GitHub mã hoá, không ai xem được, kể cả trong log.

---

## Bước 4 — Bật và chạy thử

1. Vào tab **Actions** trên repo → nếu hỏi thì bấm **"I understand... enable"**.
2. Chọn workflow **"Trading signals (cloud)"** (menu trái).
3. Bấm **Run workflow** → **Run workflow** (chạy thử ngay).
4. Đợi ~2 phút, bấm vào lần chạy để xem log:
   - Thấy dòng `EURUSD H1 | NO_TRADE/BUY/SELL | ... | ADX=...` là **đang lấy được giá**.
   - Nếu có tín hiệu đủ điều kiện → **mail sẽ về hộp thư**.

Từ đó nó **tự chạy mỗi giờ**, kể cả khi máy bạn tắt.

---

## Ghi chú

- **Giữ repo ở chế độ Public** để GitHub Actions miễn phí không giới hạn phút.
  (Code public không sao — bí mật nằm trong Secrets, không nằm trong code.)
- Muốn chạy **30 phút/lần** thay vì mỗi giờ: sửa dòng `cron` trong
  `.github/workflows/signals.yml` thành `"*/30 * * * *"`.
- Dữ liệu giá lấy từ Twelve Data nên **hơi lệch broker của bạn** một chút —
  bình thường với tín hiệu tham khảo. Vào lệnh vẫn đặt trên tài khoản của bạn.
- File `cloud_state.json` bot tự cập nhật để **không gửi trùng** một tín hiệu.
- Bản chạy ở máy (START-BOT.bat) và bản cloud **có thể chạy song song** —
  nhưng để tránh nhận mail 2 lần, nên chọn một. Khuyên: dùng **bản cloud**.
