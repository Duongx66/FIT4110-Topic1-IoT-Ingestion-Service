import csv
import json
import os
import threading
import uuid
from pathlib import Path
from datetime import datetime, timezone
from enum import Enum
from http import HTTPStatus
from typing import Dict, List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import paho.mqtt.client as mqtt
import requests

# Đọc biến môi trường với giá trị mặc định
SERVICE_NAME = os.getenv("SERVICE_NAME", "iot-ingestion")
SERVICE_VERSION = os.getenv("SERVICE_VERSION", "0.5.0")
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "local-dev-token")
MQTT_ENABLED = os.getenv("MQTT_ENABLED", "false").lower() == "true"
MQTT_HOST = os.getenv("MQTT_HOST", "")
MQTT_PORT = int(os.getenv("MQTT_PORT", "8883"))
MQTT_USERNAME = os.getenv("MQTT_USERNAME", "")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")
MQTT_INPUT_TOPIC = os.getenv(
    "MQTT_INPUT_TOPIC", "smart-campus/raw/iot/environment"
)
MQTT_OUTPUT_TOPIC = os.getenv(
    "MQTT_OUTPUT_TOPIC", "smart-campus/events/sensor"
)
MQTT_CLIENT_ID = os.getenv("MQTT_CLIENT_ID", "iot-ingestion-lab05")
CORE_EVENTS_URL = os.getenv("CORE_EVENTS_URL", "")
CORE_ENABLED = os.getenv("CORE_ENABLED", "false").lower() == "true"
MQTT_STATUS = "disabled"
CORE_STATUS = "disabled"
MQTT_CLIENT: Optional[mqtt.Client] = None


app = FastAPI(
    title="FIT4110 Lab 05 - IoT Ingestion Service",
    version=SERVICE_VERSION,
    description=(
        "IoT Ingestion API chạy trong ngữ cảnh Docker Compose cho Lab 05. "
        "Luồng logic được kế thừa từ Lab 04 và tiếp tục được dùng để kiểm thử end‑to‑end."
    ),
)


class SensorMetric(str, Enum):
    temperature = "temperature"
    humidity = "humidity"
    motion = "motion"
    smoke = "smoke"
    co2 = "co2"
    light = "light"
    battery = "battery"


class SensorUnit(str, Enum):
    celsius = "celsius"
    percent = "percent"
    boolean = "boolean"
    ppm = "ppm"
    lux = "lux"


class ProblemDetails(BaseModel):
    type: str = "about:blank"
    title: str
    status: int = Field(..., ge=400, le=599)
    detail: str
    instance: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    mqtt_status: str
    core_status: str


class SensorReadingCreate(BaseModel):
    device_id: str = Field(..., min_length=3, examples=["ESP32-LAB-A01"])
    metric: SensorMetric = Field(..., examples=["temperature"])
    value: float = Field(
        ...,
        ge=-40,
        le=80,
        description="Boundary range used in Lab 03 và Lab 04: -40 đến 80.",
        examples=[31.5],
    )
    unit: Optional[SensorUnit] = Field(default=None, examples=["celsius"])
    timestamp: str = Field(..., examples=["2026-05-13T08:30:00+07:00"])


class SensorReading(BaseModel):
    reading_id: str
    device_id: str
    metric: SensorMetric
    value: float
    unit: Optional[SensorUnit] = None
    timestamp: str
    created_at: str


class SensorReadingCreated(BaseModel):
    reading_id: str
    device_id: str
    metric: SensorMetric
    accepted: bool
    created_at: str


READINGS: List[Dict] = []
EVENTS: List[Dict] = []
RAW_EVENTS: List[Dict] = []


class IoTEvent(BaseModel):
    eventType: str = Field(..., min_length=1)
    eventId: str = Field(..., min_length=1)
    occurredAt: str
    correlationId: str
    source: str = "iot-ingestion"
    deviceId: str = Field(..., min_length=3)
    metric: SensorMetric
    value: float
    unit: Optional[SensorUnit] = None
    timestamp: str
    locationId: Optional[str] = None
    threshold: Optional[float] = None
    status: Optional[str] = None
    alertLevel: Optional[str] = None
    reason: Optional[str] = None


class EventAccepted(BaseModel):
    eventId: str
    acceptedAt: str


class RawEnvironmentSample(BaseModel):
    event_id: str = Field(..., min_length=1)
    event_type: str = Field(..., min_length=1)
    source_service: Optional[str] = None
    device_id: str = Field(..., min_length=3)
    timestamp: str = Field(..., min_length=1)
    location: Optional[str] = None
    temperature_c: Optional[float] = Field(...)
    humidity_percent: Optional[float] = Field(...)
    motion_detected: bool
    light_lux: Optional[float] = None
    co2_ppm: Optional[float] = None
    smoke_ppm: Optional[float] = None
    battery_percent: Optional[float] = None


