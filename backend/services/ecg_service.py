from typing import Any

from backend.events.kafka.producer import KafkaProducerService
from backend.events.schema.sensor_event import SensorEvent



class SensorService:
    """
    Business logic for sensor ingestion.

    The service receives validated sensor data and
    publishes it to Kafka.
    """

    def __init__(self, kafka_producer: KafkaProducerService):
        self.kafka_producer = kafka_producer

    def publish_sensor_event(
        self,
        sensor_event: SensorEvent,
        user_id: str,
    ) -> None:
        """
        Publish a validated sensor event to Kafka.
        """

        event_data: dict[str, Any] = sensor_event.model_dump()

        # Add backend/user metadata.
        event_data["user_id"] = user_id

        self.kafka_producer.publish_sensor_data(
            sensor_data=event_data,
            user_id=user_id,
        )