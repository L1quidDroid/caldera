#!/bin/bash
# Simple Azure CALDERA Deployment
# Creates infrastructure and outputs deployment scripts

set -euo pipefail

# Generate unique identifiers
TIMESTAMP=$(date +%Y%m%d-%H%M)
RG_NAME="rg-caldera-demo-${TIMESTAMP}"
LOCATION="australiaeast"
ADMIN_USER="tonyto"
ADMIN_PASS="P@ssw0rd123!"

echo "🚀 Deploying CALDERA to Azure"
echo "Resource Group: $RG_NAME"
echo "Location: $LOCATION"

# Create resource group
echo "Creating resource group..."
az group create --name "$RG_NAME" --location "$LOCATION" --output none

# Create virtual network
echo "Creating virtual network..."
az network vnet create \
    --resource-group "$RG_NAME" \
    --name vnet-purple-demo \
    --address-prefix 10.0.0.0/16 \
    --subnet-name subnet-demo \
    --subnet-prefix 10.0.1.0/24 \
    --output none

# Create Network Security Group
echo "Creating network security group..."
az network nsg create \
    --resource-group "$RG_NAME" \
    --name nsg-purple-demo \
    --output none

# Add NSG rules
echo "Adding firewall rules..."
az network nsg rule create --resource-group "$RG_NAME" --nsg-name nsg-purple-demo \
    --name AllowSSH --priority 100 --destination-port-ranges 22 --protocol Tcp --output none

az network nsg rule create --resource-group "$RG_NAME" --nsg-name nsg-purple-demo \
    --name AllowRDP --priority 110 --destination-port-ranges 3389 --protocol Tcp --output none

az network nsg rule create --resource-group "$RG_NAME" --nsg-name nsg-purple-demo \
    --name AllowCALDERA --priority 120 --destination-port-ranges 8888 --protocol Tcp --output none

az network nsg rule create --resource-group "$RG_NAME" --nsg-name nsg-purple-demo \
    --name AllowKibana --priority 130 --destination-port-ranges 5601 --protocol Tcp --output none

az network nsg rule create --resource-group "$RG_NAME" --nsg-name nsg-purple-demo \
    --name AllowElasticsearch --priority 140 --destination-port-ranges 9200 --protocol Tcp --output none

az network nsg rule create --resource-group "$RG_NAME" --nsg-name nsg-purple-demo \
    --name AllowAgentC2 --priority 150 --destination-port-ranges 7010-7012 --protocol Tcp --output none

# Create CALDERA+ELK Server VM
echo "Creating CALDERA+ELK server VM..."
az vm create \
    --resource-group "$RG_NAME" \
    --name caldera-elk-server \
    --image Ubuntu2204 \
    --size Standard_B2s \
    --admin-username "$ADMIN_USER" \
    --admin-password "$ADMIN_PASS" \
    --vnet-name vnet-purple-demo \
    --subnet subnet-demo \
    --nsg nsg-purple-demo \
    --public-ip-address-allocation static \
    --output none

# Get server public IP
SERVER_IP=$(az vm show -d --resource-group "$RG_NAME" --name caldera-elk-server \
    --query publicIps -o tsv)

echo ""
echo "✅ Infrastructure deployed successfully!"
echo ""
echo "CALDERA+ELK Server: $SERVER_IP"
echo "Username: $ADMIN_USER"
echo "Password: $ADMIN_PASS"
echo ""
echo "Next steps:"
echo "1. Upload setup script: scp caldera_server_setup_v2.sh ${ADMIN_USER}@${SERVER_IP}:~/"
echo "2. Upload Magma dist: scp /tmp/magma-dist.tar.gz ${ADMIN_USER}@${SERVER_IP}:~/"
echo "3. Run setup: ssh ${ADMIN_USER}@${SERVER_IP} 'bash caldera_server_setup_v2.sh'"
echo ""
echo "Resource Group: $RG_NAME"
echo "To cleanup: az group delete --name $RG_NAME --yes --no-wait"
