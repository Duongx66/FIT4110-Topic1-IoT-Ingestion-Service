# BIÊN BẢN ĐÀM PHÁN HỢP ĐỒNG API / EVENT CONTRACT

## Thông tin chung

* **Dependency:** Pair 06
* **Product:** Smart Campus Operations Platform
* **Producer / Provider:** IoT Ingestion (Product B)
* **Consumer:** Analytics Service (Product A)
* **Cơ chế tích hợp:** Message Queue / Event Bus
* **Topic/Queue:** `iot.telemetry`
* **Phiên bản:** v1.0
* **Ngày:** 2026-08-11
* **Người ghi:** Nhóm Analytics Service (Product A)

---

# Issue #1 — Thống nhất Event và Topic

* **Raised by:** Consumer
* **Endpoint:** Event message
* **Concern:** Analytics Service cần xác định rõ các loại event để xử lý đúng nghiệp vụ telemetry và trạng thái thiết bị.

### Proposal

IoT Ingestion sẽ publish 2 loại event:

* `telemetry.ingested`
* `device.status.changed`

Cả hai event sử dụng chung Topic/Queue:

`iot.telemetry`

### Resolution

**Accepted**

### Rationale

Analytics Service cần nhận cả hai loại event để:

* Aggregate dữ liệu telemetry.
* Theo dõi trạng thái hoạt động của thiết bị.
* Phát hiện thiết bị mất kết nối.
* Tổng hợp trạng thái theo khu vực.
* Cung cấp dữ liệu cho Dashboard.
* Phục vụ `TemperatureMetric` và `DailySummaryReport`.

### Impact

Provider phải publish đúng `eventType` đã thỏa thuận và gửi event vào Topic/Queue `iot.telemetry`.

---

# Issue #2 — Thống nhất khóa aggregate

* **Raised by:** Consumer
* **Endpoint:** Event payload
* **Concern:** Analytics Service cần khóa rõ ràng để aggregate dữ liệu theo thiết bị và khu vực.

### Proposal

Payload phải có:

* `deviceId`
* `zoneId`

Analytics Service sử dụng kết hợp:

* `deviceId`
* `zoneId`
* `time_bucket`

để phục vụ aggregate theo giờ/ngày.

### Resolution

**Accepted**

### Rationale

* `deviceId` xác định thiết bị phát sinh telemetry.
* `zoneId` xác định khu vực hoạt động của thiết bị.
* `time_bucket` do Analytics Service xác định từ timestamp để aggregate theo giờ hoặc ngày.

Ví dụ:

```text
deviceId = SENSOR-001
zoneId   = ZONE-A
date     = 2026-08-11
hour     = 09
```

### Impact

Provider phải gửi đầy đủ `deviceId` và `zoneId`.

Consumer sử dụng hai trường này làm khóa phục vụ aggregate.

---

# Issue #3 — Idempotency và Event ID

* **Raised by:** Consumer
* **Endpoint:** Event payload
* **Concern:** Event có thể bị gửi lại do retry, dẫn đến nguy cơ double count trong Analytics Service.

### Proposal

* `eventId` là bắt buộc.
* `eventId` phải có định dạng UUID.
* Analytics Service thực hiện deduplicate theo `eventId`.

### Resolution

**Accepted**

### Rationale

Event Bus hoặc Message Queue có thể thực hiện retry hoặc gửi trùng event. Việc dedupe theo `eventId` giúp tránh:

* Double count.
* Aggregate sai.
* Lưu trữ dữ liệu trùng lặp.

### Impact

Provider cần tạo `eventId` duy nhất và hợp lệ.

Consumer phải kiểm tra trùng lặp trước khi xử lý event.

---

# Issue #4 — Phân biệt occurredAt, sampledAt và changedAt

* **Raised by:** Provider
* **Endpoint:** Event payload
* **Concern:** Các timestamp có ý nghĩa khác nhau và cần được thống nhất để tránh Analytics Service xử lý sai dữ liệu.

### Proposal

