# Script để test IoT Ingestion API
# Sử dụng: .\test-api.ps1

Write-Host "🧪 Testing FIT4110 IoT Ingestion API..." -ForegroundColor Cyan
Write-Host ""

# Test 1: Health Check
Write-Host "1️⃣  Testing GET /health" -ForegroundColor Yellow
try {
    $health = Invoke-WebRequest -Uri "http://localhost:8000/health" -Method GET
    Write-Host "   ✅ Status: $($health.StatusCode)" -ForegroundColor Green
    $health.Content | ConvertFrom-Json | Format-Table -AutoSize
} catch {
    Write-Host "   ❌ Failed: $_" -ForegroundColor Red
}

Write-Host ""

# Test 2: Create Reading
Write-Host "2️⃣  Testing POST /readings (with auth)" -ForegroundColor Yellow
try {
    $body = @{
        device_id = "ESP32-LAB-A01"
        metric = "temperature"
        value = 31.5
        unit = "celsius"
        timestamp = "2026-05-13T08:30:00+07:00"
    } | ConvertTo-Json

    $headers = @{
        'Authorization' = 'Bearer local-dev-token'
        'Content-Type' = 'application/json'
    }

    $response = Invoke-WebRequest -Uri "http://localhost:8000/readings" -Method POST -Body $body -Headers $headers
    Write-Host "   ✅ Status: $($response.StatusCode)" -ForegroundColor Green
    $response.Content | ConvertFrom-Json | Format-Table -AutoSize
    $reading_id = ($response.Content | ConvertFrom-Json).reading_id
} catch {
    Write-Host "   ❌ Failed: $_" -ForegroundColor Red
}

Write-Host ""

# Test 3: Get Latest Readings
Write-Host "3️⃣  Testing GET /readings/latest (with auth)" -ForegroundColor Yellow
try {
    $headers = @{
        'Authorization' = 'Bearer local-dev-token'
    }

    $response = Invoke-WebRequest -Uri "http://localhost:8000/readings/latest?limit=5" -Method GET -Headers $headers
    Write-Host "   ✅ Status: $($response.StatusCode)" -ForegroundColor Green
    $content = $response.Content | ConvertFrom-Json
    Write-Host "   📊 Total readings: $($content.items.Count)" -ForegroundColor Cyan
    $content.items | Format-Table -AutoSize
} catch {
    Write-Host "   ❌ Failed: $_" -ForegroundColor Red
}

Write-Host ""

# Test 4: Test Unauthorized (missing auth)
Write-Host "4️⃣  Testing unauthorized access (should fail)" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/readings/latest" -Method GET -ErrorAction Stop
    Write-Host "   ❌ Should have failed but didn't!" -ForegroundColor Red
} catch {
    Write-Host "   ✅ Expected error (401 Unauthorized)" -ForegroundColor Green
    Write-Host "   📝 Error: $($_.Exception.Response.StatusCode)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "✅ All tests completed!" -ForegroundColor Green
