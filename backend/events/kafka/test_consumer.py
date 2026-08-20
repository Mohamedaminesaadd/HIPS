"""
Test consumer for HPIS Kafka.

Run from the project root:

python -m backend.events.kafka.test_consumer
"""

import logging

from backend.events.kafka.consumer import KafkaConsumerService
from backend.events.kafka.topics import SENSORS_TOPIC


# ============================================================
# Logging
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)


# ============================================================
# Message handler
# ============================================================

def handle_sensor_event(event: dict) -> None:
    """
    Handle a sensor event received from Kafka.
    """

    print("\n" + "=" * 60)
    print("SENSOR EVENT RECEIVED")
    print("=" * 60)

    print(f"Topic:     {event['topic']}")
    print(f"Partition: {event['partition']}")
    print(f"Offset:    {event['offset']}")
    print(f"Key:       {event['key']}")

    print("\nPayload:")

    print(event["value"])

    print("=" * 60)


# ============================================================
# Main
# ============================================================

def main():

    consumer = KafkaConsumerService(
        group_id="hpis-test-consumer",
        topics=[SENSORS_TOPIC],
    )

    consumer.run(handle_sensor_event)


if __name__ == "__main__":
    main()