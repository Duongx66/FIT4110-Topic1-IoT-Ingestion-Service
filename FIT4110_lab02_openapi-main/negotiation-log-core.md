# Biên bản đàm phán hợp đồng API

- Cặp đàm phán: Pair 05
- Product: Smart Campus Operations Platform
- Provider: IoT Ingestion
- Consumer: Core Business
- Phiên: v1.0
- Ngày:

---

## Issue #1

- Raised by: Consumer
- Endpoint: Event message `iot.sensor.reading.created`
- Concern: Consumer cần xác định danh sách `sensorType` hợp lệ.
- Proposal: IoT Ingestion sẽ dùng enum `sensorType` gồm `[temperature, humidity, smoke, motion]`.
- Resolution: Accepted
- Rationale: Chốt danh sách giúp tránh mismatch khi Core Business phân tích dữ liệu.
- Impact: Provider phải validate `sensorType` trước khi publish.

---

## Issue #2

- Raised by: Provider
- Endpoint: Event message `iot.sensor.threshold.exceeded`
- Concern: Core Business cần biết ngưỡng đã vượt.
- Proposal: Thêm field `threshold` trong payload cảnh báo.
- Resolution: Accepted
- Rationale: `threshold` giúp Core Business xác định mức độ nghiêm trọng và ưu tiên xử lý.
- Impact: Payload threshold event cần thêm field bắt buộc.

---

## Issue #3

- Raised by: Consumer
- Endpoint: Event payload
- Concern: Cần định danh event duy nhất để xử lý idempotent.
- Proposal: Bắt buộc `eventId` là UUID và Core Business sẽ dedupe theo `eventId`.
- Resolution: Accepted
- Rationale: Tránh xử lý lặp khi event được gửi lại do retry.
- Impact: Provider cần tạo eventId hợp lệ và consumer phải lưu trạng thái đã xử lý.

---

## Issue #4

- Raised by: Provider
- Endpoint: Event payload
- Concern: `timestamp` và `occurredAt` có thể bị nhầm lẫn.
- Proposal: `timestamp` là thời điểm cảm biến đo, `occurredAt` là thời điểm IoT Ingestion publish event.
- Resolution: Accepted
- Rationale: Phân biệt rõ hai mốc giúp consumer xác định nếu event bị stale.
- Impact: Provider nên gửi cả hai trường nếu có thể.

---

## Issue #5

- Raised by: Consumer
- Endpoint: Event payload
- Concern: `correlationId` cần để trace workflow.
- Proposal: `correlationId` là optional nhưng khuyến khích gửi.
- Resolution: Accepted
- Rationale: Không bắt buộc để tránh block producer, nhưng vẫn hỗ trợ trace khi có.
- Impact: Provider vẫn publish event nếu không có trường này.

---

## Issue #6

- Raised by: Consumer
- Endpoint: Event payload
- Concern: `unit` cần thống nhất theo loại sensor.
- Proposal: Định rõ đơn vị theo `sensorType`: `temperature` => `celsius`, `humidity` => `percent`, `smoke` => `ppm`, `motion` => `event`.
- Resolution: Accepted
- Rationale: Giữ payload dễ parse và tránh sai lệch khi xử lý policy.
- Impact: Provider cần gửi đơn vị phù hợp với sensorType.

---

## Issue #7

- Raised by: Consumer
- Endpoint: Envelope metadata
- Concern: Envelope metadata cần thống nhất để chuẩn hóa event cho toàn hệ thống.
- Proposal: Dùng `occurredAt` thay vì `timestamp` cho envelope metadata và bổ sung trường `source = "iot-ingestion"`.
- Resolution: Accepted
- Rationale: `occurredAt` giúp phân biệt thời điểm IoT Ingestion publish event, `source` giúp xác định service producer rõ ràng.
- Impact: Provider cần cập nhật event payload metadata và ghi nhận thỏa thuận này trong contract.

---

# Chốt hợp đồng v1.0

Provider sign-off: IoT Ingestion Team
Consumer sign-off: Core Business Team
Witness (GV/TA):    
Date: 2026-08-11

---

## Ghi chú warning nếu Spectral còn cảnh báo

| Warning | Lý do chấp nhận tạm thời | Kế hoạch sửa |
|---|---|---|
|  |  |  |
