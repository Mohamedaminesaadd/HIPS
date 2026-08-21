"""
RabbitMQ connection manager for HPIS.
"""

import logging

import pika

from backend.events.rabbitmq.config import (
    RABBITMQ_HOST,
    RABBITMQ_PORT,
    RABBITMQ_USER,
    RABBITMQ_PASSWORD,
    RABBITMQ_VHOST,
)


logger = logging.getLogger(__name__)


class RabbitMQConnection:
    """
    Manages a RabbitMQ connection and channel.
    """

    def __init__(self):

        self.connection = None
        self.channel = None

    # ========================================================
    # Connect
    # ========================================================

    def connect(self) -> None:

        logger.info(
            "Connecting to RabbitMQ at %s:%s",
            RABBITMQ_HOST,
            RABBITMQ_PORT,
        )

        credentials = pika.PlainCredentials(
            RABBITMQ_USER,
            RABBITMQ_PASSWORD,
        )

        parameters = pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            port=RABBITMQ_PORT,
            virtual_host=RABBITMQ_VHOST,
            credentials=credentials,
        )

        self.connection = (
            pika.BlockingConnection(
                parameters
            )
        )

        self.channel = (
            self.connection.channel()
        )

        logger.info(
            "Connected to RabbitMQ successfully."
        )

    # ========================================================
    # Get channel
    # ========================================================

    def get_channel(self):

        if self.channel is None:

            raise RuntimeError(
                "RabbitMQ is not connected."
            )

        return self.channel

    # ========================================================
    # Close
    # ========================================================

    def close(self) -> None:

        if (
            self.connection is not None
            and self.connection.is_open
        ):

            logger.info(
                "Closing RabbitMQ connection..."
            )

            self.connection.close()

            logger.info(
                "RabbitMQ connection closed."
            )

        self.connection = None
        self.channel = None