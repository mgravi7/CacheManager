from redis.asyncio import Redis, from_url
from typing import Optional
from .user_uuid_to_id_cache import UserUUIDtoIdCache
from .user_id_to_uuid_cache import UserIdToUUIDCache
import asyncio
import logging

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Singleton cache manager with self-healing Redis connection.
    
    Features:
    - Automatic reconnection on Redis pod failures
    - Background health checks every 10 seconds
    - Connection pool with optimized timeouts
    - Graceful degradation when cache unavailable
    
    Each cache class defines its own default TTL based on domain requirements.
    """
    
    _instance: Optional['CacheManager'] = None
    HEALTH_CHECK_INTERVAL = 10  # seconds
    FAILURE_THRESHOLD = 3  # consecutive failures before reconnect

    def __new__(cls) -> 'CacheManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self.redis: Optional[Redis] = None
            self.uuid_to_id_cache: Optional[UserUUIDtoIdCache] = None
            self.id_to_uuid_cache: Optional[UserIdToUUIDCache] = None
            self._redis_url: Optional[str] = None
            self._health_check_task: Optional[asyncio.Task] = None
            self._reconnect_lock = asyncio.Lock()
            self._initialized = True

    async def connect(self, redis_url: str = "redis://localhost:6379") -> None:
        """
        Initialize Redis connection with connection pool and health monitoring.
        
        Connection pool configuration:
        - max_connections: 50 (limit pool size)
        - socket_timeout: 5.0s (read/write operations)
        - socket_connect_timeout: 2.0s (fast failure detection)
        - retry_on_timeout: True (retry transient failures)
        - health_check_interval: 30s (built-in pool validation)
        
        Starts background health check task for proactive failure detection.
        """
        if self.redis is not None:
            return
        
        self._redis_url = redis_url
        
        logger.info(f"Connecting to Redis: {redis_url}")
        
        self.redis = from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=False,
            max_connections=50,
            socket_timeout=5.0,
            socket_connect_timeout=2.0,
            retry_on_timeout=True,
            health_check_interval=30,
        )
        
        # Verify connection
        try:
            await asyncio.wait_for(self.redis.ping(), timeout=2.0)
            logger.info("Redis connection established successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            await self.redis.aclose()
            self.redis = None
            raise
        
        # Create cache instances
        self.uuid_to_id_cache = UserUUIDtoIdCache(self.redis)
        self.id_to_uuid_cache = UserIdToUUIDCache(self.redis)
        
        # Start background health check
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        logger.info("Background health check started")

    async def disconnect(self) -> None:
        """Gracefully close Redis connection and stop health checks."""
        # Stop health check task
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
            self._health_check_task = None
        
        # Close Redis connection
        if self.redis:
            await self.redis.aclose()
            self.redis = None
            self.uuid_to_id_cache = None
            self.id_to_uuid_cache = None
        
        logger.info("Redis connection closed")

    async def _health_check_loop(self):
        """
        Background task for proactive health monitoring.
        
        Checks Redis connection every 10 seconds.
        After 3 consecutive failures, attempts reconnection.
        """
        consecutive_failures = 0
        
        while True:
            try:
                await asyncio.sleep(self.HEALTH_CHECK_INTERVAL)
                
                if self.redis is None:
                    logger.warning("Redis connection is None, skipping health check")
                    continue
                
                # Perform health check
                try:
                    await asyncio.wait_for(self.redis.ping(), timeout=2.0)
                    
                    # Health check passed
                    if consecutive_failures > 0:
                        logger.info("Redis health check recovered")
                    consecutive_failures = 0
                    
                except Exception as e:
                    consecutive_failures += 1
                    logger.warning(
                        f"Redis health check failed ({consecutive_failures}/{self.FAILURE_THRESHOLD}): {e}"
                    )
                    
                    # Trigger reconnection after threshold
                    if consecutive_failures >= self.FAILURE_THRESHOLD:
                        logger.error(
                            f"Redis health check failed {self.FAILURE_THRESHOLD} times, "
                            "attempting reconnection..."
                        )
                        await self._reconnect()
                        consecutive_failures = 0  # Reset after reconnect attempt
            
            except asyncio.CancelledError:
                logger.info("Health check loop cancelled")
                break
            except Exception as e:
                logger.error(f"Unexpected error in health check loop: {e}", exc_info=True)

    async def _reconnect(self):
        """
        Attempt to reconnect to Redis.
        
        Creates new connection pool and cache instances.
        Thread-safe with reconnect lock.
        """
        async with self._reconnect_lock:
            try:
                logger.info("Starting Redis reconnection...")
                
                # Close old connection
                old_redis = self.redis
                if old_redis:
                    try:
                        await old_redis.aclose()
                    except Exception as e:
                        logger.warning(f"Error closing old Redis connection: {e}")
                
                # Create new connection
                self.redis = from_url(
                    self._redis_url,
                    encoding="utf-8",
                    decode_responses=False,
                    max_connections=50,
                    socket_timeout=5.0,
                    socket_connect_timeout=2.0,
                    retry_on_timeout=True,
                    health_check_interval=30,
                )
                
                # Test new connection
                await asyncio.wait_for(self.redis.ping(), timeout=2.0)
                
                # Recreate cache instances
                self.uuid_to_id_cache = UserUUIDtoIdCache(self.redis)
                self.id_to_uuid_cache = UserIdToUUIDCache(self.redis)
                
                logger.info("Redis reconnection successful")
                
            except Exception as e:
                logger.error(f"Redis reconnection failed: {e}", exc_info=True)
                self.redis = None
                self.uuid_to_id_cache = None
                self.id_to_uuid_cache = None