Đối với `telemetry.ingested`:

* `occurredAt`: thời điểm IoT Ingestion phát sinh/publish event.
* `sampledAt`: thời điểm cảm biến thực hiện đo dữ liệu.

Đối với `device.status.changed`:

* `occurredAt`: thời điểm IoT Ingestion publish event.
* `changedAt`: thời điểm trạng thái thiết bị thực sự thay đổi.

Tất cả timestamp sử dụng chuẩn:

`ISO 8601 UTC`

### Resolution

**Accepted**

### Rationale

Analytics Service cần phân biệt:

* Thời điểm dữ liệu được cảm biến thu thập.
* Thời điểm event được publish.
* Thời điểm trạng thái thiết bị thay đổi.

Việc này hỗ trợ:

* Phát hiện stale data.
* Xử lý event đến không đúng thứ tự.
* Aggregate chính xác theo thời gian.
* Phân tích trend.

### Impact

Provider phải gửi timestamp đúng ngữ nghĩa của từng event.

Consumer sử dụng timestamp phù hợp cho từng nghiệp vụ aggregate và monitoring.

---

# Issue #5 — Correlation ID

* **Raised by:** Consumer
* **Endpoint:** Event envelope
* **Concern:** Analytics Service cần trace luồng xử lý event và có thể liên kết event với các hệ thống downstream khác.

### Proposal

`correlationId` là trường **bắt buộc** đối với cả hai loại event.

### Resolution

**Accepted**

### Rationale

`correlationId` giúp:

* Trace luồng xử lý.
* Liên kết các event liên quan.
* Hỗ trợ debugging.
* Hỗ trợ theo dõi lỗi giữa các service.

### Impact

Provider phải gửi `correlationId` hợp lệ trong mỗi event.

Consumer có thể sử dụng trường này để trace và liên kết các luồng xử lý.

---

# Issue #6 — Thống nhất metric, value và unit

* **Raised by:** Consumer
* **Endpoint:** Payload của `telemetry.ingested`
* **Concern:** Analytics Service cần đơn vị thống nhất để aggregate và hiển thị Dashboard chính xác.

### Proposal

Thống nhất:

| metric        | unit      |
| ------------- | --------- |
| `temperature` | `celsius` |
| `humidity`    | `percent` |
| `smoke`       | `ppm`     |
| `motion`      | `boolean` |

`value` không được `null` đối với event `telemetry.ingested` hợp lệ.

### Resolution

**Accepted**

### Rationale

Việc thống nhất đơn vị giúp Analytics Service:

* Aggregate chính xác.
* So sánh dữ liệu giữa các thiết bị.
* Hiển thị Dashboard đúng đơn vị.
* Tính toán `TemperatureMetric` và các báo cáo tổng hợp.

### Impact

Provider phải gửi `metric`, `value` và `unit` phù hợp.

Consumer có thể dựa trên `metric` và `unit` để xử lý dữ liệu.

---

# Issue #7 — Chuẩn hóa Event Envelope

* **Raised by:** Consumer
* **Endpoint:** Event metadata
* **Concern:** Analytics Service cần metadata thống nhất để nhận diện nguồn event và xử lý các event theo một cấu trúc chung.

### Proposal

Cả hai event sử dụng envelope chung gồm:

* `eventId`
* `eventType`
* `occurredAt`
* `correlationId`
* `source`
* `data`

Trong đó:

```text
source = "iot-ingestion"
```

là giá trị bắt buộc.

### Resolution

**Accepted**

### Rationale

Envelope thống nhất giúp Consumer:

* Nhận diện Producer.
* Xác định loại event.
* Trace event.
* Dedupe event.
* Xử lý các event theo một cấu trúc chung.

### Impact

Provider phải tuân thủ cấu trúc envelope đã thống nhất.

Analytics Service sẽ đọc `eventType` để xác định loại xử lý và `source` để xác định nguồn phát sinh event.

---

# Hợp đồng Event đã thống nhất

## 1. Event: `telemetry.ingested`

