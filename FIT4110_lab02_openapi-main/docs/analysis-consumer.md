# Phân tích yêu cầu — vai Consumer

- Cặp đàm phán: Pair 05
- Product: Smart Campus Operations Platform
- Consumer service: Core Business
- Provider service: IoT Ingestion
- Người viết: Student
- Ngày: 2026-08-11

---

## 1. Resource Consumer cần nhận

| Resource | Consumer dùng để làm gì? | Field bắt buộc với Consumer | Field có thể tùy chọn |
|---|---|---|---|
| SensorEvent | Nhận dữ liệu cảm biến thô để đánh giá policy / bất thường | eventId, eventType, deviceId, sensorType, value, unit, timestamp | correlationId, locationId, source, occurredAt |
| ThresholdEvent | Nhận cảnh báo vượt ngưỡng để kích hoạt workflow xử lý | eventId, eventType, deviceId, sensorType, value, unit, timestamp, threshold | correlationId, locationId, source, occurredAt |

---

## 2. Event Consumer mong muốn

| Cơ chế | Event name | Khi nào nhận | Kỳ vọng xử lý |
|---|---|---|---|
| Queue async | `iot.sensor.reading.created` | IoT Ingestion gửi sensor đọc mới | Cập nhật trạng thái policy và điều phối rule kiểm tra |
| Queue async | `iot.sensor.threshold.exceeded` | Khi sensor vượt ngưỡng cài đặt | Tạo alert nội bộ và kiểm tra tác động |

---

## 3. Error case Consumer cần xử lý

| Tình huống | Consumer hiểu là gì? | Consumer sẽ xử lý thế nào? |
|---|---|---|---|
| Sự kiện thiếu field bắt buộc | Payload không hợp lệ | Bỏ qua event, log lỗi, có thể gửi metric `invalid_event` |
| sensorType không hợp lệ | Data contract mismatch | Bỏ qua, yêu cầu điều tra phía IoT Ingestion |
| value ngoài khoảng hợp lệ | Dữ liệu sensor bị nhiễu | Bỏ qua hoặc gán category `out_of_range` |
| Trùng eventId / duplicate | Retry lặp lại | Dedupe bằng eventId, chỉ xử lý 1 lần |
| Sự kiện quá cũ | Dữ liệu stale | Bỏ qua nếu `timestamp` xa quá so với `occurredAt` hoặc giờ hiện tại |
| Thiếu correlationId khi cần trace | Khó debug | Ghi cảnh báo và vẫn xử lý nếu dữ liệu hợp lệ |

---

## 4. Giả định bổ sung

- IoT Ingestion chịu trách nhiệm đảm bảo `eventId` là UUID duy nhất.
- `timestamp` là thời điểm cảm biến đo được, `occurredAt` là thời điểm event được publish.
- Core Business sẽ xử lý event idempotently nếu nhận lại nhiều lần.

---

## 5. Câu hỏi cho Provider

1. `sensorType` có danh sách giá trị cố định hay mở rộng động?
2. IoT Ingestion có gửi `locationId` không nếu thiết bị gắn cố định?
3. Nếu event gửi thiếu `correlationId`, Core Business có chấp nhận không?

---

## 6. Rủi ro tích hợp

| Rủi ro | Tác động | Đề xuất xử lý |
|---|---|---|
| Định danh event không đồng nhất | Core Business không biết event nào nhận | Chốt `eventType` cố định trong contract |
| Thiếu `eventId` hoặc trùng `eventId` | Dữ liệu bị xử lý lặp | Bắt buộc `eventId` và consumer phải dedupe |
| Sai `format` timestamp | Không so sánh được thời gian | Chốt `date-time` ISO 8601 và validate tại producer |
| `unit` không thống nhất | Sai tính toán policy | Chốt đơn vị cố định cho từng `sensorType` |
| Payload mở rộng không báo trước | Consumer parse lỗi | Dùng `additionalProperties: false` hoặc chốt schema rõ ràng |
