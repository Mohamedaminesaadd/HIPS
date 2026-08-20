"""
Reusable Kafka consumer for HPIS.

The FastAPI backend runs directly on the host machine,
therefore Kafka is accessed through localhost:9092.
"""

import json
import logging
from typing import Callable, Optional

from confluent_kafka import Consumer, KafkaError, KafkaException

from backend.events.kafka.config import KAFKA_CONSUMER_CONFIG


logger = logging.getLogger(__name__)


class KafkaConsumerService:
    """
    Generic reusable Kafka consumer.

    Responsibilities:
    - connect to Kafka
    - subscribe to topics
    - consume messages
    - deserialize JSON
    - handle Kafka errors
    - commit offsets
    - shutdown cleanly
    """

    def __init__(
        self,
        group_id: str,
        topics: list[str],
    ):
        """
        Parameters
        ----------
        group_id:
            Kafka consumer group.

        topics:
            List of Kafka topics to subscribe to.
        """

        config = KAFKA_CONSUMER_CONFIG.copy()

        # Each consumer must have a unique group depending
        # on its responsibility.
        config["group.id"] = group_id

        self._consumer = Consumer(config)

        self._topics = topics

        self._running = False

        logger.info(
            "Kafka consumer initialized: broker=%s group=%s",
            config["bootstrap.servers"],
            group_id,
        )

    # ========================================================
    # Subscribe
    # ========================================================

    def subscribe(self) -> None:
        """
        Subscribe to configured Kafka topics.
        """

        self._consumer.subscribe(self._topics)

        logger.info(
            "Subscribed to Kafka topics: %s",
            self._topics,
        )

    # ========================================================
    # Consume one message
    # ========================================================

    def consume(
        self,
        timeout: float = 1.0,
    ) -> Optional[dict]:
        """
        Consume one Kafka message.

        Returns:
            dict:
                Deserialized JSON message.

            None:
                If there is no message available yet.
        """

        message = self._consumer.poll(timeout)

        # ----------------------------------------------------
        # No message
        # ----------------------------------------------------

        if message is None:
            return None

        # ----------------------------------------------------
        # Kafka error
        # ----------------------------------------------------

        if message.error():

            # Partition reached end of available data.
            # This is not a fatal error.
            if message.error().code() == KafkaError._PARTITION_EOF:
                logger.debug(
                    "Reached end of partition: "
                    "topic=%s partition=%s offset=%s",
                    message.topic(),
                    message.partition(),
                    message.offset(),
                )

                return None

            logger.error(
                "Kafka consumer error: %s",
                message.error(),
            )

            return None

        # ----------------------------------------------------
        # Decode key
        # ----------------------------------------------------

        key = message.key()

        if key is not None:
            key = key.decode("utf-8")

        # ----------------------------------------------------
        # Decode value
        # ----------------------------------------------------

        try:
            value = message.value().decode("utf-8")

            data = json.loads(value)

        except (UnicodeDecodeError, json.JSONDecodeError) as exc:

            logger.error(
                "Failed to deserialize Kafka message: %s",
                exc,
            )

            # Commit the malformed message so that the
            # consumer does not get stuck on it forever.
            self.commit(message)

            return None

        # ----------------------------------------------------
        # Build event
        # ----------------------------------------------------

        event = {
            "key": key,
            "value": data,
            "topic": message.topic(),
            "partition": message.partition(),
            "offset": message.offset(),
            "timestamp": message.timestamp(),
        }

        logger.debug(
            "Kafka message received: "
            "topic=%s partition=%s offset=%s key=%s",
            message.topic(),
            message.partition(),
            message.offset(),
            key,
        )

        return event

    # ========================================================
    # Commit
    # ========================================================

    def commit(self, message=None) -> None:
        """
        Commit the processed Kafka message offset.
        """

        try:

            if message is not None:
                self._consumer.commit(
                    message=message,
                    asynchronous=False,
                )

            else:
                self._consumer.commit(
                    asynchronous=False,
                )

            logger.debug("Kafka offset committed.")

        except KafkaException as exc:

            logger.error(
                "Failed to commit Kafka offset: %s",
                exc,
            )

    # ========================================================
    # Run loop
    # ========================================================

    def run(
        self,
        message_handler: Callable[[dict], None],
    ) -> None:
        """
        Continuously consume Kafka messages.

        message_handler receives the decoded event.

        Example:

            def handler(event):
                print(event)

            consumer.run(handler)
        """

        self.subscribe()

        self._running = True

        logger.info("Kafka consumer started.")

        try:

            while self._running:

                event = self.consume(timeout=1.0)

                if event is None:
                    continue

                try:

                    # Process the event.
                    message_handler(event)

                    # Commit ONLY after successful processing.
                    self.commit()

                except Exception:

                    logger.exception(
                        "Error while processing Kafka message."
                    )

                    # Do NOT commit the offset.
                    #
                    # This means Kafka can redeliver the
                    # message after restart.
                    continue

        except KeyboardInterrupt:

            logger.info(
                "Kafka consumer interrupted by user."
            )

        finally:

            self.close()

    # ========================================================
    # Stop
    # ========================================================

    def stop(self) -> None:
        """
        Stop the consumer loop.
        """

        self._running = False

        logger.info("Stopping Kafka consumer...")

    # ========================================================
    # Close
    # ========================================================

    def close(self) -> None:
        """
        Close Kafka consumer and leave consumer group.
        """

        logger.info("Closing Kafka consumer...")

        self._consumer.close()

        logger.info("Kafka consumer closed.")