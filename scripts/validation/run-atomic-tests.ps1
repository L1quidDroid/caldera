#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Execute Atomic Red Team tests and verify detection in CALDERA + ELK.

.DESCRIPTION
    Runs predefined Atomic Red Team tests and validates detection in CALDERA operations and ELK Stack.
    Tests common MITRE ATT&CK techniques and confirms purple team integration.

.PARAMETER CalderaUrl
    CALDERA server URL (default: http://localhost:8888).

.PARAMETER ElasticsearchUrl
    Elasticsearch URL (default: http://localhost:9200).

.PARAMETER AtomicsFolder
    Atomic Red Team installation folder (default: C:\AtomicRedTeam).

.PARAMETER Techniques
    Array of MITRE ATT&CK techniques to test (default: T1078, T1003, T1059.001).

.EXAMPLE
    .\run-atomic-tests.ps1

.EXAMPLE
    .\run-atomic-tests.ps1 -Techniques @("T1078", "T1082", "T1059.001") -CalderaUrl "http://10.0.1.4:8888"

.NOTES
    Requires: Invoke-AtomicRedTeam module, CALDERA API access
    Author: Triskele Labs
    Date: December 2025
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$CalderaUrl = "http://localhost:8888",

    [Parameter(Mandatory = $false)]
    [string]$ElasticsearchUrl = "http://localhost:9200",

    [Parameter(Mandatory = $false)]
    [string]$AtomicsFolder = "C:\AtomicRedTeam",

    [Parameter(Mandatory = $false)]
    [string[]]$Techniques = @("T1078", "T1003", "T1059.001")
)

$ErrorActionPreference = "Stop"

# Import Invoke-AtomicRedTeam module
if (!(Get-Module -ListAvailable -Name Invoke-AtomicRedTeam)) {
    Write-Error "Invoke-AtomicRedTeam module not installed. Run install-atomic-red-team.ps1 first."
    exit 1
}

Import-Module Invoke-AtomicRedTeam

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Atomic Red Team Test Execution" -ForegroundColor White
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

$script:TestResults = @()

function Write-TestLog {
    param(
        [string]$Message,
        [ValidateSet('Info', 'Success', 'Warning', 'Error')]
        [string]$Status = 'Info'
    )
    
    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    switch ($Status) {
        'Info'    { Write-Host "[$timestamp] ℹ️  $Message" -ForegroundColor Cyan }
        'Success' { Write-Host "[$timestamp] ✅ $Message" -ForegroundColor Green }
        'Warning' { Write-Host "[$timestamp] ⚠️  $Message" -ForegroundColor Yellow }
        'Error'   { Write-Host "[$timestamp] ❌ $Message" -ForegroundColor Red }
    }
}

function Test-CalderaDetection {
    param(
        [string]$Technique,
        [int]$WaitSeconds = 30
    )
    
    Write-TestLog "Waiting ${WaitSeconds}s for CALDERA to ingest events..." -Status Info
    Start-Sleep -Seconds $WaitSeconds
    
    try {
        $operations = Invoke-RestMethod -Uri "$CalderaUrl/api/v2/operations" -Method GET -Headers @{KEY="ADMIN123"} -TimeoutSec 10
        
        $recentOps = $operations | Where-Object { 
            $_.created -gt (Get-Date).AddMinutes(-5).ToString("yyyy-MM-dd HH:mm:ss")
        }
        
        if ($recentOps) {
            Write-TestLog "CALDERA detected $($recentOps.Count) recent operation(s)" -Status Success
            return $true
        } else {
            Write-TestLog "No recent CALDERA operations found" -Status Warning
            return $false
        }
    } catch {
        Write-TestLog "Failed to query CALDERA API: $_" -Status Error
        return $false
    }
}

function Test-ElkDetection {
    param(
        [string]$Technique,
        [int]$WaitSeconds = 30
    )
    
    Write-TestLog "Waiting ${WaitSeconds}s for ELK to ingest events..." -Status Info
    Start-Sleep -Seconds $WaitSeconds
    
    try {
        $searchQuery = @{
            query = @{
                bool = @{
                    must = @(
                        @{
                            range = @{
                                "@timestamp" = @{
                                    gte = "now-5m"
                                }
                            }
                        },
                        @{
                            match = @{
                                mitre_technique = $Technique
                            }
                        }
                    )
                }
            }
        } | ConvertTo-Json -Depth 10
        
        $searchResult = Invoke-RestMethod -Uri "$ElasticsearchUrl/caldera-*/_search" -Method POST -Body $searchQuery -ContentType "application/json" -TimeoutSec 10
        
        if ($searchResult.hits.total.value -gt 0) {
            Write-TestLog "ELK detected $($searchResult.hits.total.value) event(s) for $Technique" -Status Success
            return $true
        } else {
            Write-TestLog "No ELK events found for $Technique" -Status Warning
            return $false
        }
    } catch {
        Write-TestLog "Failed to query Elasticsearch: $_" -Status Warning
        return $false
    }
}

# ============================================================================
# Execute Atomic Tests
# ============================================================================

foreach ($technique in $Techniques) {
    Write-Host ""
    Write-Host "───────────────────────────────────────────────────────" -ForegroundColor Gray
    Write-Host "  Testing Technique: $technique" -ForegroundColor Yellow
    Write-Host "───────────────────────────────────────────────────────" -ForegroundColor Gray
    Write-Host ""
    
    $testResult = @{
        Technique = $technique
        ExecutionStatus = "NotRun"
        CalderaDetected = $false
        ElkDetected = $false
        ErrorMessage = ""
    }
    
    # Get technique information
    try {
        $techniqueInfo = Get-AtomicTechnique -Path $AtomicsFolder | Where-Object { $_.Technique -eq $technique }
        
        if (!$techniqueInfo) {
            Write-TestLog "Technique $technique not found in Atomic Red Team" -Status Error
            $testResult.ErrorMessage = "Technique not found"
            $script:TestResults += [PSCustomObject]$testResult
            continue
        }
        
        Write-TestLog "Technique: $($techniqueInfo.DisplayName)" -Status Info
        Write-TestLog "Tactic: $($techniqueInfo.Tactic -join ', ')" -Status Info
        Write-TestLog "Available tests: $($techniqueInfo.atomic_tests.Count)" -Status Info
    } catch {
        Write-TestLog "Failed to retrieve technique info: $_" -Status Error
        $testResult.ErrorMessage = $_.Exception.Message
        $script:TestResults += [PSCustomObject]$testResult
        continue
    }
    
    # Check prerequisites
    Write-TestLog "Checking prerequisites..." -Status Info
    try {
        Invoke-AtomicTest $technique -CheckPrereqs -ErrorAction SilentlyContinue
        Write-TestLog "Prerequisites verified" -Status Success
    } catch {
        Write-TestLog "Prerequisites missing, attempting to install..." -Status Warning
        try {
            Invoke-AtomicTest $technique -GetPrereqs -ErrorAction Stop
            Write-TestLog "Prerequisites installed" -Status Success
        } catch {
            Write-TestLog "Failed to install prerequisites: $_" -Status Error
            $testResult.ErrorMessage = "Prerequisite installation failed"
            $script:TestResults += [PSCustomObject]$testResult
            continue
        }
    }
    
    # Execute test
    Write-TestLog "Executing Atomic test for $technique..." -Status Info
    try {
        Invoke-AtomicTest $technique -TestNumbers 1 -TimeoutSeconds 60 -ErrorAction Stop
        Write-TestLog "Test executed successfully" -Status Success
        $testResult.ExecutionStatus = "Success"
    } catch {
        Write-TestLog "Test execution failed: $_" -Status Error
        $testResult.ExecutionStatus = "Failed"
        $testResult.ErrorMessage = $_.Exception.Message
        $script:TestResults += [PSCustomObject]$testResult
        continue
    }
    
    # Verify detection in CALDERA
    $testResult.CalderaDetected = Test-CalderaDetection -Technique $technique -WaitSeconds 30
    
    # Verify detection in ELK
    $testResult.ElkDetected = Test-ElkDetection -Technique $technique -WaitSeconds 30
    
    # Cleanup
    Write-TestLog "Running cleanup..." -Status Info
    try {
        Invoke-AtomicTest $technique -TestNumbers 1 -Cleanup -ErrorAction SilentlyContinue
        Write-TestLog "Cleanup completed" -Status Success
    } catch {
        Write-TestLog "Cleanup warning: $_" -Status Warning
    }
    
    $script:TestResults += [PSCustomObject]$testResult
}

# ============================================================================
# Summary
# ============================================================================
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Test Execution Summary" -ForegroundColor White
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

$successfulTests = $script:TestResults | Where-Object { $_.ExecutionStatus -eq "Success" }
$calderaDetections = $script:TestResults | Where-Object { $_.CalderaDetected -eq $true }
$elkDetections = $script:TestResults | Where-Object { $_.ElkDetected -eq $true }

Write-Host "Total Tests: $($script:TestResults.Count)" -ForegroundColor White
Write-Host "  ✅ Executed Successfully: $($successfulTests.Count)" -ForegroundColor Green
Write-Host "  ⚠️  Failed: $($script:TestResults.Count - $successfulTests.Count)" -ForegroundColor Yellow
Write-Host ""
Write-Host "Detection Coverage:" -ForegroundColor White
Write-Host "  CALDERA: $($calderaDetections.Count) / $($script:TestResults.Count)" -ForegroundColor $(if ($calderaDetections.Count -eq $script:TestResults.Count) { "Green" } else { "Yellow" })
Write-Host "  ELK Stack: $($elkDetections.Count) / $($script:TestResults.Count)" -ForegroundColor $(if ($elkDetections.Count -eq $script:TestResults.Count) { "Green" } else { "Yellow" })
Write-Host ""

# Detailed results table
Write-Host "Detailed Results:" -ForegroundColor Cyan
$script:TestResults | Format-Table -Property Technique, ExecutionStatus, CalderaDetected, ElkDetected, ErrorMessage -AutoSize

Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Review CALDERA operations: $CalderaUrl/campaign" -ForegroundColor White
Write-Host "  2. Check ELK dashboards: $($ElasticsearchUrl -replace ':9200', ':5601')/app/dashboards" -ForegroundColor White
Write-Host "  3. Analyze detection gaps for failed detections" -ForegroundColor White
Write-Host ""

if ($successfulTests.Count -eq $script:TestResults.Count) {
    Write-Host "🎉 All tests executed successfully!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "⚠️  Some tests failed. Review errors above." -ForegroundColor Yellow
    exit 1
}
