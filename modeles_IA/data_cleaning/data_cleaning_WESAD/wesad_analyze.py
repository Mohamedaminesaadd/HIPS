"""
wesad_analyze.py — Analyse du dataset : séparabilité des features, corrélations,
baseline XGBoost en validation Leave-One-Subject-Out (LOSO).
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import f1_score, accuracy_score, confusion_matrix
from xgboost import XGBClassifier
from wesad_config import OUTPUT_DIR

META = ["subject", "label", "label_name", "target_binary", "target_3class"]
KEY_FEATURES = ["ecg_mean_hr", "ecg_rmssd", "ecg_sdnn", "ecg_lf_hf",
                "temp_mean", "mot_energy"]


def load_dataset(path=OUTPUT_DIR / "wesad_dataset.csv"):
    return pd.read_csv(path)


def plot_feature_by_condition(df, path):
    order = ["baseline", "stress", "amusement", "meditation"]
    colors = {"baseline": "#4c9be8", "stress": "#e8564c",
              "amusement": "#f0a03c", "meditation": "#5cc98b"}
    feats = [f for f in KEY_FEATURES if f in df.columns]
    fig, axes = plt.subplots(2, (len(feats) + 1) // 2, figsize=(13, 7))
    for ax, feat in zip(axes.ravel(), feats):
        data = [df[df["label_name"] == c][feat].dropna() for c in order]
        bp = ax.boxplot(data, tick_labels=order, patch_artist=True, showfliers=False)
        for patch, c in zip(bp["boxes"], order):
            patch.set_facecolor(colors[c]); patch.set_alpha(0.7)
        ax.set_title(feat, fontsize=11); ax.tick_params(axis="x", rotation=30, labelsize=8)
    for ax in axes.ravel()[len(feats):]:
        ax.axis("off")
    fig.suptitle("Features clés par condition", fontsize=13)
    fig.tight_layout(rect=[0, 0, 1, 0.96]); fig.savefig(path, dpi=110); plt.close(fig)


def plot_corr_with_target(df, path):
    feat_cols = [c for c in df.columns if c not in META]
    corr = df[feat_cols].corrwith(df["target_binary"]).sort_values()
    fig, ax = plt.subplots(figsize=(8, 7))
    ax.barh(corr.index, corr.values,
            color=["#e8564c" if v > 0 else "#4c9be8" for v in corr.values])
    ax.axvline(0, color="k", lw=0.8)
    ax.set_xlabel("corrélation avec le stress (1) vs non-stress (0)")
    ax.set_title("Quelles features distinguent le stress ?")
    fig.tight_layout(); fig.savefig(path, dpi=110); plt.close(fig)
    return corr


def loso_xgboost(df, target="target_binary"):
    """Validation Leave-One-Subject-Out avec XGBoost."""
    feat_cols = [c for c in df.columns if c not in META]
    subjects = sorted(df["subject"].unique())
    results, all_true, all_pred = [], [], []
    importances = np.zeros(len(feat_cols))
    for test_s in subjects:
        train, test = df[df["subject"] != test_s], df[df["subject"] == test_s]
        X_tr, y_tr = train[feat_cols].values, train[target].astype(int).values
        X_te, y_te = test[feat_cols].values, test[target].astype(int).values
        if len(np.unique(y_tr)) < 2:
            continue
        clf = XGBClassifier(n_estimators=200, max_depth=4, learning_rate=0.05,
                            subsample=0.9, colsample_bytree=0.9,
                            eval_metric="logloss", random_state=42)
        clf.fit(X_tr, y_tr)
        y_pred = clf.predict(X_te)
        results.append({"test_subject": test_s, "n_test": len(y_te),
                        "accuracy": accuracy_score(y_te, y_pred),
                        "f1_macro": f1_score(y_te, y_pred, average="macro")})
        all_true.extend(y_te); all_pred.extend(y_pred)
        importances += clf.feature_importances_
    res_df = pd.DataFrame(results)
    imp = pd.Series(importances / max(1, len(res_df)),
                    index=feat_cols).sort_values(ascending=False)
    return res_df, imp, confusion_matrix(all_true, all_pred)


def plot_importance(imp, path, top=15):
    fig, ax = plt.subplots(figsize=(8, 6))
    imp.head(top)[::-1].plot.barh(ax=ax, color="#5a67d8")
    ax.set_title("Importance des features (XGBoost, moyenne LOSO)")
    ax.set_xlabel("importance"); fig.tight_layout(); fig.savefig(path, dpi=110); plt.close(fig)


def plot_confusion(cm, path, names=("non-stress", "stress")):
    fig, ax = plt.subplots(figsize=(4.5, 4))
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks([0, 1]); ax.set_yticks([0, 1])
    ax.set_xticklabels(names); ax.set_yticklabels(names)
    ax.set_xlabel("prédit"); ax.set_ylabel("réel")
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, cm[i, j], ha="center", va="center",
                    color="white" if cm[i, j] > cm.max() / 2 else "black",
                    fontsize=13, fontweight="bold")
    ax.set_title("Matrice de confusion (LOSO cumulée)")
    fig.colorbar(im, fraction=0.046, pad=0.04)
    fig.tight_layout(); fig.savefig(path, dpi=110); plt.close(fig)


def main():
    df = load_dataset()
    plot_feature_by_condition(df, OUTPUT_DIR / "04_features_par_condition.png")
    corr = plot_corr_with_target(df, OUTPUT_DIR / "05_correlation_stress.png")
    print("\nTop features corrélées au stress :")
    print(corr.reindex(corr.abs().sort_values(ascending=False).index).head(6).to_string())

    print("\n===== BASELINE XGBoost - LOSO (stress vs non-stress) =====")
    res, imp, cm = loso_xgboost(df)
    print(res.to_string(index=False))
    print(f"\nAccuracy moyenne : {res['accuracy'].mean():.3f} (+/- {res['accuracy'].std():.3f})")
    print(f"F1-macro moyen   : {res['f1_macro'].mean():.3f} (+/- {res['f1_macro'].std():.3f})")

    plot_importance(imp, OUTPUT_DIR / "06_importance_features.png")
    plot_confusion(cm, OUTPUT_DIR / "07_matrice_confusion.png")
    print("\nfigures d'analyse écrites dans", OUTPUT_DIR)


if __name__ == "__main__":
    main()