# Script để start IoT Ingestion service với Docker Compose
# Sử dụng: .\start-docker.ps1

Write-Host "🚀 Starting FIT4110 IoT Ingestion Service with Docker Compose..." -ForegroundColor Cyan

docker compose up -d

Write-Host "✅ Service started!" -ForegroundColor Green
Write-Host "📍 API base URL: http://localhost:8000" -ForegroundColor Yellow
Write-Host "🏥 Health check: http://localhost:8000/health" -ForegroundColor Yellow
Write-Host ""
Write-Host "⏳ Waiting 5 seconds for service to be ready..." -ForegroundColor Gray
Start-Sleep -Seconds 5

Write-Host "🔍 Testing /health endpoint..." -ForegroundColor Cyan
$response = Invoke-WebRequest -Uri "http://localhost:8000/health" -Method GET
if ($response.StatusCode -eq 200) {
    Write-Host "✅ Service is healthy!" -ForegroundColor Green
    $response.Content | ConvertFrom-Json | Format-Table
} else {
    Write-Host "❌ Service health check failed!" -ForegroundColor Red
}

Write-Host ""
Write-Host "📋 Container Status:" -ForegroundColor Cyan
docker compose ps

Write-Host ""
Write-Host "💡 Next steps:" -ForegroundColor Yellow
Write-Host "  - Test API: .\test-api.ps1" -ForegroundColor Gray
Write-Host "  - View logs: docker compose logs -f" -ForegroundColor Gray
Write-Host "  - Stop service: docker compose down" -ForegroundColor Gray
