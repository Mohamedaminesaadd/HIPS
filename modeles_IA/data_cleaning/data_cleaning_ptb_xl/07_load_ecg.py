from pathlib import Path

import pandas as pd
import wfdb


# ==========================================================
# Configuration
# ==========================================================
path =r"/home/mohamed-amine/Documents/PlatformIO/Projects/datasets/ptb-xl-a-large-publicly-available-electrocardiography-dataset-1.0.3"
PTBXL_DIR = Path(path)


DATABASE_PATH = PTBXL_DIR / "ptbxl_database.csv"


# ==========================================================
# 1. Load metadata
# ==========================================================

df = pd.read_csv(DATABASE_PATH)


# ==========================================================
# 2. Select the first ECG
# ==========================================================

row = df.iloc[0]


print("=" * 60)
print("SELECTED ECG")
print("=" * 60)

print("ECG ID:", row["ecg_id"])
print("Patient ID:", row["patient_id"])
print("Filename:", row["filename_hr"])


# ==========================================================
# 3. Build ECG path
# ==========================================================

ecg_path = PTBXL_DIR / row["filename_hr"]


print("\nECG path:")
print(ecg_path)


# ==========================================================
# 4. Check that the files exist
# ==========================================================

dat_file = Path(
    str(ecg_path) + ".dat"
)

hea_file = Path(
    str(ecg_path) + ".hea"
)


print("\nFiles:")

print(
    ".dat:",
    dat_file.exists(),
    dat_file
)

print(
    ".hea:",
    hea_file.exists(),
    hea_file
)


# ==========================================================
# 5. Load ECG using WFDB
# ==========================================================

record = wfdb.rdrecord(
    str(ecg_path)
)


# ==========================================================
# 6. Display information
# ==========================================================

print("\n" + "=" * 60)
print("ECG INFORMATION")
print("=" * 60)

print("Sampling frequency:", record.fs)

print("Number of signals:", record.n_sig)

print("Signal names:", record.sig_name)

print("Signal shape:", record.p_signal.shape)

print("Signal units:", record.units)