"""
Reusable Kafka producer for HPIS.

The producer is designed to be initialized once when the
FastAPI application starts and reused throughout the
application lifetime.
"""

import json
import logging
from typing import Any, Optional

from confluent_kafka import Producer

from backend.events.kafka.config import KAFKA_PRODUCER_CONFIG
from backend.events.kafka.topics import (
    SENSORS_TOPIC,
    INSIGHTS_TOPIC,
    ALERTS_TOPIC,
)


logger = logging.getLogger(__name__)


class KafkaProducerService:
    """
    Reusable Kafka producer service.

    One instance should normally be created during FastAPI
    application startup and reused by the application.
    """

    def __init__(self):
        self._producer = Producer(KAFKA_PRODUCER_CONFIG)

        logger.info(
            "Kafka producer initialized with broker: %s",
            KAFKA_PRODUCER_CONFIG["bootstrap.servers"],
        )

    # ========================================================
    # Internal delivery callback
    # ========================================================

    @staticmethod
    def _delivery_callback(err, msg):
        """
        Called by Kafka when a message has been delivered
        successfully or when delivery has failed.
        """

        if err is not None:
            logger.error(
                "Kafka message delivery failed: %s",
                err,
            )
            return

        logger.debug(
            "Kafka message delivered successfully: "
            "topic=%s partition=%s offset=%s",
            msg.topic(),
            msg.partition(),
            msg.offset(),
        )

    # ========================================================
    # Generic publish method
    # ========================================================

    def publish(
        self,
        topic: str,
        message: dict[str, Any],
        key: Optional[str] = None,
    ) -> None:
        """
        Publish a JSON message to Kafka.

        Parameters
        ----------
        topic:
            Kafka topic name.

        message:
            Python dictionary that will be serialized to JSON.

        key:
            Kafka message key. For HPIS this will normally
            be user_id.
        """

        try:
            serialized_message = json.dumps(
                message,
                separators=(",", ":"),
            ).encode("utf-8")

            serialized_key = (
                key.encode("utf-8")
                if key is not None
                else None
            )

            self._producer.produce(
                topic=topic,
                key=serialized_key,
                value=serialized_message,
                callback=self._delivery_callback,
            )

            self._producer.poll(0)

            logger.debug(
                "Kafka message queued: topic=%s key=%s",
                topic,
                key,
            )

        except BufferError:
            logger.warning(
                "Kafka producer local queue is full. "
                "Waiting for queued messages to be delivered."
            )

            self._producer.poll(1)

            self._producer.produce(
                topic=topic,
                key=serialized_key,
                value=serialized_message,
                callback=self._delivery_callback,
            )

            self._producer.poll(0)

        except Exception:
            logger.exception(
                "Failed to publish Kafka message to topic=%s",
                topic,
            )
            raise

    # ========================================================
    # Sensor data
    # ========================================================

    def publish_sensor_data(
        self,
        sensor_data: dict[str, Any],
        user_id: str,
    ) -> None:
        """
        Publish wearable sensor data to hpis.sensors.

        user_id is used as the Kafka message key.
        """

        self.publish(
            topic=SENSORS_TOPIC,
            message=sensor_data,
            key=user_id,
        )

    # ========================================================
    # Insight
    # ========================================================

    def publish_insight(
        self,
        insight: dict[str, Any],
        user_id: str,
    ) -> None:
        """
        Publish an AI/processing insight to hpis.insights.
        """

        self.publish(
            topic=INSIGHTS_TOPIC,
            message=insight,
            key=user_id,
        )

    # ========================================================
    # Alert
    # ========================================================

    def publish_alert(
        self,
        alert: dict[str, Any],
        user_id: str,
    ) -> None:
        """
        Publish an alert to hpis.alerts.
        """

        self.publish(
            topic=ALERTS_TOPIC,
            message=alert,
            key=user_id,
        )

    # ========================================================
    # Flush
    # ========================================================

    def flush(self, timeout: float = 10.0) -> int:
        """
        Wait for queued Kafka messages to be delivered.
        """

        remaining = self._producer.flush(timeout)

        if remaining > 0:
            logger.warning(
                "%d Kafka message(s) were not delivered "
                "within %.2f seconds.",
                remaining,
                timeout,
            )

        return remaining

    # ========================================================
    # Close
    # ========================================================

    def close(self) -> None:
        """
        Flush pending messages before shutting down.
        """

        logger.info("Closing Kafka producer...")

        self.flush()

        logger.info("Kafka producer closed.")


# ============================================================
# Backward compatibility
# ============================================================

HPISKafkaProducer = KafkaProducerService