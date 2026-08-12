"""
==========================================================
Step 13 - PTB-XL DataLoaders
==========================================================

Objective:

1. Load train.csv
2. Load validation.csv
3. Load test.csv
4. Create PTBXLDataset for each split
5. Create DataLoaders
6. Verify batch shapes

Expected:

    One ECG:
        [12, 5000]

    One batch:
        [BATCH_SIZE, 12, 5000]

    Labels:
        [BATCH_SIZE, 5]
==========================================================
"""

from pathlib import Path

import torch
from torch.utils.data import DataLoader, Dataset
import numpy as np
import pandas as pd
from data_cleaning.data_cleaning_ptb_xl.ptb_dataset import PTBXLDataset

# ==========================================================
# CONFIGURATION
# ==========================================================


path =r"/home/mohamed-amine/Documents/PlatformIO/Projects/datasets/data_cleanig/data_cleaning_ptb_xl"

DATA_DIR = Path(path)

BATCH_SIZE = 32

NUM_WORKERS = 0

PIN_MEMORY = torch.cuda.is_available()


# ==========================================================
# CREATE DATASETS
# ==========================================================

def create_datasets():

    train_dataset = PTBXLDataset(
        DATA_DIR / "train.csv",
        use_hr=True
    )

    validation_dataset = PTBXLDataset(
        DATA_DIR / "validation.csv",
        use_hr=True
    )

    test_dataset = PTBXLDataset(
        DATA_DIR / "test.csv",
        use_hr=True
    )

    return (
        train_dataset,
        validation_dataset,
        test_dataset
    )


# ==========================================================
# CREATE DATALOADERS
# ==========================================================

def create_dataloaders():

    (
        train_dataset,
        validation_dataset,
        test_dataset
    ) = create_datasets()


    train_loader = DataLoader(
        train_dataset,
        batch_size=BATCH_SIZE,
        shuffle=True,
        num_workers=NUM_WORKERS,
        pin_memory=PIN_MEMORY
    )


    validation_loader = DataLoader(
        validation_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=NUM_WORKERS,
        pin_memory=PIN_MEMORY
    )


    test_loader = DataLoader(
        test_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=NUM_WORKERS,
        pin_memory=PIN_MEMORY
    )


    return (
        train_loader,
        validation_loader,
        test_loader
    )


# ==========================================================
# TEST
# ==========================================================

if __name__ == "__main__":

    print("=" * 70)
    print("STEP 13 - PTB-XL DATALOADER")
    print("=" * 70)


    (
        train_loader,
        validation_loader,
        test_loader
    ) = create_dataloaders()


    print(
        "\nTrain samples:",
        len(train_loader.dataset)
    )

    print(
        "Validation samples:",
        len(validation_loader.dataset)
    )

    print(
        "Test samples:",
        len(test_loader.dataset)
    )


    # ------------------------------------------------------
    # Get one batch
    # ------------------------------------------------------

    X, y = next(
        iter(train_loader)
    )


    print("\n" + "=" * 70)
    print("BATCH CHECK")
    print("=" * 70)


    print(
        "X shape:",
        X.shape
    )

    print(
        "X dtype:",
        X.dtype
    )

    print(
        "y shape:",
        y.shape
    )

    print(
        "y dtype:",
        y.dtype
    )


    print(
        "\nExpected X:"
    )

    print(
        f"[{BATCH_SIZE}, 12, 5000]"
    )


    print(
        "\nExpected y:"
    )

    print(
        f"[{BATCH_SIZE}, 5]"
    )


    print(
        "\nFirst labels:"
    )

    print(y[:5])