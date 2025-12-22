#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Validate CALDERA + ELK Stack deployment.

.DESCRIPTION
    Comprehensive validation of CALDERA server, ELK Stack, agents, and connectivity.
    Runs health checks on all components and verifies integration.

.PARAMETER CalderaUrl
    CALDERA server URL (default: http://localhost:8888).

.PARAMETER KibanaUrl
    Kibana URL (default: http://localhost:5601).

.PARAMETER ElasticsearchUrl
    Elasticsearch URL (default: http://localhost:9200).

.EXAMPLE
    .\validate-deployment.ps1

.EXAMPLE
    .\validate-deployment.ps1 -CalderaUrl "http://10.0.1.4:8888" -KibanaUrl "http://10.0.2.4:5601" -ElasticsearchUrl "http://10.0.2.4:9200"

.NOTES
    Author: Triskele Labs
    Date: December 2025
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$CalderaUrl = "http://localhost:8888",

    [Parameter(Mandatory = $false)]
    [string]$KibanaUrl = "http://localhost:5601",

    [Parameter(Mandatory = $false)]
    [string]$ElasticsearchUrl = "http://localhost:9200"
)

$ErrorActionPreference = "Continue"

$script:PassedChecks = 0
$script:FailedChecks = 0
$script:WarningChecks = 0

function Write-Check {
    param(
        [string]$Message,
        [ValidateSet('Info', 'Success', 'Warning', 'Error')]
        [string]$Status = 'Info'
    )
    
    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    switch ($Status) {
        'Info'    { Write-Host "[$timestamp] ℹ️  $Message" -ForegroundColor Cyan }
        'Success' { Write-Host "[$timestamp] ✅ $Message" -ForegroundColor Green; $script:PassedChecks++ }
        'Warning' { Write-Host "[$timestamp] ⚠️  $Message" -ForegroundColor Yellow; $script:WarningChecks++ }
        'Error'   { Write-Host "[$timestamp] ❌ $Message" -ForegroundColor Red; $script:FailedChecks++ }
    }
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  CALDERA + ELK Stack Deployment Validation" -ForegroundColor White
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# 1. CALDERA Server Health Check
# ============================================================================
Write-Check "Checking CALDERA server health..." -Status Info

try {
    $healthResponse = Invoke-RestMethod -Uri "$CalderaUrl/api/v2/health" -Method GET -Headers @{KEY="ADMIN123"} -TimeoutSec 10
    Write-Check "CALDERA server is responding (version: $($healthResponse.version))" -Status Success
} catch {
    Write-Check "CALDERA server health check failed: $_" -Status Error
}

# Check CALDERA API authentication
try {
    $agentsResponse = Invoke-RestMethod -Uri "$CalderaUrl/api/v2/agents" -Method GET -Headers @{KEY="ADMIN123"} -TimeoutSec 10
    $agentCount = $agentsResponse.Count
    Write-Check "CALDERA API authentication successful ($agentCount agents)" -Status Success
} catch {
    Write-Check "CALDERA API authentication failed: $_" -Status Error
}

# Check CALDERA plugins
try {
    $pluginsResponse = Invoke-RestMethod -Uri "$CalderaUrl/api/v2/plugins" -Method GET -Headers @{KEY="ADMIN123"} -TimeoutSec 10
    $pluginCount = $pluginsResponse.Count
    Write-Check "CALDERA plugins loaded: $pluginCount" -Status Success
    
    $enabledPlugins = $pluginsResponse | Where-Object { $_.enabled -eq $true }
    Write-Check "Enabled plugins: $($enabledPlugins.name -join ', ')" -Status Info
} catch {
    Write-Check "Failed to retrieve CALDERA plugins: $_" -Status Warning
}

# ============================================================================
# 2. Elasticsearch Health Check
# ============================================================================
Write-Check "Checking Elasticsearch health..." -Status Info

try {
    $esHealth = Invoke-RestMethod -Uri "$ElasticsearchUrl/_cluster/health" -Method GET -TimeoutSec 10
    
    if ($esHealth.status -eq "green") {
        Write-Check "Elasticsearch cluster status: GREEN" -Status Success
    } elseif ($esHealth.status -eq "yellow") {
        Write-Check "Elasticsearch cluster status: YELLOW (acceptable for single-node)" -Status Warning
    } else {
        Write-Check "Elasticsearch cluster status: RED" -Status Error
    }
    
    Write-Check "Elasticsearch nodes: $($esHealth.number_of_nodes)" -Status Info
    Write-Check "Elasticsearch indices: $($esHealth.active_shards)" -Status Info
} catch {
    Write-Check "Elasticsearch health check failed: $_" -Status Error
}

# Check Elasticsearch indices
try {
    $indices = Invoke-RestMethod -Uri "$ElasticsearchUrl/_cat/indices/caldera-*?format=json" -Method GET -TimeoutSec 10
    if ($indices.Count -gt 0) {
        Write-Check "CALDERA indices found: $($indices.Count)" -Status Success
        foreach ($index in $indices) {
            Write-Check "  - $($index.index): $($index.'docs.count') documents" -Status Info
        }
    } else {
        Write-Check "No CALDERA indices found (expected if no logs sent yet)" -Status Warning
    }
} catch {
    Write-Check "Failed to retrieve Elasticsearch indices: $_" -Status Warning
}

# ============================================================================
# 3. Kibana Health Check
# ============================================================================
Write-Check "Checking Kibana health..." -Status Info

try {
    $kibanaStatus = Invoke-RestMethod -Uri "$KibanaUrl/api/status" -Method GET -TimeoutSec 10
    
    if ($kibanaStatus.status.overall.level -eq "available") {
        Write-Check "Kibana status: AVAILABLE" -Status Success
    } else {
        Write-Check "Kibana status: $($kibanaStatus.status.overall.level)" -Status Warning
    }
    
    Write-Check "Kibana version: $($kibanaStatus.version.number)" -Status Info
} catch {
    Write-Check "Kibana health check failed: $_" -Status Error
}

# ============================================================================
# 4. Agent Connectivity Check
# ============================================================================
Write-Check "Checking CALDERA agent connectivity..." -Status Info

try {
    $agents = Invoke-RestMethod -Uri "$CalderaUrl/api/v2/agents" -Method GET -Headers @{KEY="ADMIN123"} -TimeoutSec 10
    
    if ($agents.Count -eq 0) {
        Write-Check "No agents registered (expected if agents not yet deployed)" -Status Warning
    } else {
        Write-Check "Total agents: $($agents.Count)" -Status Success
        
        $redAgents = $agents | Where-Object { $_.group -eq "red" }
        $blueAgents = $agents | Where-Object { $_.group -eq "blue" }
        
        Write-Check "Red team agents: $($redAgents.Count)" -Status Info
        Write-Check "Blue team agents: $($blueAgents.Count)" -Status Info
        
        foreach ($agent in $agents) {
            $lastSeen = [datetime]$agent.last_seen
            $secondsSinceLastSeen = ((Get-Date) - $lastSeen).TotalSeconds
            
            if ($secondsSinceLastSeen -lt 60) {
                Write-Check "  ✅ Agent $($agent.paw) ($($agent.host)): Active" -Status Success
            } elseif ($secondsSinceLastSeen -lt 300) {
                Write-Check "  ⚠️  Agent $($agent.paw) ($($agent.host)): Last seen $([int]$secondsSinceLastSeen)s ago" -Status Warning
            } else {
                Write-Check "  ❌ Agent $($agent.paw) ($($agent.host)): Inactive (last seen $([int]$secondsSinceLastSeen)s ago)" -Status Error
            }
        }
    }
} catch {
    Write-Check "Failed to retrieve CALDERA agents: $_" -Status Error
}

# ============================================================================
# 5. Network Connectivity Check
# ============================================================================
Write-Check "Checking network connectivity..." -Status Info

# Test CALDERA port
try {
    $calderaUri = [System.Uri]$CalderaUrl
    $calderaConnection = Test-NetConnection -ComputerName $calderaUri.Host -Port $calderaUri.Port -WarningAction SilentlyContinue
    
    if ($calderaConnection.TcpTestSucceeded) {
        Write-Check "CALDERA port $($calderaUri.Port) is accessible" -Status Success
    } else {
        Write-Check "CALDERA port $($calderaUri.Port) is not accessible" -Status Error
    }
} catch {
    Write-Check "Failed to test CALDERA network connectivity: $_" -Status Error
}

# Test Kibana port
try {
    $kibanaUri = [System.Uri]$KibanaUrl
    $kibanaConnection = Test-NetConnection -ComputerName $kibanaUri.Host -Port $kibanaUri.Port -WarningAction SilentlyContinue
    
    if ($kibanaConnection.TcpTestSucceeded) {
        Write-Check "Kibana port $($kibanaUri.Port) is accessible" -Status Success
    } else {
        Write-Check "Kibana port $($kibanaUri.Port) is not accessible" -Status Error
    }
} catch {
    Write-Check "Failed to test Kibana network connectivity: $_" -Status Error
}

# Test Elasticsearch port
try {
    $esUri = [System.Uri]$ElasticsearchUrl
    $esConnection = Test-NetConnection -ComputerName $esUri.Host -Port $esUri.Port -WarningAction SilentlyContinue
    
    if ($esConnection.TcpTestSucceeded) {
        Write-Check "Elasticsearch port $($esUri.Port) is accessible" -Status Success
    } else {
        Write-Check "Elasticsearch port $($esUri.Port) is not accessible" -Status Error
    }
} catch {
    Write-Check "Failed to test Elasticsearch network connectivity: $_" -Status Error
}

# ============================================================================
# 6. Summary
# ============================================================================
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Validation Summary" -ForegroundColor White
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

Write-Host "Total Checks: $($script:PassedChecks + $script:FailedChecks + $script:WarningChecks)" -ForegroundColor White
Write-Host "  ✅ Passed:   $script:PassedChecks" -ForegroundColor Green
Write-Host "  ⚠️  Warnings: $script:WarningChecks" -ForegroundColor Yellow
Write-Host "  ❌ Failed:   $script:FailedChecks" -ForegroundColor Red
Write-Host ""

if ($script:FailedChecks -eq 0) {
    Write-Host "🎉 All critical checks passed!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Access URLs:" -ForegroundColor Cyan
    Write-Host "  CALDERA: $CalderaUrl" -ForegroundColor White
    Write-Host "  Kibana:  $KibanaUrl" -ForegroundColor White
    Write-Host "  Elasticsearch: $ElasticsearchUrl" -ForegroundColor White
    Write-Host ""
    Write-Host "Default Credentials:" -ForegroundColor Cyan
    Write-Host "  CALDERA: admin / admin" -ForegroundColor White
    Write-Host "  API Key: ADMIN123" -ForegroundColor White
    Write-Host ""
    exit 0
} else {
    Write-Host "⚠️  Some checks failed. Review errors above." -ForegroundColor Yellow
    exit 1
}
