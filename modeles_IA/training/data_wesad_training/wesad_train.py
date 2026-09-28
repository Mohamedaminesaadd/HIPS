"""
WESAD Stress Classification
============================

Pipeline:
    wesad_dataset_clean.csv
            |
            v
    Leave-One-Subject-Out (LOSO)
            |
            v
    Median Imputation
            |
            v
    StandardScaler
            |
            v
    XGBoost
            |
            v
    Subject-wise evaluation

Metrics:
    - Accuracy
    - Balanced Accuracy
    - Precision
    - Recall
    - F1-score
    - ROC-AUC
    - Macro F1

Outputs:
    - resultats_loso.csv
    - classification_report.txt
    - metriques_resume.json
    - 08_confusion_finale.png
    - 09_importance_finale.png
    - 10_accuracy_by_subject.png
    - 11_precision_recall_f1_by_subject.png
    - 12_mean_metrics.png
    - modele_stress_xgb.joblib
"""

from pathlib import Path
import json
import argparse
import warnings

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.base import clone
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

from sklearn.pipeline import Pipeline

from sklearn.model_selection import (
    LeaveOneGroupOut,
    GroupKFold,
    RandomizedSearchCV
)

from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    classification_report,
    confusion_matrix,
    ConfusionMatrixDisplay
)

from xgboost import XGBClassifier

import joblib


warnings.filterwarnings("ignore")


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

OUTPUT_DIR = BASE_DIR / "outputs"

