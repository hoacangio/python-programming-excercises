## Wireframe 1: Màn hình Xem Danh Mục & Biểu Đồ (Portfolio Dashboard)

Màn hình này đóng vai trò là trang chủ, nơi tổng hợp toàn bộ tình hình đầu tư và hiển thị biểu đồ phân tích kỹ thuật.

```text
+------------------------+-------------------------------------------------------------+
|        SIDEBAR         |                      XEM DANH MỤC                           |
|                        |                                                             |
| ◉ Xem danh mục         |  [ Tổng vốn: 150.000.000đ ]  [ Tổng giá trị: 165.000.000đ ] |
| ◯ Thêm giao dịch       |  [ % Lời/Lỗ: ▲ +10.0% ]                                     |
| ◯ Cài đặt cảnh báo     |                                                             |
|                        |-------------------------------------------------------------|
|                        |  Danh Sách Cổ Phiếu Đang Giữ                                |
|                        |  | Mã  | SL   | Giá vốn | Giá TT  | Giá trị HT | % Lời/Lỗ | |
|                        |  | FPT | 1000 | 95.000  | 105.000 | 105.000.000| +10.53%  | |
|                        |  | VNM | 500  | 70.000  | 67.200  | 33.600.000 | -4.00%   | |
|                        |                                                             |
|                        |-------------------------------------------------------------|
|                        |  Biểu Đồ Lịch Sử Giá                                        |
|                        |  [ Chọn mã: FPT ▼ ] [ Từ ngày - Đến ngày ] [ Interval: 1d ▼]|
|                        |                                                             |
|                        |  +-------------------------------------------------------+  |
|                        |  |                         (▲) Marker Mua xanh           |  |
|                        |  |    Candlestick Chart      |                           |  |
|                        |  |                           |                           |  |
|                        |  |      |             (▼) Marker Bán đỏ                  |  |
|                        |  |     [ ]                                               |  |
|                        |  |      |                                                |  |
|                        |  +-------------------------------------------------------+  |
+------------------------+-------------------------------------------------------------+

```

* **Menu Điều Hướng:** Giao diện sử dụng `st.sidebar` để tạo menu chuyển đổi giữa các tính năng bao gồm Thêm giao dịch, Xem danh mục và Cài đặt cảnh báo.


* **Tổng Quan (Metrics):** Sử dụng `st.metric` để hiển thị các chỉ số tổng quan gồm Tổng vốn (total_invested), Tổng giá trị hiện tại (current_value), và phần trăm lời/lỗ (total_pnl_percent) có kèm mũi tên báo xu hướng xanh/đỏ.


* **Bảng Danh Mục:** Hiển thị trực quan qua `st.dataframe` hoặc `st.data_editor`. Bảng chứa các cột chi tiết từ hàm `get_portfolio_summary`: symbol, quantity, average_cost, current_price, invested_value, current_value, pnl, và pnl_percent. Các mã có số lượng tồn bằng 0 sẽ không hiển thị.


* **Biểu Đồ (Charts):** Được vẽ bằng `st.plotly_chart`. Người dùng có thể lọc theo mã cổ phiếu (symbol), ngày bắt đầu (start date), ngày kết thúc (end date) và khung thời gian (interval). Biểu đồ hiển thị dạng nến (candlestick) kết hợp với các marker biểu diễn giao dịch mua (màu xanh) và bán (màu đỏ).



---

## Wireframe 2: Màn hình Thêm Giao Dịch (Add Transaction)

Giao diện chuyên biệt dùng để ghi nhận các lệnh mua hoặc bán cổ phiếu.

