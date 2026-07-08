"""
wesad_train.py — Entraînement du modèle de détection de stress (XGBoost).

Méthodologie (défendable en soutenance) :
  - Validation LEAVE-ONE-SUBJECT-OUT (LOSO) : on teste sur un sujet jamais vu.
  - Pipeline FOLD-SAFE : imputation + scaling appris SEULEMENT sur le train
    de chaque pli => aucune fuite de données (data leakage).
  - Déséquilibre des classes géré via scale_pos_weight (calculé par pli).
  - Tuning en NESTED CV (optionnel) : recherche sur les sujets de train seulement.
  - Métriques complètes + matrice de confusion + importance des features.
  - Sauvegarde du modèle final (entraîné sur TOUS les sujets) pour le déploiement.

Usage :
  python wesad_train.py                 # binaire, hyperparams par défaut
  python wesad_train.py --tune          # + tuning nested CV
  python wesad_train.py --target 3class # cible 3 classes
"""
import sys, json
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import joblib
from sklearn.model_selection import LeaveOneGroupOut, GroupKFold, RandomizedSearchCV
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (accuracy_score, balanced_accuracy_score, f1_score,
                             classification_report, confusion_matrix, roc_auc_score)
from xgboost import XGBClassifier
from wesad_config import OUTPUT_DIR, BINARY_NAMES, THREE_CLASS_NAMES

NON_FEATURES = ["subject", "label", "label_name", "target_binary",
                "target_3class", "ppg_hr_diff", "ppg_reliable"]

DEFAULT_PARAMS = dict(
    n_estimators=300, max_depth=4, learning_rate=0.05,
    subsample=0.9, colsample_bytree=0.9, min_child_weight=3,
    gamma=0.0, reg_lambda=1.0, eval_metric="logloss",
    tree_method="hist", random_state=42,
)
PARAM_GRID = {
    "model__max_depth": [3, 4, 5, 6],
    "model__learning_rate": [0.02, 0.05, 0.1],
    "model__n_estimators": [200, 300, 500],
    "model__subsample": [0.7, 0.9, 1.0],
    "model__colsample_bytree": [0.7, 0.9, 1.0],
    "model__min_child_weight": [1, 3, 5],
}


def load_xy(path, target="target_binary"):
    df = pd.read_csv(path).dropna(subset=[target]).reset_index(drop=True)
    feat_cols = [c for c in df.columns if c not in NON_FEATURES]
    return df[feat_cols].values, df[target].astype(int).values, df["subject"].values, feat_cols


def build_pipeline(params, y_train):
    """Pipeline fold-safe : imputation -> scaling -> XGBoost.
    scale_pos_weight gère le déséquilibre (binaire)."""
    p = dict(params)
    classes = np.unique(y_train)
    if len(classes) == 2:
        p["scale_pos_weight"] = np.sum(y_train == 0) / max(1, np.sum(y_train == 1))
    else:
        p["objective"] = "multi:softprob"; p["num_class"] = len(classes)
    return Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale",  StandardScaler()),
        ("model",  XGBClassifier(**p)),
    ])


def tune_on_train(X_tr, y_tr, g_tr, n_iter=25, seed=42):
    """Tuning SUR LE TRAIN uniquement (GroupKFold interne) = partie 'nested'."""
    base = build_pipeline(DEFAULT_PARAMS, y_tr)
    inner = GroupKFold(n_splits=min(4, len(np.unique(g_tr))))
    search = RandomizedSearchCV(base, PARAM_GRID, n_iter=n_iter, cv=inner,
                                scoring="f1_macro", random_state=seed, n_jobs=-1, refit=True)
    search.fit(X_tr, y_tr, groups=g_tr)
    best = {k.replace("model__", ""): v for k, v in search.best_params_.items()}
    return {**DEFAULT_PARAMS, **best}


def evaluate_loso(X, y, groups, target_names, tune=False):
    logo = LeaveOneGroupOut()
    rows, all_true, all_pred, all_proba = [], [], [], []
    importances = None
    n_folds = logo.get_n_splits(groups=groups)
    for i, (tr, te) in enumerate(logo.split(X, y, groups=groups), 1):
        test_subject = groups[te][0]
        X_tr, X_te, y_tr, y_te = X[tr], X[te], y[tr], y[te]
        if len(np.unique(y_tr)) < 2:
            continue
        params = tune_on_train(X_tr, y_tr, groups[tr]) if tune else DEFAULT_PARAMS
        pipe = build_pipeline(params, y_tr); pipe.fit(X_tr, y_tr)
        y_pred = pipe.predict(X_te); proba = pipe.predict_proba(X_te)
        acc = accuracy_score(y_te, y_pred)
        bacc = balanced_accuracy_score(y_te, y_pred)
        f1 = f1_score(y_te, y_pred, average="macro")
        auc = np.nan
        if len(target_names) == 2 and len(np.unique(y_te)) == 2:
            auc = roc_auc_score(y_te, proba[:, 1])
        rows.append({"fold": i, "test_subject": test_subject, "n_test": len(y_te),
                     "accuracy": acc, "balanced_acc": bacc, "f1_macro": f1, "roc_auc": auc})
        all_true.extend(y_te); all_pred.extend(y_pred)
        all_proba.extend(proba[:, 1] if len(target_names) == 2 else [np.nan]*len(y_te))
        imp = pipe.named_steps["model"].feature_importances_
        importances = imp if importances is None else importances + imp
        print(f"  pli {i:2d}/{n_folds} | test={test_subject:>4s} | acc={acc:.3f} f1={f1:.3f}")
    res = pd.DataFrame(rows)
    return res, np.array(all_true), np.array(all_pred), np.array(all_proba), importances/max(1,len(res))


