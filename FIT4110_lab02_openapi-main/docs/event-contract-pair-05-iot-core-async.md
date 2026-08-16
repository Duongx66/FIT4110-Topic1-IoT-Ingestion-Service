# Event Contract — IoT Ingestion → Core Business

- Dependency số: 5
- Producer: IoT Ingestion
- Consumer: Core Business
- Cơ chế: Queue async
- Event name chính:
  - `iot.sensor.reading.created`
  - `iot.sensor.threshold.exceeded`
- Topic/queue đề xuất: `iot.sensor.events`
- Người ghi: Student
- Ngày: 2026-08-11

## 1. Mục đích nghiệp vụ

IoT Ingestion publish sự kiện cảm biến mới để Core Business đánh giá policy, phát hiện bất thường hoặc kích hoạt workflow xử lý khi giá trị vượt ngưỡng.

## 2. Event name / topic

| Mục | Giá trị |
|---|---|
| Event name | `iot.sensor.reading.created` hoặc `iot.sensor.threshold.exceeded` |
| Topic/queue | `iot.sensor.events` |
| Producer | IoT Ingestion |
| Consumer | Core Business |
| Cơ chế | Queue async |

## 3. Payload tối thiểu

```json
{
  "eventId": "uuid",
  "eventType": "iot.sensor.reading.created",
  "occurredAt": "2026-08-11T12:00:00Z",
  "correlationId": "uuid",
  "source": "iot-ingestion",
  "deviceId": "SENSOR-001",
  "sensorType": "temperature",
  "value": 38.5,
  "unit": "celsius",
  "timestamp": "2026-08-11T12:00:00Z",
  "locationId": "LOC-01"
}
```

### 3.1. Thuộc tính bắt buộc

- `eventId`: UUID duy nhất của event.
- `eventType`: `iot.sensor.reading.created` hoặc `iot.sensor.threshold.exceeded`.
- `occurredAt`: Thời điểm event được publish.
- `source`: Tên service producer, ví dụ `iot-ingestion`.
- `deviceId`: Mã thiết bị cảm biến.
- `sensorType`: Loại cảm biến, enum: `temperature`, `humidity`, `smoke`, `motion`.
- `value`: Giá trị đo được.
- `unit`: Đơn vị đo tương ứng với `sensorType`.
- `timestamp`: Thời điểm cảm biến đo.

### 3.2. Thuộc tính tùy chọn

- `correlationId`: UUID để trace workflow xuyên service.
- `locationId`: Mã vị trí lắp đặt thiết bị.
- `threshold`: Mức ngưỡng đã vượt cho event `iot.sensor.threshold.exceeded`.

## 4. Ràng buộc cần thống nhất

| Vấn đề | Quyết định tạm thời |
|---|---|
| Event id bắt buộc không? | Có, `eventId` phải là UUID và duy nhất. |
| Có cần `correlationId` không? | Có, optional nhưng rất khuyến khích. |
| Có gửi event duplicate không? | Có thể, consumer phải xử lý idempotent. |
| Retry khi lỗi | Producer retry, consumer dedupe theo `eventId`. |
| Dead-letter queue | Được ghi nhận ở Lab 03. |
| `unit` | Chốt theo `sensorType`: `temperature` => `celsius`, `humidity` => `percent`, `smoke` => `ppm`, `motion` => `event`. |

## 5. Ghi chú kỹ thuật

- `eventType` dùng định danh đầy đủ domain-style.
- Payload định dạng JSON.
- Consumer có thể sử dụng `eventId` để tránh xử lý lại hoặc lưu log.
- Nếu `timestamp` quá cũ so với `occurredAt`, consumer có thể coi là stale.

## 6. Issue chuyển sang Lab 03

1. Thiết kế retry/backoff và dead-letter queue cho event async.
2. Cơ chế version event schema nếu payload thay đổi.
3. Phân quyền và bảo mật cho broker/topic.