def load_device_registry() -> Dict[str, Dict[str, str]]:
    configured_path = os.getenv("DEVICE_REGISTRY_PATH")
    candidates = [
        Path(configured_path) if configured_path else None,
        Path(__file__).resolve().parents[2] / "data" / "IoT_device_registry.csv",
        Path("data") / "IoT_device_registry.csv",
    ]
    for path in candidates:
        if path and path.exists():
            with path.open(newline="", encoding="utf-8") as registry_file:
                return {
                    row["device_id"]: row
                    for row in csv.DictReader(registry_file)
                    if row.get("device_id")
                }
    return {}


DEVICE_REGISTRY = load_device_registry()


def on_mqtt_connect(client: mqtt.Client, userdata: object, flags: dict, reason_code: object, properties: object = None) -> None:
    global MQTT_STATUS
    if reason_code == 0:
        MQTT_STATUS = "connected"
        client.subscribe(MQTT_INPUT_TOPIC, qos=1)
        print(f"MQTT connected; subscribed to {MQTT_INPUT_TOPIC}", flush=True)
    else:
        MQTT_STATUS = f"connect_failed:{reason_code}"


def on_mqtt_disconnect(client: mqtt.Client, userdata: object, disconnect_flags: object, reason_code: object, properties: object = None) -> None:
    global MQTT_STATUS
    MQTT_STATUS = "disconnected"
    print(f"MQTT disconnected: {reason_code}", flush=True)


def on_mqtt_message(client: mqtt.Client, userdata: object, message: mqtt.MQTTMessage) -> None:
    try:
        sample = RawEnvironmentSample.model_validate(json.loads(message.payload))
        normalized = classify_sample(sample)
        RAW_EVENTS.append(sample.model_dump())
        EVENTS.append(normalized)
        client.publish(MQTT_OUTPUT_TOPIC, json.dumps(normalized), qos=1)
        send_to_core(sample)
        print(f"MQTT processed event {sample.event_id}", flush=True)
    except Exception as error:
        print(f"MQTT rejected message: {error}", flush=True)


def start_mqtt() -> None:
    global MQTT_CLIENT, MQTT_STATUS
    if not MQTT_ENABLED:
        MQTT_STATUS = "disabled"
        return
    if not MQTT_HOST or not MQTT_USERNAME or not MQTT_PASSWORD:
        MQTT_STATUS = "missing_configuration"
        print("MQTT enabled but configuration is incomplete", flush=True)
        return

    MQTT_CLIENT = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id=MQTT_CLIENT_ID,
        protocol=mqtt.MQTTv5,
    )
    MQTT_CLIENT.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    MQTT_CLIENT.tls_set()
    MQTT_CLIENT.on_connect = on_mqtt_connect
    MQTT_CLIENT.on_disconnect = on_mqtt_disconnect
    MQTT_CLIENT.on_message = on_mqtt_message
    try:
        MQTT_STATUS = "connecting"
        MQTT_CLIENT.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
        threading.Thread(target=MQTT_CLIENT.loop_forever, daemon=True).start()
    except Exception as error:
        MQTT_STATUS = f"connection_error:{type(error).__name__}"
        print(f"MQTT connection failed: {error}", flush=True)


def stop_mqtt() -> None:
    if MQTT_CLIENT is not None:
        MQTT_CLIENT.disconnect()


def send_to_core(sample: RawEnvironmentSample) -> None:
    global CORE_STATUS
    if not CORE_ENABLED:
        CORE_STATUS = "disabled"
        return
    if not CORE_EVENTS_URL:
        CORE_STATUS = "missing_configuration"
        return

    metric_values = [
        ("temperature", sample.temperature_c, "celsius"),
        ("humidity", sample.humidity_percent, "percent"),
        ("smoke", sample.smoke_ppm, "ppm"),
    ]
    metric, value, unit = next(
        ((name, value, unit) for name, value, unit in metric_values if value is not None),
        (None, None, None),
    )
    if metric is None:
        CORE_STATUS = "skipped_no_numeric_metric"
        return

    core_event = {
        "eventType": "sensor.reading.created",
        "eventId": str(uuid.uuid4()),
        "occurredAt": sample.timestamp,
        "correlationId": str(uuid.uuid4()),
        "source": "iot-ingestion",
        "deviceId": sample.device_id,
        "metric": metric,
        "value": value,
        "unit": unit,
        "locationId": sample.location or DEVICE_REGISTRY.get(sample.device_id, {}).get("location"),
    }
    try:
        response = requests.post(CORE_EVENTS_URL, json=core_event, timeout=5)
        response.raise_for_status()
        CORE_STATUS = "connected"
        print(f"Core accepted event {core_event['eventId']}: {response.status_code}", flush=True)
    except requests.RequestException as error:
        CORE_STATUS = f"error:{type(error).__name__}"
        print(f"Core event delivery failed: {error}", flush=True)


