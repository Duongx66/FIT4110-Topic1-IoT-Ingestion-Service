# Phân tích yêu cầu — vai Provider

- Cặp đàm phán: Pair 05
- Product: Smart Campus Operations Platform
- Provider service: IoT Ingestion
- Consumer service: Core Business
- Người viết: Student
- Ngày: 2026-08-11

---

## 1. Resource chính

| Resource | Mô tả | Thuộc tính bắt buộc | Thuộc tính tùy chọn |
|---|---|---|---|
| SensorEvent | Dữ liệu cảm biến được publish lên queue | eventId, eventType, deviceId, sensorType, value, unit, timestamp | correlationId, locationId, source, occurredAt |
| ThresholdEvent | Event cảnh báo khi cảm biến vượt threshold | eventId, eventType, deviceId, sensorType, value, unit, threshold, timestamp | correlationId, locationId, source, occurredAt |

---

## 2. Action/API dự kiến

| Method | Path | Mục đích | Consumer gọi khi nào? |
|---|---|---|---|
| POST | queue/topic message | Publish sensor event mới | IoT Ingestion gửi khi có dữ liệu cảm biến mới |
| POST | queue/topic message | Publish threshold exceeded event | IoT Ingestion gửi khi cảm biến vượt ngưỡng |

---

## 3. Error case

| Status | Tình huống | Response body dự kiến |
|---:|---|---|
| 400 | Payload sai định dạng | `Problem` hoặc reject event với lý do validation |
| 422 | Dữ liệu đúng JSON nhưng sai business rule | `Problem` hoặc event bị loại bỏ |
| 409 | Dispatch event duplicate | `Problem` hoặc dedupe log |
| 500 | Lỗi hệ thống queue hoặc broker | `Problem` hoặc retry later |
| 503 | Hệ thống downstream quá tải | `Problem` hoặc send to DLQ |

---

## 4. Giả định bổ sung

- IoT Ingestion chịu trách nhiệm xác thực `eventId` là UUID và gửi `sensorType` hợp lệ.
- Core Business chấp nhận event async và xử lý idempotently.
- Nếu không có `correlationId`, IoT Ingestion vẫn publish nhưng ghi remark.

---

## 5. Câu hỏi cho Consumer

1. Core Business có cần `locationId` để xác định vùng hay chỉ cần `deviceId`?
2. Nếu `sensorType` mở rộng, IoT Ingestion nên gửi raw string hay chỉ dùng enum đã định nghĩa?
3. Người dùng muốn event stale bị loại bỏ sau bao lâu?

---

## 6. Rủi ro tích hợp

| Rủi ro | Tác động | Đề xuất xử lý |
|---|---|---|
| `sensorType` khác nhau giữa producer và consumer | Core Business không xử lý đúng | Chốt danh sách `sensorType` hoặc dùng enum mở rộng |
| `value` không đồng bộ đơn vị | Sai phân tích policy | Chốt `unit` cố định cho từng loại cảm biến |
| `eventId` trùng | Dữ liệu bị xử lý lặp | Dùng idempotency và reject duplicate |
| Thiếu `correlationId` | Khó trace | Đặt correlationId optional nhưng khuyến khích gửi |
