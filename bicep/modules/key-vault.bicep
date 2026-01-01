// ============================================================================
// Azure Key Vault Module for Caldera Secrets Management
// ============================================================================
// Creates a Key Vault for storing sensitive deployment secrets.
// Use this module to avoid hardcoding credentials in parameter files.
//
// Usage in main.bicep:
//   module keyVault 'modules/key-vault.bicep' = {
//     name: 'keyVaultDeployment'
//     params: {
//       location: location
//       keyVaultName: 'kv-caldera-${environment}'
//       adminObjectId: adminObjectId
//     }
//   }
//
// Then reference secrets:
//   adminPassword: keyVault.outputs.adminPasswordReference
// ============================================================================

@description('Azure region for Key Vault deployment')
param location string = resourceGroup().location

@description('Name of the Key Vault')
@minLength(3)
@maxLength(24)
param keyVaultName string

@description('Object ID of the admin user/service principal for Key Vault access')
param adminObjectId string

@description('Enable soft delete for Key Vault')
param enableSoftDelete bool = true

@description('Soft delete retention period in days')
@minValue(7)
@maxValue(90)
param softDeleteRetentionInDays int = 90

@description('Enable purge protection')
param enablePurgeProtection bool = true

@description('Environment tag')
@allowed(['dev', 'stage', 'prod-lab'])
param environment string = 'dev'

@description('Tags to apply to resources')
param tags object = {}

// Combine default and custom tags
var defaultTags = {
  project: 'caldera'
  environment: environment
  managedBy: 'bicep'
}
var allTags = union(defaultTags, tags)

// ============================================================================
// Key Vault Resource
// ============================================================================
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyVaultName
  location: location
  tags: allTags
  properties: {
    tenantId: subscription().tenantId
    sku: {
      family: 'A'
      name: 'standard'
    }
    enableSoftDelete: enableSoftDelete
    softDeleteRetentionInDays: softDeleteRetentionInDays
    enablePurgeProtection: enablePurgeProtection
    enableRbacAuthorization: true
    enabledForDeployment: true
    enabledForTemplateDeployment: true
    enabledForDiskEncryption: false
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      defaultAction: 'Allow'
      bypass: 'AzureServices'
    }
  }
}

// ============================================================================
// Role Assignment for Admin Access
// ============================================================================
// Key Vault Secrets Officer role
var secretsOfficerRoleId = 'b86a8fe4-44ce-4948-aee5-eccb2c155cd7'

resource adminRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, adminObjectId, secretsOfficerRoleId)
  scope: keyVault
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', secretsOfficerRoleId)
    principalId: adminObjectId
    principalType: 'User'
  }
}

// ============================================================================
// Default Secrets (placeholders - set actual values post-deployment)
// ============================================================================

// Admin Password for VMs
resource adminPasswordSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'adminPassword'
  properties: {
    value: 'PLACEHOLDER-CHANGE-ME-${uniqueString(resourceGroup().id)}'
    contentType: 'text/plain'
    attributes: {
      enabled: true
    }
  }
}

// Caldera API Key (Red Team)
resource calderaApiKeyRedSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'calderaApiKeyRed'
  properties: {
    value: uniqueString(resourceGroup().id, 'red', utcNow())
    contentType: 'text/plain'
    attributes: {
      enabled: true
    }
  }
}

// Caldera API Key (Blue Team)
resource calderaApiKeyBlueSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'calderaApiKeyBlue'
  properties: {
    value: uniqueString(resourceGroup().id, 'blue', utcNow())
    contentType: 'text/plain'
    attributes: {
      enabled: true
    }
  }
}

// Caldera Encryption Key
resource calderaEncryptionKeySecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'calderaEncryptionKey'
  properties: {
    value: uniqueString(resourceGroup().id, 'encryption', utcNow())
    contentType: 'text/plain'
    attributes: {
      enabled: true
    }
  }
}

// Elastic API Key (optional)
resource elasticApiKeySecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'elasticApiKey'
  properties: {
    value: ''
    contentType: 'text/plain'
    attributes: {
      enabled: true
    }
  }
}

// ============================================================================
// Outputs
// ============================================================================

@description('Key Vault resource ID')
output keyVaultId string = keyVault.id

@description('Key Vault name')
output keyVaultName string = keyVault.name

@description('Key Vault URI')
output keyVaultUri string = keyVault.properties.vaultUri

@description('Reference for adminPassword secret (use in other modules)')
output adminPasswordReference object = {
  keyVault: {
    id: keyVault.id
  }
  secretName: 'adminPassword'
}

@description('Reference for Caldera API Key Red')
output calderaApiKeyRedReference object = {
  keyVault: {
    id: keyVault.id
  }
  secretName: 'calderaApiKeyRed'
}

@description('Reference for Caldera API Key Blue')
output calderaApiKeyBlueReference object = {
  keyVault: {
    id: keyVault.id
  }
  secretName: 'calderaApiKeyBlue'
}

@description('Reference for Caldera Encryption Key')
output calderaEncryptionKeyReference object = {
  keyVault: {
    id: keyVault.id
  }
  secretName: 'calderaEncryptionKey'
}