Event được phát sinh khi IoT Ingestion nhận được một bản ghi telemetry hợp lệ từ thiết bị.

```json
{
  "eventId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "eventType": "telemetry.ingested",
  "occurredAt": "2026-08-11T09:15:00Z",
  "correlationId": "f1e2d3c4-b5a6-7890-abcd-ef1234567890",
  "source": "iot-ingestion",
  "data": {
    "deviceId": "SENSOR-001",
    "zoneId": "ZONE-A",
    "metric": "temperature",
    "value": 38.5,
    "unit": "celsius",
    "sampledAt": "2026-08-11T09:14:58Z"
  }
}
```

Analytics Service sử dụng event này để:

* Aggregate telemetry theo `deviceId`.
* Aggregate telemetry theo `zoneId`.
* Aggregate theo giờ/ngày.
* Tính average, minimum và maximum.
* Phục vụ Dashboard.
* Tổng hợp `TemperatureMetric`.
* Tạo dữ liệu cho `DailySummaryReport`.

---

## 2. Event: `device.status.changed`

Event được phát sinh khi trạng thái của thiết bị IoT thay đổi.

```json
{
  "eventId": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "eventType": "device.status.changed",
  "occurredAt": "2026-08-11T09:20:00Z",
  "correlationId": "a2b3c4d5-e6f7-8901-abcd-234567890123",
  "source": "iot-ingestion",
  "data": {
    "deviceId": "SENSOR-001",
    "zoneId": "ZONE-A",
    "previousStatus": "ONLINE",
    "currentStatus": "OFFLINE",
    "changedAt": "2026-08-11T09:20:00Z"
  }
}
```

Analytics Service sử dụng event này để:

* Theo dõi trạng thái thiết bị.
* Thống kê số lượng thiết bị `ONLINE` / `OFFLINE`.
* Xác định thiết bị mất kết nối.
* Tổng hợp trạng thái thiết bị theo `zoneId`.
* Phục vụ các KPI về tình trạng hệ thống IoT.

---

# Payload tối thiểu đã thống nhất

## Event Envelope chung

| Trường          | Kiểu          | Bắt buộc | Quy định                                          |
| --------------- | ------------- | -------- | ------------------------------------------------- |
| `eventId`       | UUID          | Có       | Dùng để idempotency và dedupe                     |
| `eventType`     | String / Enum | Có       | `telemetry.ingested` hoặc `device.status.changed` |
| `occurredAt`    | ISO 8601 UTC  | Có       | Thời điểm event được publish                      |
| `correlationId` | UUID / String | Có       | Dùng để trace luồng                               |
| `source`        | String        | Có       | Giá trị `iot-ingestion`                           |
| `data`          | Object        | Có       | Payload nghiệp vụ                                 |

## Payload của telemetry.ingested

| Trường      | Bắt buộc | Ý nghĩa                                      |
| ----------- | -------- | -------------------------------------------- |
| `deviceId`  | Có       | ID của thiết bị                              |
| `zoneId`    | Có       | Khu vực của thiết bị                         |
| `metric`    | Có       | `temperature`, `humidity`, `smoke`, `motion` |
| `value`     | Có       | Không được null                              |
| `unit`      | Có       | Phụ thuộc vào metric                         |
| `sampledAt` | Có       | Thời điểm cảm biến đo dữ liệu                |

## Payload của device.status.changed

| Trường           | Bắt buộc | Ý nghĩa                       |
| ---------------- | -------- | ----------------------------- |
| `deviceId`       | Có       | ID thiết bị                   |
| `zoneId`         | Có       | Khu vực thiết bị              |
| `previousStatus` | Có       | Trạng thái trước khi thay đổi |
| `currentStatus`  | Có       | Trạng thái mới                |
| `changedAt`      | Có       | Thời điểm trạng thái thay đổi |

---

# Ràng buộc đã thống nhất

