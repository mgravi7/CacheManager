from fastapi import FastAPI, HTTPException, status
from contextlib import asynccontextmanager
from cache_manager import CacheManager
from .api import router as user_router
import os
import asyncio


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager for startup and shutdown events.
    Manages CacheManager connection lifecycle.
    """
    # Startup: Initialize cache manager
    cache_manager = CacheManager()
    
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    await cache_manager.connect(redis_url=redis_url)
    
    app.state.cache_manager = cache_manager
    
    yield
    
    # Shutdown: Cleanup
    await cache_manager.disconnect()


app = FastAPI(
    title="CacheManager User API",
    description="Proof-of-concept API demonstrating type-safe async caching with Redis",
    version="0.1.0",
    lifespan=lifespan
)

# Include user router
app.include_router(user_router)


@app.get("/", summary="Root endpoint")
async def root():
    """Root endpoint providing API information."""
    return {
        "message": "CacheManager User API",
        "version": "0.1.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health", summary="Health check")
async def health_check():
    """
    Health check endpoint for Kubernetes liveness/readiness probes.
    
    Returns:
        200: Service is healthy and Redis is connected
        503: Service is unhealthy (Redis connection issues)
    
    Kubernetes will restart the pod if this endpoint fails repeatedly.
    """
    cache_manager = CacheManager()
    
    if cache_manager.redis is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cache not initialized"
        )
    
    try:
        # Test Redis connection with timeout
        await asyncio.wait_for(cache_manager.redis.ping(), timeout=2.0)
        
        return {
            "status": "healthy",
            "redis": "connected",
            "cache_manager": "operational"
        }
    
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis health check timeout"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Redis unhealthy: {str(e)}"
        )
