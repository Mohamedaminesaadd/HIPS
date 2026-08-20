"""
Kafka consumer responsible for storing sensor events
from hpis.sensors into Cassandra.
"""

import logging

from backend.events.kafka.consumer import KafkaConsumerService
from backend.events.kafka.topics import SENSORS_TOPIC

from backend.database.cassandra import CassandraConnection
from backend.services.cassandra_sensor_service import (
    CassandraSensorService,
)


logger = logging.getLogger(__name__)


# ============================================================
# Configuration
# ============================================================

KAFKA_GROUP_ID = "cassandra-group"


# ============================================================
# Message handler
# ============================================================

class SensorStorageConsumer:
    """
    Consumes sensor events from Kafka and stores them
    in Cassandra.
    """

    def __init__(self):

        # ----------------------------------------------------
        # Cassandra
        # ----------------------------------------------------

        self.cassandra = CassandraConnection()

        self.cassandra.connect()

        self.cassandra_service = CassandraSensorService(
            cassandra=self.cassandra,
        )

        # ----------------------------------------------------
        # Kafka
        # ----------------------------------------------------

        self.kafka_consumer = KafkaConsumerService(
            group_id=KAFKA_GROUP_ID,
            topics=[SENSORS_TOPIC],
        )

    # ========================================================
    # Handle event
    # ========================================================

    def handle_event(
        self,
        event: dict,
    ) -> None:
        """
        Process one Kafka sensor event.
        """

        logger.info(
            "Received sensor event from Kafka: "
            "topic=%s partition=%s offset=%s",
            event["topic"],
            event["partition"],
            event["offset"],
        )

        # ----------------------------------------------------
        # Extract payload
        # ----------------------------------------------------

        sensor_data = event["value"]

        # ----------------------------------------------------
        # Store in Cassandra
        # ----------------------------------------------------

        self.cassandra_service.save_sensor_event(
            sensor_data=sensor_data,
        )

        logger.info(
            "Sensor event successfully stored in Cassandra."
        )

    # ========================================================
    # Run
    # ========================================================

    def run(self) -> None:
        """
        Start the Kafka → Cassandra consumer.
        """

        logger.info(
            "Starting sensor storage consumer..."
        )

        try:

            self.kafka_consumer.run(
                message_handler=self.handle_event,
            )

        finally:

            self.close()

    # ========================================================
    # Close
    # ========================================================

    def close(self) -> None:
        """
        Close Cassandra resources.
        """

        logger.info(
            "Closing sensor storage consumer..."
        )

        self.cassandra.close()

        logger.info(
            "Sensor storage consumer closed."
        )


# ============================================================
# Main
# ============================================================

def main():

    consumer = SensorStorageConsumer()

    try:

        consumer.run()

    except KeyboardInterrupt:

        logger.info(
            "Sensor storage consumer stopped."
        )

        consumer.close()


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