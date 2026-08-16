$ErrorActionPreference = "Stop"

$BaseUrl = if ($env:BASE_URL) { $env:BASE_URL } else { "http://localhost:4010" }
$AuthHeader = "Authorization: Bearer test-token"

Write-Host "[Lab02] Testing Prism mock server at $BaseUrl"
Write-Host ""

Write-Host "[1/5] Happy path: GET /health"
curl.exe -i "$BaseUrl/health"
Write-Host "`n---"

Write-Host "[2/5] Happy path: GET /sensor-events/recent"
curl.exe -i "$BaseUrl/sensor-events/recent" -H $AuthHeader
Write-Host "`n---"

Write-Host "[3/5] Happy path: POST /sensor-events"
$payload = '{
  "eventType": "SENSOR_READING",
  "eventId": "0196fb3d-4ad7-7d1e-9f49-5d5148d2babc",
  "occurredAt": "2026-08-11T12:00:00Z",
  "correlationId": "5f8d9abc-1234-4d5e-9f01-23456789abcd",
  "source": "iot-ingestion",
  "deviceId": "SENSOR-001",
  "sensorType": "temperature",
  "value": 38.5,
  "unit": "celsius",
  "timestamp": "2026-08-11T11:59:58Z",
  "locationId": "LOC-01"
}'
curl.exe -i -X POST "$BaseUrl/sensor-events" -H $AuthHeader -H "Content-Type: application/json" -d $payload
Write-Host "`n---"

Write-Host "[4/5] Error case: GET /sensor-events/recent without token"
curl.exe -i "$BaseUrl/sensor-events/recent"
Write-Host "`n---"

Write-Host "[5/5] Error case: POST /sensor-events invalid payload"
curl.exe -i -X POST "$BaseUrl/sensor-events" -H $AuthHeader -H "Content-Type: application/json" -d '{ "eventType": "SENSOR_UNKNOWN", "eventId": "0196fb3d-4ad7-7d1e-9f49-5d5148d2babc", "occurredAt": "2026-08-11T12:00:00Z", "source": "iot-ingestion", "deviceId": "SENSOR-001", "sensorType": "temperature", "value": 38.5, "unit": "celsius", "timestamp": "2026-08-11T11:59:58Z" }'
Write-Host ""
