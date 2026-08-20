"""
HPIS Sensor Stream Processor.

Responsibilities:
    Kafka hpis.sensors
        ↓
    collect recent heart-rate values
        ↓
    30-second window
        ↓
    calculate average HR
        ↓
    Kafka hpis.insights

This service is intentionally independent from:
    - FastAPI
    - Cassandra
    - Redis
    - RabbitMQ
    - AI agents
"""

import logging
import time
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from backend.events.kafka.consumer import KafkaConsumerService
from backend.events.kafka.producer import KafkaProducerService
from backend.events.kafka.topics import (
    SENSORS_TOPIC,
    INSIGHTS_TOPIC,
)


logger = logging.getLogger(__name__)


# ============================================================
# Configuration
# ============================================================

KAFKA_GROUP_ID = "hpis-streams-group"

WINDOW_SECONDS = 30


class SensorStreamProcessor:
    """
    Processes real-time sensor events from Kafka.

    Current processing:
        - 30-second heart-rate window
        - average heart rate
        - publish result to hpis.insights
    """

    def __init__(self):

        # ----------------------------------------------------
        # Kafka consumer
        # ----------------------------------------------------

        self.consumer = KafkaConsumerService(
            group_id=KAFKA_GROUP_ID,
            topics=[SENSORS_TOPIC],
        )

        # ----------------------------------------------------
        # Kafka producer
        # ----------------------------------------------------

        self.producer = KafkaProducerService()

        # ----------------------------------------------------
        # HR windows
        #
        # Structure:
        #
        # {
        #     "user123": [
        #         (timestamp, 72),
        #         (timestamp, 75),
        #         (timestamp, 80)
        #     ]
        # }
        # ----------------------------------------------------

        self.hr_windows: dict[
            str,
            list[tuple[float, float]]
        ] = defaultdict(list)

    # ========================================================
    # Process one sensor event
    # ========================================================

    def process_event(
        self,
        event: dict[str, Any],
    ) -> None:
        """
        Process one sensor event received from Kafka.
        """

        sensor_data = event["value"]

        # ----------------------------------------------------
        # Extract user ID
        # ----------------------------------------------------

        user_id = sensor_data.get("user_id")

        if not user_id:
            logger.warning(
                "Ignoring sensor event without user_id."
            )
            return

        # ----------------------------------------------------
        # Extract heart rate
        # ----------------------------------------------------

        heart_rate = sensor_data.get("heart_rate")

        if heart_rate is None:
            logger.debug(
                "Sensor event has no heart_rate: user=%s",
                user_id,
            )
            return

        try:
            heart_rate = float(heart_rate)

        except (TypeError, ValueError):

            logger.warning(
                "Invalid heart_rate for user=%s: %s",
                user_id,
                heart_rate,
            )

            return

        # ----------------------------------------------------
        # Validate HR
        # ----------------------------------------------------

        if heart_rate <= 0 or heart_rate > 250:

            logger.warning(
                "Ignoring unrealistic heart_rate: "
                "user=%s hr=%s",
                user_id,
                heart_rate,
            )

            return

        # ----------------------------------------------------
        # Use processing time for window management
        # ----------------------------------------------------

        current_time = time.time()

        # ----------------------------------------------------
        # Add HR to user's window
        # ----------------------------------------------------

        self.hr_windows[user_id].append(
            (
                current_time,
                heart_rate,
            )
        )

        logger.debug(
            "HR added to window: user=%s hr=%s",
            user_id,
            heart_rate,
        )

        # ----------------------------------------------------
        # Remove values outside the 30-second window
        # ----------------------------------------------------

        self._remove_expired_values(
            user_id=user_id,
            current_time=current_time,
        )

        # ----------------------------------------------------
        # Calculate average
        # ----------------------------------------------------

        self._calculate_and_publish_hr_average(
            user_id=user_id,
        )

    # ========================================================
    # Remove expired values
    # ========================================================

    def _remove_expired_values(
        self,
        user_id: str,
        current_time: float,
    ) -> None:
        """
        Remove HR values older than WINDOW_SECONDS.
        """

        window = self.hr_windows[user_id]

        cutoff_time = (
            current_time - WINDOW_SECONDS
        )

        self.hr_windows[user_id] = [
            (timestamp, heart_rate)
            for timestamp, heart_rate in window
            if timestamp >= cutoff_time
        ]

    # ========================================================
    # Calculate average
    # ========================================================

    def _calculate_and_publish_hr_average(
        self,
        user_id: str,
    ) -> None:
        """
        Calculate the current average HR and publish
        an insight to Kafka.
        """

        window = self.hr_windows[user_id]

        if not window:
            return

        heart_rates = [
            heart_rate
            for _, heart_rate in window
        ]

        average_hr = (
            sum(heart_rates) / len(heart_rates)
        )

        # ----------------------------------------------------
        # Current timestamp
        # ----------------------------------------------------

        timestamp_ms = int(
            time.time() * 1000
        )

        # ----------------------------------------------------
        # Build insight
        # ----------------------------------------------------

        insight = {
            "user_id": user_id,
            "timestamp": timestamp_ms,
            "source": "hr_stream_processor",

            "result": {
                "average_heart_rate": round(
                    average_hr,
                    2,
                ),

                "samples": len(
                    heart_rates
                ),

                "window_seconds": WINDOW_SECONDS,
            },
        }

        # ----------------------------------------------------
        # Publish
        # ----------------------------------------------------

        self.producer.publish_insight(
            insight=insight,
            user_id=user_id,
        )

        logger.info(
            "HR insight published: "
            "user=%s average_hr=%.2f samples=%d",
            user_id,
            average_hr,
            len(heart_rates),
        )

    # ========================================================
    # Run
    # ========================================================

    def run(self) -> None:
        """
        Start the stream processor.
        """

        logger.info(
            "Starting HPIS sensor stream processor..."
        )

        logger.info(
            "Kafka input topic: %s",
            SENSORS_TOPIC,
        )

        logger.info(
            "Kafka output topic: %s",
            INSIGHTS_TOPIC,
        )

        logger.info(
            "Window size: %s seconds",
            WINDOW_SECONDS,
        )

        try:

            self.consumer.run(
                message_handler=self.process_event,
            )

        except KeyboardInterrupt:

            logger.info(
                "Stream processor interrupted."
            )

        finally:

            self.close()

    # ========================================================
    # Close
    # ========================================================

    def close(self) -> None:
        """
        Close Kafka producer.
        """

        logger.info(
            "Closing sensor stream processor..."
        )

        self.producer.close()

        logger.info(
            "Sensor stream processor closed."
        )


# ============================================================
# Main
# ============================================================

def main():

    processor = SensorStreamProcessor()

    processor.run()


if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(name)s | "
            "%(message)s"
        ),
    )

    main()