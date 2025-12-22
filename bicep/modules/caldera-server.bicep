// ============================================================================
// CALDERA Server Module
// ============================================================================
// Based on successful deployment at 4.196.116.97
// FIXES: Password auth enabled, Magma build in extension, systemd service
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

var vmName = 'vm-caldera-${environment}'
var nicName = 'nic-${vmName}'
var pipName = 'pip-${vmName}'
var osDiskName = '${vmName}-osdisk'

// Public IP
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

// Network Interface
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

// Virtual Machine
resource vm 'Microsoft.Compute/virtualMachines@2023-07-01' = {
  name: vmName
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    hardwareProfile: {
      vmSize: vmSize
    }
    osProfile: {
      computerName: vmName
      adminUsername: adminUsername
      adminPassword: adminPassword
      linuxConfiguration: {
        disablePasswordAuthentication: false // CRITICAL: Enable for Azure run-command
        ssh: {
          publicKeys: empty(sshPublicKey) ? [] : [
            {
              path: '/home/${adminUsername}/.ssh/authorized_keys'
              keyData: sshPublicKey
            }
          ]
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
        name: osDiskName
        createOption: 'FromImage'
        managedDisk: {
          storageAccountType: 'Premium_LRS'
        }
        diskSizeGB: 128
      }
    }
    networkProfile: {
      networkInterfaces: [
        {
          id: nic.id
        }
      ]
    }
    diagnosticsProfile: {
      bootDiagnostics: {
        enabled: true
      }
    }
  }
}

// Custom Script Extension - CALDERA Setup
resource vmExtension 'Microsoft.Compute/virtualMachines/extensions@2023-07-01' = {
  parent: vm
  name: 'caldera-setup'
  location: location
  properties: {
    publisher: 'Microsoft.Azure.Extensions'
    type: 'CustomScript'
    typeHandlerVersion: '2.1'
    autoUpgradeMinorVersion: true
    settings: {
      commandToExecute: 'bash -c "$(cat <<\'SETUP_SCRIPT\'\n#!/bin/bash\nset -euo pipefail\n\n# Setup logging\nLOG_FILE=/var/log/caldera-setup.log\nexec 1> >(tee -a \"$LOG_FILE\")\nexec 2>&1\n\necho \"[$(date)] Starting CALDERA setup...\"\n\n# Install dependencies\nexport DEBIAN_FRONTEND=noninteractive\napt-get update -qq\napt-get install -y python3-venv python3-pip python3-dev build-essential git curl -qq\n\n# Install Node.js 20.x (for Magma build)\necho \"[$(date)] Installing Node.js 20.x...\"\ncurl -fsSL https://deb.nodesource.com/setup_20.x | bash -\napt-get install -y nodejs -qq\nnode --version\nnpm --version\n\n# Clone CALDERA\necho \"[$(date)] Cloning CALDERA repository...\"\ncd /home/${adminUsername}\nif [ ! -d \"caldera\" ]; then\n  git clone https://github.com/mitre/caldera.git --recursive --branch master\nfi\ncd caldera\n\n# Create virtual environment\necho \"[$(date)] Creating Python virtual environment...\"\npython3 -m venv caldera_venv\nsource caldera_venv/bin/activate\npip install --upgrade pip setuptools wheel --quiet\necho \"[$(date)] Installing Python requirements...\"\npip install -r requirements.txt --quiet\ndeactivate\n\n# Build Magma frontend (CRITICAL - prevents FileNotFoundError)\necho \"[$(date)] Building Magma frontend...\"\ncd plugins/magma\nnpm install --quiet\ntimeout 300 npm run build || { echo \"Magma build failed\"; exit 1; }\nif [ -d \"dist\" ]; then\n  echo \"[$(date)] Magma dist/ created successfully ($(du -sh dist | cut -f1))\"\nelse\n  echo \"ERROR: Magma dist/ not found after build\"\n  exit 1\nfi\n\n# Configure CALDERA\necho \"[$(date)] Configuring CALDERA...\"\ncd /home/${adminUsername}/caldera\ncat > conf/local.yml << \"EOF\"\nhost: 0.0.0.0\nplugins:\n  - access\n  - atomic\n  - compass\n  - fieldmanual\n  - gameboard\n  - magma\n  - manx\n  - response\n  - sandcat\n  - stockpile\n  - training\nusers:\n  red:\n    red: admin\n  blue:\n    blue: admin\nEOF\n\n# Create systemd service\necho \"[$(date)] Creating systemd service...\"\ncat > /etc/systemd/system/caldera.service << EOF\n[Unit]\nDescription=CALDERA Adversary Emulation Platform\nAfter=network.target\nWants=network-online.target\n\n[Service]\nType=simple\nUser=${adminUsername}\nWorkingDirectory=/home/${adminUsername}/caldera\nExecStart=/home/${adminUsername}/caldera/caldera_venv/bin/python /home/${adminUsername}/caldera/server.py --insecure\nRestart=always\nRestartSec=10\nStandardOutput=journal\nStandardError=journal\n\n[Install]\nWantedBy=multi-user.target\nEOF\n\n# Set permissions\nchown -R ${adminUsername}:${adminUsername} /home/${adminUsername}/caldera\n\n# Enable and start service\necho \"[$(date)] Starting CALDERA service...\"\nsystemctl daemon-reload\nsystemctl enable caldera\nsystemctl start caldera\n\n# Wait for startup\nsleep 20\n\n# Verify health\nif curl -sf http://localhost:8888 > /dev/null; then\n  echo \"[$(date)] ✅ CALDERA setup complete - service healthy\"\n  systemctl status caldera --no-pager\nelse\n  echo \"[$(date)] ❌ CALDERA setup failed - service not responding\"\n  systemctl status caldera --no-pager\n  journalctl -u caldera -n 50 --no-pager\n  exit 1\nfi\n\necho \"[$(date)] CALDERA deployment completed successfully\"\nSETUP_SCRIPT\n)"'
    }
  }
}

// Azure Monitor Agent Extension
resource amaExtension 'Microsoft.Compute/virtualMachines/extensions@2023-07-01' = {
  parent: vm
  name: 'AzureMonitorLinuxAgent'
  location: location
  properties: {
    publisher: 'Microsoft.Azure.Monitor'
    type: 'AzureMonitorLinuxAgent'
    typeHandlerVersion: '1.25'
    autoUpgradeMinorVersion: true
    settings: {
      workspaceId: reference(logAnalyticsWorkspaceId, '2022-10-01').customerId
    }
    protectedSettings: {
      workspaceKey: listKeys(logAnalyticsWorkspaceId, '2022-10-01').primarySharedKey
    }
  }
  dependsOn: [
    vmExtension
  ]
}

output vmId string = vm.id
output vmName string = vm.name
output publicIpAddress string = pip.properties.ipAddress
output privateIpAddress string = nic.properties.ipConfigurations[0].properties.privateIPAddress
output fqdn string = pip.properties.dnsSettings.fqdn
output systemAssignedIdentity string = vm.identity.principalId
