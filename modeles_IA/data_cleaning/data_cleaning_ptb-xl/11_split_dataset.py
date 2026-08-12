"""
==========================================================
Step 11 - PTB-XL Train / Validation / Test Split
==========================================================

Objective:

1. Load PTB-XL metadata.
2. Inspect strat_fold.
3. Use the official PTB-XL split.
4. Create train / validation / test DataFrames.
5. Verify patient leakage.
6. Save the split metadata.

Official PTB-XL recommendation:

    folds 1-8  -> training
    fold 9     -> validation
    fold 10    -> test
==========================================================
"""

from pathlib import Path

import pandas as pd


# ==========================================================
# CONFIGURATION
# ==========================================================


path =r"/home/mohamed-amine/Documents/PlatformIO/Projects/datasets/ptb-xl-a-large-publicly-available-electrocardiography-dataset-1.0.3"
PTBXL_DIR = Path(path)

DATABASE_PATH = (
    PTBXL_DIR / "ptbxl_database.csv"
)

OUTPUT_DIR = Path(
    "data/processed"
)


# ==========================================================
# CREATE OUTPUT DIRECTORY
# ==========================================================

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ==========================================================
# LOAD METADATA
# ==========================================================

print("=" * 70)
print("STEP 11 - PTB-XL DATASET SPLIT")
print("=" * 70)


df = pd.read_csv(
    DATABASE_PATH
)


print("\nTotal ECG recordings:")
print(len(df))


print("\nTotal patients:")
print(df["patient_id"].nunique())


# ==========================================================
# CHECK strat_fold
# ==========================================================

print("\n" + "=" * 70)
print("STRATIFIED FOLDS")
print("=" * 70)


print(
    df["strat_fold"]
    .value_counts()
    .sort_index()
)


# ==========================================================
# CREATE SPLITS
# ==========================================================

train_df = df[
    df["strat_fold"].between(1, 8)
].copy()


val_df = df[
    df["strat_fold"] == 9
].copy()


test_df = df[
    df["strat_fold"] == 10
].copy()


# ==========================================================
# DISPLAY SIZES
# ==========================================================

print("\n" + "=" * 70)
print("SPLIT SIZES")
print("=" * 70)


print(
    f"Train ECGs      : {len(train_df)}"
)

print(
    f"Validation ECGs : {len(val_df)}"
)

print(
    f"Test ECGs       : {len(test_df)}"
)


print(
    f"Total           : "
    f"{len(train_df) + len(val_df) + len(test_df)}"
)


# ==========================================================
# PATIENT COUNTS
# ==========================================================

print("\n" + "=" * 70)
print("PATIENT COUNTS")
print("=" * 70)


print(
    "Train patients      :",
    train_df["patient_id"].nunique()
)

print(
    "Validation patients :",
    val_df["patient_id"].nunique()
)

print(
    "Test patients       :",
    test_df["patient_id"].nunique()
)


# ==========================================================
# PATIENT LEAKAGE CHECK
# ==========================================================

print("\n" + "=" * 70)
print("PATIENT LEAKAGE CHECK")
print("=" * 70)


train_patients = set(
    train_df["patient_id"]
)

val_patients = set(
    val_df["patient_id"]
)

test_patients = set(
    test_df["patient_id"]
)


train_val_overlap = (
    train_patients &
    val_patients
)


train_test_overlap = (
    train_patients &
    test_patients
)


val_test_overlap = (
    val_patients &
    test_patients
)


print(
    "Train ∩ Validation:",
    len(train_val_overlap)
)

print(
    "Train ∩ Test:",
    len(train_test_overlap)
)

print(
    "Validation ∩ Test:",
    len(val_test_overlap)
)


# ==========================================================
# FINAL LEAKAGE RESULT
# ==========================================================

if (
    len(train_val_overlap) == 0
    and
    len(train_test_overlap) == 0
    and
    len(val_test_overlap) == 0
):

    print(
        "\n[OK] No patient leakage detected."
    )

else:

    print(
        "\n[WARNING] Patient overlap detected!"
    )


# ==========================================================
# SAVE SPLITS
# ==========================================================

train_path = (
    OUTPUT_DIR /
    "train.csv"
)

val_path = (
    OUTPUT_DIR /
    "validation.csv"
)

test_path = (
    OUTPUT_DIR /
    "test.csv"
)


train_df.to_csv(
    train_path,
    index=False
)

val_df.to_csv(
    val_path,
    index=False
)

test_df.to_csv(
    test_path,
    index=False
)


# ==========================================================
# FINAL OUTPUT
# ==========================================================

print("\n" + "=" * 70)
print("FILES SAVED")
print("=" * 70)


print(
    "Train:",
    train_path
)

print(
    "Validation:",
    val_path
)

print(
    "Test:",
    test_path
)