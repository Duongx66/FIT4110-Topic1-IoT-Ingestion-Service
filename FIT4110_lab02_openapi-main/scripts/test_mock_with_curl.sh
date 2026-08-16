#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:4010}"
AUTH_HEADER="Authorization: Bearer test-token"

echo "[Lab02] Testing Prism mock server at $BASE_URL"
echo

echo "[1/5] Happy path: GET /health"
curl -i "$BASE_URL/health"
echo "
---"

echo "[2/5] Happy path: GET /sensor-events/recent"
curl -i "$BASE_URL/sensor-events/recent" -H "$AUTH_HEADER"
echo "
---"

echo "[3/5] Happy path: POST /sensor-events"
curl -i -X POST "$BASE_URL/sensor-events" \
  -H "$AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -d '{
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
echo "
---"

echo "[4/5] Error case: GET /sensor-events/recent without token"
curl -i "$BASE_URL/sensor-events/recent"
echo "
---"

echo "[5/5] Error case: POST /sensor-events invalid payload"
curl -i -X POST "$BASE_URL/sensor-events" \
  -H "$AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -d '{ "eventType": "SENSOR_UNKNOWN", "eventId": "0196fb3d-4ad7-7d1e-9f49-5d5148d2babc", "occurredAt": "2026-08-11T12:00:00Z", "source": "iot-ingestion", "deviceId": "SENSOR-001", "sensorType": "temperature", "value": 38.5, "unit": "celsius", "timestamp": "2026-08-11T11:59:58Z" }'
echo
