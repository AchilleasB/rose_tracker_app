# Azure Deployment Guide for Rose Tracker App

## Overview

This guide explains how to deploy the Rose Tracker application to Azure Container Instances (ACI) with Redis for shared state management. The application uses a **single smart deployment script** that handles everything without deleting containers.

## Architecture

### Production Deployment (Recommended)
- **App Container**: Flask application with YOLO ML model
- **Redis Container**: Shared state management for sessions and data
- **Azure Container Registry**: Docker image storage
- **Separate Container Instances**: App and Redis in different ACI instances

### Key Features
- ✅ **No Container Deletion**: Uses `--overwrite` to update existing containers
- ✅ **Smart Management**: Creates containers if they don't exist, updates if they do
- ✅ **Redis Integration**: Optional Redis for shared state across multiple workers
- ✅ **Version Control**: Support for different image tags
- ✅ **Idempotent**: Safe to run multiple times

## Quick Start

### Single Command Deployment

```powershell
# Deploy everything with default settings
.\deploy-azure.ps1

# Deploy with specific version tag
.\deploy-azure.ps1 -ImageTag v1.1

# Deploy with custom resource group
.\deploy-azure.ps1 -ResourceGroup "my-rg" -ImageTag "production"
```

### What the Script Does

1. **Resource Group**: Creates if doesn't exist
2. **Azure Container Registry**: Creates if doesn't exist
3. **Docker Image**: Builds and pushes to ACR
4. **Redis Container**: Creates if doesn't exist
5. **App Container**: Creates if doesn't exist, updates with new image if exists
6. **Health Check**: Tests application and Redis connectivity
7. **Summary**: Shows deployment details and access URLs

## Configuration

### Script Parameters

```powershell
param(
    [string]$ResourceGroup = "rg_group8",           # Your Azure resource group
    [string]$Location = "westeurope",               # Azure region
    [string]$RedisContainerName = "rose-tracker-redis",     # Redis container name
    [string]$AppContainerName = "rose-tracker-container",   # App container name
    [string]$AcrName = "rosetrackeracr",            # Azure Container Registry name
    [string]$ImageTag = "production"                    # Docker image tag
)
```

### Environment Variables

The script automatically configures these environment variables for the app container:

```bash
USE_REDIS=true                     # Enable Redis for shared state
REDIS_HOST=<redis-ip>              # Redis container IP (auto-detected)
REDIS_PORT=6379                    # Redis port
REDIS_DB=0                         # Redis database number
REDIS_PASSWORD=                    # Redis password (empty for container)
REDIS_SESSION_TTL=3600             # Session TTL in seconds (1 hour)
DEPLOYMENT_ENV=production          # Production environment
FLASK_APP=app.py                   # Flask application entry point
FLASK_ENV=production               # Production Flask environment
FLASK_DEBUG=0                      # Disable debug mode
```

## Redis Implementation

### Why Redis?

The application uses Redis for **shared state management** in production to solve multi-worker issues:

#### Problems Solved
- **Session Management**: Sessions persist across worker restarts
- **Shared State**: Multiple workers share the same data
- **Consistent Counts**: All workers see the same total unique roses count
- **Cross-Worker Access**: Any worker can access any session

#### Development vs Production
- **Development**: Uses in-memory state (no Redis required)
- **Production**: Uses Redis for shared state (enabled by default)

### Redis Data Structure

#### Session Data
```python
{
    'start_time': float,           # Session start timestamp
    'last_update': float,          # Last frame processing time
    'last_count_update': float,    # Last count update time
    'display_count': int,          # Smoothed count for display
    'frame_counts': list,          # Recent frame counts for smoothing
    'session_unique_roses': set,   # Unique roses in this session
    'frame_count': int,            # Total frames processed
    'session_number': int          # Sequential session number
}
```

#### Persistent Data
```python
{
    'total_unique_roses': set,     # All unique roses across all sessions
    'session_history': list,       # Completed session statistics
    'last_session_id': str,        # Last active session ID
    'next_session_number': int,    # Next session number (atomic counter)
    'cumulative_unique_roses': int # Running total of unique roses
}
```

