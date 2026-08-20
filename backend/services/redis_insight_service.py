"""
Redis service for HPIS insights.

This service stores the latest insight/state for each user.

Redis is used as a hot/current-state store, not as the
permanent historical database.
"""

import json
import logging
from typing import Any

from backend.database.redis import RedisConnection


logger = logging.getLogger(__name__)


class RedisInsightService:
    """
    Stores and retrieves the latest HPIS insight for users.
    """

    KEY_PREFIX = "hpis:user"

    def __init__(
        self,
        redis_connection: RedisConnection,
    ):
        """
        Initialize the Redis insight service.
        """

        self.redis_connection = redis_connection

        self.client = (
            redis_connection.get_client()
        )

    # ========================================================
    # Build Redis key
    # ========================================================

    @classmethod
    def _build_latest_key(
        cls,
        user_id: str,
    ) -> str:
        """
        Build the Redis key used for the user's latest state.

        Example:

        hpis:user:test-user-001:latest
        """

        return (
            f"{cls.KEY_PREFIX}:"
            f"{user_id}:latest"
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

        The complete insight is stored as JSON.
        """

        # ----------------------------------------------------
        # Extract user ID
        # ----------------------------------------------------

        user_id = insight.get("user_id")

        if not user_id:

            raise ValueError(
                "Insight is missing user_id."
            )

        # ----------------------------------------------------
        # Build Redis key
        # ----------------------------------------------------

        key = self._build_latest_key(
            user_id
        )

        # ----------------------------------------------------
        # Serialize insight
        # ----------------------------------------------------

        value = json.dumps(
            insight,
            separators=(",", ":"),
        )

        # ----------------------------------------------------
        # Store
        # ----------------------------------------------------

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

    # ========================================================
    # Get latest insight
    # ========================================================

    def get_latest_insight(
        self,
        user_id: str,
    ) -> dict[str, Any] | None:
        """
        Retrieve the latest insight for a user.
        """

        key = self._build_latest_key(
            user_id
        )

        value = self.client.get(
            key
        )

        if value is None:

            return None

        return json.loads(
            value
        )

    # ========================================================
    # Delete latest insight
    # ========================================================

    def delete_latest_insight(
        self,
        user_id: str,
    ) -> None:
        """
        Delete the latest insight for a user.
        """

        key = self._build_latest_key(
            user_id
        )

        self.client.delete(
            key
        )

        logger.info(
            "Latest insight deleted from Redis: "
            "user_id=%s",
            user_id,
        )