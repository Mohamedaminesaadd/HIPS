"""
==========================================================
Step 12 - PTB-XL Full Preprocessing Pipeline
==========================================================

This file merges everything from steps 02 -> 11 into ONE
pipeline whose final deliverable is:

    1. Clean metadata with multi-label diagnostic classes
       (NORM, MI, STTC, CD, HYP) as one-hot columns.
    2. Official train / validation / test split
       (strat_fold 1-8 / 9 / 10), leakage-checked.
    3. Saved split CSVs (data/processed/{train,val,test}.csv)
       ready to be consumed by a Dataset class.
    4. A PyTorch Dataset class (PTBXLDataset) that, for each
       sample:
            - loads the raw 12-lead ECG (wfdb)
            - band-pass filters it (0.5 - 40 Hz, Butterworth)
            - z-score normalizes it per lead
            - returns (signal_tensor, label_tensor)

Run this file once to build the CSVs. Then import
PTBXLDataset in your training script.
==========================================================
"""

from pathlib import Path
import ast

import numpy as np
import pandas as pd
import wfdb

from scipy.signal import butter, filtfilt

import torch
from torch.utils.data import Dataset


# ==========================================================
# CONFIGURATION
# ==========================================================

path = r"/home/mohamed-amine/Documents/PlatformIO/Projects/datasets/ptb-xl-a-large-publicly-available-electrocardiography-dataset-1.0.3"
PTBXL_DIR = Path(path)

DATABASE_PATH = PTBXL_DIR / "ptbxl_database.csv"
SCP_PATH = PTBXL_DIR / "scp_statements.csv"


OUTPUT_DIR = Path(r"/home/mohamed-amine/Documents/PlatformIO/Projects/datasets/data_cleanig")

TARGET_CLASSES = ["NORM", "MI", "STTC", "CD", "HYP"]

FS = 500
LOWCUT = 0.5
HIGHCUT = 40.0
FILTER_ORDER = 4

USE_HR = True  # True -> filename_hr (500Hz), False -> filename_lr (100Hz)


# ==========================================================
# 1. METADATA + SCP DECODING  (steps 02, 03, 04)
# ==========================================================

def load_metadata_with_classes():
    """
    Load ptbxl_database.csv, decode scp_codes, and attach
    one multi-hot column per TARGET_CLASSES diagnostic class.
    """

    df = pd.read_csv(DATABASE_PATH)
    scp = pd.read_csv(SCP_PATH, index_col=0)

    df["scp_codes"] = df["scp_codes"].apply(ast.literal_eval)

    def get_diagnostic_classes(scp_codes):
        classes = set()

        for code in scp_codes:
            if code not in scp.index:
                continue

            row = scp.loc[code]

            if row["diagnostic"] == 1:
                diagnostic_class = row["diagnostic_class"]

                if pd.notna(diagnostic_class):
                    classes.add(diagnostic_class)

        return sorted(classes)

    df["diagnostic_classes"] = df["scp_codes"].apply(
        get_diagnostic_classes
    )

    return df


def add_label_columns(df):
    """
    Step 05 equivalent: turn diagnostic_classes (list) into
    one binary column per TARGET_CLASSES, e.g. df["NORM"] = 0/1.
    Rows with no target class at all are dropped (no usable label).
    """

    for cls in TARGET_CLASSES:
        df[cls] = df["diagnostic_classes"].apply(
            lambda classes: 1 if cls in classes else 0
        )

    has_label = df[TARGET_CLASSES].sum(axis=1) > 0

    n_dropped = (~has_label).sum()

    if n_dropped > 0:
        print(f"[INFO] Dropping {n_dropped} ECGs with no target diagnostic class.")

    df = df[has_label].reset_index(drop=True)

    return df


# ==========================================================
# 2. TRAIN / VAL / TEST SPLIT  (step 11)
# ==========================================================

def split_and_save(df):

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    train_df = df[df["strat_fold"].between(1, 8)].copy()
    val_df = df[df["strat_fold"] == 9].copy()
    test_df = df[df["strat_fold"] == 10].copy()

    train_p = set(train_df["patient_id"])
    val_p = set(val_df["patient_id"])
    test_p = set(test_df["patient_id"])

    overlap = (
        len(train_p & val_p)
        + len(train_p & test_p)
        + len(val_p & test_p)
    )

    if overlap == 0:
        print("[OK] No patient leakage detected.")
    else:
        print("[WARNING] Patient overlap detected!")

    keep_cols = [
        "ecg_id",
        "patient_id",
        "age",
        "sex",
        "filename_lr",
        "filename_hr",
        "strat_fold",
    ] + TARGET_CLASSES

    train_df[keep_cols].to_csv(OUTPUT_DIR / "train.csv", index=False)
    val_df[keep_cols].to_csv(OUTPUT_DIR / "validation.csv", index=False)
    test_df[keep_cols].to_csv(OUTPUT_DIR / "test.csv", index=False)

    print(
        f"\nSaved -> train: {len(train_df)}, "
        f"val: {len(val_df)}, test: {len(test_df)}"
    )

    return train_df, val_df, test_df


# ==========================================================
# 3. SIGNAL PREPROCESSING  (steps 09, 10)
# ==========================================================

