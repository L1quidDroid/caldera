// ============================================================================
// Log Analytics Workspace Module
// ============================================================================
// Central logging for audit, compliance, and threat hunting
// MITRE ATT&CK-aligned KQL queries for purple team operations
// ============================================================================

param location string
param environment string
param tags object

@description('Log retention in days')
param retentionDays int = 30

var workspaceName = 'law-caldera-${environment}-${uniqueString(resourceGroup().id)}'

resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: workspaceName
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: retentionDays
    features: {
      enableLogAccessUsingOnlyResourcePermissions: true
    }
    workspaceCapping: {
      dailyQuotaGb: environment == 'dev' ? 1 : (environment == 'stage' ? 5 : 10)
    }
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

// Saved queries for MITRE ATT&CK detection
resource savedQuery 'Microsoft.OperationalInsights/workspaces/savedSearches@2020-08-01' = {
  parent: logAnalyticsWorkspace
  name: 'MITREAttackDetections'
  properties: {
    category: 'Purple Team'
    displayName: 'MITRE ATT&CK Detections'
    query: '''
      union *
      | where TimeGenerated > ago(24h)
      | where Message contains "MITRE" or Message contains "ATT&CK" or Message contains "T1"
      | extend Technique = extract("(T[0-9]{4}(\\\\.[0-9]{3})?)", 1, Message)
      | where isnotempty(Technique)
      | summarize Count=count(), FirstSeen=min(TimeGenerated), LastSeen=max(TimeGenerated) by Technique, Computer, _ResourceId
      | order by Count desc
    '''
    version: 2
  }
}

resource savedQueryCalderaOperations 'Microsoft.OperationalInsights/workspaces/savedSearches@2020-08-01' = {
  parent: logAnalyticsWorkspace
  name: 'CalderaOperations'
  properties: {
    category: 'Purple Team'
    displayName: 'CALDERA Operations Activity'
    query: '''
      Syslog
      | where ProcessName contains "caldera" or ProcessName contains "python"
      | where SyslogMessage contains "operation" or SyslogMessage contains "agent"
      | extend OperationId = extract("operation[_-]id[=:]['\\\"]?([a-f0-9-]+)", 1, SyslogMessage)
      | extend AgentId = extract("agent[_-]id[=:]['\\\"]?([a-f0-9-]+)", 1, SyslogMessage)
      | project TimeGenerated, Computer, Facility, SeverityLevel, OperationId, AgentId, SyslogMessage
      | order by TimeGenerated desc
    '''
    version: 2
  }
}

// Alert rule for failed agent check-ins
resource alertRule 'Microsoft.Insights/scheduledQueryRules@2023-03-15-preview' = {
  name: 'caldera-agent-checkin-failure'
  location: location
  tags: tags
  properties: {
    displayName: 'CALDERA Agent Check-in Failure'
    description: 'Alert when agents fail to check in for 10 minutes'
    severity: 2
    enabled: true
    evaluationFrequency: 'PT5M'
    scopes: [
      logAnalyticsWorkspace.id
    ]
    targetResourceTypes: [
      'Microsoft.OperationalInsights/workspaces'
    ]
    windowSize: 'PT10M'
    criteria: {
      allOf: [
        {
          query: '''
            Heartbeat
            | where Computer contains "agent"
            | summarize LastHeartbeat=max(TimeGenerated) by Computer
            | where LastHeartbeat < ago(10m)
          '''
          timeAggregation: 'Count'
          operator: 'GreaterThan'
          threshold: 0
          failingPeriods: {
            numberOfEvaluationPeriods: 1
            minFailingPeriodsToAlert: 1
          }
        }
      ]
    }
    autoMitigate: false
  }
}

output workspaceId string = logAnalyticsWorkspace.id
output workspaceName string = logAnalyticsWorkspace.name
output customerId string = logAnalyticsWorkspace.properties.customerId
