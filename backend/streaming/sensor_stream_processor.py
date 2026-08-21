"""
HPIS Sensor Stream Processor.

Flow:

    Kafka hpis.sensors
            ↓
    collect sensor events
            ↓
    30-second event-time windows
            ↓
    calculate HR statistics
            ↓
    Kafka hpis.insights

Current aggregation:
    - average heart rate
    - minimum heart rate
    - maximum heart rate
    - number of samples

Each user has independent windows.
"""

import logging
import time
from collections import defaultdict
from typing import Any

from backend.events.kafka.consumer import KafkaConsumerService
from backend.events.kafka.producer import KafkaProducerService
from backend.events.kafka.topics import (
    SENSORS_TOPIC,
)


logger = logging.getLogger(__name__)


# ============================================================
# Configuration
# ============================================================

KAFKA_GROUP_ID = "hpis-streams-group"

WINDOW_SECONDS = 30


class SensorStreamProcessor:
    """
    Processes sensor events from Kafka using fixed
    30-second windows per user.
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
        # Windows
        #
        # Structure:
        #
        # {
        #     "user123": {
        #         "window_start": 1000,
        #         "heart_rates": [72, 75, 80]
        #     }
        # }
        # ----------------------------------------------------

        self.user_windows: dict[
            str,
            dict[str, Any],
        ] = {}

    # ========================================================
    # Process event
    # ========================================================

    def process_event(
        self,
        event: dict[str, Any],
    ) -> None:
        """
        Process one Kafka sensor event.
        """

        sensor_data = event.get("value")

        if not sensor_data:
            logger.warning(
                "Received empty sensor event."
            )
            return

        # ----------------------------------------------------
        # User ID
        # ----------------------------------------------------

        user_id = sensor_data.get("user_id")

        if not user_id:

            logger.warning(
                "Ignoring event without user_id."
            )

            return

        # ----------------------------------------------------
        # Heart rate
        # ----------------------------------------------------

        heart_rate = sensor_data.get(
            "heart_rate"
        )

        if heart_rate is None:

            logger.debug(
                "No heart_rate for user=%s",
                user_id,
            )

            return

        try:

            heart_rate = float(
                heart_rate
            )

        except (
            TypeError,
            ValueError,
        ):

            logger.warning(
                "Invalid heart_rate: "
                "user=%s value=%s",
                user_id,
                heart_rate,
            )

            return

        # ----------------------------------------------------
        # Validate HR
        # ----------------------------------------------------

        if (
            heart_rate <= 0
            or heart_rate > 250
        ):

            logger.warning(
                "Ignoring unrealistic HR: "
                "user=%s value=%s",
                user_id,
                heart_rate,
            )

            return

        # ----------------------------------------------------
        # Event timestamp
        #
        # ESP32 timestamp is expected in milliseconds.
        # ----------------------------------------------------

        timestamp_ms = sensor_data.get(
            "timestamp"
        )

        if timestamp_ms is None:

            # Fallback to current server time
            timestamp_ms = int(
                time.time() * 1000
            )

        try:

            timestamp_ms = int(
                timestamp_ms
            )

        except (
            TypeError,
            ValueError,
        ):

            logger.warning(
                "Invalid timestamp: "
                "user=%s value=%s",
                user_id,
                timestamp_ms,
            )

            return

        # ----------------------------------------------------
        # Convert timestamp to seconds
        # ----------------------------------------------------

        event_time = (
            timestamp_ms / 1000.0
        )

        # ----------------------------------------------------
        # Determine window
        # ----------------------------------------------------

        window_start = (
            int(
                event_time
                // WINDOW_SECONDS
            )
            * WINDOW_SECONDS
        )

        window_end = (
            window_start
            + WINDOW_SECONDS
        )

        # ----------------------------------------------------
        # Get existing user window
        # ----------------------------------------------------

        current_window = (
            self.user_windows.get(
                user_id
            )
        )

        # ----------------------------------------------------
        # First event for user
        # ----------------------------------------------------

        if current_window is None:

            self._create_window(
                user_id=user_id,
                window_start=window_start,
                heart_rate=heart_rate,
            )

            logger.debug(
                "Created first window: "
                "user=%s start=%s end=%s",
                user_id,
                window_start,
                window_end,
            )

            return

        current_window_start = (
            current_window["window_start"]
        )

        # ----------------------------------------------------
        # Same window
        # ----------------------------------------------------

        if (
            window_start
            == current_window_start
        ):

            current_window[
                "heart_rates"
            ].append(
                heart_rate
            )

            logger.debug(
                "Added HR to window: "
                "user=%s hr=%s",
                user_id,
                heart_rate,
            )

            return

        # ----------------------------------------------------
        # New window detected
        # ----------------------------------------------------

        if window_start > current_window_start:

            # Finalize previous window
            self._finalize_window(
                user_id=user_id,
            )

            # Create new window
            self._create_window(
                user_id=user_id,
                window_start=window_start,
                heart_rate=heart_rate,
            )

            logger.debug(
                "Started new window: "
                "user=%s start=%s",
                user_id,
                window_start,
            )

            return

        # ----------------------------------------------------
        # Late / old event
        # ----------------------------------------------------

        logger.warning(
            "Ignoring late event: "
            "user=%s event_window=%s "
            "current_window=%s",
            user_id,
            window_start,
            current_window_start,
        )

    # ========================================================
    # Create window
    # ========================================================

    def _create_window(
        self,
        user_id: str,
        window_start: int,
        heart_rate: float,
    ) -> None:
        """
        Create a new window for a user.
        """

        self.user_windows[user_id] = {
            "window_start": window_start,
            "heart_rates": [
                heart_rate
            ],
        }

    # ========================================================
    # Finalize window
    # ========================================================

    def _finalize_window(
        self,
        user_id: str,
    ) -> None:
        """
        Calculate statistics for a completed window
        and publish an insight.
        """

        window = self.user_windows.get(
            user_id
        )

        if window is None:
            return

        heart_rates = window[
            "heart_rates"
        ]

        if not heart_rates:
            return

        # ----------------------------------------------------
        # Statistics
        # ----------------------------------------------------

        average_hr = (
            sum(heart_rates)
            / len(heart_rates)
        )

        minimum_hr = min(
            heart_rates
        )

        maximum_hr = max(
            heart_rates
        )

        window_start = (
            window["window_start"]
        )

        window_end = (
            window_start
            + WINDOW_SECONDS
        )

        # ----------------------------------------------------
        # Insight
        # ----------------------------------------------------

        insight = {
            "user_id": user_id,

            "timestamp": int(
                time.time() * 1000
            ),

            "source": (
                "hr_stream_processor"
            ),

            "window": {
                "start": (
                    window_start * 1000
                ),
                "end": (
                    window_end * 1000
                ),
                "duration_seconds": (
                    WINDOW_SECONDS
                ),
            },

            "result": {
                "average_heart_rate": round(
                    average_hr,
                    2,
                ),

                "minimum_heart_rate": round(
                    minimum_hr,
                    2,
                ),

                "maximum_heart_rate": round(
                    maximum_hr,
                    2,
                ),

                "samples": len(
                    heart_rates
                ),
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
            "Completed HR window: "
            "user=%s "
            "start=%s "
            "end=%s "
            "samples=%d "
            "average=%.2f "
            "min=%.2f "
            "max=%.2f",
            user_id,
            window_start,
            window_end,
            len(heart_rates),
            average_hr,
            minimum_hr,
            maximum_hr,
        )

        # ----------------------------------------------------
        # Remove completed window
        # ----------------------------------------------------

        del self.user_windows[
            user_id
        ]

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
            "Input topic: %s",
            SENSORS_TOPIC,
        )

        logger.info(
            "Consumer group: %s",
            KAFKA_GROUP_ID,
        )

        logger.info(
            "Window size: %s seconds",
            WINDOW_SECONDS,
        )

        try:

            self.consumer.run(
                message_handler=(
                    self.process_event
                ),
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

        # ----------------------------------------------------
        # Important:
        #
        # We intentionally do not finalize incomplete
        # windows here yet.
        #
        # A production implementation would persist
        # window state or handle graceful finalization.
        # ----------------------------------------------------

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