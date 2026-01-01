// ============================================================================
// Windows Agent Module - Red Team Target
// ============================================================================
// Windows Server 2022 with Sandcat agent and optional Atomic Red Team
// ============================================================================

param location string
param environment string
param vmSize string
param adminUsername string
@secure()
param adminPassword string
param subnetId string
@description('Optional Log Analytics Workspace resource ID for diagnostics')
param logAnalyticsWorkspaceId string = ''
param tags object

var vmName = 'vm-windows-agent-${environment}'
var nicName = 'nic-${vmName}'
var pipName = 'pip-${vmName}'

resource pip 'Microsoft.Network/publicIPAddresses@2023-05-01' = {
  name: pipName
  location: location
  tags: tags
  sku: { name: 'Standard' }
  properties: {
    publicIPAllocationMethod: 'Static'
  }
}

resource nic 'Microsoft.Network/networkInterfaces@2023-05-01' = {
  name: nicName
  location: location
  tags: tags
  properties: {
    ipConfigurations: [{
      name: 'ipconfig1'
      properties: {
        subnet: { id: subnetId }
        privateIPAllocationMethod: 'Dynamic'
        publicIPAddress: { id: pip.id }
      }
    }]
  }
}

resource vm 'Microsoft.Compute/virtualMachines@2023-07-01' = {
  name: vmName
  location: location
  tags: tags
  identity: { type: 'SystemAssigned' }
  properties: {
    hardwareProfile: { vmSize: vmSize }
    osProfile: {
      computerName: vmName
      adminUsername: adminUsername
      adminPassword: adminPassword
      windowsConfiguration: {
        provisionVMAgent: true
        enableAutomaticUpdates: false
      }
    }
    storageProfile: {
      imageReference: {
        publisher: 'MicrosoftWindowsServer'
        offer: 'WindowsServer'
        sku: '2022-datacenter-azure-edition'
        version: 'latest'
      }
      osDisk: {
        name: '${vmName}-osdisk'
        createOption: 'FromImage'
        managedDisk: { storageAccountType: 'Premium_LRS' }
        diskSizeGB: 128
      }
    }
    networkProfile: {
      networkInterfaces: [{ id: nic.id }]
    }
    diagnosticsProfile: { bootDiagnostics: { enabled: true } }
  }
}

// Custom Script Extension - Install Sandcat agent and Winlogbeat
resource vmExtension 'Microsoft.Compute/virtualMachines/extensions@2023-07-01' = {
  parent: vm
  name: 'install-caldera-agent-winlogbeat'
  location: location
  properties: {
    publisher: 'Microsoft.Compute'
    type: 'CustomScriptExtension'
    typeHandlerVersion: '1.10'
    autoUpgradeMinorVersion: true
    protectedSettings: {
      // Decode base64 script into a temp file, then execute with Caldera/ELK IPs
      commandToExecute: '''
powershell.exe -ExecutionPolicy Bypass -Command "$script=[System.Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('${installScript}'));$path='C:\Windows\Temp\install-windows-agent.ps1';Set-Content -Path $path -Value $script -Force; & $path -calderaServerIp ${calderaServerIp} -elkServerIp ${elkServerIp}"
'''
    }
  }
}

// Send platform metrics to Log Analytics when provided
resource vmDiagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = if (!empty(logAnalyticsWorkspaceId)) {
  name: 'vm-windows-agent-diagnostics'
  scope: vm
  properties: {
    workspaceId: logAnalyticsWorkspaceId
    metrics: [
      {
        category: 'AllMetrics'
        enabled: true
        retentionPolicy: {
          days: 0
          enabled: false
        }
      }
    ]
    logs: []
  }
}

output vmId string = vm.id
output vmName string = vm.name
output publicIpAddress string = pip.properties.ipAddress
output privateIpAddress string = nic.properties.ipConfigurations[0].properties.privateIPAddress
