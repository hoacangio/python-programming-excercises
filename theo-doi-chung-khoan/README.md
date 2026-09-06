# Theo Dõi Chứng Khoán

Ứng dụng theo dõi danh mục chứng khoán bằng Python + Streamlit. Xem thiết kế chi tiết tại [docs/requirements.md](docs/requirements.md) và [docs/assignments.md](docs/assignments.md).

## 1. Yêu cầu ban đầu

- Python 3.10+ và Git (nếu chạy không dùng Docker)
- Docker và Docker Compose (nếu chạy bằng Docker)

Kiểm tra phiên bản Python:

```bash
python --version
```

Nếu chưa cài Python, bạn có thể tải tại:

- Windows: https://www.python.org/downloads/windows/
- macOS: https://www.python.org/downloads/macos/
- Linux: dùng trình quản lý gói của distro (apt, dnf, pacman,...)

## 2. Cài đặt và chạy bằng Docker (khuyến nghị)

### 2.1 Chuẩn bị file môi trường

```bash
cd theo-doi-chung-khoan
cp .env.example .env
```

Mở `.env` và điền `TELEGRAM_BOT_TOKEN` nếu muốn dùng tính năng cảnh báo qua Telegram. `DATABASE_URL` mặc định dùng SQLite (`sqlite:///data/portfolio.db`); file database nằm trong thư mục `data/` được mount vào container nên dữ liệu vẫn tồn tại sau khi `docker compose down`.

### 2.2 Build và chạy toàn bộ hệ thống

```bash
docker compose up --build
```

Lệnh này khởi chạy 2 service:

- `app`: Streamlit dashboard, truy cập tại http://localhost:8501
- `alert_bot`: worker quét cảnh báo giá, chạy độc lập với Streamlit

### 2.3 Chạy nền và dừng

```bash
docker compose up -d --build
docker compose down
```

## 3. Cài đặt và chạy không dùng Docker

### 3.1 Tạo môi trường ảo

#### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
```

#### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Sau khi kích hoạt thành công, dấu nhắc terminal sẽ hiện thêm `.venv`.

### 3.2 Cập nhật pip và cài thư viện

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3.3 Cấu hình biến môi trường

```bash
cp .env.example .env
```

Khi chạy không dùng Docker, giữ `DATABASE_URL=sqlite:///data/portfolio.db` (mặc định); file SQLite sẽ được tạo trong thư mục `data/`.

### 3.4 Chạy ứng dụng

```bash
streamlit run app.py
```

### 3.5 Chạy worker cảnh báo (tùy chọn)

```bash
python alert_bot.py
```

Bản đầu tiên dùng Cron để gọi lệnh trên mỗi 5 phút (xem [docs/requirements.md](docs/requirements.md) mục "Lưu ý kỹ thuật").

## 4. Chạy test

```bash
pytest
```

## 5. Lưu ý khi làm việc nhóm

- Không commit `.venv`, `.env` hoặc dữ liệu trong `data/` lên Git
- Khi thêm package mới, cập nhật lại `requirements.txt`
- Sau khi thêm giao dịch/cảnh báo, tải lại dữ liệu danh mục/cảnh báo tương ứng (không cache dữ liệu ghi)

## 6. Xử lý lỗi thường gặp

### Lỗi: "python is not recognized"

Cài Python và thêm vào PATH, hoặc trên Windows dùng:

```bash
py -3 -m venv .venv
```

### Lỗi: "No module named ..."

Môi trường ảo chưa được kích hoạt hoặc package chưa được cài:

```bash
pip install -r requirements.txt
```

### Lỗi: Streamlit không chạy

```bash
streamlit --version
```

Nếu không hiển thị phiên bản, cài lại Streamlit:

```bash
pip install streamlit
```

### Lỗi: `app` không ghi được database khi chạy Docker

Kiểm tra thư mục `data/` đã tồn tại và có quyền ghi (SQLite ghi file tại `/app/data/portfolio.db` trong container):

```bash
mkdir -p data
docker compose ps
```
