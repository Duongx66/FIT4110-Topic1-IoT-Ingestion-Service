# RUN_COMPOSE.md – Hướng dẫn chạy Lab 05

Tài liệu này hướng dẫn người khác clone repo sạch và chạy lại stack Compose của Lab 05.

---

## 1. Clone repo

```bash
git clone <repo-url>
cd FIT4110_lab05_docker_compose_readiness
```

---

## 2. Cài dependencies cho Newman/Prism/Spectral (tuỳ chọn)

```bash
npm install
```

---

## 3. Build & chạy stack Docker Compose
npm run test:compose
```bash
# Copy .env.example sang .env và chỉnh sửa nếu cần
cp .env.example .env

# Build images (nếu chưa có) và khởi động các container trong nền
docker compose up -d --build
```

Lệnh trên sẽ tạo các container:

- `fit4110-db-lab05` (PostgreSQL)
- `fit4110-ai-lab05` (AI service mẫu chạy port 9000)
- `fit4110-api-lab05` (API FastAPI trên port 8000)

Theo dõi log:

```bash
docker compose logs -f
```

Sau vài giây, kiểm tra health của mỗi service:

```bash
# API
curl http://localhost:8000/health

# AI service
curl http://localhost:9000/health

# DB readiness
docker exec -it fit4110-db-lab05 pg_isready -U $POSTGRES_USER
```

Khi bật cấu hình Analytics trong `.env`, API sẽ publish event envelope vào broker anonymous `192.168.1.51:1883`, topic `iot.telemetry`. Kiểm tra trạng thái:

```bash
curl http://localhost:8000/health
```

Giá trị mong đợi là `analytics_status: connected`.

API đọc registry thiết bị từ `data/IoT_device_registry.csv`. Gửi một raw environment sample để service validate, normalize và classify:

```bash
curl -X POST http://localhost:8000/ingest/raw \
	-H "Authorization: Bearer local-dev-token" \
	-H "Content-Type: application/json" \
	-d '{"event_id":"raw-demo-001","event_type":"iot.environment.sampled","device_id":"esp32-lab-a101","timestamp":"2026-08-26T09:00:00Z","temperature_c":31.2,"humidity_percent":68.5,"motion_detected":false,"light_lux":420,"co2_ppm":650,"smoke_ppm":0.02,"battery_percent":87}'
```

Thiết bị không có trong registry sẽ được trả về với `status=invalid_device`, `alertLevel=high` và `reason=device_not_registered`.

Bạn cũng có thể truy cập endpoint `/predict` của AI service để xem kết quả mẫu:

```bash
curl -X POST http://localhost:9000/predict
```

---

## 4. Chạy Newman test trên stack Compose (tuỳ chọn)

```bash
npm run test:compose
```

Report sinh tại:

```text
reports/newman-lab05-compose.xml
reports/newman-lab05-compose.html
```

---

## 5. Dừng stack

Khi không cần nữa, dừng và xoá các container bằng:

```bash
docker compose down
```

Nếu muốn xoá volume dữ liệu của DB, thêm tuỳ chọn `-v`:

```bash
docker compose down -v
```

---

## 6. Lệnh nhanh

Bạn có thể dùng Makefile:

```bash
make compose-up
make compose-down
make logs
```

---

## 7. Mẹo gỡ lỗi

- Sử dụng `docker compose ps` để xem trạng thái container.
- Nếu API trả lỗi kết nối DB, hãy kiểm tra biến môi trường `POSTGRES_*` trong `.env` và đảm bảo DB đã sẵn sàng (`pg_isready`).
- Nếu AI service cần tải mô hình lớn, tăng `start_period` của healthcheck trong `docker-compose.yml`.