| Vấn đề                   | Quyết định                                                           |
| ------------------------ | -------------------------------------------------------------------- |
| `eventId` bắt buộc       | Có                                                                   |
| `eventType` bắt buộc     | Có                                                                   |
| `occurredAt` bắt buộc    | Có                                                                   |
| `correlationId` bắt buộc | Có                                                                   |
| `source` bắt buộc        | Có                                                                   |
| `deviceId` bắt buộc      | Có                                                                   |
| `zoneId` bắt buộc        | Có                                                                   |
| Timestamp                | ISO 8601 UTC                                                         |
| `value` được null        | Không đối với `telemetry.ingested` hợp lệ                            |
| Event có thể gửi trùng   | Có                                                                   |
| Consumer phải idempotent | Có                                                                   |
| Dedupe key               | `eventId`                                                            |
| Retry                    | Sẽ đặc tả tại Lab 03                                                 |
| Dead-Letter Queue        | Sẽ đặc tả tại Lab 03                                                 |
| Event ordering           | Chưa đảm bảo, Consumer cần xử lý event đến không đúng thứ tự nếu cần |

---

# Error Cases / Các vấn đề đã ghi nhận

Hai bên thống nhất cần tiếp tục đặc tả ở các Lab tiếp theo đối với các trường hợp:

1. Dữ liệu telemetry sai định dạng.
2. Thiếu `deviceId`, `zoneId` hoặc `correlationId`.
3. `eventType` không thuộc hai event đã thỏa thuận.
4. `metric` không thuộc danh sách metric được hỗ trợ.
5. `unit` không phù hợp với `metric`.
6. `value` bị null đối với telemetry hợp lệ.
7. Producer và Consumer hiểu khác nhau về trạng thái `ONLINE` / `OFFLINE`.
8. Event bị gửi trùng do retry.
9. Event đến không đúng thứ tự.
10. Consumer không thể xử lý event.
11. Lỗi hoặc timeout ở downstream.
12. Event không hợp lệ cần được xử lý thông qua cơ chế retry hoặc Dead-Letter Queue trong đặc tả tiếp theo.

---

# Chốt hợp đồng v1.0

Hai bên thống nhất hợp đồng tích hợp event giữa IoT Ingestion và Analytics Service như sau:

* **Producer:** IoT Ingestion
* **Consumer:** Analytics Service
* **Topic/Queue:** `iot.telemetry`
* **Cơ chế:** Message Queue / Event Bus
* **Event 1:** `telemetry.ingested`
* **Event 2:** `device.status.changed`
* **Aggregate keys:** `deviceId`, `zoneId`, `time_bucket`
* **Idempotency key:** `eventId`
* **Trace key:** `correlationId`
* **Event source:** `iot-ingestion`
* **Timestamp format:** ISO 8601 UTC

---

**Provider sign-off:** IoT Ingestion Team

**Consumer sign-off:** Analytics Service Team

**Witness (GV/TA):** __________________________

**Date:** 2026-08-11

---

# Ghi chú Warning nếu Spectral còn cảnh báo

| Warning                                                  | Lý do chấp nhận tạm thời                                                 | Kế hoạch sửa                                                                  |
| -------------------------------------------------------- | ------------------------------------------------------------------------ | ----------------------------------------------------------------------------- |
| Một số trường enum hoặc schema chưa được validate đầy đủ | Hợp đồng v1.0 ưu tiên thống nhất cấu trúc event và payload giữa hai nhóm | Bổ sung schema validation trong OpenAPI/AsyncAPI                              |
| Retry policy chưa được định nghĩa                        | Chưa nằm trong phạm vi Lab 02                                            | Đặc tả retry tại Lab 03                                                       |
| Dead-Letter Queue chưa được định nghĩa                   | Chưa nằm trong phạm vi phiên bản contract hiện tại                       | Bổ sung DLQ và error handling tại Lab 03                                      |
| Event ordering chưa được đảm bảo                         | Message Queue/Event Bus có thể deliver event không theo thứ tự           | Consumer xử lý stale/out-of-order event dựa trên `sampledAt` hoặc `changedAt` |
