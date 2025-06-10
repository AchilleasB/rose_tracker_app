# Redis Implementation for Shared State Management (Production Only)

## Overview

This implementation adds **optional** Redis-based shared state management to solve the multi-worker session and persistent data issues in the Rose Tracker application. Redis is only used in production environments, while development uses simple in-memory state management.

## Configuration

### Environment Variables

```bash
# Enable/Disable Redis (default: false for development, true for production)
USE_REDIS=false                    # Development: in-memory state
USE_REDIS=true                     # Production: Redis shared state

# Redis Configuration (only used when USE_REDIS=true)
REDIS_HOST=localhost              # Redis server host
REDIS_PORT=6379                   # Redis server port
REDIS_DB=0                        # Redis database number
REDIS_PASSWORD=                   # Redis password (optional)
REDIS_SESSION_TTL=3600            # Session TTL in seconds (1 hour default)
```

## Usage

### Development Environment (In-Memory State)

**Default behavior** - No Redis required:

```bash
# Development docker-compose (no Redis)
docker-compose -f docker-compose.dev.yml up --build

# Health check response
curl http://localhost:5000/health
# Response: {"status": "healthy", "redis": "disabled", "state_management": "in-memory"}
```

**Features in Development:**
- ✅ Simple in-memory session management
- ✅ No external dependencies
- ✅ Fast startup and operation
- ❌ Sessions don't persist across worker restarts
- ❌ Not suitable for multiple workers

### Production Environment (Redis Shared State)

**For multi-worker deployments** - Redis required:

```bash
# Production docker-compose (with Redis)
docker-compose -f docker-compose.prod.yml up --build

# Health check response
curl http://localhost:5000/health
# Response: {"status": "healthy", "redis": "connected", "state_management": "redis"}
```

**Features in Production:**
- ✅ Shared state across multiple workers
- ✅ Session persistence across worker restarts
- ✅ Consistent total counts across workers
- ✅ Scalable to multiple workers
- ❌ Requires Redis infrastructure

## Problem Solved

### Before Redis (In-Memory State Issues in Production)
- **Session Management**: Each worker had its own `active_sessions` dictionary
- **Persistent Data**: Each worker had its own `persistent_data` dictionary
- **Cross-Worker Access**: Session started in Worker A couldn't be accessed by Worker B
- **Total Counts**: Each worker maintained separate counts, leading to inconsistencies
- **Session Loss**: Sessions were lost when workers restarted

### After Redis (Shared State Solution in Production)
- **Centralized Sessions**: All sessions stored in Redis with TTL
- **Shared Persistent Data**: All workers share the same persistent data
- **Cross-Worker Access**: Any worker can access any session
- **Consistent Counts**: All workers see the same total unique roses count
- **Session Persistence**: Sessions survive worker restarts (within TTL)

## Architecture

### Components

1. **Conditional RedisService** (`src/services/redis_service.py`)
   - Only loaded when `USE_REDIS=true`
   - Manages Redis connections and operations
   - Handles serialization/deserialization of complex data types
   - Provides atomic operations for session numbering

2. **Updated RealtimeTrackingService** (`src/services/tracking_service/realtime_tracking_service.py`)
   - Conditionally uses Redis or in-memory storage based on `USE_REDIS`
   - Maintains backward compatibility
   - Same API regardless of storage backend

3. **Configuration** (`config/settings.py`)
   - `USE_REDIS` environment variable controls behavior
   - Redis connection settings only used when enabled
   - Clear logging of which mode is active

4. **Health Check Endpoint** (`/health`)
   - Reports current state management mode
   - Verifies Redis connectivity when enabled
   - Useful for monitoring and debugging

## Deployment

### Local Development

```bash
# Simple development setup (no Redis)
docker-compose -f docker-compose.dev.yml up --build
```

### Production Deployment

#### Option 1: Docker Compose (Recommended for testing)
```bash
# Production setup with Redis
docker-compose -f docker-compose.prod.yml up --build
```

