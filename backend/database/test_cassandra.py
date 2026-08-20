"""
Test Python → Cassandra connection.

Run from the project root:

python -m backend.database.test_cassandra
"""

import logging

from backend.database.cassandra import CassandraConnection


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)


def main():

    print("=" * 60)
    print("HPIS Cassandra Connection Test")
    print("=" * 60)

    cassandra = CassandraConnection()

    try:
        # ----------------------------------------------------
        # Connect
        # ----------------------------------------------------

        cassandra.connect()

        # ----------------------------------------------------
        # Get session
        # ----------------------------------------------------

        session = cassandra.get_session()

        # ----------------------------------------------------
        # Test query
        # ----------------------------------------------------

        row = session.execute(
            "SELECT keyspace_name "
            "FROM system_schema.keyspaces "
            "WHERE keyspace_name = 'hpis'"
        ).one()

        if row is not None:
            print("Cassandra connection successful!")
            print("Keyspace: hpis")
        else:
            print("Connected to Cassandra, but keyspace 'hpis' was not found.")

    except Exception as exc:

        print("Cassandra connection failed!")
        print(f"Error: {exc}")

        raise

    finally:

        cassandra.close()

    print("=" * 60)


if __name__ == "__main__":
    main()