def print_report(res, y_true, y_pred, target_names):
    print("\n" + "="*60 + "\nRESULTATS LOSO (agrégés)\n" + "="*60)
    print(f"Accuracy       : {res['accuracy'].mean():.3f} +/- {res['accuracy'].std():.3f}")
    print(f"Balanced acc.  : {res['balanced_acc'].mean():.3f} +/- {res['balanced_acc'].std():.3f}")
    print(f"F1-macro       : {res['f1_macro'].mean():.3f} +/- {res['f1_macro'].std():.3f}")
    if res["roc_auc"].notna().any():
        print(f"ROC-AUC        : {res['roc_auc'].mean():.3f} +/- {res['roc_auc'].std():.3f}")
    print("\nRapport de classification (fenêtres cumulées) :")
    print(classification_report(y_true, y_pred, target_names=target_names, digits=3))


def plot_confusion(y_true, y_pred, names, path):
    cm = confusion_matrix(y_true, y_pred)
    cmn = cm.astype(float) / cm.sum(axis=1, keepdims=True)
    fig, ax = plt.subplots(figsize=(1.6+1.3*len(names), 1.2+1.1*len(names)))
    im = ax.imshow(cmn, cmap="Blues", vmin=0, vmax=1)
    ax.set_xticks(range(len(names))); ax.set_yticks(range(len(names)))
    ax.set_xticklabels(names, rotation=20); ax.set_yticklabels(names)
    ax.set_xlabel("prédit"); ax.set_ylabel("réel")
    for i in range(len(names)):
        for j in range(len(names)):
            ax.text(j, i, f"{cm[i,j]}\n{cmn[i,j]:.0%}", ha="center", va="center",
                    color="white" if cmn[i,j] > 0.5 else "black", fontsize=10)
    ax.set_title("Matrice de confusion - LOSO"); fig.colorbar(im, fraction=0.046, pad=0.04)
    fig.tight_layout(); fig.savefig(path, dpi=120); plt.close(fig)


def plot_importance(importances, feat_cols, path, top=15):
    imp = pd.Series(importances, index=feat_cols).sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(8, 6))
    imp.head(top)[::-1].plot.barh(ax=ax, color="#5a67d8")
    ax.set_title("Importance des features (XGBoost, moyenne LOSO)"); ax.set_xlabel("importance")
    fig.tight_layout(); fig.savefig(path, dpi=120); plt.close(fig)
    return imp


def train_final_model(X, y, feat_cols, params, path):
    """Modèle FINAL sur TOUS les sujets -> à déployer (téléphone / passerelle)."""
    pipe = build_pipeline(params, y); pipe.fit(X, y)
    joblib.dump({"pipeline": pipe, "features": feat_cols}, path)
    print(f"\nmodèle final sauvegardé : {path}")
    return pipe


def main():
    tune = "--tune" in sys.argv
    target = "target_3class" if "3class" in sys.argv else "target_binary"
    names = list(THREE_CLASS_NAMES.values()) if target == "target_3class" else list(BINARY_NAMES.values())
    print(f"Cible : {target}  |  tuning : {tune}")
    X, y, groups, feat_cols = load_xy(OUTPUT_DIR / "wesad_dataset_clean.csv", target)
    print(f"{X.shape[0]} fenêtres, {X.shape[1]} features, {len(np.unique(groups))} sujets\n")
    res, y_true, y_pred, y_proba, importances = evaluate_loso(X, y, groups, names, tune=tune)
    print_report(res, y_true, y_pred, names)
    res.to_csv(OUTPUT_DIR / "resultats_loso.csv", index=False)
    plot_confusion(y_true, y_pred, names, OUTPUT_DIR / "08_confusion_finale.png")
    imp = plot_importance(importances, feat_cols, OUTPUT_DIR / "09_importance_finale.png")
    summary = {"target": target, "tuned": tune, "n_windows": int(X.shape[0]),
               "n_subjects": int(len(np.unique(groups))),
               "accuracy_mean": float(res["accuracy"].mean()),
               "accuracy_std": float(res["accuracy"].std()),
               "balanced_acc_mean": float(res["balanced_acc"].mean()),
               "f1_macro_mean": float(res["f1_macro"].mean()),
               "roc_auc_mean": float(res["roc_auc"].mean()) if res["roc_auc"].notna().any() else None,
               "top_features": imp.head(8).round(4).to_dict()}
    with open(OUTPUT_DIR / "metriques_resume.json", "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    final_params = tune_on_train(X, y, groups) if tune else DEFAULT_PARAMS
    train_final_model(X, y, feat_cols, final_params, OUTPUT_DIR / "modele_stress_xgb.joblib")


if __name__ == "__main__":
    main()