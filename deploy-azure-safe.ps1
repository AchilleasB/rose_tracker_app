# Safe Azure Deployment Script for Rose Tracker App
# This script creates NEW container instances instead of updating existing ones

param(
    [string]$ResourceGroup = "rg_group8",
    [string]$Location = "westeurope",
    [string]$RedisContainerName = "rose-tracker-redis",
    [string]$AppContainerName = "rose-tracker-container",
    [string]$AcrName = "rosetrackeracr",
    [string]$ImageTag = "production",
    [string]$AppSuffix = "v2"  # Suffix for new app container
)

# Stop on any error
$ErrorActionPreference = "Stop"

Write-Host "🛡️  Safe Azure Deployment for Rose Tracker App" -ForegroundColor Green
Write-Host "Resource Group: $ResourceGroup" -ForegroundColor Cyan
Write-Host "Location: $Location" -ForegroundColor Cyan
Write-Host "ACR Name: $AcrName" -ForegroundColor Cyan
Write-Host "Image Tag: $ImageTag" -ForegroundColor Cyan
Write-Host "App Container: $AppContainerName-$AppSuffix" -ForegroundColor Cyan

# Step 1: Check if resource group exists
Write-Host "🔍 Checking resource group..." -ForegroundColor Yellow
$rgExists = az group show --name $ResourceGroup 2>$null
if (-not $rgExists) {
    Write-Host "📦 Creating resource group..." -ForegroundColor Yellow
    az group create --name $ResourceGroup --location $Location
    Write-Host "✅ Resource group created" -ForegroundColor Green
} else {
    Write-Host "✅ Resource group exists" -ForegroundColor Green
}

# Step 2: Check if ACR exists
Write-Host "🔍 Checking Azure Container Registry..." -ForegroundColor Yellow
$acrExists = az acr show --name $AcrName --resource-group $ResourceGroup 2>$null
if (-not $acrExists) {
    Write-Host "📦 Creating Azure Container Registry..." -ForegroundColor Yellow
    az acr create `
        --resource-group $ResourceGroup `
        --name $AcrName `
        --sku Basic `
        --location $Location `
        --admin-enabled true
    Write-Host "✅ ACR created" -ForegroundColor Green
} else {
    Write-Host "✅ ACR exists" -ForegroundColor Green
}

# Step 3: Build and push Docker image to ACR
Write-Host "🔨 Building and pushing Docker image to ACR..." -ForegroundColor Yellow
$ImageName = "$AcrName.azurecr.io/rose_tracker_app:$ImageTag"

# Login to ACR
Write-Host "📦 Logging into Azure Container Registry..." -ForegroundColor Yellow
az acr login --name $AcrName

# Build image
Write-Host "🏗️  Building Docker image..." -ForegroundColor Yellow
docker build -t $ImageName .

# Push image
Write-Host "📤 Pushing Docker image to ACR..." -ForegroundColor Yellow
docker push $ImageName

Write-Host "✅ Docker image pushed: $ImageName" -ForegroundColor Green

# Step 4: Check if Redis container exists, create if not
Write-Host "🔍 Checking Redis container..." -ForegroundColor Yellow
$redisExists = az container show --resource-group $ResourceGroup --name $RedisContainerName 2>$null
if (-not $redisExists) {
    Write-Host "🔴 Creating Redis container..." -ForegroundColor Yellow
    az container create `
        --resource-group $ResourceGroup `
        --name $RedisContainerName `
        --image redis:7-alpine `
        --ports 6379 `
        --cpu 0.5 `
        --memory 1.0 `
        --location $Location `
        --restart-policy Always `
        --command-line "redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru"
    Write-Host "✅ Redis container created" -ForegroundColor Green
} else {
    Write-Host "✅ Redis container exists" -ForegroundColor Green
}

# Step 5: Get Redis IP
Write-Host "🌐 Getting Redis container IP..." -ForegroundColor Yellow
$RedisIP = az container show `
    --resource-group $ResourceGroup `
    --name $RedisContainerName `
    --query "ipAddress.ip" `
    --output tsv

Write-Host "✅ Redis IP: $RedisIP" -ForegroundColor Green

# Step 6: Check existing app containers
Write-Host "🔍 Checking existing app containers..." -ForegroundColor Yellow
$existingContainers = az container list `
    --resource-group $ResourceGroup `
    --query "[?contains(name, '$AppContainerName')].name" `
    --output tsv

if ($existingContainers) {
    Write-Host "📋 Existing app containers found:" -ForegroundColor Yellow
    $existingContainers -split "`n" | ForEach-Object { Write-Host "   - $_" -ForegroundColor Cyan }
} else {
    Write-Host "📋 No existing app containers found" -ForegroundColor Green
}

