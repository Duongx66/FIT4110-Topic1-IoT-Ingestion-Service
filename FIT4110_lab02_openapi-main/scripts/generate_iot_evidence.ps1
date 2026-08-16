$ErrorActionPreference = 'Stop'

$base = 'http://127.0.0.1:4010'
$auth = 'Authorization: Bearer test-token'

Write-Host "[Lab02] Generating IoT mock request evidence files..."

$p1 = curl.exe -i "$base/health" | Out-String
$p2 = curl.exe -i "$base/sensor-events/recent" -H $auth | Out-String

$payload = @'
{"eventType":"SENSOR_READING","eventId":"0196fb3d-4ad7-7d1e-9f49-5d5148d2babc","occurredAt":"2026-08-11T12:00:00Z","correlationId":"5f8d9abc-1234-4d5e-9f01-23456789abcd","source":"iot-ingestion","deviceId":"SENSOR-001","sensorType":"temperature","value":38.5,"unit":"celsius","timestamp":"2026-08-11T11:59:58Z","locationId":"LOC-01"}
'@

$p3 = curl.exe -i -X POST "$base/sensor-events" -H $auth -H 'Content-Type: application/json' -d $payload | Out-String
$p4 = curl.exe -i "$base/sensor-events/recent" | Out-String

$invalid = @'
{"eventType":12345}
'@
$p5 = curl.exe -i -X POST "$base/sensor-events" -H $auth -H 'Content-Type: application/json' -d $invalid | Out-String

Set-Content -Path 'evidence\buoi-02\mock-screenshots\req-01-health.txt' -Value @('REQUEST 1: GET /health', $p1)
Set-Content -Path 'evidence\buoi-02\mock-screenshots\req-02-sensor-events-recent.txt' -Value @('REQUEST 2: GET /sensor-events/recent with Authorization', $p2)
Set-Content -Path 'evidence\buoi-02\mock-screenshots\req-03-post-sensor-events-valid.txt' -Value @('REQUEST 3: POST /sensor-events valid payload', $p3)
Set-Content -Path 'evidence\buoi-02\mock-screenshots\req-04-sensor-events-recent-no-auth.txt' -Value @('REQUEST 4: GET /sensor-events/recent without Authorization', $p4)
Set-Content -Path 'evidence\buoi-02\mock-screenshots\req-05-post-sensor-events-invalid.txt' -Value @('REQUEST 5: POST /sensor-events invalid payload', $p5)

Write-Host "[Lab02] IoT mock evidence generated."