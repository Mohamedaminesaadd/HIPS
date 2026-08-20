"""
HPIS Redis Insight Consumer.

Flow:

    Kafka hpis.insights
            ↓
    RedisInsightConsumer
            ↓
    RedisInsightService
            ↓
    Redis
"""

import logging

from backend.events.kafka.consumer import KafkaConsumerService
from backend.events.kafka.topics import INSIGHTS_TOPIC

from backend.database.redis import RedisConnection
from backend.services.redis_insight_service import (
    RedisInsightService,
)


logger = logging.getLogger(__name__)


# ============================================================
# Configuration
# ============================================================

KAFKA_GROUP_ID = "redis-insights-group"


class RedisInsightConsumer:
    """
    Consumes insight events from Kafka and stores the latest
    insight for each user in Redis.
    """

    def __init__(self):

        # ----------------------------------------------------
        # Redis connection
        # ----------------------------------------------------

        self.redis_connection = RedisConnection()

        self.redis_connection.connect()

        self.redis_service = RedisInsightService(
            redis_connection=self.redis_connection,
        )

        # ----------------------------------------------------
        # Kafka consumer
        # ----------------------------------------------------

        self.kafka_consumer = KafkaConsumerService(
            group_id=KAFKA_GROUP_ID,
            topics=[INSIGHTS_TOPIC],
        )

    # ========================================================
    # Handle insight
    # ========================================================

    def handle_insight(
        self,
        event: dict,
    ) -> None:
        """
        Process one Kafka insight event.
        """

        logger.info(
            "Received insight from Kafka: "
            "topic=%s partition=%s offset=%s",
            event["topic"],
            event["partition"],
            event["offset"],
        )

        # ----------------------------------------------------
        # Extract Kafka payload
        # ----------------------------------------------------

        insight = event["value"]

        # ----------------------------------------------------
        # Store in Redis
        # ----------------------------------------------------

        self.redis_service.store_latest_insight(
            insight=insight,
        )

        logger.info(
            "Insight successfully stored in Redis."
        )

    # ========================================================
    # Run
    # ========================================================

    def run(self) -> None:
        """
        Start the Redis insight consumer.
        """

        logger.info(
            "Starting Redis insight consumer..."
        )

        logger.info(
            "Kafka input topic: %s",
            INSIGHTS_TOPIC,
        )

        try:

            self.kafka_consumer.run(
                message_handler=self.handle_insight,
            )

        finally:

            self.close()

    # ========================================================
    # Close
    # ========================================================

    def close(self) -> None:
        """
        Close Redis resources.
        """

        logger.info(
            "Closing Redis insight consumer..."
        )

        self.redis_connection.close()

        logger.info(
            "Redis insight consumer closed."
        )


# ============================================================
# Main
# ============================================================

def main():

    consumer = RedisInsightConsumer()

    try:

        consumer.run()

    except KeyboardInterrupt:

        logger.info(
            "Redis insight consumer stopped."
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