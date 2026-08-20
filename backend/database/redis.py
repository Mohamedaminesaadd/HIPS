"""
Redis connection manager for HPIS.

Redis is used as the hot/current-state data store.
"""

import logging

import redis


logger = logging.getLogger(__name__)


# ============================================================
# Redis configuration
# ============================================================

REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0

# Development password.
#
# In production, load this from an environment variable.
REDIS_PASSWORD = "hpis2025"


class RedisConnection:
    """
    Manages the Redis client connection.
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
        Create and test the Redis connection.
        """

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

        # Test authentication + connection
        self.client.ping()

        logger.info(
            "Connected to Redis successfully."
        )

    # ========================================================
    # Get client
    # ========================================================

    def get_client(self):
        """
        Return the Redis client.
        """

        if self.client is None:
            raise RuntimeError(
                "Redis client is not initialized. "
                "Call connect() first."
            )

        return self.client

    # ========================================================
    # Close
    # ========================================================

    def close(self) -> None:
        """
        Close Redis connection.
        """

        if self.client is not None:

            logger.info(
                "Closing Redis connection..."
            )

            self.client.close()

            self.client = None

            logger.info(
                "Redis connection closed."
            )