```text
+------------------------+-------------------------------------------------------------+
|        SIDEBAR         |                      THÊM GIAO DỊCH                         |
|                        |                                                             |
| ◯ Xem danh mục         |  +-------------------------------------------------------+  |
| ◉ Thêm giao dịch       |  | Mã cổ phiếu (Symbol): [ Ví dụ: FPT                  ] |  |
| ◯ Cài đặt cảnh báo     |  |                                                       |  |
|                        |  | Loại giao dịch:       [ ( ) BUY      ( ) SELL       ] |  |
|                        |  |                                                       |  |
|                        |  | Số lượng:             [ Ví dụ: 1000                 ] |  |
|                        |  |                                                       |  |
|                        |  | Giá giao dịch:        [ Ví dụ: 95000                ] |  |
|                        |  |                                                       |  |
|                        |  | Ghi chú (Tùy chọn):   [ Nhập ghi chú...             ] |  |
|                        |  |                                                       |  |
|                        |  | [         Nút Bấm: Thêm Giao Dịch                   ] |  |
|                        |  +-------------------------------------------------------+  |
|                        |                                                             |
|                        |  [ Alert: Giao dịch thêm thành công! ]                      |
+------------------------+-------------------------------------------------------------+

```

* **Form Nhập Liệu:** Sử dụng khối `st.form` để đóng gói toàn bộ các thao tác thêm giao dịch.


* **Các Trường Thông Tin Bắt Buộc:** Yêu cầu nhập Mã cổ phiếu (symbol), Số lượng (quantity) lớn hơn 0, Giá (price) lớn hơn 0, và chọn Loại giao dịch (transaction_type) là BUY hoặc SELL.


* **Trường Thông Tin Tùy Chọn:** Cho phép nhập thêm Ghi chú (notes) nếu cần.


* **Xử Lý Logic:** Sau khi bấm lưu, hệ thống sẽ chuẩn hóa mã cổ phiếu (viết hoa, cắt khoảng trắng) và kiểm tra xem giao dịch SELL có vượt quá số lượng cổ phiếu đang khả dụng hay không.



---

## Wireframe 3: Màn hình Cài Đặt Cảnh Báo (Price Alerts)

Nơi người dùng cấu hình các mốc giá để nhận thông báo qua Telegram khi thị trường biến động.

```text
+------------------------+-------------------------------------------------------------+
|        SIDEBAR         |                      CÀI ĐẶT CẢNH BÁO                       |
|                        |                                                             |
| ◯ Xem danh mục         |  +--- Tạo Cảnh Báo Mới ----------------------------------+  |
| ◯ Thêm giao dịch       |  | Mã cổ phiếu: [ FPT ]      Loại: [ TAKE_PROFIT ▼ ]     |  |
| ◉ Cài đặt cảnh báo     |  |                                                       |  |
|                        |  | Điều kiện:   [ GREATER_THAN_OR_EQUAL (>=) ▼ ]         |  |
|                        |  |                                                       |  |
|                        |  | Giá mục tiêu:[ 115000 ]                               |  |
|                        |  |                                                       |  |
|                        |  | [               Nút Bấm: Tạo Cảnh Báo               ] |  |
|                        |  +-------------------------------------------------------+  |
|                        |                                                             |
|                        |  Danh Sách Cảnh Báo Đang Hoạt Động                          |
|                        |  | ID | Mã  | Giá Mục Tiêu | Điều Kiện | Loại        | Tắt| |
|                        |  | 1  | FPT | 115.000      | >=        | TAKE_PROFIT | [x]| |
|                        |  | 2  | VNM | 60.000       | <=        | STOP_LOSS   | [x]| |
+------------------------+-------------------------------------------------------------+

```

* **Giao Diện Cài Đặt:** Cung cấp form để người dùng thiết lập ngưỡng Cắt lỗ (STOP_LOSS) hoặc Chốt lời (TAKE_PROFIT) cho từng mã cổ phiếu cụ thể.


* **Cấu Hình Tham Số:** Cho phép chọn Điều kiện kích hoạt (condition) là Lớn hơn hoặc bằng (GREATER_THAN_OR_EQUAL) hoặc Nhỏ hơn hoặc bằng (LESS_THAN_OR_EQUAL) so với Mức giá mục tiêu (target_price).


* **Bảng Danh Sách Cảnh Báo:** Liệt kê các cảnh báo với các cột dữ liệu: id, symbol, target_price, condition, alert_type, is_active và created_at. Danh sách này sẽ sắp xếp các cảnh báo mới nhất lên trước.


* **Tính Năng Tắt Cảnh Báo:** Hỗ trợ người dùng thao tác tắt (deactivate) các cảnh báo đang ở trạng thái kích hoạt (active) thông qua ID của cảnh báo.