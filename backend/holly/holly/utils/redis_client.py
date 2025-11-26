"""Redis client utility with connection pooling and error handling."""

import json
from typing import Any, Dict, Optional
import redis
from django.conf import settings
from loguru import logger


class RedisClient:
    """Singleton Redis client with connection pooling."""

    _instance: Optional['RedisClient'] = None
    _redis_client: Optional[redis.StrictRedis] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize Redis client if not already initialized."""
        if self._redis_client is None:
            try:
                self._redis_client = redis.StrictRedis.from_url(
                    settings.CELERY_RESULT_BACKEND,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                    health_check_interval=30
                )
                # Test connection
                self._redis_client.ping()
                logger.info("Redis connection established successfully")
            except (redis.ConnectionError, redis.TimeoutError) as e:
                logger.warning(f"Redis connection failed: {e}. Real-time features will be disabled.")
                self._redis_client = None
            except Exception as e:
                logger.error(f"Unexpected error connecting to Redis: {e}")
                self._redis_client = None

    def is_available(self) -> bool:
        """Check if Redis is available."""
        if self._redis_client is None:
            return False
        try:
            self._redis_client.ping()
            return True
        except (redis.ConnectionError, redis.TimeoutError):
            return False

    def publish(self, channel: str, message: Dict[str, Any]) -> bool:
        """
        Publish a message to a Redis channel.

        Args:
            channel: Redis channel name
            message: Message dictionary to publish

        Returns:
            True if published successfully, False otherwise
        """
        if not self.is_available():
            logger.warning(f"Cannot publish to {channel}: Redis not available")
            return False

        try:
            self._redis_client.publish(channel, json.dumps(message))
            logger.debug(f"Published to {channel}: {message}")
            return True
        except Exception as e:
            logger.error(f"Failed to publish to {channel}: {e}")
            return False

    def get_pubsub(self):
        """
        Get a pubsub object for subscribing to channels.

        Returns:
            Pubsub object or None if Redis unavailable
        """
        if not self.is_available():
            logger.warning("Cannot create pubsub: Redis not available")
            return None

        try:
            return self._redis_client.pubsub()
        except Exception as e:
            logger.error(f"Failed to create pubsub: {e}")
            return None

    def reconnect(self) -> bool:
        """
        Attempt to reconnect to Redis.

        Returns:
            True if reconnected successfully, False otherwise
        """
        try:
            self._redis_client = redis.StrictRedis.from_url(
                settings.CELERY_RESULT_BACKEND,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            self._redis_client.ping()
            logger.info("Redis reconnection successful")
            return True
        except Exception as e:
            logger.error(f"Redis reconnection failed: {e}")
            self._redis_client = None
            return False


# Singleton instance
redis_client = RedisClient()