## Deployment Process

### Step-by-Step Breakdown

#### 1. Resource Group & ACR Setup
```powershell
# Check/create resource group
az group create --name $ResourceGroup --location $Location

# Check/create Azure Container Registry
az acr create --resource-group $ResourceGroup --name $AcrName --sku Basic --location $Location --admin-enabled true
```

#### 2. Docker Image Build & Push
```powershell
# Login to ACR
az acr login --name $AcrName

# Build and push image
docker build -t $ImageName .
docker push $ImageName
```

#### 3. Redis Container Deployment
```powershell
# Create Redis container (if doesn't exist)
az container create \
  --resource-group $ResourceGroup \
  --name $RedisContainerName \
  --image redis:7-alpine \
  --ports 6379 \
  --cpu 0.5 \
  --memory 1.0 \
  --location $Location \
  --restart-policy Always \
  --command-line "redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru"
```

#### 4. App Container Deployment/Update
```powershell
# Update existing container with new image (no deletion)
az container create \
  --resource-group $ResourceGroup \
  --name $AppContainerName \
  --image $ImageName \
  --ports 5000 \
  --cpu 2.0 \
  --memory 4.0 \
  --location $Location \
  --restart-policy Always \
  --environment-variables \
    USE_REDIS=true \
    REDIS_HOST=$RedisIP \
    REDIS_PORT=6379 \
    REDIS_DB=0 \
    REDIS_PASSWORD= \
    REDIS_SESSION_TTL=3600 \
    DEPLOYMENT_ENV=production \
    FLASK_APP=app.py \
    FLASK_ENV=production \
    FLASK_DEBUG=0 \
  --overwrite
```

## Monitoring and Health Checks

### Health Check Endpoint

The application provides a health check endpoint that reports Redis status:

```bash
# Get app container IP
APP_IP=$(az container show \
  --resource-group $ResourceGroup \
  --name $AppContainerName \
  --query "ipAddress.ip" \
  --output tsv)

# Test health
curl http://$APP_IP:5000/health
```

#### Expected Responses

**Production with Redis:**
```json
{
  "status": "healthy",
  "redis": "connected",
  "state_management": "redis",
  "message": "Application is running normally with Redis"
}
```

**Development (no Redis):**
```json
{
  "status": "healthy",
  "redis": "disabled",
  "state_management": "in-memory",
  "message": "Application is running in development mode"
}
```

### Container Logs

```powershell
# View app container logs
az container logs --resource-group $ResourceGroup --name $AppContainerName

# View Redis container logs
az container logs --resource-group $ResourceGroup --name $RedisContainerName
```

### Container Status

```powershell
# Check app container status
az container show --resource-group $ResourceGroup --name $AppContainerName

# Check Redis container status
az container show --resource-group $ResourceGroup --name $RedisContainerName
```

## Scaling and Multiple Workers

### Multiple App Instances

The application supports multiple workers with Redis shared state:

```powershell
# Deploy additional app containers
az container create \
  --resource-group $ResourceGroup \
  --name rose-tracker-app-2 \
  --image $ImageName \
  --ports 5000 \
  --cpu 1.0 \
  --memory 2.0 \
  --location $Location \
  --restart-policy Always \
  --environment-variables \
    USE_REDIS=true \
    REDIS_HOST=$RedisIP \
    REDIS_PORT=6379 \
    DEPLOYMENT_ENV=production \
  --overwrite
```

### Load Balancer Setup

For multiple app instances, use Azure Application Gateway:

```powershell
# Create public IP for load balancer
az network public-ip create \
  --resource-group $ResourceGroup \
  --name rose-tracker-lb-ip \
  --sku Standard

# Create application gateway
az network application-gateway create \
  --resource-group $ResourceGroup \
  --name rose-tracker-gateway \
  --location $Location \
  --vnet-name rose-tracker-vnet \
  --subnet default \
  --public-ip-address rose-tracker-lb-ip \
  --http-settings-cookie-based-affinity Enabled \
  --frontend-port 80 \
  --http-settings-port 5000 \
  --servers $AppIP1 $AppIP2
```