@app.on_event("startup")
def mqtt_startup() -> None:
    start_mqtt()


@app.on_event("shutdown")
def mqtt_shutdown() -> None:
    stop_mqtt()


def classify_sample(sample: RawEnvironmentSample) -> Dict[str, object]:
    status_value = "normal"
    alert_level = "low"
    reasons: List[str] = []

    if sample.device_id not in DEVICE_REGISTRY:
        status_value = "invalid_device"
        alert_level = "high"
        reasons.append("device_not_registered")
    elif any(
        value is None
        for value in (sample.temperature_c, sample.humidity_percent)
    ):
        status_value = "sensor_error"
        alert_level = "high"
        reasons.append("missing_sensor_value")
    else:
        if sample.temperature_c is not None and sample.temperature_c >= 35:
            reasons.append("high_temperature")
        if sample.humidity_percent is not None and sample.humidity_percent >= 80:
            reasons.append("high_humidity")
        if sample.co2_ppm is not None and sample.co2_ppm >= 1000:
            reasons.append("high_co2")
        if sample.smoke_ppm is not None and sample.smoke_ppm >= 0.5:
            reasons.append("smoke_detected")
        if sample.battery_percent is not None and sample.battery_percent < 20:
            reasons.append("low_battery")
        if reasons:
            status_value = "danger" if any(
                reason in reasons for reason in ("smoke_detected", "high_co2")
            ) else "warning"
            alert_level = "high" if status_value == "danger" else "medium"

    return {
        "eventType": "iot.sensor.normalized",
        "eventId": sample.event_id,
        "occurredAt": sample.timestamp,
        "correlationId": sample.event_id,
        "source": "iot-ingestion",
        "deviceId": sample.device_id,
        "locationId": sample.location or DEVICE_REGISTRY.get(sample.device_id, {}).get("location"),
        "status": status_value,
        "alertLevel": alert_level,
        "reason": ",".join(reasons) if reasons else "within_threshold",
        "timestamp": sample.timestamp,
        "metrics": {
            "temperature_c": sample.temperature_c,
            "humidity_percent": sample.humidity_percent,
            "motion_detected": sample.motion_detected,
            "light_lux": sample.light_lux,
            "co2_ppm": sample.co2_ppm,
            "smoke_ppm": sample.smoke_ppm,
            "battery_percent": sample.battery_percent,
        },
    }


def build_problem(
    *,
    status_code: int,
    title: str,
    detail: str,
    instance: Optional[str] = None,
    problem_type: str = "about:blank",
) -> Dict:
    problem = {
        "type": problem_type,
        "title": title,
        "status": status_code,
        "detail": detail,
    }
    if instance:
        problem["instance"] = instance
    return problem


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict):
        problem = exc.detail
    else:
        problem = build_problem(
            status_code=exc.status_code,
            title=HTTPStatus(exc.status_code).phrase,
            detail=str(exc.detail),
            instance=str(request.url.path),
        )

    problem.setdefault("status", exc.status_code)
    problem.setdefault("title", HTTPStatus(exc.status_code).phrase)
    problem.setdefault("type", "about:blank")
    problem.setdefault("detail", "Request failed")
    problem.setdefault("instance", str(request.url.path))

    return JSONResponse(
        status_code=exc.status_code,
        content=problem,
        media_type="application/problem+json",
        headers=getattr(exc, "headers", None),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    first_error = exc.errors()[0] if exc.errors() else {}
    location = ".".join(str(item) for item in first_error.get("loc", []))
    message = first_error.get("msg", "Request validation error")
    detail = f"{location}: {message}" if location else message

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=build_problem(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            title="Validation error",
            detail=detail,
            instance=str(request.url.path),
            problem_type="https://smart-campus.local/problems/validation-error",
        ),
        media_type="application/problem+json",
    )


