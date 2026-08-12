"""
==========================================================
Step 9 - PTB-XL ECG Preprocessing
==========================================================

Objective:

1. Load a PTB-XL ECG.
2. Apply a Butterworth band-pass filter.
3. Remove very low-frequency baseline drift.
4. Reduce high-frequency noise.
5. Compare raw vs filtered ECG.
6. Keep all 12 ECG leads.

Input:
    ptbxl/records500/

Output:
    Filtered ECG signal
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
print("STEP 9 - ECG PREPROCESSING")
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
# BUILD ECG PATH
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


print("\nRaw ECG:")
print("Sampling frequency:", record.fs)
print("Shape:", signal.shape)
print("Leads:", record.sig_name)


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
    Apply a zero-phase Butterworth
    band-pass filter to every ECG lead.
    """

    nyquist = 0.5 * fs

    low = lowcut / nyquist
    high = highcut / nyquist


    b, a = butter(
        order,
        [low, high],
        btype="band"
    )


    filtered_signal = np.zeros_like(
        signal
    )


    for lead in range(
        signal.shape[1]
    ):

        filtered_signal[:, lead] = (
            filtfilt(
                b,
                a,
                signal[:, lead]
            )
        )


    return filtered_signal


# ==========================================================
# APPLY FILTER
# ==========================================================

filtered_signal = bandpass_filter(
    signal=signal,
    fs=FS,
    lowcut=LOWCUT,
    highcut=HIGHCUT,
    order=FILTER_ORDER
)


# ==========================================================
# BASIC INFORMATION
# ==========================================================

print("\nFiltering:")
print("Low cutoff :", LOWCUT, "Hz")
print("High cutoff:", HIGHCUT, "Hz")
print("Order      :", FILTER_ORDER)

print(
    "\nFiltered shape:",
    filtered_signal.shape
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
# COMPARE RAW AND FILTERED SIGNAL
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
# Raw ECG
# ----------------------------------------------------------

axes[0].plot(
    time,
    signal[:, lead_index]
)

axes[0].set_title(
    f"Raw ECG - Lead {lead_name}"
)

axes[0].set_ylabel(
    "Amplitude"
)

axes[0].grid(
    True,
    alpha=0.3
)


# ----------------------------------------------------------
# Filtered ECG
# ----------------------------------------------------------

axes[1].plot(
    time,
    filtered_signal[:, lead_index]
)

axes[1].set_title(
    f"Filtered ECG - Lead {lead_name}"
)

axes[1].set_xlabel(
    "Time (seconds)"
)

axes[1].set_ylabel(
    "Amplitude"
)

axes[1].grid(
    True,
    alpha=0.3
)


plt.tight_layout()

plt.show()


# ==========================================================
# COMPARE ALL 12 LEADS
# ==========================================================

fig, axes = plt.subplots(
    12,
    1,
    figsize=(15, 22),
    sharex=True
)


for i in range(12):

    axes[i].plot(
        time,
        filtered_signal[:, i]
    )

    axes[i].set_ylabel(
        record.sig_name[i]
    )

    axes[i].grid(
        True,
        alpha=0.3
    )


axes[-1].set_xlabel(
    "Time (seconds)"
)


fig.suptitle(
    "Filtered PTB-XL ECG - 12 Leads",
    fontsize=16
)


plt.tight_layout()

plt.show()