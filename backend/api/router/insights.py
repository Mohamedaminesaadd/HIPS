"""
FastAPI routes for HPIS insights.
"""

import logging

from fastapi import (
    APIRouter,
    HTTPException,
    Request,
)

from backend.services.redis_insight_service import (
    RedisInsightService,
)


logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/api/insights",
    tags=["Insights"],
)


# ============================================================
# GET latest insight
# ============================================================

@router.get("/{user_id}")
def get_latest_insight(
    user_id: str,
    request: Request,
):
    """
    Return the latest insight for a user.

    Example:

        GET /api/insights/test-user-001
    """

    logger.info(
        "Requesting latest insight for user=%s",
        user_id,
    )

    # --------------------------------------------------------
    # Get Redis service from FastAPI application state
    # --------------------------------------------------------

    redis_service: RedisInsightService = (
        request.app.state.redis_insight_service
    )

    # --------------------------------------------------------
    # Read Redis
    # --------------------------------------------------------

    insight = redis_service.get_latest_insight(
        user_id=user_id,
    )

    # --------------------------------------------------------
    # No insight found
    # --------------------------------------------------------

    if insight is None:

        raise HTTPException(
            status_code=404,
            detail=(
                f"No insight found for user "
                f"{user_id}"
            ),
        )

    return {
        "success": True,
        "data": insight,
    }