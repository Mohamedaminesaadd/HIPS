"""
==========================================================
Step 14 - PTB-XL 1D CNN
==========================================================

Input:

    [batch, 12, 5000]

Output:

    [batch, 5]

Classes:

    NORM
    MI
    STTC
    CD
    HYP
==========================================================
"""

import torch
import torch.nn as nn


# ==========================================================
# MODEL
# ==========================================================

class ECG1DCNN(nn.Module):

    def __init__(
        self,
        num_classes=5
    ):

        super().__init__()


        # ==================================================
        # Block 1
        # ==================================================

        self.features = nn.Sequential(

            nn.Conv1d(
                in_channels=12,
                out_channels=32,
                kernel_size=7,
                padding=3
            ),

            nn.BatchNorm1d(32),

            nn.ReLU(),

            nn.MaxPool1d(
                kernel_size=2
            ),


            # ==================================================
            # Block 2
            # ==================================================

            nn.Conv1d(
                in_channels=32,
                out_channels=64,
                kernel_size=7,
                padding=3
            ),

            nn.BatchNorm1d(64),

            nn.ReLU(),

            nn.MaxPool1d(
                kernel_size=2
            ),


            # ==================================================
            # Block 3
            # ==================================================

            nn.Conv1d(
                in_channels=64,
                out_channels=128,
                kernel_size=7,
                padding=3
            ),

            nn.BatchNorm1d(128),

            nn.ReLU(),

            nn.MaxPool1d(
                kernel_size=2
            )
        )


        # ==================================================
        # Global pooling
        # ==================================================

        self.global_pool = nn.AdaptiveAvgPool1d(
            1
        )


        # ==================================================
        # Classifier
        # ==================================================

        self.classifier = nn.Sequential(

            nn.Linear(
                128,
                64
            ),

            nn.ReLU(),

            nn.Dropout(
                p=0.3
            ),

            nn.Linear(
                64,
                num_classes
            )
        )


    # ======================================================
    # Forward
    # ======================================================

    def forward(
        self,
        x
    ):

        # x:
        # [batch, 12, 5000]

        x = self.features(x)

        # [batch, 128, reduced_time]

        x = self.global_pool(x)

        # [batch, 128, 1]

        x = x.squeeze(
            -1
        )

        # [batch, 128]

        x = self.classifier(x)

        # [batch, 5]

        return x


# ==========================================================
# TEST MODEL
# ==========================================================

if __name__ == "__main__":

    print("=" * 70)
    print("STEP 14 - ECG CNN")
    print("=" * 70)


    model = ECG1DCNN(
        num_classes=5
    )


    print(model)


    # ------------------------------------------------------
    # Fake batch
    # ------------------------------------------------------

    X = torch.randn(
        4,
        12,
        5000
    )


    # ------------------------------------------------------
    # Forward pass
    # ------------------------------------------------------

    output = model(X)


    print("\nInput shape:")
    print(X.shape)


    print("\nOutput shape:")
    print(output.shape)


    print(
        "\nExpected output:"
    )

    print(
        "torch.Size([4, 5])"
    )


    # ------------------------------------------------------
    # Number of parameters
    # ------------------------------------------------------

    parameters = sum(
        p.numel()
        for p in model.parameters()
        if p.requires_grad
    )


    print(
        "\nTrainable parameters:",
        f"{parameters:,}"
    )