# ============================================================================
# CALDERA Sandcat Agent Installation (Windows)
# ============================================================================
# Production-ready agent installer for red team execution platform
#
# Target: Windows Server 2022
# Deployment: Azure VM via CustomScript extension
# ============================================================================

param(
    [string]$CalderaServerIp = "",
    [string]$CalderaServerPort = "8888",
    [string]$AgentGroup = "red",
    [string]$ELKServerIp = "",
    [string]$LogPath = "C:\AzureData"
)

# ============================================================================
# LOGGING SETUP
# ============================================================================

$LogFile = Join-Path $LogPath "caldera-agent-setup.log"
$null = New-Item -ItemType Directory -Path $LogPath -Force

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogMessage = "[$Timestamp] [$Level] $Message"
    Write-Host $LogMessage
    Add-Content -Path $LogFile -Value $LogMessage
}

function Write-Success {
    param([string]$Message)
    Write-Log "✓ $Message" "SUCCESS"
}

function Write-Warning {
    param([string]$Message)
    Write-Log "⚠ $Message" "WARN"
}

function Write-Error {
    param([string]$Message)
    Write-Log "✗ $Message" "ERROR"
}

# Start transcript
$null = Start-Transcript -Path $LogFile -Append

# ============================================================================
# VALIDATION
# ============================================================================

if ([string]::IsNullOrEmpty($CalderaServerIp)) {
    Write-Error "CalderaServerIp parameter is required"
    exit 1
}

Write-Log "=========================================="
Write-Log "CALDERA Windows Agent Installation"
Write-Log "=========================================="
Write-Log "Server: ${CalderaServerIp}:${CalderaServerPort}"
Write-Log "Agent Group: $AgentGroup"
Write-Log "ELK Server: $ELKServerIp"

# ============================================================================
# SANDCAT AGENT INSTALLATION
# ============================================================================

