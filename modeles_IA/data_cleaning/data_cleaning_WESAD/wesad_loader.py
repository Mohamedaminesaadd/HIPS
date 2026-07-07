"""
wesad_loader.py — Charge un SXX.pkl et extrait UNIQUEMENT les 4 signaux mappés.
"""
import pickle
import numpy as np
from wesad_config import WESAD_ROOT, SENSOR_MAP, FS_LABEL


def _acc_magnitude(acc_xyz):
    """Accéléromètre 3 axes (N,3) -> norme (N,). Idem pour ton gyroscope."""
    acc_xyz = np.asarray(acc_xyz, dtype=np.float64)
    return np.sqrt(np.sum(acc_xyz ** 2, axis=1))


def load_subject(subject, root=WESAD_ROOT):
    """Renvoie {'subject', 'signals', 'fs', 'label', 'fs_label'}."""
    pkl_path = root / subject / f"{subject}.pkl"
    if not pkl_path.exists():
        raise FileNotFoundError(
            f"Introuvable : {pkl_path}\n-> vérifie WESAD_ROOT dans wesad_config.py")

    # encoding='latin1' OBLIGATOIRE : pkl WESAD créés en Python 2
    with open(pkl_path, "rb") as f:
        data = pickle.load(f, encoding="latin1")

    signals, fs = {}, {}
    for name, (device, key, sample_rate) in SENSOR_MAP.items():
        raw = np.asarray(data["signal"][device][key], dtype=np.float64)
        sig = _acc_magnitude(raw) if key == "ACC" else raw.reshape(-1)
        signals[name] = sig
        fs[name] = sample_rate

    label = np.asarray(data["label"]).reshape(-1).astype(int)
    return {"subject": subject, "signals": signals, "fs": fs,
            "label": label, "fs_label": FS_LABEL}


def summarize(rec):
    """Résumé texte d'un sujet chargé (debug / EDA rapide)."""
    lines = [f"=== {rec['subject']} ==="]
    dur = len(rec["label"]) / rec["fs_label"]
    lines.append(f"durée totale : {dur:.0f} s ({dur/60:.1f} min)")
    for name, sig in rec["signals"].items():
        lines.append(f"  {name:7s} : {len(sig):>8d} éch. @ {rec['fs'][name]:>4d} Hz "
                     f"| min={np.min(sig):.3g} max={np.max(sig):.3g} mean={np.mean(sig):.3g}")
    vals, counts = np.unique(rec["label"], return_counts=True)
    rep = ", ".join(f"{v}:{c/rec['fs_label']:.0f}s" for v, c in zip(vals, counts))
    lines.append(f"  labels (durée) : {rep}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(summarize(load_subject("S2")))