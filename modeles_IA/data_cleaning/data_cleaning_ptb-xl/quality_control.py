"""
==========================================================
Step 8 - PTB-XL ECG Quality Control
==========================================================

Objective:
    1. Load an ECG from PTB-XL.
    2. Verify its structure.
    3. Check for invalid numerical values.
    4. Check whether the signal is flat.
    5. Check every ECG lead.
    6. Display useful signal statistics.
    7. Visualize all 12 ECG leads.

Input:
    ptbxl/ptbxl_database.csv
    ptbxl/records500/

Output:
    Quality-control report
    12-lead ECG visualization
==========================================================
"""

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import wfdb


# ==========================================================
# CONFIGURATION
# ==========================================================

path =r"/home/mohamed-amine/Documents/PlatformIO/Projects/datasets/ptb-xl-a-large-publicly-available-electrocardiography-dataset-1.0.3"
PTBXL_DIR = Path(path)


DATABASE_PATH = PTBXL_DIR / "ptbxl_database.csv"

# ECG index to inspect
ECG_INDEX = 0

# PTB-XL high-resolution sampling frequency
EXPECTED_FS = 500

# Expected signal dimensions
EXPECTED_LEADS = 12
EXPECTED_SAMPLES = 5000

# Threshold for detecting an almost-flat signal
FLAT_THRESHOLD = 1e-8


# ==========================================================
# QUALITY CONTROL FUNCTION
# ==========================================================

def check_ecg_quality(
    signal,
    sampling_frequency,
    lead_names
):
    """
    Perform basic quality control on an ECG signal.

    Parameters
    ----------
    signal : np.ndarray
        ECG signal with shape (samples, leads).

    sampling_frequency : float
        ECG sampling frequency.

    lead_names : list
        Names of the ECG leads.

    Returns
    -------
    valid : bool
        True if the ECG passes basic QC.

    problems : list
        List of detected problems.
    """

    problems = []


    # ------------------------------------------------------
    # 1. Check dimensions
    # ------------------------------------------------------

    if signal.ndim != 2:

        problems.append(
            f"Signal must be 2D, "
            f"but got {signal.ndim}D"
        )

    else:

        n_samples, n_leads = signal.shape

        if n_leads != EXPECTED_LEADS:

            problems.append(
                f"Expected {EXPECTED_LEADS} leads, "
                f"got {n_leads}"
            )

        if n_samples != EXPECTED_SAMPLES:

            problems.append(
                f"Expected approximately "
                f"{EXPECTED_SAMPLES} samples, "
                f"got {n_samples}"
            )


    # ------------------------------------------------------
    # 2. Check sampling frequency
    # ------------------------------------------------------

    if sampling_frequency != EXPECTED_FS:

        problems.append(
            f"Expected sampling frequency "
            f"{EXPECTED_FS} Hz, "
            f"got {sampling_frequency} Hz"
        )


    # ------------------------------------------------------
    # 3. Check NaN
    # ------------------------------------------------------

    nan_count = np.isnan(signal).sum()

    if nan_count > 0:

        problems.append(
            f"Signal contains "
            f"{nan_count} NaN values"
        )


    # ------------------------------------------------------
    # 4. Check infinity
    # ------------------------------------------------------

    inf_count = np.isinf(signal).sum()

    if inf_count > 0:

        problems.append(
            f"Signal contains "
            f"{inf_count} infinite values"
        )


    # ------------------------------------------------------
    # 5. Check completely flat signal
    # ------------------------------------------------------

    global_std = np.std(signal)

    if global_std < FLAT_THRESHOLD:

        problems.append(
            "Signal is almost completely flat"
        )


    # ------------------------------------------------------
    # 6. Check every lead
    # ------------------------------------------------------

    lead_results = []

    for i, lead_name in enumerate(lead_names):

        lead = signal[:, i]

        lead_min = np.min(lead)
        lead_max = np.max(lead)
        lead_mean = np.mean(lead)
        lead_std = np.std(lead)

        lead_results.append(
            {
                "lead": lead_name,
                "min": lead_min,
                "max": lead_max,
                "mean": lead_mean,
                "std": lead_std,
            }
        )

        # Check flat individual lead

        if lead_std < FLAT_THRESHOLD:

            problems.append(
                f"Lead {lead_name} "
                f"is almost flat"
            )


    # ------------------------------------------------------
    # 7. Final result
    # ------------------------------------------------------

    valid = len(problems) == 0

    return valid, problems, lead_results


# ==========================================================
# LOAD METADATA
# ==========================================================

print("=" * 70)
print("STEP 8 - PTB-XL ECG QUALITY CONTROL")
print("=" * 70)


print("\nLoading metadata...")

df = pd.read_csv(
    DATABASE_PATH
)

