"""
RabbitMQ publisher for HPIS AI tasks.
"""

import json
import logging
from typing import Any

from backend.events.rabbitmq.connection import (
    RabbitMQConnection,
)

from backend.events.rabbitmq.queues import (
    STRESS_QUEUE,
    ECG_QUEUE,
    SLEEP_QUEUE,
)


logger = logging.getLogger(__name__)


class RabbitMQPublisher:
    """
    Publishes AI tasks to RabbitMQ queues.
    """

    def __init__(
        self,
        connection: RabbitMQConnection,
    ):

        self.connection = connection

        self.channel = (
            connection.get_channel()
        )

        # Declare queues
        self._declare_queues()

    # ========================================================
    # Queue declaration
    # ========================================================

    def _declare_queues(self):

        queues = [
            STRESS_QUEUE,
            ECG_QUEUE,
            SLEEP_QUEUE,
        ]

        for queue in queues:

            self.channel.queue_declare(
                queue=queue,
                durable=True,
            )

            logger.info(
                "RabbitMQ queue ready: %s",
                queue,
            )

    # ========================================================
    # Generic publish
    # ========================================================

    def publish(
        self,
        queue: str,
        message: dict[str, Any],
    ) -> None:

        body = json.dumps(
            message
        ).encode("utf-8")

        self.channel.basic_publish(
            exchange="",
            routing_key=queue,
            body=body,
            properties=(
                self._message_properties()
            ),
        )

        logger.info(
            "RabbitMQ task published: queue=%s",
            queue,
        )

    # ========================================================
    # Message properties
    # ========================================================

    @staticmethod
    def _message_properties():

        import pika

        return pika.BasicProperties(
            delivery_mode=2,
            content_type="application/json",
        )

    # ========================================================
    # Stress task
    # ========================================================

    def publish_stress_task(
        self,
        user_id: str,
        data: dict[str, Any],
    ) -> None:

        self.publish(
            queue=STRESS_QUEUE,
            message={
                "task": "stress_analysis",
                "user_id": user_id,
                "data": data,
            },
        )

    # ========================================================
    # ECG task
    # ========================================================

    def publish_ecg_task(
        self,
        user_id: str,
        data: dict[str, Any],
    ) -> None:

        self.publish(
            queue=ECG_QUEUE,
            message={
                "task": "ecg_analysis",
                "user_id": user_id,
                "data": data,
            },
        )

    # ========================================================
    # Sleep task
    # ========================================================

    def publish_sleep_task(
        self,
        user_id: str,
        data: dict[str, Any],
    ) -> None:

        self.publish(
            queue=SLEEP_QUEUE,
            message={
                "task": "sleep_analysis",
                "user_id": user_id,
                "data": data,
            },
        )