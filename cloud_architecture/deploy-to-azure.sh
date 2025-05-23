#!/bin/bash
# Deployment script for Crypto Trading Platform on Azure

# Configuration
RESOURCE_GROUP="crypto-trading-rg"
LOCATION="eastus"
CLUSTER_NAME="crypto-trading-aks"
NODE_COUNT=3
NODE_VM_SIZE="Standard_D2s_v3"
ACR_NAME="cryptotradingregistry"
COSMOS_DB_ACCOUNT="crypto-trading-db"
COSMOS_DB_NAME="trading"
KEYVAULT_NAME="crypto-trading-vault"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting deployment of Crypto Trading Platform to Azure...${NC}"

# Login to Azure
echo -e "${YELLOW}Logging in to Azure...${NC}"
az login

# Create Resource Group
echo -e "${YELLOW}Creating Resource Group $RESOURCE_GROUP in $LOCATION...${NC}"
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create Azure Container Registry (ACR)
echo -e "${YELLOW}Creating Azure Container Registry $ACR_NAME...${NC}"
az acr create --resource-group $RESOURCE_GROUP --name $ACR_NAME --sku Standard --admin-enabled true

# Get ACR credentials
ACR_USERNAME=$(az acr credential show --name $ACR_NAME --query "username" -o tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query "passwords[0].value" -o tsv)

echo -e "${GREEN}ACR $ACR_NAME created successfully.${NC}"

# Create AKS cluster
echo -e "${YELLOW}Creating AKS cluster $CLUSTER_NAME...${NC}"
az aks create \
    --resource-group $RESOURCE_GROUP \
    --name $CLUSTER_NAME \
    --node-count $NODE_COUNT \
    --node-vm-size $NODE_VM_SIZE \
    --enable-addons monitoring \
    --attach-acr $ACR_NAME \
    --generate-ssh-keys

echo -e "${GREEN}AKS cluster $CLUSTER_NAME created successfully.${NC}"

# Create Cosmos DB account with SQL API
echo -e "${YELLOW}Creating Cosmos DB account $COSMOS_DB_ACCOUNT...${NC}"
az cosmosdb create \
    --name $COSMOS_DB_ACCOUNT \
    --resource-group $RESOURCE_GROUP \
    --kind GlobalDocumentDB \
    --default-consistency-level Session

# Create Cosmos DB SQL database
echo -e "${YELLOW}Creating Cosmos DB database $COSMOS_DB_NAME...${NC}"
az cosmosdb sql database create \
    --account-name $COSMOS_DB_ACCOUNT \
    --resource-group $RESOURCE_GROUP \
    --name $COSMOS_DB_NAME

echo -e "${GREEN}Cosmos DB account and database created successfully.${NC}"

# Create containers for different data collections
echo -e "${YELLOW}Creating Cosmos DB containers for users, strategies, and trading data...${NC}"
COLLECTIONS=("users" "strategies" "trades" "orders" "balances" "commissions")

for COLL in "${COLLECTIONS[@]}"
do
    az cosmosdb sql container create \
        --account-name $COSMOS_DB_ACCOUNT \
        --database-name $COSMOS_DB_NAME \
        --name $COLL \
        --partition-key-path "/id" \
        --resource-group $RESOURCE_GROUP
done

echo -e "${GREEN}Cosmos DB containers created successfully.${NC}"

# Create Key Vault
echo -e "${YELLOW}Creating Key Vault $KEYVAULT_NAME...${NC}"
az keyvault create \
    --name $KEYVAULT_NAME \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION \
    --enabled-for-template-deployment true

# Get connection string for Cosmos DB
COSMOS_CONNECTION_STRING=$(az cosmosdb keys list --name $COSMOS_DB_ACCOUNT --resource-group $RESOURCE_GROUP --type connection-strings --query "connectionStrings[0].connectionString" -o tsv)

# Store secrets in Key Vault
echo -e "${YELLOW}Storing secrets in Key Vault...${NC}"
az keyvault secret set --vault-name $KEYVAULT_NAME --name "database-url" --value "$COSMOS_CONNECTION_STRING"
az keyvault secret set --vault-name $KEYVAULT_NAME --name "jwt-secret" --value "$(openssl rand -base64 32)"

echo -e "${GREEN}Key Vault configured with secrets.${NC}"

# Get credentials for kubectl
echo -e "${YELLOW}Getting AKS credentials for kubectl...${NC}"
az aks get-credentials --resource-group $RESOURCE_GROUP --name $CLUSTER_NAME

# Create Kubernetes secrets for application
echo -e "${YELLOW}Creating Kubernetes secrets...${NC}"
kubectl create secret generic crypto-trading-secrets \
    --from-literal=database-url="$COSMOS_CONNECTION_STRING" \
    --from-literal=jwt-secret="$(az keyvault secret show --vault-name $KEYVAULT_NAME --name jwt-secret --query value -o tsv)"

echo -e "${GREEN}Kubernetes secrets created.${NC}"

# Replace ACR_NAME placeholder in kubernetes-deployment.yaml
sed -i "s/\${ACR_NAME}/$ACR_NAME/g" kubernetes-deployment.yaml

# Build and push Docker images to ACR
echo -e "${YELLOW}Building and pushing Docker images to ACR...${NC}"
# Build API image
docker build -t $ACR_NAME.azurecr.io/crypto-trading-api:latest ./backend
docker login $ACR_NAME.azurecr.io -u $ACR_USERNAME -p $ACR_PASSWORD
docker push $ACR_NAME.azurecr.io/crypto-trading-api:latest

# Build Web App image
docker build -t $ACR_NAME.azurecr.io/crypto-trading-webapp:latest ./web_dashboard
docker push $ACR_NAME.azurecr.io/crypto-trading-webapp:latest

# Build Agentic AI image
docker build -t $ACR_NAME.azurecr.io/crypto-trading-agentic-ai:latest ./agentic_ai
docker push $ACR_NAME.azurecr.io/crypto-trading-agentic-ai:latest

echo -e "${GREEN}Docker images built and pushed to ACR.${NC}"

# Deploy to AKS
echo -e "${YELLOW}Deploying application to AKS...${NC}"
kubectl apply -f kubernetes-deployment.yaml

echo -e "${GREEN}Deployment completed successfully.${NC}"
echo -e "${YELLOW}Checking deployment status...${NC}"

sleep 30
kubectl get pods
kubectl get services
kubectl get ingress

echo -e "${YELLOW}Application endpoints:${NC}"
echo -e "API: https://api.cryptotrading-platform.com"
echo -e "Web App: https://app.cryptotrading-platform.com"
echo -e "AI Service: https://ai.cryptotrading-platform.com"

echo -e "${GREEN}Crypto Trading Platform deployment complete!${NC}"
