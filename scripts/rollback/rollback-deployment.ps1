#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Rollback CALDERA + ELK Stack deployment using Azure snapshots.

.DESCRIPTION
    Creates snapshots before deployment and restores VMs from snapshots on failure.
    Provides disaster recovery and rollback capabilities for CALDERA infrastructure.

.PARAMETER ResourceGroup
    Azure resource group name.

.PARAMETER CreateSnapshots
    Create snapshots of all VMs in the resource group.

.PARAMETER RestoreFromSnapshots
    Restore VMs from latest snapshots.

.PARAMETER SnapshotPrefix
    Prefix for snapshot names (default: caldera-snapshot).

.EXAMPLE
    .\rollback-deployment.ps1 -ResourceGroup "rg-caldera-prod" -CreateSnapshots

.EXAMPLE
    .\rollback-deployment.ps1 -ResourceGroup "rg-caldera-prod" -RestoreFromSnapshots

.NOTES
    Requires: Azure CLI, appropriate Azure permissions
    Author: Triskele Labs
    Date: December 2025
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ResourceGroup,

    [Parameter(Mandatory = $false)]
    [switch]$CreateSnapshots,

    [Parameter(Mandatory = $false)]
    [switch]$RestoreFromSnapshots,

    [Parameter(Mandatory = $false)]
    [string]$SnapshotPrefix = "caldera-snapshot"
)

$ErrorActionPreference = "Stop"

