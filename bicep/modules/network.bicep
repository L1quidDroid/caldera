// ============================================================================
// Network Module - Isolated VNet for Purple Team Lab
// ============================================================================
// Separate subnets for CALDERA, ELK, and agents with NSG rules
// Based on deployment learnings: proper C2 isolation, SSH access, port security
// ============================================================================

param location string
param environment string
param tags object
@description('CIDR allowed for management/UI access (SSH/RDP/HTTP/Kibana/Caldera)')
param managementCidr string = '0.0.0.0/0'

var vnetName = 'vnet-caldera-${environment}'
var calderaSubnetName = 'snet-caldera-server'
var elkSubnetName = 'snet-elk-stack'
var agentsSubnetName = 'snet-agents'

// Virtual Network
resource vnet 'Microsoft.Network/virtualNetworks@2023-05-01' = {
  name: vnetName
  location: location
  tags: tags
  properties: {
    addressSpace: {
      addressPrefixes: [
        '10.0.0.0/16'
      ]
    }
    subnets: [
      {
        name: calderaSubnetName
        properties: {
          addressPrefix: '10.0.1.0/24'
          networkSecurityGroup: {
            id: nsgCaldera.id
          }
          privateEndpointNetworkPolicies: 'Disabled'
        }
      }
      {
        name: elkSubnetName
        properties: {
          addressPrefix: '10.0.2.0/24'
          networkSecurityGroup: {
            id: nsgElk.id
          }
        }
      }
      {
        name: agentsSubnetName
        properties: {
          addressPrefix: '10.0.3.0/24'
          networkSecurityGroup: {
            id: nsgAgents.id
          }
        }
      }
    ]
  }
}

// NSG: CALDERA Server
resource nsgCaldera 'Microsoft.Network/networkSecurityGroups@2023-05-01' = {
  name: 'nsg-caldera-${environment}'
  location: location
  tags: tags
  properties: {
    securityRules: [
      {
        name: 'AllowSSH'
        properties: {
          priority: 100
          direction: 'Inbound'
          access: 'Allow'
          protocol: 'Tcp'
          sourcePortRange: '*'
          destinationPortRange: '22'
          sourceAddressPrefix: managementCidr
          destinationAddressPrefix: '*'
          description: 'Allow SSH for management'
        }
      }
      {
        name: 'AllowCALDERA'
        properties: {
          priority: 110
          direction: 'Inbound'
          access: 'Allow'
          protocol: 'Tcp'
          sourcePortRange: '*'
          destinationPortRange: '8888'
          sourceAddressPrefix: managementCidr
          destinationAddressPrefix: '*'
          description: 'Allow CALDERA web UI'
        }
      }
      {
        name: 'AllowAgentC2'
        properties: {
          priority: 120
          direction: 'Inbound'
          access: 'Allow'
          protocol: 'Tcp'
          sourcePortRange: '*'
          destinationPortRanges: [
            '7010'
            '7011'
            '7012'
          ]
          sourceAddressPrefix: '10.0.3.0/24'
          destinationAddressPrefix: '*'
          description: 'Allow agent C2 from agents subnet only'
        }
      }
      {
        name: 'AllowHTTP'
        properties: {
          priority: 130
          direction: 'Inbound'
          access: 'Allow'
          protocol: 'Tcp'
          sourcePortRange: '*'
          destinationPortRanges: [
            '80'
            '443'
            '8080'
          ]
          sourceAddressPrefix: managementCidr
          destinationAddressPrefix: '*'
          description: 'Allow HTTP/HTTPS'
        }
      }
    ]
  }
}

// NSG: ELK Stack
resource nsgElk 'Microsoft.Network/networkSecurityGroups@2023-05-01' = {
  name: 'nsg-elk-${environment}'
  location: location
  tags: tags
  properties: {
    securityRules: [
      {
        name: 'AllowSSH'
        properties: {
          priority: 100
          direction: 'Inbound'
          access: 'Allow'
          protocol: 'Tcp'
          sourcePortRange: '*'
          destinationPortRange: '22'
          sourceAddressPrefix: managementCidr
          destinationAddressPrefix: '*'
          description: 'Allow SSH for management'
        }
      }
      {
        name: 'AllowKibana'
        properties: {
          priority: 110
          direction: 'Inbound'
          access: 'Allow'
          protocol: 'Tcp'
          sourcePortRange: '*'
          destinationPortRange: '5601'
          sourceAddressPrefix: managementCidr
          destinationAddressPrefix: '*'
          description: 'Allow Kibana web UI'
        }
      }
      {
        name: 'AllowElasticsearch'
        properties: {
          priority: 120
          direction: 'Inbound'
          access: 'Allow'
          protocol: 'Tcp'
          sourcePortRange: '*'
          destinationPortRange: '9200'
          sourceAddressPrefix: '10.0.0.0/16'
          destinationAddressPrefix: '*'
          description: 'Allow Elasticsearch from VNet only'
        }
      }
      {
        name: 'AllowBeats'
        properties: {
          priority: 130
          direction: 'Inbound'
          access: 'Allow'
          protocol: 'Tcp'
          sourcePortRange: '*'
          destinationPortRange: '5044'
          sourceAddressPrefix: '10.0.0.0/16'
          destinationAddressPrefix: '*'
          description: 'Allow Filebeat/Metricbeat from VNet'
        }
      }
    ]
  }
}

// NSG: Agent VMs
resource nsgAgents 'Microsoft.Network/networkSecurityGroups@2023-05-01' = {
  name: 'nsg-agents-${environment}'
  location: location
  tags: tags
  properties: {
    securityRules: [
      {
        name: 'AllowSSH'
        properties: {
          priority: 100
          direction: 'Inbound'
          access: 'Allow'
          protocol: 'Tcp'
          sourcePortRange: '*'
          destinationPortRange: '22'
          sourceAddressPrefix: managementCidr
          destinationAddressPrefix: '*'
          description: 'Allow SSH for Linux agents'
        }
      }
      {
        name: 'AllowRDP'
        properties: {
          priority: 110
          direction: 'Inbound'
          access: 'Allow'
          protocol: 'Tcp'
          sourcePortRange: '*'
          destinationPortRange: '3389'
          sourceAddressPrefix: managementCidr
          destinationAddressPrefix: '*'
          description: 'Allow RDP for Windows agents'
        }
      }
      {
        name: 'AllowCALDERAC2Outbound'
        properties: {
          priority: 100
          direction: 'Outbound'
          access: 'Allow'
          protocol: 'Tcp'
          sourcePortRange: '*'
          destinationPortRanges: [
            '7010'
            '7011'
            '7012'
            '8888'
          ]
          sourceAddressPrefix: '*'
          destinationAddressPrefix: '10.0.1.0/24'
          description: 'Allow C2 to CALDERA server'
        }
      }
      {
        name: 'AllowELKBeatsOutbound'
        properties: {
          priority: 110
          direction: 'Outbound'
          access: 'Allow'
          protocol: 'Tcp'
          sourcePortRange: '*'
          destinationPortRange: '5044'
          sourceAddressPrefix: '*'
          destinationAddressPrefix: '10.0.2.0/24'
          description: 'Allow log shipping to ELK'
        }
      }
    ]
  }
}

output vnetId string = vnet.id
output vnetName string = vnet.name
output calderaSubnetId string = vnet.properties.subnets[0].id
output elkSubnetId string = vnet.properties.subnets[1].id
output agentsSubnetId string = vnet.properties.subnets[2].id
output nsgCalderaId string = nsgCaldera.id
output nsgElkId string = nsgElk.id
output nsgAgentsId string = nsgAgents.id
