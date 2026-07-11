"""
agent_sleep.py — Agent de détection de stress (HPIS).

Reçoit une fenêtre (~60 s) de signaux physiologiques bruts — ECG, BVP/PPG,
température, mouvement — au même format que le pipeline d'entraînement WESAD
(voir modeles_IA/data_cleaning/data_cleaning_WESAD/wesad_config.py::SENSOR_MAP),
en extrait les mêmes features (wesad_features.extract_window_features) et
prédit le stress avec le modèle XGBoost entraîné
(modeles_IA/model/modele_stress_xgb.joblib).

Le module est réutilisé tel quel (pas de duplication du calcul des features)
pour éviter tout écart entre l'entraînement et l'inférence.

Point d'entrée destiné à être branché sur le callback du consumer RabbitMQ de
l'orchestrateur d'agents : predict_stress(payload) -> dict.
"""
import sys
from pathlib import Path

import numpy as np
import joblib

AGENTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = AGENTS_DIR.parent.parent
WESAD_PIPELINE_DIR = PROJECT_ROOT / "modeles_IA" / "data_cleaning" / "data_cleaning_WESAD"
MODEL_PATH = PROJECT_ROOT / "modeles_IA" / "model" / "modele_stress_xgb.joblib"

sys.path.insert(0, str(WESAD_PIPELINE_DIR))
from wesad_features import extract_window_features  # noqa: E402

SIGNAL_NAMES = ("ecg", "bvp", "temp", "motion")


def _vector_magnitude(x, y, z):
    """Norme d'un signal 3 axes (accéléromètre ou gyroscope) -> signal 1D."""
    return np.sqrt(np.asarray(x, dtype=np.float64) ** 2
                    + np.asarray(y, dtype=np.float64) ** 2
                    + np.asarray(z, dtype=np.float64) ** 2)


def _window_from_payload(payload: dict) -> dict:
    """Convertit le message reçu en dict attendu par extract_window_features :
    {'ecg': (signal, fs), 'bvp': (signal, fs), 'temp': (signal, fs), 'motion': (signal, fs)}.

    Format attendu par signal : {"fs": <Hz>, "samples": [...]}.
    Pour "motion", on accepte aussi {"fs": <Hz>, "x": [...], "y": [...], "z": [...]}
    (accéléromètre ou gyroscope 3 axes -> norme calculée ici, comme à l'entraînement).
    """
    missing = [name for name in SIGNAL_NAMES if name not in payload]
    if missing:
        raise ValueError(f"signaux manquants dans le payload : {missing}")

    win = {}
    for name in ("ecg", "bvp", "temp"):
        block = payload[name]
        win[name] = (np.asarray(block["samples"], dtype=np.float64), float(block["fs"]))

    motion = payload["motion"]
    if "samples" in motion:
        mot_sig = np.asarray(motion["samples"], dtype=np.float64)
    else:
        mot_sig = _vector_magnitude(motion["x"], motion["y"], motion["z"])
    win["motion"] = (mot_sig, float(motion["fs"]))
    return win


class StressAgent:
    """Charge le modèle une seule fois, prédit ensuite fenêtre par fenêtre."""

    def __init__(self, model_path: Path = MODEL_PATH):
        bundle = joblib.load(model_path)
        self.pipeline = bundle["pipeline"]
        self.feature_names = bundle["features"]

    def predict(self, payload: dict) -> dict:
        """payload = une fenêtre brute (~60 s de signaux).
        Retourne le label de stress, sa probabilité et les features calculées."""
        win = _window_from_payload(payload)
        feats = extract_window_features(win)

        row = [feats.get(name, np.nan) for name in self.feature_names]
        X = np.asarray([row], dtype=np.float64)

        proba_stress = float(self.pipeline.predict_proba(X)[0, 1])
        pred = int(self.pipeline.predict(X)[0])

        return {
            "subject_id": payload.get("subject_id"),
            "timestamp": payload.get("timestamp"),
            "stress": bool(pred),
            "label": "stress" if pred else "non-stress",
            "probability_stress": proba_stress,
            "features": feats,
        }


_agent: StressAgent | None = None


def get_agent() -> StressAgent:
    global _agent
    if _agent is None:
        _agent = StressAgent()
    return _agent


def predict_stress(payload: dict) -> dict:
    """Point d'entrée simple, à appeler depuis le callback du consumer RabbitMQ."""
    return get_agent().predict(payload)


if __name__ == "__main__":
    # Auto-test local avec un signal synthétique (pas besoin de matériel réel).
    rng = np.random.default_rng(42)
    fake_payload = {
        "subject_id": "test-subject",
        "timestamp": 0,
        "ecg":    {"fs": 700, "samples": rng.normal(0, 1, 700 * 60).tolist()},
        "bvp":    {"fs": 64,  "samples": rng.normal(0, 1, 64 * 60).tolist()},
        "temp":   {"fs": 4,   "samples": (33 + rng.normal(0, 0.1, 4 * 60)).tolist()},
        "motion": {"fs": 700, "samples": (1 + rng.normal(0, 0.05, 700 * 60)).tolist()},
    }
    result = predict_stress(fake_payload)
    print(f"{result['label']} (p_stress={result['probability_stress']:.3f})")
