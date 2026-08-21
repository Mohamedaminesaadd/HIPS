"""
Test RabbitMQ publisher.

Publishes one test AI task to the sleep queue.
"""

import logging

from backend.events.rabbitmq.connection import RabbitMQConnection
from backend.events.rabbitmq.publisher import RabbitMQPublisher


logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s | "
        "%(levelname)s | "
        "%(name)s | "
        "%(message)s"
    ),
)


def main():

    connection = RabbitMQConnection()

    try:
        connection.connect()

        publisher = RabbitMQPublisher(
            connection=connection
        )

        message = {
            "task": "sleep_analysis",
            "user_id": "test-user-001",
            "data": {
                "sleep_duration": 7.5,
                "sleep_quality": 85,
            },
        }

        publisher.publish(
            queue="hpis.ai.sleep",
            message=message,
        )

        print()
        print("RabbitMQ test message published!")
        print("Queue: hpis.ai.sleep")
        print("User: test-user-001")

    finally:
        connection.close()


if __name__ == "__main__":
    main()