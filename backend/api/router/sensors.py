from fastapi import APIRouter, Request, status

from backend.events.schema.sensor_event import SensorEvent
from backend.services.sensor_service import SensorService


router = APIRouter(
    prefix="/api/sensors",
    tags=["Sensors"],
)


@router.post(
    "",
    status_code=status.HTTP_202_ACCEPTED,
)
async def receive_sensor_data(
    sensor_event: SensorEvent,
    request: Request,
):
    """
    Receive validated sensor data and publish it to Kafka.

    Authentication will be added later.
    For now, a temporary test user is used.
    """

    # Temporary development user.
    # Later this will come from JWT authentication.
    user_id = "test-user-001"

    # Get the single Kafka producer created during
    # FastAPI application startup.
    kafka_producer = request.app.state.kafka_producer

    # Create the sensor service.
    sensor_service = SensorService(
        kafka_producer=kafka_producer,
    )

    # Publish the validated sensor event to Kafka.
    sensor_service.publish_sensor_event(
        sensor_event=sensor_event,
        user_id=user_id,
    )

    return {
        "status": "accepted",
        "message": "Sensor data published to Kafka",
        "topic": "hpis.sensors",
        "user_id": user_id,
    }