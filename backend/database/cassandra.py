"""
Cassandra connection manager for HPIS.

Cassandra is running inside Docker and exposes port 9042
to the host machine.
"""

import logging

from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider


logger = logging.getLogger(__name__)


# ============================================================
# Cassandra configuration
# ============================================================

CASSANDRA_HOST = "localhost"
CASSANDRA_PORT = 9042
CASSANDRA_KEYSPACE = "hpis"


class CassandraConnection:
    """
    Manages the Cassandra cluster connection and session.
    """

    def __init__(
        self,
        host: str = CASSANDRA_HOST,
        port: int = CASSANDRA_PORT,
    ):
        self.host = host
        self.port = port

        self.cluster = None
        self.session = None

    # ========================================================
    # Connect
    # ========================================================

    def connect(self) -> None:
        """
        Connect to Cassandra.
        """

        logger.info(
            "Connecting to Cassandra at %s:%s",
            self.host,
            self.port,
        )

        self.cluster = Cluster(
            [self.host],
            port=self.port,
        )

        self.session = self.cluster.connect(
            CASSANDRA_KEYSPACE
        )

        logger.info(
            "Connected to Cassandra keyspace: %s",
            CASSANDRA_KEYSPACE,
        )

    # ========================================================
    # Get session
    # ========================================================

    def get_session(self):
        """
        Return the active Cassandra session.
        """

        if self.session is None:
            raise RuntimeError(
                "Cassandra session is not initialized. "
                "Call connect() first."
            )

        return self.session

    # ========================================================
    # Close
    # ========================================================

    def close(self) -> None:
        """
        Close Cassandra connection.
        """

        if self.cluster is not None:
            logger.info("Closing Cassandra connection...")

            self.cluster.shutdown()

            self.cluster = None
            self.session = None

            logger.info("Cassandra connection closed.")