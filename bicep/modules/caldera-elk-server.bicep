// ============================================================================
// CALDERA & ELK Server Module
// ============================================================================
param location string
param environment string
param vmSize string
param adminUsername string
@secure()
param adminPassword string
param sshPublicKey string
param subnetId string
@description('Optional Log Analytics Workspace resource ID for diagnostics')
param logAnalyticsWorkspaceId string = ''

@description('Storage account type for OS disk (use Standard_LRS for Free/Student accounts if Premium fails)')
@allowed(['Premium_LRS', 'Standard_LRS', 'StandardSSD_LRS'])
param osDiskType string = 'Premium_LRS'

param tags object

var vmName = 'vm-caldera-elk-${environment}'
var nicName = 'nic-${vmName}'
var pipName = 'pip-${vmName}'
var osDiskName = '${vmName}-osdisk'

resource pip 'Microsoft.Network/publicIPAddresses@2023-05-01' = {
  name: pipName
  location: location
  tags: tags
  sku: {
    name: 'Standard'
  }
  properties: {
    publicIPAllocationMethod: 'Static'
    dnsSettings: {
      domainNameLabel: '${vmName}-${uniqueString(resourceGroup().id)}'
    }
  }
}

resource nic 'Microsoft.Network/networkInterfaces@2023-05-01' = {
  name: nicName
  location: location
  tags: tags
  properties: {
    ipConfigurations: [
      {
        name: 'ipconfig1'
        properties: {
          subnet: {
            id: subnetId
          }
          privateIPAllocationMethod: 'Dynamic'
          publicIPAddress: {
            id: pip.id
          }
        }
      }
    ]
  }
}

resource vm 'Microsoft.Compute/virtualMachines@2023-07-01' = {
  name: vmName
  location: location
  tags: tags
  properties: {
    hardwareProfile: {
      vmSize: vmSize
    }
    osProfile: {
      computerName: vmName
      adminUsername: adminUsername
      adminPassword: adminPassword
      linuxConfiguration: {
        disablePasswordAuthentication: false
        ssh: !empty(sshPublicKey) ? {
          publicKeys: [
            {
              path: '/home/${adminUsername}/.ssh/authorized_keys'
              keyData: sshPublicKey
            }
          ]
        } : null
      }
    }
    storageProfile: {
      imageReference: {
        publisher: 'Canonical'
        offer: '0001-com-ubuntu-server-jammy'
        sku: '22_04-lts-gen2'
        version: 'latest'
      }
      osDisk: {
        name: osDiskName
        createOption: 'FromImage'
        managedDisk: {
          storageAccountType: osDiskType
        }
        diskSizeGB: 256 // Increased for both apps
      }
    }
    networkProfile: {
      networkInterfaces: [
        {
          id: nic.id
        }
      ]
    }
  }
}

@secure()
param installScript string

resource vmExtension 'Microsoft.Compute/virtualMachines/extensions@2023-07-01' = {
  parent: vm
  name: 'caldera-elk-setup'
  location: location
  properties: {
    publisher: 'Microsoft.Azure.Extensions'
    type: 'CustomScript'
    typeHandlerVersion: '2.1'
    autoUpgradeMinorVersion: true
    // Decode provided base64 payload into an executable script to avoid inline quoting issues
    protectedSettings: {
      commandToExecute: 'bash -c "echo ${installScript} | base64 -d > /tmp/install-caldera-elk.sh && chmod +x /tmp/install-caldera-elk.sh && /tmp/install-caldera-elk.sh"'
    }
  }
}

// Send platform metrics to Log Analytics when provided
resource vmDiagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = if (!empty(logAnalyticsWorkspaceId)) {
  name: 'vm-caldera-elk-diagnostics'
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
output fqdn string = pip.properties.dnsSettings.fqdn