print(
    f"Total ECG recordings: {len(df)}"
)


# ==========================================================
# SELECT ECG
# ==========================================================

if ECG_INDEX < 0 or ECG_INDEX >= len(df):

    raise IndexError(
        f"ECG_INDEX={ECG_INDEX} is outside "
        f"the dataset range."
    )


row = df.iloc[ECG_INDEX]


print("\n" + "=" * 70)
print("SELECTED ECG")
print("=" * 70)

print(
    f"ECG ID      : {row['ecg_id']}"
)

print(
    f"Patient ID  : {row['patient_id']}"
)

print(
    f"Age         : {row['age']}"
)

print(
    f"Sex         : {row['sex']}"
)

print(
    f"Signal path : {row['filename_hr']}"
)

print(
    f"SCP codes   : {row['scp_codes']}"
)


# ==========================================================
# BUILD ECG PATH
# ==========================================================

ecg_path = PTBXL_DIR / row["filename_hr"]


print("\n" + "=" * 70)
print("FILE CHECK")
print("=" * 70)


dat_file = Path(
    str(ecg_path) + ".dat"
)

hea_file = Path(
    str(ecg_path) + ".hea"
)


print(
    f".dat file : {dat_file}"
)

print(
    f"Exists    : {dat_file.exists()}"
)


print(
    f".hea file : {hea_file}"
)

print(
    f"Exists    : {hea_file.exists()}"
)


if not dat_file.exists():

    raise FileNotFoundError(
        f"DAT file not found:\n{dat_file}"
    )


if not hea_file.exists():

    raise FileNotFoundError(
        f"HEA file not found:\n{hea_file}"
    )


# ==========================================================
# LOAD ECG
# ==========================================================

print("\n" + "=" * 70)
print("LOADING ECG")
print("=" * 70)


record = wfdb.rdrecord(
    str(ecg_path)
)


signal = record.p_signal


# ==========================================================
# BASIC INFORMATION
# ==========================================================

print(
    f"Sampling frequency : {record.fs} Hz"
)

print(
    f"Number of signals  : {record.n_sig}"
)

print(
    f"Signal shape       : {signal.shape}"
)

print(
    f"Signal names       : {record.sig_name}"
)

print(
    f"Signal units       : {record.units}"
)


# ==========================================================
# QUALITY CONTROL
# ==========================================================

print("\n" + "=" * 70)
print("QUALITY CONTROL")
print("=" * 70)


valid, problems, lead_results = check_ecg_quality(
    signal=signal,
    sampling_frequency=record.fs,
    lead_names=record.sig_name,
)


# ==========================================================
# GLOBAL STATISTICS
# ==========================================================

print("\nGlobal statistics:")

print(
    f"Minimum value : {np.min(signal):.6f}"
)

print(
    f"Maximum value : {np.max(signal):.6f}"
)

print(
    f"Mean value    : {np.mean(signal):.6f}"
)

print(
    f"Std value     : {np.std(signal):.6f}"
)

print(
    f"NaN count     : {np.isnan(signal).sum()}"
)

print(
    f"Inf count     : {np.isinf(signal).sum()}"
)


# ==========================================================
# LEAD STATISTICS
# ==========================================================

print("\n" + "=" * 70)
print("LEAD STATISTICS")
print("=" * 70)


print(
    f"{'Lead':>5} "
    f"{'Min':>12} "
    f"{'Max':>12} "
    f"{'Mean':>12} "
    f"{'Std':>12}"
)

print("-" * 65)


for result in lead_results:

    print(
        f"{result['lead']:>5} "
        f"{result['min']:>12.6f} "
        f"{result['max']:>12.6f} "
        f"{result['mean']:>12.6f} "
        f"{result['std']:>12.6f}"
    )


# ==========================================================
# FINAL QC RESULT
# ==========================================================

print("\n" + "=" * 70)
print("FINAL QUALITY RESULT")
print("=" * 70)


if valid:

    print("STATUS: VALID")

    print(
        "The ECG passed all basic quality checks."
    )

else:

    print("STATUS: INVALID")

    print("\nProblems detected:")

    for problem in problems:

        print(
            f"  - {problem}"
        )


# ==========================================================
# TIME AXIS
# ==========================================================

time = np.arange(
    signal.shape[0]
) / record.fs


# ==========================================================
# VISUALIZE ALL 12 LEADS
# ==========================================================

print("\nDisplaying ECG...")


fig, axes = plt.subplots(
    EXPECTED_LEADS,
    1,
    figsize=(16, 22),
    sharex=True
)


for i in range(EXPECTED_LEADS):

    axes[i].plot(
        time,
        signal[:, i]
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
    f"PTB-XL ECG {row['ecg_id']} - 12 Leads",
    fontsize=16
)


plt.tight_layout()

plt.show()