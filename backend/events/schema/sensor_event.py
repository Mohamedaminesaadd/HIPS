from typing import Optional

from pydantic import BaseModel, Field


class IMUVector(BaseModel):
    x: float
    y: float
    z: float


class IMUData(BaseModel):
    acc: IMUVector
    gyro: IMUVector


class PPGData(BaseModel):
    red: int
    ir: int


class BatteryData(BaseModel):
    level: float = Field(ge=0, le=100)
    voltage: float = Field(ge=0)


class SensorEvent(BaseModel):
    """
    Sensor packet received by the FastAPI backend.

    user_id is intentionally NOT included here.
    It should come from authentication/user context,
    not from an untrusted request body.
    """

    device_id: str = Field(min_length=1)

    timestamp: int

    ecg: list[float] = Field(default_factory=list)

    heart_rate: Optional[float] = Field(
        default=None,
        ge=0,
    )

    spo2: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
    )

    temperature: Optional[float] = None

    ppg: Optional[PPGData] = None

    imu: Optional[IMUData] = None

    battery: Optional[BatteryData] = None