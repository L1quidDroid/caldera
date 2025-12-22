#!C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe -ExecutionPolicy Bypass -Command
# ============================================================================
# Windows Agent Setup Script (for Bicep CustomScriptExtension)
# ============================================================================
# This script is downloaded and executed on the Windows VM.
# It installs Sandcat and Winlogbeat.
# ============================================================================

param(
    [string]$calderaServerIp,
    [string]$elkServerIp
)

# Start logging
Start-Transcript -Path "C:\AzureData\CustomData.log" -Append

Write-Host "Starting Windows Agent setup..."
Write-Host "CALDERA Server IP: $calderaServerIp"
Write-Host "ELK Server IP: $elkServerIp"

# Install Sandcat Agent
try {
    Write-Host "Installing Sandcat agent..."
    $calderaUrl = "http://$calderaServerIp:8888"
    $sandcatUrl = "$calderaUrl/file/download"
    $agentPath = "$env:TEMP\sandcat.exe"
    
    Invoke-WebRequest -Uri $sandcatUrl -OutFile $agentPath -UseBasicParsing -TimeoutSec 60
    
    Start-Process -FilePath $agentPath -ArgumentList "-server", "$calderaUrl", "-group", "red", "-v" -WindowStyle Hidden
    
    Write-Host "✅ Sandcat agent started successfully."
}
catch {
    Write-Warning "❌ Sandcat agent installation failed: $_"
}

# Install Winlogbeat
try {
    Write-Host "Installing Winlogbeat..."
    $winlogbeatUrl = 'https://artifacts.elastic.co/downloads/beats/winlogbeat/winlogbeat-8.11.0-windows-x86_64.zip'
    $winlogbeatZip = "$env:TEMP\winlogbeat.zip"
    $winlogbeatDir = "C:\Program Files\Winlogbeat"

    Invoke-WebRequest -Uri $winlogbeatUrl -OutFile $winlogbeatZip -UseBasicParsing
    
    Expand-Archive -Path $winlogbeatZip -DestinationPath "$env:TEMP\winlogbeat" -Force
    
    New-Item -ItemType Directory -Force -Path $winlogbeatDir | Out-Null
    
    Copy-Item -Path "$env:TEMP\winlogbeat\winlogbeat-*\*" -Destination $winlogbeatDir -Recurse -Force

    # Create Winlogbeat configuration
    $winlogbeatConfig = @"
winlogbeat.event_logs:
  - name: Application
    ignore_older: 72h
  - name: Security
  - name: System
  - name: Microsoft-Windows-Sysmon/Operational

output.logstash:
  hosts: ["$elkServerIp:5044"]

logging.level: info
logging.to_files: true
logging.files:
  path: C:/ProgramData/winlogbeat/Logs
"@
    
    Set-Content -Path "$winlogbeatDir\winlogbeat.yml" -Value $winlogbeatConfig -Force

    # Install and start the service
    & "$winlogbeatDir\install-service-winlogbeat.ps1"
    Start-Service winlogbeat

    Write-Host "✅ Winlogbeat configured and started."
}
catch {
    Write-Warning "❌ Winlogbeat installation failed: $_"
}

Stop-Transcript