DATASET_PATH = Path(
    "/home/mohamed-amine/Documents/PlatformIO/Projects/datasets/data_cleanig/wesad_dataset.csv"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# FEATURES THAT MUST NOT BE USED BY THE MODEL
# ============================================================

NON_FEATURES = [
    "subject",
    "label",
    "label_name",
    "target_binary",
    "target_3class",
    "ppg_hr_diff",
    "ppg_reliable",
]


# ============================================================
# DEFAULT XGBOOST PARAMETERS
# ============================================================

DEFAULT_PARAMS = dict(
    n_estimators=300,
    max_depth=4,
    learning_rate=0.05,
    subsample=0.9,
    colsample_bytree=0.9,
    min_child_weight=3,
    gamma=0.0,
    reg_lambda=1.0,
    eval_metric="logloss",
    tree_method="hist",
    random_state=42,
)


# ============================================================
# HYPERPARAMETER SEARCH SPACE
# ============================================================

PARAM_GRID = {
    "model__max_depth": [
        3,
        4,
        5,
        6
    ],

    "model__learning_rate": [
        0.03,
        0.05,
        0.1
    ],

    "model__n_estimators": [
        200,
        300,
        400,
        500
    ],

    "model__subsample": [
        0.8,
        0.9,
        1.0
    ],

    "model__colsample_bytree": [
        0.8,
        0.9,
        1.0
    ],

    "model__min_child_weight": [
        1,
        3,
        5
    ],
}


# ============================================================
# ARGUMENTS
# ============================================================

def parse_args():

    parser = argparse.ArgumentParser(
        description="WESAD stress classification using LOSO."
    )

    parser.add_argument(
        "--tune",
        action="store_true",
        help="Enable hyperparameter tuning."
    )

    parser.add_argument(
        "--target",
        choices=[
            "binary",
            "3class"
        ],
        default="binary",
        help="Target type."
    )

    parser.add_argument(
        "--data",
        type=str,
        default=str(DATASET_PATH),
        help="Path to cleaned WESAD CSV."
    )

    return parser.parse_args()


# ============================================================
# LOAD DATA
# ============================================================

def load_xy(
    csv_path,
    target="binary"
):
    """
    Load WESAD dataset and separate:
        X = features
        y = target
        groups = subject IDs
    """

    csv_path = Path(csv_path)

    if not csv_path.exists():

        raise FileNotFoundError(
            f"Dataset not found: {csv_path}"
        )

    df = pd.read_csv(
        csv_path
    )

    print()
    print("=" * 70)
    print("DATASET")
    print("=" * 70)

    print(
        f"Dataset path: {csv_path}"
    )

    print(
        f"Number of samples: {len(df)}"
    )

    print(
        f"Number of columns: {len(df.columns)}"
    )

    # --------------------------------------------------------
    # Target
    # --------------------------------------------------------

    if target == "binary":

        target_column = "target_binary"

    else:

        target_column = "target_3class"

    if target_column not in df.columns:

        raise ValueError(
            f"Missing target column: {target_column}"
        )

    if "subject" not in df.columns:

        raise ValueError(
            "Missing 'subject' column."
        )

    # --------------------------------------------------------
    # Remove rows with missing target
    # --------------------------------------------------------

    df = df.dropna(
        subset=[
            target_column
        ]
    ).copy()

    # --------------------------------------------------------
    # Groups
    # --------------------------------------------------------

    groups = df["subject"].values

    # --------------------------------------------------------
    # Features
    # --------------------------------------------------------

    excluded = set(
        NON_FEATURES
    )

    excluded.add(
        target_column
    )

    feature_columns = [
        column
        for column in df.columns
        if column not in excluded
    ]

    if not feature_columns:

        raise ValueError(
            "No feature columns found."
        )

    X = df[
        feature_columns
    ].copy()

    y = df[
        target_column
    ].astype(int).values

    # --------------------------------------------------------
    # Remove non-numeric columns
    # --------------------------------------------------------

    numeric_columns = X.select_dtypes(
        include=[np.number]
    ).columns

    X = X[
        numeric_columns
    ]

    print(
        f"Features used: {len(X.columns)}"
    )

    print(
        f"Target: {target_column}"
    )

    print(
        f"Subjects: {sorted(pd.unique(groups))}"
    )

    print()
    print("Target distribution:")

    print(
        pd.Series(y).value_counts().sort_index()
    )

    return (
        X,
        y,
        groups,
        list(X.columns)
    )


# ============================================================
# BUILD MODEL PIPELINE
# ============================================================

def build_pipeline(
    target="binary",
    y_train=None
):
    """
    Build fold-safe preprocessing + XGBoost.

    Imputation and scaling are fitted only on the training fold.
    """

    params = DEFAULT_PARAMS.copy()

    # --------------------------------------------------------
    # Binary classification
    # --------------------------------------------------------

    if target == "binary":

        params[
            "objective"
        ] = "binary:logistic"

        params[
            "num_class"
        ] = None

        # Calculate class weight only from training data
        if y_train is not None:

            counts = np.bincount(
                y_train
            )

            if (
                len(counts) >= 2
                and counts[1] > 0
            ):

                params[
                    "scale_pos_weight"
                ] = counts[0] / counts[1]

            else:

                params[
                    "scale_pos_weight"
                ] = 1.0

        else:

            params[
                "scale_pos_weight"
            ] = 1.0

    # --------------------------------------------------------
    # 3-class classification
    # --------------------------------------------------------

    else:

        params[
            "objective"
        ] = "multi:softprob"

        params[
            "num_class"
        ] = 3

        params[
            "eval_metric"
        ] = "mlogloss"

    model = XGBClassifier(
        **params
    )

    pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(
                    strategy="median"
                )
            ),

            (
                "scaler",
                StandardScaler()
            ),

            (
                "model",
                model
            ),
        ]
    )

    return pipeline


# ============================================================
# HYPERPARAMETER TUNING
# ============================================================

def tune_on_train(
    X_train,
    y_train,
    groups_train,
    target="binary"
):
    """
    Hyperparameter tuning using GroupKFold.

    The held-out LOSO subject is never used during tuning.
    """

    print()
    print(
        "Starting hyperparameter tuning..."
    )

    pipeline = build_pipeline(
        target=target,
        y_train=y_train
    )

    unique_groups = np.unique(
        groups_train
    )

    n_splits = min(
        4,
        len(unique_groups)
    )

    if n_splits < 2:

        print(
            "Not enough groups for tuning."
        )

        return pipeline

    group_kfold = GroupKFold(
        n_splits=n_splits
    )

    search = RandomizedSearchCV(
        estimator=pipeline,
        param_distributions=PARAM_GRID,
        n_iter=20,
        scoring="f1_macro",
        cv=group_kfold.split(
            X_train,
            y_train,
            groups_train
        ),
        random_state=42,
        n_jobs=-1,
        verbose=0
    )

    search.fit(
        X_train,
        y_train
    )

    print(
        "Best parameters:"
    )

    print(
        search.best_params_
    )

    print(
        f"Best CV F1-macro: "
        f"{search.best_score_:.4f}"
    )

    return search.best_estimator_


# ============================================================
# METRICS
# ============================================================

