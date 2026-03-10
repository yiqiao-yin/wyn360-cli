#!/usr/bin/env bash
#
# Deploy WYN360 Web Terminal to Azure
#
# Prerequisites:
#   - Azure CLI installed and logged in (az login)
#   - Docker installed
#
# Usage:
#   bash deploy-azure.sh
#
set -euo pipefail

# ── Configuration ──────────────────────────────────────────────
PREFIX="wyn360terminal"
LOCATION="westus2"

RESOURCE_GROUP="${PREFIX}-rg"
ACR_NAME="${PREFIX}acr"
APP_PLAN="${PREFIX}-plan"
WEB_APP="${PREFIX}-app"
IMAGE_NAME="wyn360-web"
IMAGE_TAG="latest"

# ── Validate prerequisites ─────────────────────────────────────
if ! command -v az &>/dev/null; then
  echo "ERROR: Azure CLI (az) not found."
  exit 1
fi

if ! az account show &>/dev/null 2>&1; then
  echo "ERROR: Not logged in. Run 'az login' first."
  exit 1
fi

if ! command -v docker &>/dev/null; then
  echo "ERROR: Docker not found."
  exit 1
fi

echo "============================================"
echo "  WYN360 Web Terminal - Azure Deployment"
echo "============================================"
echo ""
echo "  Resources to create (all prefixed '${PREFIX}'):"
echo "    Resource Group:  $RESOURCE_GROUP"
echo "    Container Reg:   $ACR_NAME"
echo "    App Plan (B1):   $APP_PLAN"
echo "    Web App:         $WEB_APP"
echo "    Location:        $LOCATION"
echo ""
echo "  URL: https://${WEB_APP}.azurewebsites.net"
echo ""
echo "  No API secrets are stored in Azure."
echo "  Users enter their own keys in the terminal."
echo ""

# ── Step 1: Resource Group ─────────────────────────────────────
echo "[1/6] Creating resource group: $RESOURCE_GROUP"
az group create \
  --name "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --output none

# ── Step 2: Container Registry ─────────────────────────────────
echo "[2/6] Creating container registry: $ACR_NAME"
az acr create \
  --resource-group "$RESOURCE_GROUP" \
  --name "$ACR_NAME" \
  --sku Basic \
  --admin-enabled true \
  --output none

ACR_SERVER="${ACR_NAME}.azurecr.io"

# ── Step 3: Build and push Docker image ────────────────────────
echo "[3/6] Building and pushing Docker image"
FULL_IMAGE="${ACR_SERVER}/${IMAGE_NAME}:${IMAGE_TAG}"

az acr login --name "$ACR_NAME"
docker build -f Dockerfile.web -t "$FULL_IMAGE" .
docker push "$FULL_IMAGE"

# ── Step 4: App Service Plan ───────────────────────────────────
echo "[4/6] Creating App Service Plan: $APP_PLAN (B1)"
az appservice plan create \
  --resource-group "$RESOURCE_GROUP" \
  --name "$APP_PLAN" \
  --is-linux \
  --sku B1 \
  --location "$LOCATION" \
  --output none

# ── Step 5: Web App ───────────────────────────────────────────
echo "[5/6] Creating Web App: $WEB_APP"
az webapp create \
  --resource-group "$RESOURCE_GROUP" \
  --plan "$APP_PLAN" \
  --name "$WEB_APP" \
  --deployment-container-image-name "$FULL_IMAGE" \
  --output none

# ── Step 6: Configure ─────────────────────────────────────────
echo "[6/6] Configuring Web App"

# Enable WebSockets (required for ttyd terminal)
az webapp config set \
  --resource-group "$RESOURCE_GROUP" \
  --name "$WEB_APP" \
  --web-sockets-enabled true \
  --output none

# Set the container port
az webapp config appsettings set \
  --resource-group "$RESOURCE_GROUP" \
  --name "$WEB_APP" \
  --settings WEBSITES_PORT=8360 \
  --output none

# Enable container logging
az webapp log config \
  --resource-group "$RESOURCE_GROUP" \
  --name "$WEB_APP" \
  --docker-container-logging filesystem \
  --output none

echo ""
echo "============================================"
echo "  Deployment complete!"
echo "============================================"
echo ""
echo "  URL: https://${WEB_APP}.azurewebsites.net"
echo ""
echo "  First startup takes 2-3 minutes while the"
echo "  container image is pulled from ACR."
echo ""
echo "  View logs:"
echo "    az webapp log tail -g $RESOURCE_GROUP -n $WEB_APP"
echo ""
echo "  Redeploy after changes:"
echo "    docker build -f Dockerfile.web -t $FULL_IMAGE ."
echo "    docker push $FULL_IMAGE"
echo "    az webapp restart -g $RESOURCE_GROUP -n $WEB_APP"
echo ""
echo "  Tear down:"
echo "    az group delete --name $RESOURCE_GROUP --yes --no-wait"
echo ""
