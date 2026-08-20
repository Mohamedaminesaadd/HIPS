"""
Test Python → Redis connection.

Run:

python -m backend.database.test_redis
"""

import logging

from backend.database.redis import RedisConnection


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

    print("=" * 60)
    print("HPIS Redis Connection Test")
    print("=" * 60)

    redis_connection = RedisConnection()

    try:

        redis_connection.connect()

        client = redis_connection.get_client()

        # ----------------------------------------------------
        # Test SET
        # ----------------------------------------------------

        client.set(
            "hpis:test",
            "redis-working",
        )

        # ----------------------------------------------------
        # Test GET
        # ----------------------------------------------------

        value = client.get(
            "hpis:test"
        )

        print(
            f"Redis test value: {value}"
        )

        if value == "redis-working":

            print(
                "Redis connection successful!"
            )

        else:

            raise RuntimeError(
                "Redis returned an unexpected value."
            )

    except Exception as exc:

        print(
            "Redis connection failed!"
        )

        print(
            f"Error: {exc}"
        )

        raise

    finally:

        redis_connection.close()

    print("=" * 60)


if __name__ == "__main__":
    main()