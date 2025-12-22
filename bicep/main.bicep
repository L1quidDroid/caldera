// ============================================================================
// CALDERA Purple Team Lab - Main Bicep Template
// ============================================================================
// Production-ready adversary emulation platform with ELK Stack
// Region: Australia East (data sovereignty compliance)
// Last Updated: 2025-12-22
// ============================================================================

targetScope = 'subscription'

@description('Environment name (dev, stage, prod-lab)')
@allowed([
  'dev'
  'stage'
  'prod-lab'
])
param environment string = 'dev'

@description('Azure region for deployment')
@allowed([
  'australiaeast'
  'australiasoutheast'
])
param location string = 'australiaeast'

@description('Unique deployment identifier (timestamp)')
param deploymentId string = utcNow('yyyyMMdd-HHmm')

@description('Owner tag for resource management')
param ownerTag string = 'tonyto'

@description('Cost center for billing allocation')
param costCenter string = 'cybersec-purple-team'

@description('MITRE ATT&CK tactic for this lab instance')
param attackTactic string = 'TA0001'

@description('Enable Atomic Red Team auto-execution')
param enableAtomicRedTeam bool = false

@description('Admin username for all VMs')
@secure()
param adminUsername string

@description('Admin password for all VMs')
@secure()
param adminPassword string

@description('SSH public key for Linux VMs')
param sshPublicKey string = ''

@description('Key Vault resource ID for secrets')
param keyVaultId string = ''

// ============================================================================
// VARIABLES
// ============================================================================

var resourceGroupName = 'rg-caldera-${environment}-${deploymentId}'
var commonTags = {
  environment: environment
  owner: ownerTag
  'cost-center': costCenter
  'mitre-attck-tactic': attackTactic
  'data-sovereignty': 'australia'
  'deployment-id': deploymentId
  workload: 'purple-team-lab'
  'managed-by': 'bicep-cicd'
}

// Environment-specific VM sizes
var vmSizes = {
  dev: {
    calderaElk: 'Standard_D4s_v3' // Larger VM for combined workload
    agent: 'Standard_B2s'
  }
  stage: {
    calderaElk: 'Standard_D8s_v3'
    agent: 'Standard_D2s_v5'
  }
  'prod-lab': {
    calderaElk: 'Standard_E8s_v3'
    agent: 'Standard_D2s_v5'
  }
}

// ============================================================================
// RESOURCE GROUP
// ============================================================================

resource resourceGroup 'Microsoft.Resources/resourceGroups@2023-07-01' = {
  name: resourceGroupName
  location: location
  tags: commonTags
}

// ============================================================================
// MODULES
// ============================================================================

// Network Infrastructure
module network 'modules/network.bicep' = {
  scope: resourceGroup
  name: 'network-deployment'
  params: {
    location: location
    environment: environment
    tags: commonTags
  }
}

// Log Analytics Workspace
module logging 'modules/logging.bicep' = {
  scope: resourceGroup
  name: 'logging-deployment'
  params: {
    location: location
    environment: environment
    tags: commonTags
    retentionDays: environment == 'prod-lab' ? 90 : 30
  }
}

// CALDERA & ELK Server (Consolidated)
module calderaElkServer 'modules/caldera-elk-server.bicep' = {
  scope: resourceGroup
  name: 'caldera-elk-server-deployment'
  params: {
    location: location
    environment: environment
    vmSize: vmSizes[environment].calderaElk
    adminUsername: adminUsername
    adminPassword: adminPassword
    sshPublicKey: sshPublicKey
    subnetId: network.outputs.calderaSubnetId // Using caldera subnet
    tags: union(commonTags, {
      role: 'caldera-elk-server'
    })
  }
}

// Windows Agent VM (Red Team target)
module windowsAgent 'modules/windows-agent.bicep' = {
  scope: resourceGroup
  name: 'windows-agent-deployment'
  params: {
    location: location
    environment: environment
    vmSize: vmSizes[environment].agent
    adminUsername: adminUsername
    adminPassword: adminPassword
    subnetId: network.outputs.agentsSubnetId
    calderaServerIp: calderaElkServer.outputs.privateIpAddress
    elkServerIp: calderaElkServer.outputs.privateIpAddress
    logAnalyticsWorkspaceId: logging.outputs.workspaceId
    enableAtomicRedTeam: enableAtomicRedTeam
    tags: union(commonTags, {
      role: 'red-team-agent'
      os: 'windows-server-2022'
      'attack-surface': 'execution-target'
    })
  }
}

// Linux Agent VM (Blue Team monitoring)
module linuxAgent 'modules/linux-agent.bicep' = {
  scope: resourceGroup
  name: 'linux-agent-deployment'
  params: {
    location: location
    environment: environment
    vmSize: vmSizes[environment].agent
    adminUsername: adminUsername
    adminPassword: adminPassword
    sshPublicKey: sshPublicKey
    subnetId: network.outputs.agentsSubnetId
    calderaServerIp: calderaElkServer.outputs.privateIpAddress
    logAnalyticsWorkspaceId: logging.outputs.workspaceId
    tags: union(commonTags, {
      role: 'blue-team-agent'
      os: 'ubuntu-22.04'
      'attack-surface': 'monitoring-target'
    })
  }
}

// ============================================================================
// OUTPUTS
// ============================================================================

output resourceGroupName string = resourceGroupName
output calderaElkServerUrl string = 'http://${calderaElkServer.outputs.publicIpAddress}:8888'
output calderaElkKibanaUrl string = 'http://${calderaElkServer.outputs.publicIpAddress}:5601'
output calderaElkServerIp string = calderaElkServer.outputs.publicIpAddress
output windowsAgentIp string = windowsAgent.outputs.publicIpAddress
output linuxAgentIp string = linuxAgent.outputs.publicIpAddress
output logAnalyticsWorkspaceId string = logging.outputs.workspaceId
output deploymentId string = deploymentId
output vnetId string = network.outputs.vnetId

output accessInstructions object = {
  caldera_elk: {
    caldera_url: 'http://${calderaElkServer.outputs.publicIpAddress}:8888'
    kibana_url: 'http://${calderaElkServer.outputs.publicIpAddress}:5601'
    default_creds: 'red:admin / blue:admin'
    ssh: 'ssh ${adminUsername}@${calderaElkServer.outputs.publicIpAddress}'
  }
  agents: {
    windows: {
      rdp: 'mstsc /v:${windowsAgent.outputs.publicIpAddress}'
      ip: windowsAgent.outputs.publicIpAddress
    }
    linux: {
      ssh: 'ssh ${adminUsername}@${linuxAgent.outputs.publicIpAddress}'
      ip: linuxAgent.outputs.publicIpAddress
    }
  }
}
