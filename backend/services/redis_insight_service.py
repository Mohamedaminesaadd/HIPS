"""
Redis service for HPIS insights.

Redis is used as a hot/current-state store.

Responsibilities:
    - Store the latest insight for a user
    - Retrieve the latest insight
    - Delete the latest insight

Redis is NOT the permanent historical database.
Historical data should be stored in Cassandra or another
persistent database.
"""

import json
import logging
from typing import Any

from redis.exceptions import RedisError

from backend.database.redis import RedisConnection


logger = logging.getLogger(__name__)


class RedisInsightService:
    """
    Service responsible for managing the latest HPIS insight
    for each user in Redis.
    """

    KEY_PREFIX = "hpis:user"
    LATEST_SUFFIX = "latest"

    def __init__(
        self,
        redis_connection: RedisConnection,
    ) -> None:
        """
        Initialize the Redis insight service.

        Args:
            redis_connection:
                Redis connection manager used by the application.
        """

        if redis_connection is None:
            raise ValueError(
                "redis_connection cannot be None."
            )

        self.redis_connection = redis_connection

    # ========================================================
    # Redis client
    # ========================================================

    @property
    def client(self):
        """
        Return the Redis client managed by RedisConnection.
        """

        return self.redis_connection.get_client()

    # ========================================================
    # Key management
    # ========================================================

    @classmethod
    def _build_latest_key(
        cls,
        user_id: str,
    ) -> str:
        """
        Build the Redis key for the latest user insight.

        Example:

            hpis:user:test-user-001:latest
        """

        if not user_id or not user_id.strip():
            raise ValueError(
                "user_id cannot be empty."
            )

        return (
            f"{cls.KEY_PREFIX}:"
            f"{user_id}:"
            f"{cls.LATEST_SUFFIX}"
        )

    # ========================================================
    # Store latest insight
    # ========================================================

    def store_latest_insight(
        self,
        insight: dict[str, Any],
    ) -> None:
        """
        Store the latest insight for a user.

        The complete insight is serialized as compact JSON.

        Args:
            insight:
                Insight dictionary containing at least `user_id`.

        Raises:
            ValueError:
                If the insight is invalid.
            RedisError:
                If Redis cannot store the value.
        """

        if not isinstance(insight, dict):
            raise ValueError(
                "Insight must be a dictionary."
            )

        user_id = insight.get("user_id")

        if not user_id:
            raise ValueError(
                "Insight is missing user_id."
            )

        key = self._build_latest_key(
            str(user_id)
        )

        try:
            value = json.dumps(
                insight,
                separators=(",", ":"),
                ensure_ascii=False,
            )

            self.client.set(
                key,
                value,
            )

            logger.info(
                "Latest insight stored in Redis: "
                "user_id=%s key=%s",
                user_id,
                key,
            )

        except RedisError:
            logger.exception(
                "Failed to store latest insight in Redis: "
                "user_id=%s",
                user_id,
            )

            raise

        except (TypeError, ValueError):
            logger.exception(
                "Failed to serialize insight: "
                "user_id=%s",
                user_id,
            )

            raise

    # ========================================================
    # Get latest insight
    # ========================================================

    def get_latest_insight(
        self,
        user_id: str,
    ) -> dict[str, Any] | None:
        """
        Retrieve the latest insight for a user.

        Returns:
            The insight dictionary if it exists.
            None if no insight exists.

        Raises:
            RedisError:
                If Redis cannot be reached.
            ValueError:
                If user_id is invalid.
        """

        key = self._build_latest_key(
            user_id
        )

        try:
            value = self.client.get(
                key
            )

            if value is None:
                logger.debug(
                    "No latest insight found: "
                    "user_id=%s",
                    user_id,
                )

                return None

            if isinstance(value, bytes):
                value = value.decode("utf-8")

            insight = json.loads(value)

            if not isinstance(insight, dict):
                logger.error(
                    "Invalid insight format in Redis: "
                    "user_id=%s",
                    user_id,
                )

                return None

            return insight

        except RedisError:
            logger.exception(
                "Failed to retrieve latest insight: "
                "user_id=%s",
                user_id,
            )

            raise

        except (json.JSONDecodeError, UnicodeDecodeError):
            logger.exception(
                "Invalid JSON stored in Redis: "
                "user_id=%s",
                user_id,
            )

            raise

    # ========================================================
    # Delete latest insight
    # ========================================================

    def delete_latest_insight(
        self,
        user_id: str,
    ) -> bool:
        """
        Delete the latest insight for a user.

        Returns:
            True if a key was deleted.
            False if the key did not exist.
        """

        key = self._build_latest_key(
            user_id
        )

        try:
            deleted = self.client.delete(
                key
            )

            was_deleted = deleted > 0

            logger.info(
                "Latest insight deleted from Redis: "
                "user_id=%s deleted=%s",
                user_id,
                was_deleted,
            )

            return was_deleted

        except RedisError:
            logger.exception(
                "Failed to delete latest insight: "
                "user_id=%s",
                user_id,
            )

            raise