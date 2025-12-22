#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Install Atomic Red Team framework for CALDERA operations.

.DESCRIPTION
    Installs Invoke-AtomicRedTeam PowerShell module and downloads ATT&CK technique definitions.
    Configures execution environment for purple team testing.

.PARAMETER AtomicsFolder
    Installation directory for Atomic Red Team techniques (default: C:\AtomicRedTeam).

.PARAMETER SkipTests
    Skip validation tests after installation.

.EXAMPLE
    .\install-atomic-red-team.ps1

.EXAMPLE
    .\install-atomic-red-team.ps1 -AtomicsFolder "D:\AtomicRedTeam" -SkipTests

.NOTES
    Requires: PowerShell 5.1+, Administrator privileges
    Author: Triskele Labs
    Date: December 2025
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$AtomicsFolder = "C:\AtomicRedTeam",

    [Parameter(Mandatory = $false)]
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"

Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Starting Atomic Red Team installation..." -ForegroundColor Cyan

# Check if running as Administrator
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Error "This script must be run as Administrator"
    exit 1
}

# Install NuGet provider
Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Installing NuGet provider..." -ForegroundColor Yellow
if (!(Get-PackageProvider -Name NuGet -ErrorAction SilentlyContinue)) {
    Install-PackageProvider -Name NuGet -MinimumVersion 2.8.5.201 -Force -Scope AllUsers
}

# Set PSGallery as trusted repository
Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Configuring PSGallery repository..." -ForegroundColor Yellow
Set-PSRepository -Name PSGallery -InstallationPolicy Trusted

# Install Invoke-AtomicRedTeam module
Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Installing Invoke-AtomicRedTeam module..." -ForegroundColor Yellow
if (Get-Module -ListAvailable -Name Invoke-AtomicRedTeam) {
    Write-Host "    Module already installed, updating to latest version..."
    Update-Module -Name Invoke-AtomicRedTeam -Force
} else {
    Install-Module -Name Invoke-AtomicRedTeam -Scope AllUsers -Force
}

# Download atomics
Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Downloading ATT&CK techniques to $AtomicsFolder..." -ForegroundColor Yellow
Import-Module Invoke-AtomicRedTeam

# Create atomics folder if it doesn't exist
if (!(Test-Path $AtomicsFolder)) {
    New-Item -ItemType Directory -Path $AtomicsFolder -Force | Out-Null
}

# Download atomics folder (this includes all technique definitions)
try {
    Invoke-Expression (New-Object Net.WebClient).DownloadString('https://raw.githubusercontent.com/redcanaryco/invoke-atomicredteam/master/install-atomicredteam.ps1')
    Install-AtomicRedTeam -InstallPath $AtomicsFolder -Force
} catch {
    Write-Error "Failed to download Atomic Red Team techniques: $_"
    exit 1
}

# Set environment variable
Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Setting environment variables..." -ForegroundColor Yellow
[System.Environment]::SetEnvironmentVariable('ATOMIC_RED_TEAM_PATH', $AtomicsFolder, [System.EnvironmentVariableTarget]::Machine)
$env:ATOMIC_RED_TEAM_PATH = $AtomicsFolder

# Verify installation
Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Verifying installation..." -ForegroundColor Yellow
$module = Get-Module -ListAvailable -Name Invoke-AtomicRedTeam
Write-Host "    ✅ Invoke-AtomicRedTeam version: $($module.Version)" -ForegroundColor Green

$atomicsPath = Join-Path $AtomicsFolder "atomics"
if (Test-Path $atomicsPath) {
    $techniqueCount = (Get-ChildItem $atomicsPath -Directory | Where-Object { $_.Name -match "^T\d{4}" }).Count
    Write-Host "    ✅ Downloaded $techniqueCount ATT&CK techniques" -ForegroundColor Green
} else {
    Write-Warning "Atomics folder not found at $atomicsPath"
}

# Run validation tests
if (-not $SkipTests) {
    Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Running validation tests..." -ForegroundColor Yellow
    
    # Test 1: List available techniques
    try {
        $techniques = Get-AtomicTechnique
        Write-Host "    ✅ Found $($techniques.Count) atomic tests" -ForegroundColor Green
    } catch {
        Write-Warning "Failed to list atomic techniques: $_"
    }
    
    # Test 2: Show details for a common technique
    try {
        $t1078 = Get-AtomicTechnique -Path $AtomicsFolder | Where-Object { $_.Technique -eq "T1078" }
        if ($t1078) {
            Write-Host "    ✅ Technique T1078 (Valid Accounts) loaded successfully" -ForegroundColor Green
        }
    } catch {
        Write-Warning "Failed to load technique T1078: $_"
    }
    
    # Test 3: Check prerequisites for a test
    Write-Host "    ℹ️ To check prerequisites for a technique, run:" -ForegroundColor Cyan
    Write-Host "      Invoke-AtomicTest T1078 -CheckPrereqs" -ForegroundColor Gray
}

# Display usage instructions
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Atomic Red Team Installation Complete" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "Usage Examples:" -ForegroundColor Yellow
Write-Host "  1. List all techniques:" -ForegroundColor White
Write-Host "     Get-AtomicTechnique" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. Show technique details:" -ForegroundColor White
Write-Host "     Get-AtomicTechnique -Path $AtomicsFolder | Where-Object { `$_.Technique -eq 'T1078' }" -ForegroundColor Gray
Write-Host ""
Write-Host "  3. Check prerequisites:" -ForegroundColor White
Write-Host "     Invoke-AtomicTest T1078 -CheckPrereqs" -ForegroundColor Gray
Write-Host ""
Write-Host "  4. Install prerequisites:" -ForegroundColor White
Write-Host "     Invoke-AtomicTest T1078 -GetPrereqs" -ForegroundColor Gray
Write-Host ""
Write-Host "  5. Execute atomic test:" -ForegroundColor White
Write-Host "     Invoke-AtomicTest T1078 -TestNumbers 1" -ForegroundColor Gray
Write-Host ""
Write-Host "  6. Execute with cleanup:" -ForegroundColor White
Write-Host "     Invoke-AtomicTest T1078 -TestNumbers 1 -Cleanup" -ForegroundColor Gray
Write-Host ""
Write-Host "Environment:" -ForegroundColor Yellow
Write-Host "  ATOMIC_RED_TEAM_PATH = $AtomicsFolder" -ForegroundColor Gray
Write-Host ""

Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] ✅ Installation complete" -ForegroundColor Green