## Cost Optimization

### Container Sizing Recommendations

| Component | CPU | Memory | Use Case |
|-----------|-----|--------|----------|
| Redis | 0.5 | 1GB | Session storage, shared state |
| App (Single) | 2.0 | 4GB | ML inference, single worker |
| App (Multiple) | 1.0 | 2GB | ML inference, multiple workers |

### Pricing Estimates

| Configuration | Monthly Cost | Use Case |
|---------------|-------------|----------|
| Single App + Redis | ~$50-80 | Development/Testing |
| Multiple Apps + Redis | ~$100-150 | Production |
| With Load Balancer | ~$120-180 | High Availability |

## Troubleshooting

### Common Issues

#### 1. Redis Connection Failed
```powershell
# Check Redis container status
az container show --resource-group $ResourceGroup --name $RedisContainerName

# Test Redis connectivity from app
az container exec \
  --resource-group $ResourceGroup \
  --name $AppContainerName \
  --exec-command "python -c 'import redis; r=redis.Redis(host=\"$RedisIP\", port=6379, socket_connect_timeout=5); print(f\"Redis connection: {r.ping()}\")'"
```

#### 2. Application Won't Start
```powershell
# Check container logs
az container logs --resource-group $ResourceGroup --name $AppContainerName

# Check environment variables
az container show \
  --resource-group $ResourceGroup \
  --name $AppContainerName \
  --query "containers[0].environmentVariables"
```

#### 3. Docker Build Failed
```powershell
# Check Docker build locally
docker build -t test-image .

# Check ACR login
az acr login --name $AcrName
```

#### 4. Container Update Failed
```powershell
# Check if container exists
az container show --resource-group $ResourceGroup --name $AppContainerName

# Force recreate if needed (will change IP)
az container delete --resource-group $ResourceGroup --name $AppContainerName --yes
.\deploy-azure.ps1
```

### Performance Monitoring

```powershell
# Monitor container performance
az monitor metrics list \
  --resource <CONTAINER_RESOURCE_ID> \
  --metric "CpuPercentage,MemoryPercentage" \
  --interval PT1M
```

## Security Considerations

### Network Security
- Use private networks for container communication
- Enable network security groups
- Consider Azure Firewall for additional protection

### Redis Security
- Enable Redis authentication for production
- Use SSL/TLS for Redis connections
- Implement proper access controls

### Container Security
- Use managed identities for ACR access
- Enable container security scanning
- Implement proper RBAC

### Monitoring and Alerting
- Enable Azure Monitor for containers
- Set up alerts for high CPU/memory usage
- Monitor Redis connection health

## Best Practices

### Deployment
1. **Use Version Tags**: Always specify image tags for version control
2. **Test Locally**: Test Docker builds locally before deployment
3. **Monitor Health**: Use health check endpoint for monitoring
4. **Backup Data**: Implement Redis backup strategies

### Scaling
1. **Start Small**: Begin with single app instance
2. **Monitor Performance**: Scale based on actual usage
3. **Use Load Balancer**: For multiple app instances
4. **Optimize Resources**: Right-size containers based on usage

### Maintenance
1. **Regular Updates**: Update Docker images regularly
2. **Security Patches**: Keep Redis and base images updated
3. **Log Rotation**: Implement proper log management
4. **Cost Monitoring**: Monitor and optimize costs

## Next Steps

1. **Initial Deployment**: Run `.\deploy-azure.ps1` for first deployment
2. **Testing**: Verify health check and application functionality
3. **Monitoring**: Set up monitoring and alerting
4. **Scaling**: Add additional app instances as needed
5. **CI/CD**: Implement automated deployment pipeline
6. **Backup**: Set up Redis backup and disaster recovery

## Support

For issues or questions:
1. Check container logs first
2. Verify health check endpoint
3. Test Redis connectivity
4. Review this documentation
5. Check Azure Container Instances documentation 