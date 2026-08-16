# Event Contract — IoT Ingestion → Analytics

## 1. Thông tin dependency

- Dependency số: #6
- Producer: IoT Ingestion
- Consumer: Analytics
- Cơ chế: Queue async
- Event/topic dự kiến: `telemetry.ingested`, `device.status.changed`
- Người ghi: Nhóm IoT Ingestion / Analytics
- Ngày: 2026-08-11

## 2. Mục đích nghiệp vụ

IoT Ingestion feed telemetry lên Analytics để tính toán aggregate theo giờ/ngày, làm dashboard, và nhận diện xu hướng thiết bị hoặc vùng.

## 3. Event name / topic

| Mục | Giá trị |
|---|---|
| Event name | `telemetry.ingested`, `device.status.changed` |
| Topic/queue | `campus.analytics.telemetry` |
| Producer | IoT Ingestion |
| Consumer | Analytics |

## 4. Payload — Mô tả chi tiết từng field

### 4.1. Envelope (metadata bắt buộc cho mọi event)

| Field | Type | Bắt buộc | Mô tả | Ví dụ |
|---|---|---|---|---|
| `eventId` | string (UUID) | ✅ | ID duy nhất của event, dùng để idempotency | `a1b2c3d4-e5f6-7890-abcd-ef1234567890` |
| `eventType` | string (enum) | ✅ | Loại event: `telemetry.ingested` hoặc `device.status.changed` | `telemetry.ingested` |
| `occurredAt` | string (ISO 8601) | ✅ | Thời điểm phát sinh event | `2026-08-11T09:15:00Z` |
| `correlationId` | string (UUID) | ✅ | ID trace xuyên service | `f1e2d3c4-b5a6-7890-abcd-ef1234567890` |
| `source` | string | ✅ | Tên service phát event | `iot-ingestion` |

### 4.2. Data — Telemetry payload

| Field | Type | Bắt buộc | Mô tả | Ví dụ |
|---|---|---|---|---|
| `deviceId` | string | ✅ | Mã định danh thiết bị IoT | `SENSOR-001` |
| `locationId` | string | ✅ | Khu vực/zone của thiết bị | `room-a101` |
| `metric` | string (enum) | ✅ | Loại chỉ số | `temperature` |
| `value` | number | ✅ | Giá trị đo được | `38.5` |
| `unit` | string | ✅ | Đơn vị đo | `celsius` |
| `status` | string | ✳️ | Trạng thái thiết bị nếu có | `online` |
| `sampledAt` | string (ISO 8601) | ✅ | Thời điểm cảm biến đo giá trị | `2026-08-11T09:14:58Z` |

### 4.3. Payload mẫu — `telemetry.ingested`

```json
{
  "eventId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "eventType": "telemetry.ingested",
  "occurredAt": "2026-08-11T09:15:00Z",
  "correlationId": "f1e2d3c4-b5a6-7890-abcd-ef1234567890",
  "source": "iot-ingestion",
  "data": {
    "deviceId": "SENSOR-001",
    "locationId": "room-a101",
    "metric": "temperature",
    "value": 38.5,
    "unit": "celsius",
    "sampledAt": "2026-08-11T09:14:58Z"
  }
}
```

## 5. Quy tắc đơn vị (unit) theo metric

| metric | unit | Khoảng giá trị hợp lệ |
|---|---|---|
| `temperature` | `celsius` | -40 đến 100 |
| `humidity` | `percent` | 0 đến 100 |
| `smoke` | `ppm` | 0 đến 10000 |
| `motion` | `boolean` | 0 hoặc 1 |

## 6. Ràng buộc cần thống nhất


| Vấn đề | Quyết định tạm thời |
|---|---|
| `eventId` có bắt buộc không? | ✅ Có — UUID, Analytics xử lý idempotent |
| `correlationId` có bắt buộc không? | ✅ Có — để nối các luồng telemetry và alert |
| `occurredAt` hay `timestamp`? | ✅ `occurredAt` — thống nhất metadata event |
| `deviceId` hay `locationId` cho aggregate? | ✅ Cả hai — deviceId cho thiết bị, locationId cho vùng |
| Event `telemetry.ingested` có gửi mọi lần đo? | ✅ Có — dùng để aggregate thời gian thực và lịch sử |
| Event `device.status.changed` có cần không? | ✅ Có — để Analytics hiển thị trạng thái thiết bị và cảnh báo downtime |
| Retry khi lỗi | IoT retry 3 lần, interval 2s — nếu vẫn lỗi thì cảnh báo vào dead-letter |

## 7. Issue chuyển sang Lab 03

1. Đặc tả AsyncAPI cho topic `campus.analytics.telemetry`
2. Thống nhất schema mẫu cho `telemetry.ingested` và `device.status.changed`
3. Quy tắc batching nếu nhiều sensor gửi cùng lúc
4. Cách xử lý dead-letter khi Analytics không parse payload