def compute_metrics(
    y_true,
    y_pred,
    y_proba=None,
    target="binary"
):
    """
    Calculate all requested metrics.
    """

    accuracy = accuracy_score(
        y_true,
        y_pred
    )

    balanced_accuracy = balanced_accuracy_score(
        y_true,
        y_pred
    )

    # --------------------------------------------------------
    # Binary
    # --------------------------------------------------------

    if target == "binary":

        precision = precision_score(
            y_true,
            y_pred,
            pos_label=1,
            zero_division=0
        )

        recall = recall_score(
            y_true,
            y_pred,
            pos_label=1,
            zero_division=0
        )

        f1 = f1_score(
            y_true,
            y_pred,
            pos_label=1,
            zero_division=0
        )

        f1_macro = f1_score(
            y_true,
            y_pred,
            average="macro",
            zero_division=0
        )

        roc_auc = np.nan

        if (
            y_proba is not None
            and len(np.unique(y_true)) == 2
        ):

            roc_auc = roc_auc_score(
                y_true,
                y_proba
            )

    # --------------------------------------------------------
    # 3-class
    # --------------------------------------------------------

    else:

        precision = precision_score(
            y_true,
            y_pred,
            average="macro",
            zero_division=0
        )

        recall = recall_score(
            y_true,
            y_pred,
            average="macro",
            zero_division=0
        )

        f1 = f1_score(
            y_true,
            y_pred,
            average="macro",
            zero_division=0
        )

        f1_macro = f1

        roc_auc = np.nan

        if (
            y_proba is not None
            and len(np.unique(y_true)) == 3
        ):

            try:

                roc_auc = roc_auc_score(
                    y_true,
                    y_proba,
                    multi_class="ovr",
                    average="macro"
                )

            except ValueError:

                roc_auc = np.nan

    return {
        "accuracy": accuracy,
        "balanced_accuracy": balanced_accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "f1_macro": f1_macro,
        "roc_auc": roc_auc,
    }


# ============================================================
# LOSO EVALUATION
# ============================================================

def evaluate_loso(
    X,
    y,
    groups,
    target="binary",
    tune=False
):
    """
    Leave-One-Subject-Out evaluation.

    Every iteration:
        train = all subjects except one
        test  = one unseen subject
    """

    logo = LeaveOneGroupOut()

    results = []

    all_true = []
    all_pred = []
    all_proba = []

    feature_importances = []

    print()
    print("=" * 70)
    print("LEAVE-ONE-SUBJECT-OUT EVALUATION")
    print("=" * 70)

    unique_subjects = sorted(
        pd.unique(groups)
    )

    print(
        f"Number of subjects: "
        f"{len(unique_subjects)}"
    )

    print()

    for fold, (
        train_idx,
        test_idx
    ) in enumerate(
        logo.split(
            X,
            y,
            groups
        ),
        start=1
    ):

        test_subject = groups[
            test_idx[0]
        ]

        train_subjects = sorted(
            pd.unique(
                groups[
                    train_idx
                ]
            )
        )

        print(
            "-" * 70
        )

        print(
            f"Fold {fold}/{len(unique_subjects)}"
        )

        print(
            f"Test subject: {test_subject}"
        )

        print(
            f"Training subjects: "
            f"{train_subjects}"
        )

        X_train = X.iloc[
            train_idx
        ]

        X_test = X.iloc[
            test_idx
        ]

        y_train = y[
            train_idx
        ]

        y_test = y[
            test_idx
        ]

        groups_train = groups[
            train_idx
        ]

        # ----------------------------------------------------
        # Build model
        # ----------------------------------------------------

        if tune:

            model = tune_on_train(
                X_train,
                y_train,
                groups_train,
                target=target
            )

        else:

            model = build_pipeline(
                target=target,
                y_train=y_train
            )

        # ----------------------------------------------------
        # Train
        # ----------------------------------------------------

        model.fit(
            X_train,
            y_train
        )

        # ----------------------------------------------------
        # Predict
        # ----------------------------------------------------

        y_pred = model.predict(
            X_test
        )

        # ----------------------------------------------------
        # Probability
        # ----------------------------------------------------

        y_proba = None

        if hasattr(
            model,
            "predict_proba"
        ):

            probabilities = model.predict_proba(
                X_test
            )

            if target == "binary":

                y_proba = probabilities[
                    :, 1
                ]

            else:

                y_proba = probabilities

        # ----------------------------------------------------
        # Metrics
        # ----------------------------------------------------

        metrics = compute_metrics(
            y_test,
            y_pred,
            y_proba,
            target=target
        )

        row = {
            "test_subject": test_subject,
            "n_train": len(train_idx),
            "n_test": len(test_idx),
            **metrics
        }

        results.append(
            row
        )

        # ----------------------------------------------------
        # Save pooled predictions
        # ----------------------------------------------------

        all_true.extend(
            y_test.tolist()
        )

        all_pred.extend(
            y_pred.tolist()
        )

        if y_proba is not None:

            if target == "binary":

                all_proba.extend(
                    y_proba.tolist()
                )

        # ----------------------------------------------------
        # Feature importance
        # ----------------------------------------------------

        try:

            xgb_model = model.named_steps[
                "model"
            ]

            importance = xgb_model.feature_importances_

            feature_importances.append(
                importance
            )

        except Exception:

            pass

        # ----------------------------------------------------
        # Print fold result
        # ----------------------------------------------------

        print(
            f"Accuracy           : "
            f"{metrics['accuracy']:.4f}"
        )

        print(
            f"Balanced Accuracy  : "
            f"{metrics['balanced_accuracy']:.4f}"
        )

        print(
            f"Precision          : "
            f"{metrics['precision']:.4f}"
        )

        print(
            f"Recall             : "
            f"{metrics['recall']:.4f}"
        )

        print(
            f"F1-score           : "
            f"{metrics['f1']:.4f}"
        )

        print(
            f"F1-macro           : "
            f"{metrics['f1_macro']:.4f}"
        )

        if not np.isnan(
            metrics["roc_auc"]
        ):

            print(
                f"ROC-AUC            : "
                f"{metrics['roc_auc']:.4f}"
            )

    results_df = pd.DataFrame(
        results
    )

    return (
        results_df,
        np.array(all_true),
        np.array(all_pred),
        np.array(all_proba)
        if all_proba
        else None,
        feature_importances
    )


