"""
Test consumer for HPIS insights.

This consumer is ONLY used to verify that the
stream processor successfully publishes messages
to hpis.insights.

Run from the project root:

python -m backend.consumers.test_insights_consumer
"""

import logging

from backend.events.kafka.consumer import KafkaConsumerService
from backend.events.kafka.topics import INSIGHTS_TOPIC


# ============================================================
# Configuration
# ============================================================

KAFKA_GROUP_ID = "hpis-insights-test-group"


# ============================================================
# Message handler
# ============================================================

def handle_insight(event: dict) -> None:
    """
    Handle one insight event received from Kafka.
    """

    print("\n" + "=" * 70)
    print("HPIS INSIGHT RECEIVED")
    print("=" * 70)

    print(f"Topic:     {event['topic']}")
    print(f"Partition: {event['partition']}")
    print(f"Offset:    {event['offset']}")
    print(f"Key:       {event['key']}")

    print("\nInsight payload:")

    print(event["value"])

    print("=" * 70)


# ============================================================
# Main
# ============================================================

def main():

    consumer = KafkaConsumerService(
        group_id=KAFKA_GROUP_ID,
        topics=[INSIGHTS_TOPIC],
    )

    try:

        consumer.run(
            message_handler=handle_insight,
        )

    except KeyboardInterrupt:

        print("\nStopping insights consumer...")

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