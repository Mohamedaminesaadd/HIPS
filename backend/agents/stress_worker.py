"""
RabbitMQ worker for the HPIS stress AI agent.

Flow:

RabbitMQ
    ↓
hpis.ai.stress
    ↓
StressAgent
    ↓
predict_stress()
    ↓
Kafka hpis.insights
"""

import json
import logging
import time

from backend.agents.agent_sleep import predict_stress

from backend.events.rabbitmq.connection import (
    RabbitMQConnection,
)

from backend.events.rabbitmq.queues import (
    STRESS_QUEUE,
)

from backend.events.kafka.producer import (
    KafkaProducerService,
)


logger = logging.getLogger(__name__)


class StressAgentWorker:
    """
    RabbitMQ worker that executes stress-analysis tasks.
    """

    def __init__(self):

        # ----------------------------------------------------
        # RabbitMQ
        # ----------------------------------------------------

        self.rabbitmq = RabbitMQConnection()

        # ----------------------------------------------------
        # Kafka
        # ----------------------------------------------------

        self.kafka_producer = (
            KafkaProducerService()
        )

    # ========================================================
    # Start
    # ========================================================

    def start(self):

        logger.info(
            "Starting stress AI agent worker..."
        )

        # Connect RabbitMQ
        self.rabbitmq.connect()

        channel = (
            self.rabbitmq.get_channel()
        )

        # ----------------------------------------------------
        # Queue
        # ----------------------------------------------------

        channel.queue_declare(
            queue=STRESS_QUEUE,
            durable=True,
        )

        # ----------------------------------------------------
        # Process one task at a time
        # ----------------------------------------------------

        channel.basic_qos(
            prefetch_count=1
        )

        # ----------------------------------------------------
        # Consumer
        # ----------------------------------------------------

        channel.basic_consume(
            queue=STRESS_QUEUE,
            on_message_callback=(
                self.handle_message
            ),
        )

        logger.info(
            "Stress agent listening on queue: %s",
            STRESS_QUEUE,
        )

        try:

            channel.start_consuming()

        except KeyboardInterrupt:

            logger.info(
                "Stress agent interrupted."
            )

        finally:

            self.close()

    # ========================================================
    # Handle RabbitMQ message
    # ========================================================

    def handle_message(
        self,
        channel,
        method,
        properties,
        body,
    ):

        try:

            # ------------------------------------------------
            # Decode message
            # ------------------------------------------------

            task = json.loads(
                body.decode("utf-8")
            )

            logger.info(
                "Received stress AI task."
            )

            user_id = task.get(
                "user_id"
            )

            payload = task.get(
                "data"
            )

            if not user_id:
                raise ValueError(
                    "Missing user_id."
                )

            if not payload:
                raise ValueError(
                    "Missing stress payload."
                )

            logger.info(
                "Processing stress task: "
                "user=%s",
                user_id,
            )

            # ------------------------------------------------
            # Run AI model
            # ------------------------------------------------

            result = predict_stress(
                payload
            )

            # ------------------------------------------------
            # Build Kafka insight
            # ------------------------------------------------

            insight = {
                "user_id": user_id,

                "timestamp": int(
                    time.time() * 1000
                ),

                "source": "stress_agent",

                "result": result,
            }

            # ------------------------------------------------
            # Publish result to Kafka
            # ------------------------------------------------

            self.kafka_producer.publish_insight(
                insight=insight,
                user_id=user_id,
            )

            logger.info(
                "Stress prediction published: "
                "user=%s label=%s probability=%.3f",
                user_id,
                result.get("label"),
                result.get(
                    "probability_stress",
                    0.0,
                ),
            )

            # ------------------------------------------------
            # ACK only after successful processing
            # ------------------------------------------------

            channel.basic_ack(
                delivery_tag=method.delivery_tag
            )

            logger.info(
                "Stress task acknowledged."
            )

        except Exception:

            logger.exception(
                "Failed to process stress AI task."
            )

            # ------------------------------------------------
            # Reject task
            #
            # For now we don't requeue automatically.
            # Later we'll add retry/dead-letter handling.
            # ------------------------------------------------

            channel.basic_nack(
                delivery_tag=method.delivery_tag,
                requeue=False,
            )

    # ========================================================
    # Close
    # ========================================================

    def close(self):

        logger.info(
            "Closing stress agent worker..."
        )

        self.kafka_producer.close()

        self.rabbitmq.close()

        logger.info(
            "Stress agent worker closed."
        )


# ============================================================
# Main
# ============================================================

def main():

    worker = StressAgentWorker()

    worker.start()


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