# ============================================================
# PRINT SUBJECT RESULTS
# ============================================================

def print_subject_results(
    results
):
    """

    Print all metrics for every WESAD subject.
    """

    print()
    print("=" * 90)
    print("SUBJECT-WISE RESULTS")
    print("=" * 90)

    columns = [
        "test_subject",
        "accuracy",
        "balanced_accuracy",
        "precision",
        "recall",
        "f1",
        "f1_macro",
        "roc_auc"
    ]

    display_df = results[
        columns
    ].copy()

    for column in columns[1:]:

        display_df[
            column
        ] = display_df[
            column
        ].map(
            lambda x: (
                f"{x:.4f}"
                if pd.notna(x)
                else "N/A"
            )
        )

    print(
        display_df.to_string(
            index=False
        )
    )


# ============================================================
# MEAN AND STANDARD DEVIATION
# ============================================================

def calculate_summary(
    results
):
    """
    Calculate subject-wise mean and standard deviation.
    """

    metrics = [
        "accuracy",
        "balanced_accuracy",
        "precision",
        "recall",
        "f1",
        "f1_macro",
        "roc_auc"
    ]

    summary = {}

    for metric in metrics:

        values = pd.to_numeric(
            results[metric],
            errors="coerce"
        )

        summary[
            metric
        ] = {
            "mean": float(
                values.mean()
            ),

            "std": float(
                values.std()
            ),

            "min": float(
                values.min()
            ),

            "max": float(
                values.max()
            )
        }

    return summary


def print_summary(
    summary
):

    print()
    print("=" * 90)
    print("MEAN ± STANDARD DEVIATION")
    print("=" * 90)

    for metric, values in summary.items():

        if np.isnan(
            values["mean"]
        ):

            print(
                f"{metric:20s}: N/A"
            )

        else:

            print(
                f"{metric:20s}: "
                f"{values['mean']:.4f} ± "
                f"{values['std']:.4f}"
            )


# ============================================================
# POOLED CLASSIFICATION REPORT
# ============================================================

def generate_classification_report(
    y_true,
    y_pred,
    target="binary"
):

    if target == "binary":

        labels = [
            0,
            1
        ]

        target_names = [
            "Non-Stress",
            "Stress"
        ]

    else:

        labels = [
            0,
            1,
            2
        ]

        target_names = [
            "Baseline",
            "Stress",
            "Amusement"
        ]

    report = classification_report(
        y_true,
        y_pred,
        labels=labels,
        target_names=target_names,
        digits=4,
        zero_division=0
    )

    return report


