// ============================================================================
// CALDERA Purple Team Lab - Main Bicep Template
// ============================================================================
// Production-ready adversary emulation platform with ELK Stack
// Region: Australia East (data sovereignty compliance)
// Last Updated: 2025-12-22
// ============================================================================

targetScope = 'resourceGroup'

@description('Environment name (dev, stage, prod-lab)')
@allowed([
  'dev'
  'stage'
  'prod-lab'
])
param environment string = 'dev'

@description('Azure region for deployment')
param location string = resourceGroup().location

@description('Unique deployment identifier (stable for student policy)')
param deploymentId string = 'caldera-dev'

@description('Owner tag for resource management')
param ownerTag string = 'tonyto'

@description('Cost center for billing allocation')
param costCenter string = 'cybersec-purple-team'

@description('MITRE ATT&CK tactic for this lab instance')
param attackTactic string = 'TA0001'

@description('Deploy agent VMs (Windows/Linux). Set false if hitting quota constraints.')
param deployAgents bool = true

@description('Storage type for OS disks. Use Standard_LRS for Free/Student accounts if Premium fails.')
@allowed(['Premium_LRS', 'Standard_LRS', 'StandardSSD_LRS'])
param osDiskType string = 'Premium_LRS'

@description('CIDR allowed to reach management and UI ports (SSH/RDP/HTTP/Kibana/Caldera). Override with your public IP CIDR for tighter access.')
param managementCidr string = '0.0.0.0/0'

@description('Admin username for all VMs')
@secure()
param adminUsername string

@description('Admin password for all VMs')
@secure()
param adminPassword string

@description('Base64-encoded content of the Caldera/ELK installation script')
@secure()
param calderaElkInstallScript string

@description('SSH public key for Linux VMs')
param sshPublicKey string

// ============================================================================
// VARIABLES
// ============================================================================

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
    calderaElk: 'Standard_D2s_v3' // available in japaneast; 2 vCPU fits student quota with agents off
    agent: 'Standard_B1s'
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
// MODULES
// ============================================================================

// Network Infrastructure
module network 'modules/network.bicep' = {
  name: 'network-deployment'
  params: {
    location: location
    environment: environment
    managementCidr: managementCidr
    tags: commonTags
  }
}

// Log Analytics Workspace
module logging 'modules/logging.bicep' = {
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
  name: 'caldera-elk-server-deployment'
  params: {
    location: location
    environment: environment
    vmSize: vmSizes[environment].calderaElk
    adminUsername: adminUsername
    adminPassword: adminPassword
    sshPublicKey: sshPublicKey
    subnetId: network.outputs.calderaSubnetId // Using caldera subnet
    installScript: calderaElkInstallScript
    logAnalyticsWorkspaceId: logging.outputs.workspaceId
    osDiskType: osDiskType
    tags: union(commonTags, {
      role: 'caldera-elk-server'
    })
  }
}

// Windows Agent VM (Red Team target)
module windowsAgentDeployment 'modules/windows-agent.bicep' = if (deployAgents) {
  name: 'windows-agent-deployment'
  params: {
    location: location
    environment: environment
    vmSize: vmSizes[environment].agent
    adminUsername: adminUsername
    adminPassword: adminPassword
    subnetId: network.outputs.agentsSubnetId
    logAnalyticsWorkspaceId: logging.outputs.workspaceId
    tags: union(commonTags, {
      role: 'red-team-agent'
      os: 'windows-server-2022'
      'attack-surface': 'execution-target'
    })
  }
}

// Linux Agent VM (Blue Team monitoring)
module linuxAgentDeployment 'modules/linux-agent.bicep' = if (deployAgents) {
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
    tags: union(commonTags, {
      role: 'blue-team-agent'
      os: 'ubuntu-22.04'
      'attack-surface': 'monitoring-target'
    })
  }
}

var windowsAgentOutputs = deployAgents ? windowsAgentDeployment.outputs : {
  publicIpAddress: ''
}
var linuxAgentOutputs = deployAgents ? linuxAgentDeployment.outputs : {
  publicIpAddress: ''
}
var windowsAgentIpValue = windowsAgentOutputs.publicIpAddress
var linuxAgentIpValue = linuxAgentOutputs.publicIpAddress

// ============================================================================
// OUTPUTS
// ============================================================================

output resourceGroupName string = resourceGroup().name
output calderaElkServerUrl string = 'http://${calderaElkServer.outputs.publicIpAddress}:8888'
output calderaElkKibanaUrl string = 'http://${calderaElkServer.outputs.publicIpAddress}:5601'
output calderaElkServerIp string = calderaElkServer.outputs.publicIpAddress
output windowsAgentIp string = windowsAgentIpValue
output linuxAgentIp string = linuxAgentIpValue
output logAnalyticsWorkspaceId string = logging.outputs.workspaceId
output deploymentId string = deploymentId
output vnetId string = network.outputs.vnetId

output accessInstructions object = {
  caldera_elk: {
    caldera_url: 'http://${calderaElkServer.outputs.publicIpAddress}:8888'
    kibana_url: 'http://${calderaElkServer.outputs.publicIpAddress}:5601'
    default_creds: 'red:admin / blue:admin'
    ssh_command: 'Use your provided admin username and the server IP.'
  }
  agents: {
    windows: {
      rdp_command: 'Use your provided admin username and the agent IP.'
      ip: windowsAgentIpValue
    }
    linux: {
      ssh_command: 'Use your provided admin username and the agent IP.'
      ip: linuxAgentIpValue
    }
  }
}
