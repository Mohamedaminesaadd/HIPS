"""
Test Kafka producer for HPIS.

Run from the project root with:

python -m backend.events.kafka.test_producer
"""

import logging
import time

from backend.events.kafka.producer import KafkaProducerService


# ============================================================
# Logging
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)


def main():
    print("=" * 60)
    print("HPIS Kafka Producer Test")
    print("=" * 60)

    # --------------------------------------------------------
    # Create producer
    # --------------------------------------------------------

    producer = KafkaProducerService()

    # --------------------------------------------------------
    # Test message
    # --------------------------------------------------------

    user_id = "test-user-001"

    sensor_data = {
        "user_id": user_id,
        "device_id": "esp32-test-001",
        "timestamp": int(time.time() * 1000),

        "ecg": [
            2048,
            2050,
            2051,
            2050,
            2049,
            2052,
            2053,
            2051,
            2050,
            2048,
        ],

        "heart_rate": 75,
        "spo2": 98,
        "temperature": 36.8,

        "ppg": {
            "red": 51000,
            "ir": 61000,
        },

        "imu": {
            "acc": {
                "x": 0.1,
                "y": 0.2,
                "z": 9.8,
            },
            "gyro": {
                "x": 0.1,
                "y": 0.2,
                "z": 0.3,
            },
        },

        "battery": {
            "level": 90,
            "voltage": 4.0,
        },
    }

    print("\nPublishing test sensor event...")

    # --------------------------------------------------------
    # Publish
    # --------------------------------------------------------

    producer.publish_sensor_data(
        sensor_data=sensor_data,
        user_id=user_id,
    )

    print("Message queued successfully.")

    # --------------------------------------------------------
    # Flush
    # --------------------------------------------------------

    print("Waiting for Kafka delivery...")

    remaining = producer.flush(timeout=10)

    # --------------------------------------------------------
    # Result
    # --------------------------------------------------------

    if remaining == 0:
        print("\nKafka message delivered successfully!")
        print("Topic: hpis.sensors")
        print(f"Key: {user_id}")
    else:
        print(
            f"\nKafka delivery incomplete. "
            f"Remaining messages: {remaining}"
        )

    print("=" * 60)


if __name__ == "__main__":
    main()