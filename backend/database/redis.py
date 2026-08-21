"""
Redis connection manager for HPIS.

Redis is initialized during FastAPI application startup
and closed during FastAPI application shutdown.
"""

import logging

import redis


logger = logging.getLogger(__name__)


# ============================================================
# Configuration
# ============================================================

REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0
REDIS_PASSWORD = "hpis2025"


class RedisConnection:
    """
    Manages the Redis client used by the application.
    """

    def __init__(
        self,
        host: str = REDIS_HOST,
        port: int = REDIS_PORT,
        db: int = REDIS_DB,
        password: str = REDIS_PASSWORD,
    ):
        self.host = host
        self.port = port
        self.db = db
        self.password = password

        self.client = None

    # ========================================================
    # Connect
    # ========================================================

    def connect(self) -> None:
        """
        Create and verify the Redis connection.
        """

        if self.client is not None:
            logger.warning(
                "Redis is already connected."
            )
            return

        logger.info(
            "Connecting to Redis at %s:%s",
            self.host,
            self.port,
        )

        self.client = redis.Redis(
            host=self.host,
            port=self.port,
            db=self.db,
            password=self.password,
            decode_responses=True,
        )

        # Verify connection and authentication
        self.client.ping()

        logger.info(
            "Connected to Redis successfully."
        )

    # ========================================================
    # Get client
    # ========================================================

    def get_client(self):
        """
        Return the active Redis client.
        """

        if self.client is None:
            raise RuntimeError(
                "Redis is not connected. "
                "The FastAPI application must be started "
                "before using Redis."
            )

        return self.client

    # ========================================================
    # Close
    # ========================================================

    def close(self) -> None:
        """
        Close Redis connection.
        """

        if self.client is None:
            return

        logger.info(
            "Closing Redis connection..."
        )

        self.client.close()

        self.client = None

        logger.info(
            "Redis connection closed."
        )