# ============================================================
# CONFUSION MATRIX
# ============================================================

def plot_confusion_matrix(
    y_true,
    y_pred,
    path,
    target="binary"
):

    if target == "binary":

        labels = [
            0,
            1
        ]

        display_labels = [
            "Non-Stress",
            "Stress"
        ]

    else:

        labels = [
            0,
            1,
            2
        ]

        display_labels = [
            "Baseline",
            "Stress",
            "Amusement"
        ]

    cm = confusion_matrix(
        y_true,
        y_pred,
        labels=labels
    )

    print()
    print("=" * 70)
    print("CONFUSION MATRIX")
    print("=" * 70)

    print(
        cm
    )

    fig, ax = plt.subplots(
        figsize=(7, 6)
    )

    display = ConfusionMatrixDisplay(
        confusion_matrix=cm,
        display_labels=display_labels
    )

    display.plot(
        ax=ax,
        values_format="d"
    )

    ax.set_title(
        "WESAD Stress Classification - Confusion Matrix"
    )

    fig.tight_layout()

    fig.savefig(
        path,
        dpi=200,
        bbox_inches="tight"
    )

    plt.close(fig)

    print(
        f"Confusion matrix saved: {path}"
    )


# ============================================================
# ACCURACY BY SUBJECT
# ============================================================

def plot_subject_accuracy(
    results,
    path
):

    fig, ax = plt.subplots(
        figsize=(10, 6)
    )

    subjects = results[
        "test_subject"
    ].astype(str)

    accuracy = results[
        "accuracy"
    ].values

    x = np.arange(
        len(subjects)
    )

    ax.bar(
        x,
        accuracy
    )

    ax.set_title(
        "WESAD Stress Classification - Accuracy by Subject"
    )

    ax.set_xlabel(
        "Test subject"
    )

    ax.set_ylabel(
        "Accuracy"
    )

    ax.set_xticks(
        x
    )

    ax.set_xticklabels(
        subjects
    )

    ax.set_ylim(
        0,
        1
    )

    ax.grid(
        axis="y",
        alpha=0.3
    )

    for i, value in enumerate(
        accuracy
    ):

        ax.text(
            i,
            min(
                value + 0.02,
                0.98
            ),
            f"{value:.2f}",
            ha="center"
        )

    fig.tight_layout()

    fig.savefig(
        path,
        dpi=200,
        bbox_inches="tight"
    )

    plt.close(fig)

    print(
        f"Accuracy graph saved: {path}"
    )


# ============================================================
# PRECISION / RECALL / F1
# ============================================================

def plot_precision_recall_f1(
    results,
    path
):

    subjects = results[
        "test_subject"
    ].astype(str)

    x = np.arange(
        len(subjects)
    )

    width = 0.25

    fig, ax = plt.subplots(
        figsize=(13, 7)
    )

    precision = results[
        "precision"
    ].values

    recall = results[
        "recall"
    ].values

    f1 = results[
        "f1"
    ].values

    ax.bar(
        x - width,
        precision,
        width,
        label="Precision"
    )

    ax.bar(
        x,
        recall,
        width,
        label="Recall"
    )

    ax.bar(
        x + width,
        f1,
        width,
        label="F1-score"
    )

    ax.set_title(
        "WESAD Stress Classification - Precision, Recall and F1-score"
    )

    ax.set_xlabel(
        "Test subject"
    )

    ax.set_ylabel(
        "Score"
    )

    ax.set_xticks(
        x
    )

    ax.set_xticklabels(
        subjects
    )

    ax.set_ylim(
        0,
        1
    )

    ax.legend()

    ax.grid(
        axis="y",
        alpha=0.3
    )

    fig.tight_layout()

    fig.savefig(
        path,
        dpi=200,
        bbox_inches="tight"
    )

    plt.close(fig)

    print(
        f"Precision/Recall/F1 graph saved: {path}"
    )


# ============================================================
# MEAN METRICS WITH STANDARD DEVIATION
# ============================================================

