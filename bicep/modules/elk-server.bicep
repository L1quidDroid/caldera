// ============================================================================
// ELK Stack Server Module
// ============================================================================
// Elasticsearch + Kibana + Logstash for threat hunting
// Based on successful ELK 8.19.9 deployment
// ============================================================================

param location string
param environment string
param vmSize string
param adminUsername string
@secure()
param adminPassword string
param sshPublicKey string
param subnetId string
param logAnalyticsWorkspaceId string
param tags object

var vmName = 'vm-elk-${environment}'
var nicName = 'nic-${vmName}'
var pipName = 'pip-${vmName}'

resource pip 'Microsoft.Network/publicIPAddresses@2023-05-01' = {
  name: pipName
  location: location
  tags: tags
  sku: { name: 'Standard' }
  properties: {
    publicIPAllocationMethod: 'Static'
    dnsSettings: { domainNameLabel: '${vmName}-${uniqueString(resourceGroup().id)}' }
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
      linuxConfiguration: {
        disablePasswordAuthentication: false
        ssh: {
          publicKeys: empty(sshPublicKey) ? [] : [{
            path: '/home/${adminUsername}/.ssh/authorized_keys'
            keyData: sshPublicKey
          }]
        }
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
        name: '${vmName}-osdisk'
        createOption: 'FromImage'
        managedDisk: { storageAccountType: 'Premium_LRS' }
        diskSizeGB: 256
      }
    }
    networkProfile: {
      networkInterfaces: [{ id: nic.id }]
    }
    diagnosticsProfile: { bootDiagnostics: { enabled: true } }
  }
}

resource vmExtension 'Microsoft.Compute/virtualMachines/extensions@2023-07-01' = {
  parent: vm
  name: 'elk-setup'
  location: location
  properties: {
    publisher: 'Microsoft.Azure.Extensions'
    type: 'CustomScript'
    typeHandlerVersion: '2.1'
    autoUpgradeMinorVersion: true
    settings: {
      commandToExecute: 'bash -c "$(cat <<\'SETUP_SCRIPT\'\n#!/bin/bash\nset -euo pipefail\n\nLOG_FILE=/var/log/elk-setup.log\nexec 1> >(tee -a \"$LOG_FILE\")\nexec 2>&1\n\necho \"[$(date)] Starting ELK Stack setup...\"\n\nexport DEBIAN_FRONTEND=noninteractive\napt-get update -qq\napt-get install -y apt-transport-https ca-certificates curl gnupg -qq\n\necho \"[$(date)] Adding Elastic repository...\"\ncurl -fsSL https://artifacts.elastic.co/GPG-KEY-elasticsearch | \\\n  gpg --dearmor -o /usr/share/keyrings/elastic.gpg\n\necho \"deb [signed-by=/usr/share/keyrings/elastic.gpg] https://artifacts.elastic.co/packages/8.x/apt stable main\" | \\\n  tee /etc/apt/sources.list.d/elastic-8.x.list > /dev/null\n\necho \"[$(date)] Installing ELK Stack 8.x...\"\napt-get update -qq\nDEBIAN_FRONTEND=noninteractive apt-get install -y elasticsearch kibana logstash -qq\n\necho \"[$(date)] Configuring Elasticsearch...\"\ncat >> /etc/elasticsearch/elasticsearch.yml << EOF\nnetwork.host: 0.0.0.0\ndiscovery.type: single-node\nxpack.security.enabled: false\nEOF\n\necho \"[$(date)] Configuring Kibana...\"\ncat >> /etc/kibana/kibana.yml << EOF\nserver.host: \"0.0.0.0\"\nelasticsearch.hosts: [\"http://localhost:9200\"]\nEOF\n\necho \"[$(date)] Configuring Logstash...\"\ncat > /etc/logstash/conf.d/caldera.conf << EOF\ninput {\n  beats { port => 5044 }\n}\nfilter {\n  if [fields][source] == \"caldera\" {\n    grok {\n      match => { \"message\" => \"%{TIMESTAMP_ISO8601:timestamp} %{LOGLEVEL:level} %{GREEDYDATA:message}\" }\n    }\n    if [message] =~ /T[0-9]{4}/ {\n      grok {\n        match => { \"message\" => \"(?<mitre_technique>T[0-9]{4}(\\\\.[0-9]{3})?)\" }\n      }\n    }\n  }\n}\noutput {\n  elasticsearch {\n    hosts => [\"localhost:9200\"]\n    index => \"caldera-%{+YYYY.MM.dd}\"\n  }\n}\nEOF\n\necho \"[$(date)] Starting ELK services...\"\nsystemctl enable elasticsearch kibana logstash\nsystemctl start elasticsearch\n\nfor i in {1..30}; do\n  if curl -s http://localhost:9200 >/dev/null 2>&1; then\n    echo \"[$(date)] Elasticsearch is up\"\n    break\n  fi\n  sleep 2\ndone\n\nsystemctl start kibana\nsystemctl start logstash\nsleep 30\n\nELK_HEALTH=$(curl -s http://localhost:9200/_cluster/health | grep -o \'\"status\":\"[^\"]*\"\' | cut -d: -f2 | tr -d \'\"\')\nif [ \"$ELK_HEALTH\" = \"green\" ] || [ \"$ELK_HEALTH\" = \"yellow\" ]; then\n  echo \"[$(date)] ✅ ELK Stack healthy (status: $ELK_HEALTH)\"\nelse\n  echo \"[$(date)] ❌ ELK Stack unhealthy\"\n  exit 1\nfi\n\necho \"[$(date)] ELK Stack deployment completed\"\nSETUP_SCRIPT\n)"'
    }
  }
}

output vmId string = vm.id
output vmName string = vm.name
output publicIpAddress string = pip.properties.ipAddress
output privateIpAddress string = nic.properties.ipConfigurations[0].properties.privateIPAddress
output fqdn string = pip.properties.dnsSettings.fqdn
output vmName string = vm.name
output publicIpAddress string = pip.properties.ipAddress
output privateIpAddress string = nic.properties.ipConfigurations[0].properties.privateIPAddress
output fqdn string = pip.properties.dnsSettings.fqdn
