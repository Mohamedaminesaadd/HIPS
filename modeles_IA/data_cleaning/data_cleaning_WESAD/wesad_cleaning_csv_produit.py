"""
wesad_clean.py — Data cleaning du dataset de features
(wesad_dataset.csv -> wesad_dataset_clean.csv).

  1. DIAGNOSTIC : NaN, doublons, colonnes constantes, valeurs impossibles,
                  cohérence ECG vs PPG.
  2. NETTOYAGE  : opérations SÛRES basées sur le DOMAINE (sans data leakage) :
                  dedup, colonnes constantes, clipping physiologique, drapeaux qualité.
  3. EXPORT     : wesad_dataset_clean.csv

ATTENTION — ce qu'on NE fait PAS ici : imputation moyenne/médiane et
StandardScaler dépendent de stats du dataset. Les appliquer sur tout le dataset
maintenant = data leakage. -> voir make_preprocessing_pipeline() en bas.
"""
import numpy as np
import pandas as pd
from wesad_config import OUTPUT_DIR

META = ["subject", "label", "label_name", "target_binary", "target_3class"]

# Bornes PHYSIOLOGIQUES (savoir métier, PAS des stats du dataset)
# un suffixe -> s'applique à ecg_* ET bvp_*
PHYSIO_RANGES = {
    "mean_hr": (40, 180),     # bpm
    "mean_rr": (333, 1500),   # ms  (= 40..180 bpm)
    "sdnn":    (0, 200),      # ms  (>200 sur 60 s = artefact)
    "rmssd":   (0, 200),      # ms
    "pnn50":   (0, 100),      # %
    "lf_hf":   (0, 10),       # ratio (>10 = artefact quasi certain)
}
TEMP_RANGE = (20, 42)         # °C
HR_AGREEMENT_BPM = 10.0       # écart max toléré FC_ecg vs FC_ppg


# ===== 1. DIAGNOSTIC =====
def diagnose(df):
    print("=" * 64, "\nDIAGNOSTIC QUALITE\n", "=" * 64, sep="")
    print(f"dimensions        : {df.shape[0]} lignes x {df.shape[1]} colonnes")
    feat_cols = [c for c in df.columns if c not in META]

    na = df[feat_cols].isna().sum(); na = na[na > 0]
    print(f"\n[NaN] colonnes manquantes : {'aucune' if na.empty else ''}")
    if not na.empty:
        print(na.to_string())

    print(f"\n[doublons] lignes identiques : {df.duplicated().sum()}")
    const = [c for c in feat_cols if df[c].nunique(dropna=True) <= 1]
    print(f"[constantes] variance nulle : {const if const else 'aucune'}")

    print("\n[physio] valeurs hors bornes plausibles :")
    any_viol = False
    for suffix, (lo, hi) in PHYSIO_RANGES.items():
        for prefix in ("ecg", "bvp"):
            col = f"{prefix}_{suffix}"
            if col in df.columns:
                bad = ((df[col] < lo) | (df[col] > hi)).sum()
                if bad:
                    any_viol = True
                    print(f"   {col:14s} : {bad:4d} hors [{lo}, {hi}]")
    for col in ("temp_mean", "temp_min", "temp_max"):
        if col in df.columns:
            bad = ((df[col] < TEMP_RANGE[0]) | (df[col] > TEMP_RANGE[1])).sum()
            if bad:
                any_viol = True
                print(f"   {col:14s} : {bad:4d} hors {TEMP_RANGE}")
    if not any_viol:
        print("   aucune")

    if {"ecg_mean_hr", "bvp_mean_hr"}.issubset(df.columns):
        diff = (df["ecg_mean_hr"] - df["bvp_mean_hr"]).abs()
        print(f"\n[cohérence ECG/PPG] |FC_ecg - FC_ppg| : "
              f"moyenne={diff.mean():.1f} bpm, max={diff.max():.1f} bpm")
        n_bad = (diff > HR_AGREEMENT_BPM).sum()
        print(f"   fenêtres PPG peu fiables (>{HR_AGREEMENT_BPM} bpm) : "
              f"{n_bad} ({100*n_bad/len(df):.1f} %)")
        if {"ecg_rmssd", "bvp_rmssd"}.issubset(df.columns):
            r_ecg, r_bvp = df["ecg_rmssd"].median(), df["bvp_rmssd"].median()
            print(f"   RMSSD médian  ECG={r_ecg:.0f} ms  vs  PPG={r_bvp:.0f} ms", end="")
            print("  <-- PPG gonflé (faux pics probables)" if r_bvp > 2 * r_ecg else "")
    print()