def plot_mean_metrics(
    results,
    path
):

    metric_names = [
        "Accuracy",
        "Balanced Accuracy",
        "Precision",
        "Recall",
        "F1-score",
        "F1-macro"
    ]

    metric_columns = [
        "accuracy",
        "balanced_accuracy",
        "precision",
        "recall",
        "f1",
        "f1_macro"
    ]

    means = []

    stds = []

    for column in metric_columns:

        values = pd.to_numeric(
            results[column],
            errors="coerce"
        )

        means.append(
            values.mean()
        )

        stds.append(
            values.std()
        )

    fig, ax = plt.subplots(
        figsize=(11, 7)
    )

    x = np.arange(
        len(metric_names)
    )

    ax.bar(
        x,
        means,
        yerr=stds,
        capsize=5
    )

    ax.set_title(
        "WESAD Stress Classification - Mean Performance"
    )

    ax.set_xlabel(
        "Metric"
    )

    ax.set_ylabel(
        "Score"
    )

    ax.set_xticks(
        x
    )

    ax.set_xticklabels(
        metric_names,
        rotation=20,
        ha="right"
    )

    ax.set_ylim(
        0,
        1
    )

    ax.grid(
        axis="y",
        alpha=0.3
    )

    for i, (
        mean,
        std
    ) in enumerate(
        zip(means, stds)
    ):

        ax.text(
            i,
            min(
                mean + std + 0.03,
                0.98
            ),
            f"{mean:.3f}",
            ha="center"
        )

    fig.tight_layout()

    fig.savefig(
        path,
        dpi=200,
        bbox_inches="tight"
    )

    plt.close(fig)

    print(
        f"Mean metrics graph saved: {path}"
    )


# ============================================================
# FEATURE IMPORTANCE
# ============================================================

def plot_feature_importance(
    feature_names,
    feature_importances,
    path,
    top_n=15
):

    if not feature_importances:

        print(
            "No feature importance available."
        )

        return

    importance_matrix = np.vstack(
        feature_importances
    )

    mean_importance = (
        importance_matrix.mean(
            axis=0
        )
    )

    importance_df = pd.DataFrame(
        {
            "feature": feature_names,
            "importance": mean_importance
        }
    )

    importance_df = importance_df.sort_values(
        "importance",
        ascending=False
    )

    importance_df = importance_df.head(
        top_n
    )

    importance_df = importance_df.sort_values(
        "importance",
        ascending=True
    )

    fig, ax = plt.subplots(
        figsize=(10, 7)
    )

    ax.barh(
        importance_df[
            "feature"
        ],
        importance_df[
            "importance"
        ]
    )

    ax.set_title(
        "WESAD XGBoost - Top Feature Importance"
    )

    ax.set_xlabel(
        "Mean feature importance"
    )

    ax.set_ylabel(
        "Feature"
    )

    ax.grid(
        axis="x",
        alpha=0.3
    )

    fig.tight_layout()

    fig.savefig(
        path,
        dpi=200,
        bbox_inches="tight"
    )

    plt.close(fig)

    print(
        f"Feature importance graph saved: {path}"
    )


# ============================================================
# FINAL MODEL
# ============================================================

def train_final_model(
    X,
    y,
    target="binary"
):

    print()
    print("=" * 70)
    print("TRAINING FINAL MODEL")
    print("=" * 70)

    final_model = build_pipeline(
        target=target,
        y_train=y
    )

    final_model.fit(
        X,
        y
    )

    return final_model


# ============================================================
# SAVE JSON SUMMARY
# ============================================================

