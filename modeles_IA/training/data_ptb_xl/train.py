"""
==========================================================
Step 15 - PTB-XL CNN Training
==========================================================

Pipeline:

    PTB-XL
       ↓
    Dataset
       ↓
    DataLoader
       ↓
    CNN
       ↓
    BCEWithLogitsLoss
       ↓
    Adam
       ↓
    Backpropagation
       ↓
    Validation
       ↓
    Save best model

Multi-label classes:

    NORM
    MI
    STTC
    CD
    HYP
==========================================================
"""

from pathlib import Path

import torch
import torch.nn as nn
from torch.optim import Adam

from tqdm import tqdm

from dataloader import create_dataloaders
from cnn_arch import ECG1DCNN


# ==========================================================
# CONFIGURATION
# ==========================================================

DEVICE = torch.device(
    "cuda"
    if torch.cuda.is_available()
    else "cpu"
)

NUM_CLASSES = 5

EPOCHS = 20

LEARNING_RATE = 1e-3

WEIGHT_DECAY = 1e-4

MODEL_DIR = Path(
    "models"
)

MODEL_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ==========================================================
# TRAIN FUNCTION
# ==========================================================

def train_one_epoch(
    model,
    loader,
    criterion,
    optimizer,
    device
):

    model.train()

    total_loss = 0.0


    progress = tqdm(
        loader,
        desc="Training"
    )


    for X, y in progress:

        X = X.to(
            device,
            non_blocking=True
        )

        y = y.to(
            device,
            non_blocking=True
        )


        # --------------------------------------------------
        # Clear gradients
        # --------------------------------------------------

        optimizer.zero_grad()


        # --------------------------------------------------
        # Forward
        # --------------------------------------------------

        logits = model(X)


        # --------------------------------------------------
        # Loss
        # --------------------------------------------------

        loss = criterion(
            logits,
            y
        )


        # --------------------------------------------------
        # Backpropagation
        # --------------------------------------------------

        loss.backward()


        # --------------------------------------------------
        # Update weights
        # --------------------------------------------------

        optimizer.step()


        total_loss += (
            loss.item()
            * X.size(0)
        )


        progress.set_postfix(
            loss=loss.item()
        )


    average_loss = (
        total_loss /
        len(loader.dataset)
    )


    return average_loss


# ==========================================================
# VALIDATION FUNCTION
# ==========================================================

def validate(
    model,
    loader,
    criterion,
    device
):

    model.eval()

    total_loss = 0.0


    with torch.no_grad():

        for X, y in loader:

            X = X.to(
                device,
                non_blocking=True
            )

            y = y.to(
                device,
                non_blocking=True
            )


            logits = model(X)


            loss = criterion(
                logits,
                y
            )


            total_loss += (
                loss.item()
                * X.size(0)
            )


    average_loss = (
        total_loss /
        len(loader.dataset)
    )


    return average_loss


# ==========================================================
# MAIN
# ==========================================================

if __name__ == "__main__":

    print("=" * 70)
    print("STEP 15 - PTB-XL CNN TRAINING")
    print("=" * 70)


    print(
        "\nDevice:",
        DEVICE
    )


    if torch.cuda.is_available():

        print(
            "GPU:",
            torch.cuda.get_device_name(0)
        )


    # ======================================================
    # DataLoaders
    # ======================================================

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


    # ======================================================
    # Model
    # ======================================================

    model = ECG1DCNN(
        num_classes=NUM_CLASSES
    )


    model = model.to(
        DEVICE
    )


    # ======================================================
    # Loss
    # ======================================================

    criterion = nn.BCEWithLogitsLoss()


    # ======================================================
    # Optimizer
    # ======================================================

    optimizer = Adam(
        model.parameters(),
        lr=LEARNING_RATE,
        weight_decay=WEIGHT_DECAY
    )


    # ======================================================
    # Training
    # ======================================================

    best_val_loss = float(
        "inf"
    )


    for epoch in range(
        1,
        EPOCHS + 1
    ):

        print("\n")
        print("=" * 70)

        print(
            f"EPOCH {epoch}/{EPOCHS}"
        )

        print("=" * 70)


        # --------------------------------------------------
        # Training
        # --------------------------------------------------

        train_loss = train_one_epoch(
            model,
            train_loader,
            criterion,
            optimizer,
            DEVICE
        )


        # --------------------------------------------------
        # Validation
        # --------------------------------------------------

        val_loss = validate(
            model,
            validation_loader,
            criterion,
            DEVICE
        )


        print(
            f"\nTrain loss: {train_loss:.4f}"
        )

        print(
            f"Validation loss: {val_loss:.4f}"
        )


        # --------------------------------------------------
        # Save best model
        # --------------------------------------------------

        if val_loss < best_val_loss:

            best_val_loss = val_loss


            model_path = (
                MODEL_DIR /
                "best_ecg_cnn.pt"
            )


            torch.save(
                {
                    "epoch": epoch,
                    "model_state_dict": (
                        model.state_dict()
                    ),
                    "optimizer_state_dict": (
                        optimizer.state_dict()
                    ),
                    "val_loss": val_loss,
                },
                model_path
            )


            print(
                "\n[OK] Best model saved:"
            )

            print(
                model_path
            )


    print("\n" + "=" * 70)

    print(
        "TRAINING COMPLETE"
    )

    print("=" * 70)

    print(
        "Best validation loss:",
        best_val_loss
    )