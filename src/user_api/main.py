from fastapi import FastAPI
from contextlib import asynccontextmanager
from cache_manager import CacheManager
from .api import router as user_router
import os


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
    """Health check endpoint."""
    cache_manager = CacheManager()
    redis_connected = cache_manager.redis is not None
    
    return {
        "status": "healthy" if redis_connected else "degraded",
        "redis_connected": redis_connected
    }