def verify_bearer_token(authorization: Optional[str] = Header(default=None)) -> None:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=build_problem(
                status_code=status.HTTP_401_UNAUTHORIZED,
                title="Unauthorized",
                detail="Missing Authorization header",
                problem_type="https://smart-campus.local/problems/unauthorized",
            ),
        )

    expected = f"Bearer {AUTH_TOKEN}"
    if authorization != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=build_problem(
                status_code=status.HTTP_401_UNAUTHORIZED,
                title="Unauthorized",
                detail="Invalid bearer token",
                problem_type="https://smart-campus.local/problems/unauthorized",
            ),
        )


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def next_reading_id() -> str:
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"R-{today}-{len(READINGS) + 1:04d}"


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=SERVICE_NAME,
        version=SERVICE_VERSION,
        mqtt_status=MQTT_STATUS,
        core_status=CORE_STATUS,
    )


@app.post(
    "/readings",
    response_model=SensorReadingCreated,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_bearer_token)],
    responses={
        401: {"model": ProblemDetails},
        422: {"model": ProblemDetails},
        429: {"model": ProblemDetails},
    },
)
def create_reading(payload: SensorReadingCreate, response: Response) -> SensorReadingCreated:
    # Ví dụ logic cảnh báo: nếu nhiệt độ >= 70 thì thêm header cảnh báo
    if payload.metric == SensorMetric.temperature and payload.value >= 70:
        response.headers["X-Warning"] = "high-temperature"

    reading_id = next_reading_id()
    created_at = now_iso()

    item = {
        "reading_id": reading_id,
        "device_id": payload.device_id,
        "metric": payload.metric.value,
        "value": payload.value,
        "unit": payload.unit.value if payload.unit else None,
        "timestamp": payload.timestamp,
        "created_at": created_at,
    }
    READINGS.append(item)

    return SensorReadingCreated(
        reading_id=reading_id,
        device_id=payload.device_id,
        metric=payload.metric,
        accepted=True,
        created_at=created_at,
    )


@app.post(
    "/sensor-events",
    response_model=EventAccepted,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(verify_bearer_token)],
    responses={401: {"model": ProblemDetails}, 422: {"model": ProblemDetails}},
)
def publish_sensor_event(payload: IoTEvent) -> EventAccepted:
    event = payload.model_dump(exclude_none=True)
    EVENTS.append(event)
    READINGS.append(
        {
            "reading_id": event["eventId"],
            "device_id": event["deviceId"],
            "metric": event["metric"],
            "value": event["value"],
            "unit": event.get("unit"),
            "timestamp": event["timestamp"],
            "created_at": now_iso(),
        }
    )
    return EventAccepted(eventId=event["eventId"], acceptedAt=now_iso())


@app.post(
    "/ingest/raw",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(verify_bearer_token)],
)
def ingest_raw_environment(sample: RawEnvironmentSample) -> Dict[str, object]:
    normalized = classify_sample(sample)
    RAW_EVENTS.append(sample.model_dump())
    EVENTS.append(normalized)
    return {"accepted": True, "event": normalized}


@app.get("/readings/latest", dependencies=[Depends(verify_bearer_token)])
def latest_readings(
    device_id: Optional[str] = Query(default=None),
    limit: int = Query(default=10, ge=1, le=100),
) -> Dict[str, List[Dict]]:
    items = READINGS

    if device_id:
        items = [item for item in items if item["device_id"] == device_id]

    return {"items": items[-limit:]}


@app.get("/sensor-events/recent", dependencies=[Depends(verify_bearer_token)])
def recent_sensor_events(
    metric: Optional[SensorMetric] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
) -> Dict[str, object]:
    events = [event for event in EVENTS if "metric" in event]
    if metric:
        events = [event for event in events if event["metric"] == metric.value]
    return {"items": events[-limit:], "nextCursor": None, "hasMore": False}


@app.get("/sensor-events/{event_id}", dependencies=[Depends(verify_bearer_token)])
def get_sensor_event(event_id: str) -> Dict:
    for event in EVENTS:
        if event["eventId"] == event_id:
            return event
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=build_problem(
            status_code=status.HTTP_404_NOT_FOUND,
            title="Not Found",
            detail=f"Event {event_id} does not exist",
            instance=f"/sensor-events/{event_id}",
        ),
    )


@app.get("/readings/{reading_id}", dependencies=[Depends(verify_bearer_token)])
def get_reading(reading_id: str) -> Dict:
    for item in READINGS:
        if item["reading_id"] == reading_id:
            return item

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=build_problem(
            status_code=status.HTTP_404_NOT_FOUND,
            title="Not Found",
            detail=f"Reading {reading_id} does not exist",
            instance=f"/readings/{reading_id}",
            problem_type="https://smart-campus.local/problems/not-found",
        ),
    )