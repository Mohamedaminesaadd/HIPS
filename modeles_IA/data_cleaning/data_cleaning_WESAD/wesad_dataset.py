"""
wesad_dataset.py — Transforme les signaux bruts en DATASET tabulaire.

Fenêtrage glissant : fenêtres de WINDOW_SECONDS décalées de SHIFT_SECONDS.
Une fenêtre n'est gardée que si >= PURITY % de ses labels = 1 seule condition.
Sortie : outputs/wesad_dataset.csv
"""
import numpy as np
import pandas as pd
from wesad_config import (SUBJECTS, OUTPUT_DIR, FS_LABEL, KEPT_LABELS,
                          LABEL_NAMES, WINDOW_SECONDS, SHIFT_SECONDS, PURITY,
                          BINARY_MAP, THREE_CLASS_MAP)
from wesad_loader import load_subject
from wesad_features import extract_window_features


def _window_label(lab_slice):
    vals, counts = np.unique(lab_slice, return_counts=True)
    return int(vals[np.argmax(counts)]), float(counts.max() / counts.sum())


def build_subject_rows(rec):
    rows = []
    total_sec = len(rec["label"]) / FS_LABEL
    t = 0.0
    while t + WINDOW_SECONDS <= total_sec:
        t0, t1 = t, t + WINDOW_SECONDS
        lab_slice = rec["label"][int(t0 * FS_LABEL):int(t1 * FS_LABEL)]
        dominant, purity = _window_label(lab_slice)
        if dominant not in KEPT_LABELS or purity < PURITY:
            t += SHIFT_SECONDS
            continue

        win, ok = {}, True
        for name in ["ecg", "bvp", "temp", "motion"]:
            fs = rec["fs"][name]
            seg = rec["signals"][name][int(t0 * fs):int(t1 * fs)]
            if len(seg) < 2:
                ok = False
                break
            win[name] = (seg, fs)
        if not ok:
            t += SHIFT_SECONDS
            continue

        feats = extract_window_features(win)
        feats.update({"subject": rec["subject"], "label": dominant,
                      "label_name": LABEL_NAMES[dominant],
                      "target_binary": BINARY_MAP.get(dominant, np.nan),
                      "target_3class": THREE_CLASS_MAP.get(dominant, np.nan)})
        rows.append(feats)
        t += SHIFT_SECONDS
    return rows


def build_dataset(subjects=SUBJECTS, dropna=True):
    all_rows, used = [], []
    for s in subjects:
        try:
            rec = load_subject(s)
        except FileNotFoundError:
            print(f"  (skip {s} : fichier absent)")
            continue
        rows = build_subject_rows(rec)
        all_rows.extend(rows)
        used.append(s)
        print(f"  {s}: {len(rows)} fenêtres")

    df = pd.DataFrame(all_rows)
    if df.empty:
        raise RuntimeError("Aucune fenêtre générée. Vérifie WESAD_ROOT.")
    meta = ["subject", "label", "label_name", "target_binary", "target_3class"]
    feat_cols = [c for c in df.columns if c not in meta]
    df = df[meta + feat_cols]
    n_before = len(df)
    if dropna:
        df = df.dropna(subset=feat_cols).reset_index(drop=True)
    print(f"\nfenêtres totales : {n_before} | après suppression NaN : {len(df)}")
    print(f"sujets utilisés  : {used}")
    return df


def report(df):
    print("\n===== RAPPORT DATASET =====")
    print(f"lignes (fenêtres) : {len(df)}")
    print("\nrépartition par condition :")
    print(df["label_name"].value_counts().to_string())
    print("\ncible binaire (0=non-stress, 1=stress) :")
    print(df["target_binary"].value_counts().to_string())
    print("\nfenêtres par sujet :")
    print(df["subject"].value_counts().to_string())


if __name__ == "__main__":
    df = build_dataset()
    report(df)
    df.to_csv(OUTPUT_DIR / "wesad_dataset.csv", index=False)
    print(f"\ndataset écrit : {OUTPUT_DIR / 'wesad_dataset.csv'}")