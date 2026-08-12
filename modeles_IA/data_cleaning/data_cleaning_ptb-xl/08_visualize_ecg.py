from pathlib import Path

import matplotlib.pyplot as plt
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

df = pd.read_csv(
    DATABASE_PATH
)


# ==========================================================
# 2. Select one ECG
# ==========================================================

row = df.iloc[0]


print("=" * 60)
print("ECG")
print("=" * 60)

print("ECG ID:", row["ecg_id"])
print("Patient ID:", row["patient_id"])
print("Path:", row["filename_hr"])


# ==========================================================
# 3. Build path
# ==========================================================

ecg_path = PTBXL_DIR / row["filename_hr"]


# ==========================================================
# 4. Load ECG
# ==========================================================

record = wfdb.rdrecord(
    str(ecg_path)
)


signal = record.p_signal


# ==========================================================
# 5. Display basic information
# ==========================================================

print("\nSampling frequency:")
print(record.fs)

print("\nSignal shape:")
print(signal.shape)

print("\nLeads:")
print(record.sig_name)


# ==========================================================
# 6. Plot all 12 leads
# ==========================================================

fig, axes = plt.subplots(
    12,
    1,
    figsize=(15, 20),
    sharex=True
)


for i in range(12):

    axes[i].plot(
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
    "Samples"
)


fig.suptitle(
    "PTB-XL 12-Lead ECG",
    fontsize=16
)


plt.tight_layout()

plt.show()