#### Option 2: Azure Container Instances
```bash
# Deploy Redis container
az container create \
  --resource-group your-rg \
  --name rose-tracker-redis \
  --image redis:7-alpine \
  --ports 6379 \
  --cpu 0.5 \
  --memory 1.0

# Deploy app with Redis enabled
az container create \
  --resource-group your-rg \
  --name rose-tracker-app \
  --image rosetrackeracr.azurecr.io/rose_tracker_app:deploy \
  --ports 5000 \
  --cpu 2.0 \
  --memory 4.0 \
  --environment-variables \
    USE_REDIS=true \
    REDIS_HOST=rose-tracker-redis \
    REDIS_PORT=6379 \
    REDIS_DB=0 \
    REDIS_SESSION_TTL=3600
```

#### Option 3: Azure Cache for Redis
```bash
# Use Azure Cache for Redis instead of container
az container create \
  --resource-group your-rg \
  --name rose-tracker-app \
  --image rosetrackeracr.azurecr.io/rose_tracker_app:deploy \
  --ports 5000 \
  --cpu 2.0 \
  --memory 4.0 \
  --environment-variables \
    USE_REDIS=true \
    REDIS_HOST=your-redis-cache.redis.cache.windows.net \
    REDIS_PORT=6380 \
    REDIS_PASSWORD=your-access-key \
    REDIS_SESSION_TTL=3600
```

## Data Structure

### Session Data
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

### Persistent Data
```python
{
    'total_unique_roses': set,     # All unique roses across all sessions
    'session_history': list,       # Completed session statistics
    'last_session_id': str,        # Last active session ID
    'next_session_number': int,    # Next session number (atomic counter)
    'cumulative_unique_roses': int # Running total of unique roses
}
```

## Benefits

### Development Mode (`USE_REDIS=false`)
- **Simple Setup**: No external dependencies
- **Fast Development**: Quick startup and testing
- **Easy Debugging**: All state in memory
- **No Infrastructure**: Works out of the box

### Production Mode (`USE_REDIS=true`)
- **Session Consistency**: Sessions work across all workers
- **Accurate Counts**: All workers see consistent total counts
- **Scalability**: Easy to add more workers
- **Reliability**: Sessions survive worker crashes
- **Monitoring**: Built-in health checks and Redis monitoring

## Monitoring and Debugging

### Health Check
```bash
curl http://localhost:5000/health
```

**Development Response:**
```json
{
    "status": "healthy",
    "redis": "disabled",
    "state_management": "in-memory",
    "message": "Application is running normally (development mode)"
}
```

**Production Response:**
```json
{
    "status": "healthy",
    "redis": "connected",
    "state_management": "redis",
    "message": "Application is running normally with Redis"
}
```

### Redis CLI Commands (Production Only)
```bash
# Connect to Redis
docker exec -it rose_tracker_redis_prod redis-cli

# List all keys
KEYS *

# Get session data
GET session:{session_id}

# Get persistent data
GET persistent_data

# Monitor Redis operations
MONITOR
```

## Migration Notes

### From Development to Production
1. Set `USE_REDIS=true` in production environment
2. Deploy Redis infrastructure
3. Update environment variables for Redis connection
4. No code changes required

### Backward Compatibility
- API endpoints remain the same
- Frontend code unchanged
- Session ID format unchanged
- Automatic fallback to in-memory if Redis fails

## Troubleshooting

### Development Issues
- **No Redis Required**: Development works without Redis
- **Check USE_REDIS**: Ensure it's set to `false` for development
- **Health Check**: Should show "in-memory" state management

### Production Issues
- **Redis Connection**: Check Redis container is running
- **Environment Variables**: Verify `USE_REDIS=true` and Redis settings
- **Health Check**: Should show "redis" state management
- **Network**: Ensure app can reach Redis container

### Common Commands
```bash
# Check current mode
curl http://localhost:5000/health

# Development logs
docker logs rose_tracker_app_dev

# Production logs
docker logs rose_tracker_app_prod

# Redis logs (production only)
docker logs rose_tracker_redis_prod
``` 