# ===== 2. NETTOYAGE =====
def clean(df, clip_physio=True, add_flags=True, drop_ppg_hrv=False,
          drop_unreliable_ppg_rows=False):
    """Retourne (df_clean, journal). Toutes opérations sûres (pas de leakage)."""
    log, df = [], df.copy()
    feat_cols = [c for c in df.columns if c not in META]

    # a) doublons
    n0 = len(df); df = df.drop_duplicates().reset_index(drop=True)
    log.append(f"doublons supprimés : {n0 - len(df)}")

    # b) colonnes constantes
    const = [c for c in feat_cols if df[c].nunique(dropna=True) <= 1]
    if const:
        df = df.drop(columns=const); log.append(f"colonnes constantes : {const}")
    feat_cols = [c for c in df.columns if c not in META]

    # c) drapeaux de qualité ECG/PPG
    if add_flags and {"ecg_mean_hr", "bvp_mean_hr"}.issubset(df.columns):
        df["ppg_hr_diff"] = (df["ecg_mean_hr"] - df["bvp_mean_hr"]).abs()
        df["ppg_reliable"] = (df["ppg_hr_diff"] <= HR_AGREEMENT_BPM).astype(int)
        log.append(f"drapeaux : ppg_hr_diff, ppg_reliable "
                   f"({df['ppg_reliable'].mean()*100:.0f} % fiables)")

    # d) suppression optionnelle des fenêtres PPG non fiables
    if drop_unreliable_ppg_rows and "ppg_reliable" in df.columns:
        n0 = len(df); df = df[df["ppg_reliable"] == 1].reset_index(drop=True)
        log.append(f"fenêtres PPG non fiables supprimées : {n0 - len(df)}")

    # e) suppression optionnelle des features de variabilité PPG (bruitées)
    if drop_ppg_hrv:
        to_drop = [c for c in ["bvp_sdnn", "bvp_rmssd", "bvp_pnn50", "bvp_lf_hf"]
                   if c in df.columns]
        df = df.drop(columns=to_drop); log.append(f"variabilité PPG supprimée : {to_drop}")

    # f) clipping physiologique (winsorisation aux bornes du domaine)
    if clip_physio:
        n_clipped = 0
        for suffix, (lo, hi) in PHYSIO_RANGES.items():
            for prefix in ("ecg", "bvp"):
                col = f"{prefix}_{suffix}"
                if col in df.columns:
                    before = df[col].copy()
                    df[col] = df[col].clip(lo, hi)
                    n_clipped += (before != df[col]).sum()
        for col in ("temp_mean", "temp_min", "temp_max"):
            if col in df.columns:
                df[col] = df[col].clip(*TEMP_RANGE)
        log.append(f"valeurs clippées aux bornes physio : {int(n_clipped)}")

    return df, log


# ===== 3. PIPELINE fold-safe (à utiliser DANS la validation, PAS ici) =====
def make_preprocessing_pipeline(model):
    """Imputation + standardisation + modèle dans un Pipeline sklearn.
    Le .fit() ne voit QUE le train du pli courant => aucune fuite.

        pipe = make_preprocessing_pipeline(XGBClassifier(...))
        logo = LeaveOneGroupOut()
        for tr, te in logo.split(X, y, groups=subjects):
            pipe.fit(X[tr], y[tr]); pipe.score(X[te], y[te])
    """
    from sklearn.pipeline import Pipeline
    from sklearn.impute import SimpleImputer
    from sklearn.preprocessing import StandardScaler
    return Pipeline([
        ("impute", SimpleImputer(strategy="median")),  # NaN restants -> médiane du TRAIN
        ("scale",  StandardScaler()),                  # centrage/réduction sur le TRAIN
        ("model",  model),
    ])


def main(in_path=OUTPUT_DIR / "wesad_dataset.csv",
         out_path=OUTPUT_DIR / "wesad_dataset_clean.csv"):
    df = pd.read_csv(in_path)
    diagnose(df)
    # recommandé : on garde tout, on clippe, on ajoute les flags.
    # mets drop_ppg_hrv=True si le PPG reste trop bruité.
    df_clean, log = clean(df, clip_physio=True, add_flags=True,
                          drop_ppg_hrv=False, drop_unreliable_ppg_rows=False)
    print("=" * 64, "\nNETTOYAGE\n", "=" * 64, sep="")
    for line in log:
        print("  -", line)
    print(f"\ndimensions finales : {df_clean.shape[0]} x {df_clean.shape[1]}")
    df_clean.to_csv(out_path, index=False)
    print(f"dataset propre écrit : {out_path}")
    return df_clean


if __name__ == "__main__":
    main()