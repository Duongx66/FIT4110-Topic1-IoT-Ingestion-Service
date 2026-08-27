# FIT4110 Lab 04 - Docker Cheatsheet

## Các lệnh nhanh

### Build Image
```bash
docker build -t fit4110/iot-ingestion:lab04 .
```

### Chạy Container với Docker Compose
```bash
# Start service
docker compose up -d

# Stop service
docker compose down

# View logs
docker compose logs -f

# Xem container status
docker compose ps
```

### Chạy Container thủ công
```bash
# Start container
docker run --rm -d \
  --name fit4110-iot-lab04 \
  -p 8000:8000 \
  --env-file .env.example \
  fit4110/iot-ingestion:lab04

# Stop container
docker stop fit4110-iot-lab04
```

### Kiểm tra API
```bash
# Health check
curl http://localhost:8000/health

# Tạo reading (yêu cầu auth)
curl -X POST http://localhost:8000/readings \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer local-dev-token" \
  -d '{
    "device_id": "ESP32-LAB-A01",
    "metric": "temperature",
    "value": 31.5,
    "unit": "celsius",
    "timestamp": "2026-05-13T08:30:00+07:00"
  }'

# Lấy latest readings
curl http://localhost:8000/readings/latest?limit=10 \
  -H "Authorization: Bearer local-dev-token"
```

## PowerShell Scripts
- `.\start-docker.ps1` - Start service
- `.\test-api.ps1` - Test API endpoints
- `.\stop-docker.ps1` - Stop service

## Docker Images
```bash
# Xem image
docker images | grep fit4110

# Tag image
docker tag fit4110/iot-ingestion:lab04 ghcr.io/your-org/iot-ingestion:v0.4.0

# Push to registry
docker push ghcr.io/your-org/iot-ingestion:v0.4.0
```

## Cleanup
```bash
# Xóa stopped containers
docker container prune

# Xóa dangling images
docker image prune

# Full cleanup
docker system prune -a
```

## Environment Variables
Tất cả biến được xác định trong `.env.example`:
- `APP_HOST` - Host address (default: 0.0.0.0)
- `APP_PORT` - Port (default: 8000)
- `SERVICE_NAME` - Service name
- `SERVICE_VERSION` - API version
- `AUTH_TOKEN` - Bearer token cho authentication

## Troubleshooting
```bash
# View container logs
docker compose logs fit4110-iot-lab04

# Enter container shell
docker exec -it fit4110-iot-lab04-compose /bin/bash

# Check container health
docker compose exec fit4110-iot-lab04 python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health').read()"
```
