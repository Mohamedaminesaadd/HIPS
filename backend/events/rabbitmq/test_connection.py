"""
Test RabbitMQ connection.
"""

import logging

from backend.events.rabbitmq.connection import (
    RabbitMQConnection,
)


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

        print()
        print(
            "RabbitMQ connection successful!"
        )

        print(
            f"Host: localhost"
        )

        print(
            f"Port: 5672"
        )

    finally:

        connection.close()


if __name__ == "__main__":

    main()