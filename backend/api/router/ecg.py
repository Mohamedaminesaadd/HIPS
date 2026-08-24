"""ECG transport endpoint for the cardiac-analysis pipeline."""

from math import isfinite

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, field_validator


ECG_SAMPLE_RATE = 250
ML_WINDOW_SECONDS = 30
ML_WINDOW_SAMPLES = ECG_SAMPLE_RATE * ML_WINDOW_SECONDS


class ECGData(BaseModel):
    fs: int = Field(gt=0)
    samples: list[float] = Field(min_length=1)

    @field_validator("samples")
    @classmethod
    def samples_must_be_finite(cls, samples: list[float]) -> list[float]:
        if not all(isfinite(sample) for sample in samples):
            raise ValueError("ECG samples must be finite numbers")
        return samples


class Vitals(BaseModel):
    hr: float | None = None
    spo2: float | None = None
    temperature: float | None = None


class ECGQuality(BaseModel):
    ecg_quality: float | None = None
    noise: float | None = None
    lead_off: bool = False


class ECGAnalysisRequest(BaseModel):
    subject_id: str = Field(min_length=1)
    timestamp: int = Field(gt=0)
    ecg: ECGData
    vitals: Vitals = Field(default_factory=Vitals)
    quality: ECGQuality = Field(default_factory=ECGQuality)


router = APIRouter(
    prefix="/api/ecg",
    tags=["ECG"],
)


@router.post(
    "/analyze",
    status_code=status.HTTP_202_ACCEPTED,
)
async def analyze_ecg(request: ECGAnalysisRequest) -> dict[str, object]:
    """Accept one raw 30-second ECG window for the future Model A pipeline."""

    if request.ecg.fs != ECG_SAMPLE_RATE:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Expected ECG sampling rate of {ECG_SAMPLE_RATE} Hz",
        )

    if len(request.ecg.samples) < ML_WINDOW_SAMPLES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Insufficient ECG samples: expected at least "
                f"{ML_WINDOW_SAMPLES}, received {len(request.ecg.samples)}"
            ),
        )

    if request.quality.lead_off:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="ECG lead is disconnected",
        )

    # Model A preprocessing and inference will be invoked here. The raw
    # waveform is deliberately left untouched so backend preprocessing remains
    # authoritative.
    return {
        "subject_id": request.subject_id,
        "status": "received",
        "ecg_samples": len(request.ecg.samples),
        "sampling_rate": request.ecg.fs,
        "window_seconds": len(request.ecg.samples) / request.ecg.fs,
        "signal_quality": request.quality.ecg_quality,
    }
