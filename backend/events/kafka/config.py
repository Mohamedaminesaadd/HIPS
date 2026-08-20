"""
Kafka configuration for HPIS backend.

The FastAPI backend runs directly on the host machine,
therefore Kafka is accessed through localhost:9092.

Inside Docker containers, the address may be different
(e.g. kafka:29092), but that is NOT used here.
"""

import os


# ============================================================
# Kafka connection
# ============================================================

KAFKA_BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP_SERVERS",
    "localhost:9092"
)


# ============================================================
# Producer configuration
# ============================================================

KAFKA_PRODUCER_CONFIG = {
    "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,

    # Reliability
    "acks": "all",

    # Retry temporary broker/network failures
    "retries": 5,

    # Wait before retrying
    "retry.backoff.ms": 100,

    # Improve batching efficiency
    "linger.ms": 5,

    # Compression
    "compression.type": "snappy",

    # Maximum number of messages kept in the local queue
    "queue.buffering.max.messages": 100000,

    # Maximum time a message can remain queued
    "queue.buffering.max.ms": 1000,
}


# ============================================================
# Consumer configuration
# ============================================================

KAFKA_CONSUMER_CONFIG = {
    "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,

    "auto.offset.reset": "earliest",

    "enable.auto.commit": False,
}


# ============================================================
# Application name
# ============================================================

KAFKA_CLIENT_ID = os.getenv(
    "KAFKA_CLIENT_ID",
    "hpis-backend"
)