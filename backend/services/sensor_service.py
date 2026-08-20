"""
Sensor service for HPIS.

This service is responsible for taking validated sensor
data and publishing it to Kafka.

It does NOT know anything about FastAPI HTTP requests.
"""

from typing import Any

from backend.events.kafka.producer import KafkaProducerService
from backend.events.schema.sensor_event import SensorEvent


class SensorService:
    """
    Business/service layer for sensor ingestion.

    Flow:

        FastAPI
           ↓
        SensorService
           ↓
        KafkaProducerService
           ↓
        Kafka
    """

    def __init__(
        self,
        kafka_producer: KafkaProducerService,
    ):
        """
        Initialize the sensor service.

        Parameters
        ----------
        kafka_producer:
            The reusable Kafka producer created by FastAPI
            during application startup.
        """

        self.kafka_producer = kafka_producer

    def publish_sensor_event(
        self,
        sensor_event: SensorEvent,
        user_id: str,
    ) -> None:
        """
        Publish a validated sensor event to Kafka.

        Parameters
        ----------
        sensor_event:
            Validated sensor data received from FastAPI.

        user_id:
            ID of the authenticated user.

        Returns
        -------
        None
        """

        # ----------------------------------------------------
        # Convert Pydantic model → Python dictionary
        # ----------------------------------------------------

        event_data: dict[str, Any] = sensor_event.model_dump()

        # ----------------------------------------------------
        # Add backend metadata
        # ----------------------------------------------------

        event_data["user_id"] = user_id

        # ----------------------------------------------------
        # Publish to Kafka
        # ----------------------------------------------------

        self.kafka_producer.publish_sensor_data(
            sensor_data=event_data,
            user_id=user_id,
        )