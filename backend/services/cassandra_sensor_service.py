"""
Cassandra service for HPIS sensor data.

This service is responsible for storing sensor events
inside Cassandra.

It does not know anything about Kafka or FastAPI.
"""

import logging
from datetime import datetime, timezone
from typing import Any

from backend.database.cassandra import CassandraConnection


logger = logging.getLogger(__name__)


class CassandraSensorService:
    """
    Service responsible for persisting sensor events
    into Cassandra.
    """

    def __init__(
        self,
        cassandra: CassandraConnection,
    ):
        """
        Initialize the Cassandra sensor service.
        """

        self.cassandra = cassandra
        self.session = cassandra.get_session()

    # ========================================================
    # Save sensor event
    # ========================================================

    def save_sensor_event(
        self,
        sensor_data: dict[str, Any],
    ) -> None:
        """
        Store one sensor event in Cassandra.
        """

        # ----------------------------------------------------
        # User ID
        # ----------------------------------------------------

        user_id = sensor_data.get("user_id")

        if not user_id:
            raise ValueError(
                "Sensor event is missing user_id."
            )

        # ----------------------------------------------------
        # Timestamp
        # ----------------------------------------------------

        timestamp_ms = sensor_data.get("timestamp")

        if timestamp_ms is None:
            raise ValueError(
                "Sensor event is missing timestamp."
            )

        event_datetime = datetime.fromtimestamp(
            timestamp_ms / 1000,
            tz=timezone.utc,
        )

        event_date = event_datetime.date()

        # ----------------------------------------------------
        # Device
        # ----------------------------------------------------

        device_id = sensor_data.get("device_id")

        # ----------------------------------------------------
        # ECG
        # ----------------------------------------------------

        ecg = sensor_data.get("ecg") or []

        # ----------------------------------------------------
        # Vitals
        # ----------------------------------------------------

        heart_rate = sensor_data.get("heart_rate")

        spo2 = sensor_data.get("spo2")

        temperature = sensor_data.get("temperature")

        # ----------------------------------------------------
        # PPG
        # ----------------------------------------------------

        ppg = sensor_data.get("ppg") or {}

        ppg_red = ppg.get("red")

        ppg_ir = ppg.get("ir")

        # ----------------------------------------------------
        # IMU
        # ----------------------------------------------------

        imu = sensor_data.get("imu") or {}

        acc = imu.get("acc") or {}

        gyro = imu.get("gyro") or {}

        acc_x = acc.get("x")
        acc_y = acc.get("y")
        acc_z = acc.get("z")

        gyro_x = gyro.get("x")
        gyro_y = gyro.get("y")
        gyro_z = gyro.get("z")

        # ----------------------------------------------------
        # Battery
        # ----------------------------------------------------

        battery = sensor_data.get("battery") or {}

        battery_level = battery.get("level")

        battery_voltage = battery.get("voltage")

        # ----------------------------------------------------
        # Cassandra query
        # ----------------------------------------------------

        query = """
            INSERT INTO hpis.sensor_data (
                user_id,
                date,
                timestamp,
                device_id,
                ecg,
                heart_rate,
                spo2,
                temperature,
                ppg_red,
                ppg_ir,
                acc_x,
                acc_y,
                acc_z,
                gyro_x,
                gyro_y,
                gyro_z,
                battery_level,
                battery_voltage
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
        """

        # ----------------------------------------------------
        # Execute query
        # ----------------------------------------------------

        self.session.execute(
            query,
            (
                user_id,
                event_date,
                event_datetime,
                device_id,
                ecg,
                heart_rate,
                spo2,
                temperature,
                ppg_red,
                ppg_ir,
                acc_x,
                acc_y,
                acc_z,
                gyro_x,
                gyro_y,
                gyro_z,
                battery_level,
                battery_voltage,
            ),
        )

        logger.info(
            "Sensor event stored in Cassandra: "
            "user_id=%s timestamp=%s",
            user_id,
            event_datetime,
        )