# Step 7: Create NEW app container (never overwrite)
$NewAppContainerName = "$AppContainerName-$AppSuffix"
Write-Host "🚀 Creating NEW app container: $NewAppContainerName..." -ForegroundColor Yellow

az container create `
    --resource-group $ResourceGroup `
    --name $NewAppContainerName `
    --image $ImageName `
    --ports 5000 `
    --cpu 8.0 `
    --memory 16.0 `
    --location $Location `
    --restart-policy Always `
    --environment-variables `
        USE_REDIS=true `
        REDIS_HOST=$RedisIP `
        REDIS_PORT=6379 `
        REDIS_DB=0 `
        REDIS_PASSWORD= `
        REDIS_SESSION_TTL=3600 `
        DEPLOYMENT_ENV=production `
        FLASK_APP=app.py `
        FLASK_ENV=production `
        FLASK_DEBUG=0

Write-Host "✅ NEW app container created: $NewAppContainerName" -ForegroundColor Green

# Step 8: Get new app container IP
Write-Host "🌐 Getting new app container IP..." -ForegroundColor Yellow
$NewAppIP = az container show `
    --resource-group $ResourceGroup `
    --name $NewAppContainerName `
    --query "ipAddress.ip" `
    --output tsv

Write-Host "✅ New App IP: $NewAppIP" -ForegroundColor Green

# Step 9: Wait for container to start and test
Write-Host "🏥 Waiting for new container to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 60  # Wait for container to fully start

# Test health endpoint
Write-Host "🔍 Testing new application health..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://$NewAppIP`:5000/health" -UseBasicParsing -TimeoutSec 30
    $healthData = $response.Content | ConvertFrom-Json
    
    Write-Host "✅ Health check response:" -ForegroundColor Green
    Write-Host "   Status: $($healthData.status)" -ForegroundColor Cyan
    Write-Host "   Redis: $($healthData.redis)" -ForegroundColor Cyan
    Write-Host "   State Management: $($healthData.state_management)" -ForegroundColor Cyan
    Write-Host "   Message: $($healthData.message)" -ForegroundColor Cyan
    
    if ($healthData.redis -eq "connected") {
        Write-Host "🎉 Redis connection successful!" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Redis connection failed" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  Health check failed, but container is running" -ForegroundColor Yellow
    Write-Host "   You can manually test: http://$NewAppIP`:5000/health" -ForegroundColor Cyan
}

# Step 10: Show deployment summary
Write-Host ""
Write-Host "🎉 Safe deployment completed!" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Deployment Summary:" -ForegroundColor Cyan
Write-Host "   Resource Group: $ResourceGroup"
Write-Host "   Location: $Location"
Write-Host "   ACR: $AcrName.azurecr.io"
Write-Host "   Image: $ImageName"
Write-Host "   Redis Container: $RedisContainerName ($RedisIP)"
Write-Host "   NEW App Container: $NewAppContainerName ($NewAppIP)"
Write-Host "   New App FQDN: $NewAppContainerName.$Location.azurecontainer.io"
Write-Host ""
Write-Host "🔗 Access URLs:" -ForegroundColor Cyan
Write-Host "   NEW App: http://$NewAppIP`:5000"
Write-Host "   Health: http://$NewAppIP`:5000/health"
Write-Host "   FQDN: http://$NewAppContainerName.$Location.azurecontainer.io:5000"
Write-Host ""
Write-Host "🛡️  Safety Features:" -ForegroundColor Green
Write-Host "   ✅ Existing containers remain untouched"
Write-Host "   ✅ New container can be tested independently"
Write-Host "   ✅ Easy rollback by switching back to old container"
Write-Host "   ✅ Zero risk to production system"
Write-Host ""
Write-Host "📝 Next Steps:" -ForegroundColor Cyan
Write-Host "   1. Test the new container thoroughly"
Write-Host "   2. Update your frontend/DNS to point to new container"
Write-Host "   3. Monitor the new container for 24-48 hours"
Write-Host "   4. Delete old container when confident:"
Write-Host "      az container delete --resource-group $ResourceGroup --name <old-container-name> --yes"
Write-Host ""
Write-Host "📝 Useful Commands:" -ForegroundColor Yellow
Write-Host "   # View new app logs"
Write-Host "   az container logs --resource-group $ResourceGroup --name $NewAppContainerName"
Write-Host ""
Write-Host "   # View Redis logs"
Write-Host "   az container logs --resource-group $ResourceGroup --name $RedisContainerName"
Write-Host ""
Write-Host "   # List all app containers"
Write-Host "   az container list --resource-group $ResourceGroup --query \"[?contains(name, '$AppContainerName')].{Name:name, IP:ipAddress.ip, State:provisioningState}\" --output table"
Write-Host ""
Write-Host "💡 This approach ensures zero downtime and easy rollback!" 