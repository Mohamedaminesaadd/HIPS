"""
HPIS FastAPI application.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.api.router.wearable import (
    router as wearable_router,
)

from backend.api.router.insights import (
    router as insights_router,
)

from backend.database.redis import (
    RedisConnection,
)

from backend.services.redis_insight_service import (
    RedisInsightService,
)


logger = logging.getLogger(__name__)


# ============================================================
# Application lifespan
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage HPIS application startup and shutdown.

    Startup:
        - Create Redis connection
        - Connect to Redis
        - Create Redis insight service
        - Store shared services in app.state

    Shutdown:
        - Close Redis connection
    """

    logger.info(
        "Starting HPIS application..."
    )

    redis_connection = None

    try:
        # ====================================================
        # Redis initialization
        # ====================================================

        redis_connection = RedisConnection()

        redis_connection.connect()

        logger.info(
            "Redis connection established."
        )

        # ====================================================
        # Redis insight service
        # ====================================================

        redis_insight_service = RedisInsightService(
            redis_connection=redis_connection,
        )

        # ====================================================
        # Application state
        # ====================================================

        app.state.redis_connection = (
            redis_connection
        )

        app.state.redis_insight_service = (
            redis_insight_service
        )

        logger.info(
            "Redis insight service initialized."
        )

        logger.info(
            "HPIS application startup complete."
        )

        # ====================================================
        # Application running
        # ====================================================

        yield

    except Exception:
        logger.exception(
            "HPIS application startup failed."
        )

        raise

    finally:
        # ====================================================
        # Shutdown
        # ====================================================

        logger.info(
            "Shutting down HPIS application..."
        )

        if redis_connection is not None:
            try:
                redis_connection.close()

                logger.info(
                    "Redis connection closed."
                )

            except Exception:
                logger.exception(
                    "Error while closing Redis connection."
                )

        logger.info(
            "HPIS application shutdown complete."
        )


# ============================================================
# FastAPI application
# ============================================================

app = FastAPI(
    title="HPIS Backend",
    description=(
        "Human Performance Intelligence System"
    ),
    version="1.0.0",
    lifespan=lifespan,
)


# ============================================================
# Routers
# ============================================================


app.include_router(
    wearable_router,
)

app.include_router(
    insights_router,
)