def save_summary_json(
    summary,
    path,
    target
):

    output = {
        "target": target,
        "evaluation": "Leave-One-Subject-Out",
        "metrics": summary
    }

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            output,
            file,
            indent=4
        )

    print(
        f"Summary JSON saved: {path}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    args = parse_args()

    print()
    print("=" * 70)
    print("WESAD STRESS CLASSIFICATION")
    print("=" * 70)

    print(
        f"Target: {args.target}"
    )

    print(
        f"Hyperparameter tuning: {args.tune}"
    )

    print(
        f"Dataset: {args.data}"
    )

    # --------------------------------------------------------
    # Load dataset
    # --------------------------------------------------------

    (
        X,
        y,
        groups,
        feature_names
    ) = load_xy(
        args.data,
        target=args.target
    )

    # --------------------------------------------------------
    # LOSO
    # --------------------------------------------------------

    (
        results,
        all_true,
        all_pred,
        all_proba,
        feature_importances
    ) = evaluate_loso(
        X,
        y,
        groups,
        target=args.target,
        tune=args.tune
    )

    # --------------------------------------------------------
    # Subject results
    # --------------------------------------------------------

    print_subject_results(
        results
    )

    # --------------------------------------------------------
    # Mean / standard deviation
    # --------------------------------------------------------

    summary = calculate_summary(
        results
    )

    print_summary(
        summary
    )

    # --------------------------------------------------------
    # Save LOSO CSV
    # --------------------------------------------------------

    results_path = (
        OUTPUT_DIR
        / "resultats_loso.csv"
    )

    results.to_csv(
        results_path,
        index=False
    )

    print()
    print(
        f"LOSO results saved: {results_path}"
    )

    # --------------------------------------------------------
    # Classification report
    # --------------------------------------------------------

    report = generate_classification_report(
        all_true,
        all_pred,
        target=args.target
    )

    print()
    print("=" * 70)
    print("POOLED CLASSIFICATION REPORT")
    print("=" * 70)

    print(
        report
    )

    report_path = (
        OUTPUT_DIR
        / "classification_report.txt"
    )

    with open(
        report_path,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            report
        )

    print(
        f"Classification report saved: "
        f"{report_path}"
    )

    # --------------------------------------------------------
    # Summary JSON
    # --------------------------------------------------------

    summary_path = (
        OUTPUT_DIR
        / "metriques_resume.json"
    )

    save_summary_json(
        summary,
        summary_path,
        args.target
    )

    # --------------------------------------------------------
    # Confusion matrix
    # --------------------------------------------------------

    confusion_path = (
        OUTPUT_DIR
        / "08_confusion_finale.png"
    )

    plot_confusion_matrix(
        all_true,
        all_pred,
        confusion_path,
        target=args.target
    )

    # --------------------------------------------------------
    # Accuracy by subject
    # --------------------------------------------------------

    accuracy_path = (
        OUTPUT_DIR
        / "10_accuracy_by_subject.png"
    )

    plot_subject_accuracy(
        results,
        accuracy_path
    )

    # --------------------------------------------------------
    # Precision / Recall / F1
    # --------------------------------------------------------

    prf_path = (
        OUTPUT_DIR
        / "11_precision_recall_f1_by_subject.png"
    )

    plot_precision_recall_f1(
        results,
        prf_path
    )

    # --------------------------------------------------------
    # Mean metrics
    # --------------------------------------------------------

    mean_metrics_path = (
        OUTPUT_DIR
        / "12_mean_metrics.png"
    )

    plot_mean_metrics(
        results,
        mean_metrics_path
    )

    # --------------------------------------------------------
    # Final model
    # --------------------------------------------------------

    final_model = train_final_model(
        X,
        y,
        target=args.target
    )

    # --------------------------------------------------------
    # Save model
    # --------------------------------------------------------

    model_path = (
        OUTPUT_DIR
        / "modele_stress_xgb.joblib"
    )

    joblib.dump(
        final_model,
        model_path
    )

    print(
        f"Final model saved: {model_path}"
    )

    # --------------------------------------------------------
    # Feature importance
    # --------------------------------------------------------

    importance_path = (
        OUTPUT_DIR
        / "09_importance_finale.png"
    )

    plot_feature_importance(
        feature_names,
        feature_importances,
        importance_path
    )

    # --------------------------------------------------------
    # Final summary
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("TRAINING COMPLETED")
    print("=" * 70)

    print()
    print("Generated files:")

    files = [
        results_path,
        report_path,
        summary_path,
        confusion_path,
        accuracy_path,
        prf_path,
        mean_metrics_path,
        importance_path,
        model_path,
    ]

    for file in files:

        print(
            f"  - {file}"
        )

    print()
    print("=" * 70)
    print("MAIN RESULTS")
    print("=" * 70)

    for metric in [
        "accuracy",
        "balanced_accuracy",
        "precision",
        "recall",
        "f1",
        "f1_macro",
        "roc_auc"
    ]:

        values = summary[
            metric
        ]

        if np.isnan(
            values["mean"]
        ):

            print(
                f"{metric:20s}: N/A"
            )

        else:

            print(
                f"{metric:20s}: "
                f"{values['mean']:.4f} ± "
                f"{values['std']:.4f}"
            )

    print()
    print(
        "You can now use the generated PNG files "
        "in Chapter 8."
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()