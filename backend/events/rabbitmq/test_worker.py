"""
Test RabbitMQ consumer.

Receives AI tasks from the sleep queue
and prints them.
"""

import json
import logging

from backend.events.rabbitmq.connection import RabbitMQConnection
from backend.events.rabbitmq.queues import SLEEP_QUEUE


logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s | "
        "%(levelname)s | "
        "%(name)s | "
        "%(message)s"
    ),
)


logger = logging.getLogger(__name__)


def handle_message(
    channel,
    method,
    properties,
    body,
):
    """
    Handle one RabbitMQ message.
    """

    try:

        message = json.loads(
            body.decode("utf-8")
        )

        logger.info(
            "Received RabbitMQ task:"
        )

        logger.info(
            "Task: %s",
            message.get("task"),
        )

        logger.info(
            "User: %s",
            message.get("user_id"),
        )

        logger.info(
            "Data: %s",
            message.get("data"),
        )

        print()
        print("=" * 60)
        print("RABBITMQ TEST MESSAGE")
        print("=" * 60)
        print(json.dumps(
            message,
            indent=4,
        ))
        print("=" * 60)

        # Acknowledge message
        channel.basic_ack(
            delivery_tag=method.delivery_tag
        )

    except Exception:

        logger.exception(
            "Failed to process RabbitMQ message."
        )

        # Reject and don't requeue for this test
        channel.basic_nack(
            delivery_tag=method.delivery_tag,
            requeue=False,
        )


def main():

    connection = RabbitMQConnection()

    try:

        connection.connect()

        channel = connection.get_channel()

        # Make sure queue exists
        channel.queue_declare(
            queue=SLEEP_QUEUE,
            durable=True,
        )

        # Only give one task at a time
        channel.basic_qos(
            prefetch_count=1
        )

        channel.basic_consume(
            queue=SLEEP_QUEUE,
            on_message_callback=handle_message,
        )

        print()
        print("=" * 60)
        print("RabbitMQ Test Worker")
        print("=" * 60)
        print(
            f"Listening on: {SLEEP_QUEUE}"
        )
        print("Waiting for messages...")
        print("Press CTRL+C to stop.")
        print("=" * 60)

        channel.start_consuming()

    except KeyboardInterrupt:

        print()
        print("Stopping RabbitMQ test worker...")

    finally:

        connection.close()


if __name__ == "__main__":
    main()