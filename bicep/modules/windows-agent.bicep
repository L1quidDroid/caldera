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
param calderaServerIp string
param logAnalyticsWorkspaceId string
param enableAtomicRedTeam bool = false
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

// Custom Script Extension - Install Sandcat agent
resource vmExtension 'Microsoft.Compute/virtualMachines/extensions@2023-07-01' = {
  parent: vm
  name: 'install-caldera-agent'
  location: location
  properties: {
    publisher: 'Microsoft.Compute'
    type: 'CustomScriptExtension'
    typeHandlerVersion: '1.10'
    autoUpgradeMinorVersion: true
    settings: {
      commandToExecute: 'powershell.exe -ExecutionPolicy Bypass -Command "$calderaUrl = \'http://${calderaServerIp}:8888\'; $sandcatUrl = \"$calderaUrl/file/download\"; $agentPath = \"$env:TEMP\\sandcat.exe\"; Invoke-WebRequest -Uri $sandcatUrl -OutFile $agentPath -UseBasicParsing; Start-Process -FilePath $agentPath -ArgumentList \'-server\',\'${calderaServerIp}:8888\',\'-group\',\'red\',\'-v\' -WindowStyle Hidden; Write-Host \'Sandcat agent started\'"'
    }
  }
}

output vmId string = vm.id
output vmName string = vm.name
output publicIpAddress string = pip.properties.ipAddress
output privateIpAddress string = nic.properties.ipConfigurations[0].properties.privateIPAddress
