# Phân công công việc


## Thành viên

- Hòa
- Lợi
- Hùng
- Hiển
- Chị Hiền

Các công việc được sắp xếp theo giai đoạn. Những mục trong cùng một giai đoạn có thể thực hiện song song nếu đã hoàn thành các điều kiện đầu vào của giai đoạn đó.

## Giai đoạn 1: Quản trị và khởi động

- [ ] Quản trị dự án: lập kế hoạch, phân công nhiệm vụ và theo dõi deadline - Hòa
- [ ] Thiết lập repository: tạo GitHub repository với cấu trúc thư mục - Hòa
- [ ] Thiết lập môi trường cộng tác: kéo repository về máy local, đọc cấu trúc dự án và tài liệu hướng dẫn, chạy `streamlit run test_moi_truong.py` để xác nhận đã cài đặt môi trường thành công - Tất cả mọi người

**Điều kiện hoàn thành:** Tất cả thành viên truy cập được repository, chạy được môi trường local và biết cách tạo branch/pull request.

## Giai đoạn 2: Chốt yêu cầu và hợp đồng kỹ thuật

- [ ] Thiết kế kiến trúc, giao diện dự kiến và cấu trúc thư mục source code/test - Hòa
- [ ] Chốt schema database và quy tắc transaction - Hòa/Hùng
- [ ] Chốt function signature, kiểu dữ liệu trả về và quy tắc lỗi - Hòa
- [ ] Chuẩn bị kịch bản kiểm thử và dữ liệu mẫu cho các chức năng - Chị Hiền

**Điều kiện hoàn thành:** Schema, API nội bộ và tiêu chí kiểm thử được thống nhất trước khi chia code cho các nhóm chức năng.

## Giai đoạn 3: Xây dựng nền tảng dùng chung

- [ ] Xây dựng nền tảng dữ liệu: cài đặt database, SQLAlchemy repository, schema, transaction và seed data cho user/transaction/price alert - Hùng

**Điều kiện hoàn thành:** Repository có thể đọc/ghi database, transaction có commit/rollback và seed data chạy được.

## Giai đoạn 4: Phát triển chức năng song song

### Nhóm A: Dữ liệu thị trường

- [ ] Xây dựng market-data service: tích hợp `yfinance` (hoặc dữ liệu giả), cài đặt `get_current_prices` và `get_price_history`, xử lý dữ liệu rỗng, lỗi API và timeout - Hiển

### Nhóm B: Giao dịch và danh mục

- [ ] Xây dựng transaction/portfolio service: `add_transaction` với giao dịch `BUY`/`SELL` và kiểm tra bán vượt tồn; `get_portfolio_summary` với số lượng tồn, giá vốn bình quân, giá trị hiện tại và PnL - Hùng

### Nhóm C: Quản lý cảnh báo

- [ ] Xây dựng alert-management service: `add_price_alert`, `list_price_alerts`, `deactivate_price_alert`, kiểm tra quyền sở hữu và trạng thái `is_active` - Lợi

### Nhóm D: Giao diện và trực quan hóa

- [ ] Xây dựng dashboard Streamlit: sidebar, form giao dịch/cảnh báo, metrics, dataframe danh mục và dữ liệu mock - Hòa

**Điều kiện bắt đầu:** Giai đoạn 3 hoàn thành và các nhóm dùng đúng function contract đã chốt ở giai đoạn 2.

## Giai đoạn 5: Worker cảnh báo và tích hợp

- [ ] Xây dựng alert worker: `process_price_alerts`, lấy alert active cùng `telegram_chat_id`, so sánh giá và chỉ tắt alert sau khi gửi thành công - Hòa
- [ ] Tích hợp Telegram và lịch chạy: gửi Bot API có timeout, tạo `alert_bot.py` độc lập với Streamlit và cấu hình Cronjob mỗi 5 phút - Lợi
- [ ] Xây dựng và tích hợp biểu đồ: kết nối `build_candlestick_chart` với `get_price_history` và transaction repository - Hiển
- [ ] Tích hợp toàn hệ thống vào Streamlit UI: kết nối các service, làm mới dữ liệu sau thao tác và hoàn thiện luồng người dùng - Hòa

**Điều kiện hoàn thành:** Luồng thêm giao dịch, xem danh mục, đặt cảnh báo, xem biểu đồ và gửi Telegram chạy được từ đầu đến cuối.

## Giai đoạn 6: Kiểm thử và sửa lỗi

- [ ] Viết và chạy unit test cho repository, market-data, transaction/portfolio và alert service - Chị Hiền phối hợp cùng người phụ trách
- [ ] Kiểm thử tích hợp database, market data và Telegram mock - Chị Hiền phối hợp cùng Hùng, Hiển và Lợi
- [ ] Kiểm thử giao diện trên luồng chính, ghi nhận kết quả và quay video - Chị Hiền
- [ ] Sửa lỗi và chạy regression test - Người phụ trách chức năng phối hợp cùng Chị Hiền

**Điều kiện hoàn thành:** Các kịch bản bắt buộc đạt, lỗi đã ghi nhận có trạng thái xử lý và không có regression nghiêm trọng.

## Giai đoạn 7: Demo và bàn giao

- [ ] Chuẩn bị dữ liệu demo và cấu hình mẫu - Chị Hiền
- [ ] Hoàn thiện README và hướng dẫn cài đặt/chạy ứng dụng - Hòa
- [ ] Cập nhật tài liệu requirements và tài liệu từng hàm - Hòa
- [ ] Kiểm tra lại repository trước khi nộp - Chị Hiền