function Write-Log {
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

# Verify Azure CLI is installed
if (!(Get-Command az -ErrorAction SilentlyContinue)) {
    Write-Log "Azure CLI is not installed. Please install from: https://aka.ms/installazurecliwindows" -Status Error
    exit 1
}

# Verify Azure login
Write-Log "Verifying Azure authentication..." -Status Info
$azAccount = az account show 2>&1 | ConvertFrom-Json
if (!$azAccount) {
    Write-Log "Not logged in to Azure. Run 'az login' first." -Status Error
    exit 1
}
Write-Log "Logged in as: $($azAccount.user.name)" -Status Success

# Verify resource group exists
Write-Log "Verifying resource group exists..." -Status Info
$rgExists = az group exists --name $ResourceGroup
if ($rgExists -ne "true") {
    Write-Log "Resource group '$ResourceGroup' does not exist" -Status Error
    exit 1
}
Write-Log "Resource group '$ResourceGroup' found" -Status Success

# ============================================================================
# Create Snapshots
# ============================================================================
if ($CreateSnapshots) {
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "  Creating VM Snapshots" -ForegroundColor White
    Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""
    
    # Get all VMs in resource group
    Write-Log "Retrieving VMs in resource group..." -Status Info
    $vms = az vm list --resource-group $ResourceGroup | ConvertFrom-Json
    
    if ($vms.Count -eq 0) {
        Write-Log "No VMs found in resource group '$ResourceGroup'" -Status Warning
        exit 0
    }
    
    Write-Log "Found $($vms.Count) VM(s)" -Status Success
    
    foreach ($vm in $vms) {
        Write-Log "Processing VM: $($vm.name)" -Status Info
        
        # Get OS disk
        $osDisk = az disk show --ids $vm.storageProfile.osDisk.managedDisk.id | ConvertFrom-Json
        $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
        $snapshotName = "$SnapshotPrefix-$($vm.name)-$timestamp"
        
        Write-Log "Creating snapshot: $snapshotName" -Status Info
        
        try {
            az snapshot create `
                --resource-group $ResourceGroup `
                --name $snapshotName `
                --source $osDisk.id `
                --location $vm.location `
                --tags "vm=$($vm.name)" "created=$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" "purpose=rollback" `
                | Out-Null
            
            Write-Log "Snapshot created: $snapshotName" -Status Success
        } catch {
            Write-Log "Failed to create snapshot for $($vm.name): $_" -Status Error
            continue
        }
        
        # Create snapshots for data disks (if any)
        if ($vm.storageProfile.dataDisks.Count -gt 0) {
            Write-Log "Found $($vm.storageProfile.dataDisks.Count) data disk(s)" -Status Info
            
            foreach ($dataDisk in $vm.storageProfile.dataDisks) {
                $dataDiskInfo = az disk show --ids $dataDisk.managedDisk.id | ConvertFrom-Json
                $dataSnapshotName = "$SnapshotPrefix-$($vm.name)-data-$($dataDisk.lun)-$timestamp"
                
                Write-Log "Creating data disk snapshot: $dataSnapshotName" -Status Info
                
                try {
                    az snapshot create `
                        --resource-group $ResourceGroup `
                        --name $dataSnapshotName `
                        --source $dataDiskInfo.id `
                        --location $vm.location `
                        --tags "vm=$($vm.name)" "lun=$($dataDisk.lun)" "created=$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" "purpose=rollback" `
                        | Out-Null
                    
                    Write-Log "Data disk snapshot created: $dataSnapshotName" -Status Success
                } catch {
                    Write-Log "Failed to create data disk snapshot: $_" -Status Error
                    continue
                }
            }
        }
    }
    
    Write-Host ""
    Write-Log "Snapshot creation complete" -Status Success
    Write-Host ""
}

# ============================================================================
# Restore from Snapshots
# ============================================================================
if ($RestoreFromSnapshots) {
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "  Restoring VMs from Snapshots" -ForegroundColor White
    Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""
    
    Write-Log "⚠️  WARNING: This will replace existing VM disks with snapshot data" -Status Warning
    $confirmation = Read-Host "Type 'YES' to confirm rollback"
    
    if ($confirmation -ne "YES") {
        Write-Log "Rollback cancelled by user" -Status Warning
        exit 0
    }
    
    # Get all snapshots in resource group
    Write-Log "Retrieving snapshots..." -Status Info
    $snapshots = az snapshot list --resource-group $ResourceGroup | ConvertFrom-Json | Where-Object { $_.name -like "$SnapshotPrefix-*" }
    
    if ($snapshots.Count -eq 0) {
        Write-Log "No snapshots found with prefix '$SnapshotPrefix'" -Status Error
        exit 1
    }
    
    # Group snapshots by VM name and get latest for each VM
    $vmSnapshots = $snapshots | Group-Object -Property { $_.tags.vm } | ForEach-Object {
        $latest = $_.Group | Sort-Object -Property timeCreated -Descending | Select-Object -First 1
        @{
            VMName = $_.Name
            Snapshot = $latest
        }
    }
    
    Write-Log "Found snapshots for $($vmSnapshots.Count) VM(s)" -Status Success
    
    foreach ($vmSnapshot in $vmSnapshots) {
        $vmName = $vmSnapshot.VMName
        $snapshot = $vmSnapshot.Snapshot
        
        Write-Log "Restoring VM: $vmName from snapshot: $($snapshot.name)" -Status Info
        
        # Get VM details
        try {
            $vm = az vm show --resource-group $ResourceGroup --name $vmName | ConvertFrom-Json
        } catch {
            Write-Log "VM '$vmName' not found, skipping..." -Status Warning
            continue
        }
        
        # Stop VM
        Write-Log "Stopping VM: $vmName" -Status Info
        az vm stop --resource-group $ResourceGroup --name $vmName --no-wait | Out-Null
        az vm wait --resource-group $ResourceGroup --name $vmName --custom "instanceView.statuses[?code=='PowerState/stopped']" | Out-Null
        Write-Log "VM stopped" -Status Success
        
        # Deallocate VM
        Write-Log "Deallocating VM: $vmName" -Status Info
        az vm deallocate --resource-group $ResourceGroup --name $vmName | Out-Null
        Write-Log "VM deallocated" -Status Success
        
        # Delete old OS disk
        $oldOsDiskId = $vm.storageProfile.osDisk.managedDisk.id
        $oldOsDiskName = $vm.storageProfile.osDisk.name
        
        # Create new disk from snapshot
        $newDiskName = "$($vm.storageProfile.osDisk.name)-restored-$(Get-Date -Format 'yyyyMMddHHmmss')"
        Write-Log "Creating new disk from snapshot: $newDiskName" -Status Info
        
        try {
            $newDisk = az disk create `
                --resource-group $ResourceGroup `
                --name $newDiskName `
                --source $snapshot.id `
                --location $vm.location `
                --sku $vm.storageProfile.osDisk.managedDisk.storageAccountType `
                | ConvertFrom-Json
            
            Write-Log "New disk created: $newDiskName" -Status Success
        } catch {
            Write-Log "Failed to create disk from snapshot: $_" -Status Error
            
            # Restart VM with old disk
            Write-Log "Restarting VM with original disk..." -Status Warning
            az vm start --resource-group $ResourceGroup --name $vmName | Out-Null
            continue
        }
        
        # Swap OS disk
        Write-Log "Swapping OS disk..." -Status Info
        try {
            az vm update `
                --resource-group $ResourceGroup `
                --name $vmName `
                --os-disk $newDisk.id `
                | Out-Null
            
            Write-Log "OS disk swapped successfully" -Status Success
        } catch {
            Write-Log "Failed to swap OS disk: $_" -Status Error
            
            # Delete new disk and restart VM
            az disk delete --ids $newDisk.id --yes | Out-Null
            az vm start --resource-group $ResourceGroup --name $vmName | Out-Null
            continue
        }
        
        # Start VM
        Write-Log "Starting VM: $vmName" -Status Info
        az vm start --resource-group $ResourceGroup --name $vmName | Out-Null
        Write-Log "VM started successfully" -Status Success
        
        # Delete old OS disk
        Write-Log "Deleting old OS disk: $oldOsDiskName" -Status Info
        az disk delete --ids $oldOsDiskId --yes | Out-Null
        Write-Log "Old disk deleted" -Status Success
        
        Write-Log "Rollback complete for VM: $vmName" -Status Success
        Write-Host ""
    }
    
    Write-Host ""
    Write-Log "All VMs restored from snapshots" -Status Success
    Write-Host ""
}

# ============================================================================
# Display Help
# ============================================================================
if (!$CreateSnapshots -and !$RestoreFromSnapshots) {
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "  CALDERA Deployment Rollback Tool" -ForegroundColor White
    Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor Yellow
    Write-Host "  Create snapshots before deployment:" -ForegroundColor White
    Write-Host "    .\rollback-deployment.ps1 -ResourceGroup 'rg-caldera-prod' -CreateSnapshots" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  Restore from snapshots (rollback):" -ForegroundColor White
    Write-Host "    .\rollback-deployment.ps1 -ResourceGroup 'rg-caldera-prod' -RestoreFromSnapshots" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Options:" -ForegroundColor Yellow
    Write-Host "  -ResourceGroup      Azure resource group name (required)" -ForegroundColor White
    Write-Host "  -CreateSnapshots    Create snapshots of all VMs" -ForegroundColor White
    Write-Host "  -RestoreFromSnapshots  Restore VMs from latest snapshots" -ForegroundColor White
    Write-Host "  -SnapshotPrefix     Snapshot name prefix (default: caldera-snapshot)" -ForegroundColor White
    Write-Host ""
}