try {
    Write-Log "Installing Sandcat agent..."
    
    $CalderaUrl = "http://$CalderaServerIp`:$CalderaServerPort"
    $SandcatUrl = "$CalderaUrl/file/download"
    $AgentPath = "$env:TEMP\sandcat.exe"
    
    # Download with retry
    $maxAttempts = 5
    $attempt = 1
    $success = $false
    
    while ($attempt -le $maxAttempts -and -not $success) {
        try {
            Write-Log "Downloading Sandcat (attempt $attempt/$maxAttempts)..."
            Invoke-WebRequest -Uri $SandcatUrl -OutFile $AgentPath `
                -UseBasicParsing -TimeoutSec 60 -ErrorAction Stop
            $success = $true
            Write-Success "Sandcat agent downloaded"
        }
        catch {
            if ($attempt -lt $maxAttempts) {
                Write-Warning "Download failed: $($_.Exception.Message). Retrying in 10s..."
                Start-Sleep -Seconds 10
            }
            else {
                throw
            }
        }
        $attempt++
    }
    
    if (-not $success) {
        throw "Failed to download Sandcat agent after $maxAttempts attempts"
    }
    
    # Start Sandcat agent
    Write-Log "Starting Sandcat agent..."
    $process = Start-Process -FilePath $AgentPath `
        -ArgumentList "-server", "$CalderaUrl", "-group", "$AgentGroup", "-v" `
        -WindowStyle Hidden `
        -PassThru `
        -ErrorAction Stop
    
    Write-Success "Sandcat agent started (PID: $($process.Id))"
    
    # Wait for process
    Start-Sleep -Seconds 10
    
    # Verify process is running
    $proc = Get-Process -Id $process.Id -ErrorAction SilentlyContinue
    if (-not $proc) {
        throw "Sandcat process crashed. Check $AgentPath for errors"
    }
    
    # Create scheduled task for persistence
    Write-Log "Creating scheduled task for agent persistence..."
    
    $TaskName = "SandcatAgent"
    $TaskPath = "\CALDERA\"
    $Action = New-ScheduledTaskAction -Execute $AgentPath `
        -Argument "-server $CalderaUrl -group $AgentGroup -v"
    $Trigger = New-ScheduledTaskTrigger -AtStartup
    $Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -RunLevel Highest
    $Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 10)
    
    # Remove existing task if it exists
    $existingTask = Get-ScheduledTask -TaskName $TaskName -TaskPath $TaskPath -ErrorAction SilentlyContinue
    if ($existingTask) {
        Unregister-ScheduledTask -TaskName $TaskName -TaskPath $TaskPath -Confirm:$false
    }
    
    Register-ScheduledTask -TaskName $TaskName -TaskPath $TaskPath `
        -Action $Action -Trigger $Trigger -Principal $Principal `
        -Settings $Settings -ErrorAction Stop | Out-Null
    
    Write-Success "Scheduled task created for persistence"
}
catch {
    Write-Error "Sandcat installation failed: $($_.Exception.Message)"
    exit 1
}

# ============================================================================
# WINLOGBEAT INSTALLATION
# ============================================================================

if (-not [string]::IsNullOrEmpty($ELKServerIp)) {
    try {
        Write-Log "Installing Winlogbeat..."
        
        $WinlogbeatUrl = 'https://artifacts.elastic.co/downloads/beats/winlogbeat/winlogbeat-8.11.0-windows-x86_64.zip'
        $WinlogbeatZip = "$env:TEMP\winlogbeat.zip"
        $WinlogbeatDir = "C:\Program Files\Winlogbeat"
        $WinlogbeatExtractDir = "$env:TEMP\winlogbeat-extract"
        
        # Download Winlogbeat
        Write-Log "Downloading Winlogbeat..."
        Invoke-WebRequest -Uri $WinlogbeatUrl -OutFile $WinlogbeatZip `
            -UseBasicParsing -TimeoutSec 120 -ErrorAction Stop
        Write-Success "Winlogbeat downloaded"
        
        # Extract and install
        Write-Log "Extracting Winlogbeat..."
        if (Test-Path $WinlogbeatExtractDir) {
            Remove-Item $WinlogbeatExtractDir -Recurse -Force
        }
        Expand-Archive -Path $WinlogbeatZip -DestinationPath $WinlogbeatExtractDir -Force
        
        $null = New-Item -ItemType Directory -Path $WinlogbeatDir -Force
        
        # Copy files
        $SourceDir = (Get-ChildItem -Path $WinlogbeatExtractDir -Directory | Select-Object -First 1).FullName
        Copy-Item -Path "$SourceDir\*" -Destination $WinlogbeatDir -Recurse -Force
        Write-Success "Winlogbeat files installed"
        
        # Create configuration
        Write-Log "Configuring Winlogbeat..."
        
        $WinlogbeatConfig = @"
winlogbeat.event_logs:
  - name: Application
    ignore_older: 72h
  - name: Security
  - name: System
  - name: Microsoft-Windows-Sysmon/Operational
    ignore_older: 72h

output.logstash:
  hosts: ["${ELKServerIp}:5044"]

logging.level: warning
logging.to_files: true
logging.files:
  path: C:\ProgramData\winlogbeat\logs
  name: winlogbeat
  keepfiles: 7
  permissions: 0600
"@
        
        Set-Content -Path "$WinlogbeatDir\winlogbeat.yml" -Value $WinlogbeatConfig -Force
        Write-Success "Winlogbeat configuration created"
        
        # Install service
        Write-Log "Installing Winlogbeat service..."
        $installScript = Get-ChildItem -Path $WinlogbeatDir -Filter "install-service-winlogbeat.ps1" | Select-Object -First 1
        if ($installScript) {
            & $installScript.FullName
            Write-Success "Winlogbeat service installed"
            
            # Start service
            Start-Service -Name "winlogbeat" -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 5
            
            if ((Get-Service -Name "winlogbeat" -ErrorAction SilentlyContinue).Status -eq "Running") {
                Write-Success "Winlogbeat service started"
            }
            else {
                Write-Warning "Winlogbeat service is not running. Check configuration."
            }
        }
        else {
            Write-Warning "Winlogbeat installation script not found"
        }
        
        # Cleanup
        Remove-Item $WinlogbeatZip -Force -ErrorAction SilentlyContinue
        Remove-Item $WinlogbeatExtractDir -Recurse -Force -ErrorAction SilentlyContinue
    }
    catch {
        Write-Warning "Winlogbeat installation failed: $($_.Exception.Message)"
    }
}
else {
    Write-Log "ELK Server IP not provided. Skipping Winlogbeat installation."
}

# ============================================================================
# SUMMARY
# ============================================================================

Write-Log "=========================================="
Write-Success "Installation completed successfully!"
Write-Log "=========================================="
Write-Log "Agent Group: $AgentGroup"
Write-Log "Server: ${CalderaServerIp}:${CalderaServerPort}"
Write-Log "Log file: $LogFile"
Write-Log "=========================================="

Stop-Transcript

exit 0
