# Script để dừng service
# Sử dụng: .\stop-docker.ps1

Write-Host "🛑 Stopping FIT4110 IoT Ingestion Service..." -ForegroundColor Cyan

docker compose down

Write-Host "✅ Service stopped and cleaned up!" -ForegroundColor Green
