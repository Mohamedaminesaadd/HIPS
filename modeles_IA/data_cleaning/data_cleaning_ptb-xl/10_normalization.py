"""
==========================================================
Step 10 - PTB-XL ECG Normalization
==========================================================

Objective:

1. Load a PTB-XL ECG.
2. Apply band-pass filtering.
3. Normalize each ECG lead independently.
4. Verify mean and standard deviation.
5. Compare filtered vs normalized ECG.

Input:
    ptbxl/records500/

Output:
    Normalized ECG
==========================================================
"""

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import wfdb

from scipy.signal import butter, filtfilt


# ==========================================================
# CONFIGURATION
# ==========================================================

path =r"/home/mohamed-amine/Documents/PlatformIO/Projects/datasets/ptb-xl-a-large-publicly-available-electrocardiography-dataset-1.0.3"
PTBXL_DIR = Path(path)


DATABASE_PATH = (
    PTBXL_DIR / "ptbxl_database.csv"
)

ECG_INDEX = 0

FS = 500

LOWCUT = 0.5

HIGHCUT = 40.0

FILTER_ORDER = 4


# ==========================================================
# LOAD METADATA
# ==========================================================

print("=" * 70)
print("STEP 10 - ECG NORMALIZATION")
print("=" * 70)


df = pd.read_csv(
    DATABASE_PATH
)


# ==========================================================
# SELECT ECG
# ==========================================================

row = df.iloc[ECG_INDEX]

print("\nSelected ECG:")
print("ECG ID:", row["ecg_id"])
print("Patient ID:", row["patient_id"])
print("Path:", row["filename_hr"])


# ==========================================================
# BUILD PATH
# ==========================================================

ecg_path = (
    PTBXL_DIR /
    row["filename_hr"]
)


# ==========================================================
# LOAD ECG
# ==========================================================

record = wfdb.rdrecord(
    str(ecg_path)
)

signal = record.p_signal


print("\nRaw ECG shape:")
print(signal.shape)


# ==========================================================
# BAND-PASS FILTER
# ==========================================================

def bandpass_filter(
    signal,
    fs,
    lowcut,
    highcut,
    order=4
):
    """
    Apply zero-phase Butterworth
    band-pass filtering to each lead.
    """

    nyquist = 0.5 * fs

    low = lowcut / nyquist
    high = highcut / nyquist


    b, a = butter(
        order,
        [low, high],
        btype="band"
    )


    filtered = np.zeros_like(
        signal
    )


    for lead in range(
        signal.shape[1]
    ):

        filtered[:, lead] = filtfilt(
            b,
            a,
            signal[:, lead]
        )


    return filtered


# ==========================================================
# FILTER
# ==========================================================

filtered_signal = bandpass_filter(
    signal,
    fs=FS,
    lowcut=LOWCUT,
    highcut=HIGHCUT,
    order=FILTER_ORDER
)


# ==========================================================
# NORMALIZATION FUNCTION
# ==========================================================

def normalize_per_lead(
    signal
):
    """
    Z-score normalization for each ECG lead.

    Input:
        signal shape = (samples, leads)

    Output:
        normalized signal
        shape = (samples, leads)
    """

    mean = np.mean(
        signal,
        axis=0,
        keepdims=True
    )

    std = np.std(
        signal,
        axis=0,
        keepdims=True
    )


    normalized = (
        signal - mean
    ) / (
        std + 1e-8
    )


    return normalized


# ==========================================================
# NORMALIZE
# ==========================================================

normalized_signal = normalize_per_lead(
    filtered_signal
)


# ==========================================================
# VERIFY NORMALIZATION
# ==========================================================

print("\n" + "=" * 70)
print("NORMALIZATION CHECK")
print("=" * 70)


print(
    "\nLead statistics after normalization:"
)


for i, lead_name in enumerate(
    record.sig_name
):

    lead = normalized_signal[:, i]

    mean = np.mean(lead)

    std = np.std(lead)

    print(
        f"{lead_name:>4} | "
        f"mean = {mean: .6f} | "
        f"std = {std: .6f}"
    )


# ==========================================================
# GLOBAL INFORMATION
# ==========================================================

print("\nNormalized shape:")

print(
    normalized_signal.shape
)


print("\nGlobal min:")

print(
    normalized_signal.min()
)


print("\nGlobal max:")

print(
    normalized_signal.max()
)


# ==========================================================
# TIME AXIS
# ==========================================================

time = (
    np.arange(
        signal.shape[0]
    ) / FS
)


# ==========================================================
# VISUALIZE FILTERED VS NORMALIZED
# ==========================================================

lead_index = 1

lead_name = (
    record.sig_name[lead_index]
)


fig, axes = plt.subplots(
    2,
    1,
    figsize=(15, 8),
    sharex=True
)


# ----------------------------------------------------------
# Filtered
# ----------------------------------------------------------

axes[0].plot(
    time,
    filtered_signal[:, lead_index]
)

axes[0].set_title(
    f"Filtered ECG - Lead {lead_name}"
)

axes[0].set_ylabel(
    "Amplitude"
)

axes[0].grid(
    True,
    alpha=0.3
)


# ----------------------------------------------------------
# Normalized
# ----------------------------------------------------------

axes[1].plot(
    time,
    normalized_signal[:, lead_index]
)

axes[1].set_title(
    f"Normalized ECG - Lead {lead_name}"
)

axes[1].set_xlabel(
    "Time (seconds)"
)

axes[1].set_ylabel(
    "Normalized amplitude"
)

axes[1].grid(
    True,
    alpha=0.3
)


plt.tight_layout()

plt.show()