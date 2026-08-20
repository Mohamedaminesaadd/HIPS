from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.api.router.wearable import router as wearable_router
from backend.api.router.sensors import router as sensors_router

from backend.events.kafka.producer import KafkaProducerService


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI application lifecycle.

    Startup:
        Create one reusable Kafka producer.

    Shutdown:
        Flush pending Kafka messages and close the producer.
    """

    # ========================================================
    # STARTUP
    # ========================================================

    app.state.kafka_producer = KafkaProducerService()

    print("Kafka producer initialized.")

    yield

    # ========================================================
    # SHUTDOWN
    # ========================================================

    print("Closing Kafka producer...")

    app.state.kafka_producer.close()

    print("Kafka producer closed.")


# ============================================================
# FastAPI application
# ============================================================

app = FastAPI(
    title="HPIS Backend",
    lifespan=lifespan,
)


# ============================================================
# Routers
# ============================================================


app.include_router(wearable_router)

app.include_router(sensors_router)