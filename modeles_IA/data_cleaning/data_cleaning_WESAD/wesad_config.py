"""
wesad_config.py — Configuration centrale du pipeline WESAD -> détection de stress (HPIS).
"""
from pathlib import Path

# ---------- 1. CHEMINS ----------
WESAD_ROOT = Path("WESAD")          # <-- dossier contenant S2/, S3/, ... S17/
OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

# S1 et S12 n'existent pas dans WESAD
SUBJECTS = [f"S{i}" for i in range(2, 18) if i != 12]

# ---------- 2. FRÉQUENCES NATIVES (Hz) ----------
FS_CHEST = 700          # ECG, ACC, Temp... du RespiBAN (chest)
FS_WRIST_BVP = 64       # BVP (PPG) du brassard E4
FS_WRIST_ACC = 32
FS_WRIST_EDA = 4
FS_WRIST_TEMP = 4
FS_LABEL = 700

# ---------- 3. MAPPING : TES CAPTEURS -> SIGNAUX WESAD ----------
#   AD8232 (ECG)          -> chest/ECG   (700 Hz)
#   MAX30102 (PPG/HR)     -> wrist/BVP   (64 Hz)
#   Capteur température   -> wrist/TEMP  (4 Hz)
#   Gyroscope (mouvement) -> chest/ACC   (700 Hz)  *proxy : voir note*
#
# NOTE gyroscope : WESAD contient un ACCÉLÉROMÈTRE, pas un gyroscope. Les deux
# mesurent l'agitation, donc les features d'activité se transfèrent. Sur ton
# device, tu remplaces l'ACC par la norme des 3 axes du gyro.
SENSOR_MAP = {
    "ecg":    ("chest", "ECG",  FS_CHEST),      # AD8232
    "bvp":    ("wrist", "BVP",  FS_WRIST_BVP),  # MAX30102
    "temp":   ("wrist", "TEMP", FS_WRIST_TEMP), # capteur température
    "motion": ("chest", "ACC",  FS_CHEST),      # gyroscope (proxy = ACC)
}

# ---------- 4. LABELS WESAD ----------
# 0=transitoire  1=baseline  2=stress  3=amusement  4=meditation  5/6/7=ignore
LABEL_NAMES = {0: "undefined", 1: "baseline", 2: "stress", 3: "amusement",
               4: "meditation", 5: "ignore", 6: "ignore", 7: "ignore"}
KEPT_LABELS = [1, 2, 3, 4]

# Cible binaire : stress vs non-stress (setup principal HPIS)
BINARY_MAP = {1: 0, 2: 1, 3: 0, 4: 0}
BINARY_NAMES = {0: "non-stress", 1: "stress"}

# Cible 3 classes (setup du papier WESAD, meditation exclue)
THREE_CLASS_LABELS = [1, 2, 3]
THREE_CLASS_MAP = {1: 0, 2: 1, 3: 2}
THREE_CLASS_NAMES = {0: "baseline", 1: "stress", 2: "amusement"}

# ---------- 5. FENÊTRAGE ----------
WINDOW_SECONDS = 60      # taille de fenêtre (comme le papier WESAD)
SHIFT_SECONDS = 5        # décalage entre 2 fenêtres (overlap)
PURITY = 0.90            # fenêtre gardée si >= 90 % des labels = 1 seule condition