def bandpass_filter(signal, fs=FS, lowcut=LOWCUT, highcut=HIGHCUT, order=FILTER_ORDER):
    """
    Zero-phase Butterworth band-pass filter, applied per lead.
    signal shape: (samples, leads)
    """

    nyquist = 0.5 * fs
    low = lowcut / nyquist
    high = highcut / nyquist

    b, a = butter(order, [low, high], btype="band")

    filtered = np.zeros_like(signal)

    for lead in range(signal.shape[1]):
        filtered[:, lead] = filtfilt(b, a, signal[:, lead])

    return filtered


def normalize_per_lead(signal):
    """
    Z-score normalization, independently per lead.
    signal shape: (samples, leads)
    """

    mean = np.mean(signal, axis=0, keepdims=True)
    std = np.std(signal, axis=0, keepdims=True)

    return (signal - mean) / (std + 1e-8)


def load_and_preprocess_ecg(
    filename,
    use_hr=USE_HR
):
    """
    Load an ECG and apply:

        raw ECG
           ↓
        band-pass filter
           ↓
        per-lead normalization

    Returns:
        normalized signal
        lead names
        sampling frequency
    """

    ecg_path = PTBXL_DIR / filename

    record = wfdb.rdrecord(
        str(ecg_path)
    )

    signal = record.p_signal

    # Use the sampling frequency stored
    # in the WFDB header.
    fs = record.fs

    filtered = bandpass_filter(
        signal,
        fs=fs
    )

    normalized = normalize_per_lead(
        filtered
    )

    return (
        normalized,
        record.sig_name,
        fs
    )


# ==========================================================
# 4. PYTORCH DATASET CLASS
# ==========================================================

class PTBXLDataset(Dataset):
    """
    Ready-to-train PyTorch Dataset.

    Reads a split CSV produced by split_and_save() and, for
    each item, loads + band-pass filters + normalizes the raw
    ECG, then returns:

        signal_tensor : FloatTensor, shape (leads, samples)
        label_tensor  : FloatTensor, shape (n_classes,)  multi-hot

    Example
    -------
        train_ds = PTBXLDataset(OUTPUT_DIR / "train.csv")
        loader = DataLoader(train_ds, batch_size=32, shuffle=True)
    """

    def __init__(self, csv_path, use_hr=USE_HR, target_classes=None):

        self.df = pd.read_csv(csv_path)
        self.use_hr = use_hr
        self.target_classes = target_classes or TARGET_CLASSES

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):

        row = self.df.iloc[idx]

        filename = (
            row["filename_hr"]
            if self.use_hr
            else row["filename_lr"]
        )

        signal, _, _ = load_and_preprocess_ecg(
            filename,
            use_hr=self.use_hr
        )

        # --------------------------------------------------
        # Quality checks
        # --------------------------------------------------

        if signal.ndim != 2:
            raise ValueError(
                f"Expected 2D ECG signal, got {signal.shape}"
            )

        if signal.shape[1] != 12:
            raise ValueError(
                f"Expected 12 leads, got {signal.shape[1]}"
            )

        # --------------------------------------------------
        # (samples, leads)
        #        ↓
        # (leads, samples)
        # --------------------------------------------------

        signal = signal.T.astype(
            np.float32
        )

        # --------------------------------------------------
        # Labels
        # --------------------------------------------------

        label = row[
            self.target_classes
        ].to_numpy(
            dtype=np.float32
        )

        # --------------------------------------------------
        # Convert to PyTorch
        # --------------------------------------------------

        signal_tensor = torch.from_numpy(
            signal
        )

        label_tensor = torch.from_numpy(
            label
        )

        return (
            signal_tensor,
            label_tensor
        )


# ==========================================================
# MAIN - build the clean, split, ready-to-train dataset
# ==========================================================

if __name__ == "__main__":

    print("=" * 70)
    print("STEP 12 - BUILDING CLEAN, SPLIT, READY-TO-TRAIN DATASET")
    print("=" * 70)

    df = load_metadata_with_classes()

    original_count = len(df)

    df = add_label_columns(df)

    print(
        f"\nOriginal ECGs: {original_count}"
    )

    print(
        f"Usable ECGs: {len(df)}"
    )

    print(
        f"Removed ECGs: {original_count - len(df)}"
    )

    print("\nLabel distribution (positives per class):")
    print(df[TARGET_CLASSES].sum())

    train_df, val_df, test_df = split_and_save(df)

    # --------------------------------------------------
    # Sanity check: load ONE sample through the full
    # pipeline (load -> filter -> normalize -> tensor)
    # --------------------------------------------------

    print("\n" + "=" * 70)
    print("SANITY CHECK - ONE SAMPLE THROUGH THE DATASET CLASS")
    print("=" * 70)

    train_ds = PTBXLDataset(OUTPUT_DIR / "train.csv")

    signal_tensor, label_tensor = train_ds[0]

    print("Signal tensor shape:", signal_tensor.shape)  # (12, samples)
    print("Label tensor:", label_tensor, "->", TARGET_CLASSES)

    print(f"\nDataset ready: {len(train_ds)} train samples.")