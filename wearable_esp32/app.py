"""
===========================================================
Application de VISUALISATION avec :
  - Filtrage ECG temps réel (passe-bande 0.5-40 Hz + notch 50 Hz) -> courbe propre
  - 4 panneaux : ECG filtré / ECG brut / PPG (rouge+IR) / Mouvement (acc+gyro)
  - Interprétation live : HR (recalculée sur les pics R), SpO2, température,
    qualité du signal, alerte lead-off (électrodes décrochées), niveau d'activité
  - Rapport de session TXT en fin de session

Dépendances :  pip install websocket-client pyqtgraph pyqt6 scipy numpy
(si besoin)    sudo apt install libxcb-cursor0

"""


import websocket
import threading
import json
import signal
import sys
from collections import deque
from datetime import datetime

import numpy as np
from scipy.signal import butter, sosfilt, sosfilt_zi, iirnotch, tf2sos, find_peaks

import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets, QtCore

# ================= CONFIGURATION =================
ESP32_IP        = "ws://10.42.0.71/ws"
OUTPUT_FILE     = "hpis_session.txt"
FS_ECG          = 250          # fréquence d'échantillonnage ECG (Hz)
BUFFER_DISPLAY  = 750          # points affichés (~3 s à 250 Hz)
BUFFER_ANALYSIS = 2000         # points pour le calcul HR/HRV (~8 s)
TREND_LEN       = 200          # points de tendance (PPG, mouvement, vitals)
MAINS_HZ        = 50           # fréquence secteur (Tunisie = 50 Hz)


# ================= FILTRE ECG TEMPS RÉEL =================
class StreamingECGFilter:
    """Filtre IIR causal à ÉTAT PRÉSERVÉ : on peut lui donner le signal par
    petits morceaux (comme le flux ESP32) sans discontinuité aux jointures.

      1) passe-bande Butterworth 0.5-40 Hz  -> enlève dérive de ligne de base
         (< 0.5 Hz) et bruit HF/EMG (> 40 Hz)
      2) notch 50 Hz                         -> enlève le 50 Hz secteur
    """
    def __init__(self, fs=FS_ECG, low=0.5, high=40.0, notch=MAINS_HZ, q=30.0):
        self.sos_bp = butter(4, [low, high], btype="band", fs=fs, output="sos")
        b_n, a_n = iirnotch(notch, q, fs=fs)
        self.sos_notch = tf2sos(b_n, a_n)
        self._zi_bp = None          # états initialisés au 1er échantillon
        self._zi_notch = None

    def process(self, samples):
        x = np.asarray(samples, dtype=float)
        if x.size == 0:
            return x
        # init des états sur la 1re valeur -> évite un gros transitoire de démarrage
        if self._zi_bp is None:
            self._zi_bp = sosfilt_zi(self.sos_bp) * x[0]
            self._zi_notch = sosfilt_zi(self.sos_notch) * 0.0
        x, self._zi_bp = sosfilt(self.sos_bp, x, zi=self._zi_bp)
        x, self._zi_notch = sosfilt(self.sos_notch, x, zi=self._zi_notch)
        return x


ecg_filter = StreamingECGFilter()

# ================= BUFFERS =================
ecg_raw_buffer  = deque([2048] * BUFFER_DISPLAY, maxlen=BUFFER_DISPLAY)   # brut (ADC)
ecg_filt_buffer = deque([0] * BUFFER_DISPLAY,   maxlen=BUFFER_DISPLAY)    # filtré (affichage)
ecg_analysis    = deque([0] * BUFFER_ANALYSIS,  maxlen=BUFFER_ANALYSIS)   # filtré (HR)

ppg_red_trend = deque([0] * TREND_LEN, maxlen=TREND_LEN)
ppg_ir_trend  = deque([0] * TREND_LEN, maxlen=TREND_LEN)
acc_mag_trend = deque([0] * TREND_LEN, maxlen=TREND_LEN)
gyro_mag_trend= deque([0] * TREND_LEN, maxlen=TREND_LEN)

# dernières valeurs reçues (pour l'interprétation)
latest = {
    "hr": None, "spo2": None, "temp": None,
    "sq": None, "noise": None, "lead_off": None,
    "bat": None, "volt": None, "hr_ecg": None,
}

# ================= STOCKAGE SESSION =================
session_packets = []
ecg_chunk_count = 0
session_start_time = None
ws_app = None


# ================= GUI =================
app = QtWidgets.QApplication([])

root = QtWidgets.QWidget()
root.setWindowTitle("HPIS — Moniteur biométrique temps réel")
root.resize(1300, 850)
layout = QtWidgets.QHBoxLayout(root)

# ---- colonne gauche : les graphes ----
glw = pg.GraphicsLayoutWidget()
layout.addWidget(glw, stretch=4)

pg.setConfigOptions(antialias=True)

# 1) ECG filtré (grand)
p_ecg = glw.addPlot(row=0, col=0, title="ECG filtré (0.5–40 Hz + notch 50 Hz)")
curve_ecg = p_ecg.plot(pen=pg.mkPen((0, 200, 100), width=1.2))
peaks_scatter = p_ecg.plot(pen=None, symbol="t", symbolBrush=(255, 60, 60),
                           symbolSize=9)
p_ecg.setLabel("left", "amplitude")
p_ecg.showGrid(x=False, y=True, alpha=0.2)

# 2) ECG brut (petit, pour comparaison)
p_raw = glw.addPlot(row=1, col=0, title="ECG brut (ADC 12-bit) — avant filtrage")
curve_raw = p_raw.plot(pen=pg.mkPen((150, 150, 150), width=0.8))
p_raw.setYRange(0, 4095)
p_raw.setLabel("left", "ADC")

# 3) PPG rouge + IR
p_ppg = glw.addPlot(row=2, col=0, title="PPG — rouge / infrarouge (MAX30102)")
curve_red = p_ppg.plot(pen=pg.mkPen((230, 60, 60), width=1.2), name="rouge")
curve_ir  = p_ppg.plot(pen=pg.mkPen((120, 60, 230), width=1.2), name="IR")
p_ppg.setLabel("left", "intensité")

# 4) Mouvement (acc + gyro)
p_mot = glw.addPlot(row=3, col=0, title="Mouvement — |accél.| et |gyro| (IMU)")
curve_acc  = p_mot.plot(pen=pg.mkPen((60, 160, 230), width=1.2))
curve_gyro = p_mot.plot(pen=pg.mkPen((230, 160, 60), width=1.2))
p_mot.setLabel("left", "magnitude")
p_mot.setLabel("bottom", "paquets (tendance)")

# l'ECG filtré prend plus de place
glw.ci.layout.setRowStretchFactor(0, 3)
glw.ci.layout.setRowStretchFactor(1, 1)
glw.ci.layout.setRowStretchFactor(2, 2)
glw.ci.layout.setRowStretchFactor(3, 2)

# ---- colonne droite : interprétation live ----
panel = QtWidgets.QTextEdit()
panel.setReadOnly(True)
panel.setMinimumWidth(320)
panel.setStyleSheet("font-family: 'DejaVu Sans Mono', monospace; font-size: 13px;")
layout.addWidget(panel, stretch=1)

root.show()


# ================= INTERPRÉTATION =================
def _color(value, good, warn, reverse=False):
    """Renvoie une couleur (vert/orange/rouge) selon des seuils."""
    if value is None:
        return "#888"
    if reverse:                       # plus c'est haut, pire c'est
        if value < good:  return "#2ecc71"
        if value < warn:  return "#f39c12"
        return "#e74c3c"
    if value >= good:  return "#2ecc71"
    if value >= warn:  return "#f39c12"
    return "#e74c3c"


def build_interpretation():
    """Construit le texte HTML du panneau d'interprétation."""
    def row(label, val, unit="", color="#ddd", note=""):
        v = "—" if val is None else val
        return (f"<div style='margin:6px 0'>"
                f"<span style='color:#aaa'>{label}</span><br>"
                f"<span style='color:{color};font-size:20px;font-weight:bold'>{v}</span>"
                f"<span style='color:#888'> {unit}</span>"
                f"<span style='color:#f39c12;font-size:11px'>  {note}</span></div>")

    hr, spo2, temp = latest["hr"], latest["spo2"], latest["temp"]
    hr_ecg, sq = latest["hr_ecg"], latest["sq"]
    lead_off, noise = latest["lead_off"], latest["noise"]
    bat, volt = latest["bat"], latest["volt"]

    html = ["<h2 style='color:#00c853'>ÉTAT PHYSIOLOGIQUE</h2>"]

    # --- alerte lead-off en priorité ---
    if lead_off:
        html.append("<div style='background:#e74c3c;color:white;padding:8px;"
                    "border-radius:6px;font-weight:bold'>⚠ ÉLECTRODES DÉCROCHÉES<br>"
                    "<span style='font-size:11px'>signal ECG non fiable</span></div>")

    # --- fréquence cardiaque ---
    hr_note = ""
    if hr is not None:
        if hr > 100:   hr_note = "(tachycardie au repos)"
        elif hr < 60:  hr_note = "(bradycardie)"
    html.append(row("Fréquence cardiaque (capteur)", hr, "bpm",
                    _color(hr, 60, 50) if hr and hr < 100 else "#f39c12", hr_note))

    # HR recalculée sur MES pics R (cohérence)
    ecg_note = ""
    if hr_ecg and hr:
        diff = abs(hr_ecg - hr)
        ecg_note = "✓ cohérent" if diff <= 8 else f"écart {diff:.0f} bpm"
    html.append(row("HR recalculée (pics R filtrés)", hr_ecg, "bpm", "#00c853", ecg_note))

    # --- SpO2 ---
    spo2_note = ""
    if spo2 is not None:
        if spo2 < 90:    spo2_note = "(hypoxémie — vérifier)"
        elif spo2 < 95:  spo2_note = "(légèrement bas)"
    html.append(row("Saturation SpO2", spo2, "%", _color(spo2, 95, 90), spo2_note))

    # --- température ---
    html.append(row("Température cutanée", temp, "°C", "#3498db"))

    html.append("<hr style='border-color:#444'>")
    html.append("<h3 style='color:#aaa'>QUALITÉ DU SIGNAL ECG</h3>")

    sq_note = "bon" if (sq or 0) >= 80 else ("moyen" if (sq or 0) >= 50 else "faible")
    html.append(row("Qualité signal", sq, "%", _color(sq, 80, 50), sq_note))
    html.append(row("Niveau de bruit", noise, "", _color(noise, 30, 60, reverse=True)))

    # --- niveau d'activité ---
    gyro_now = gyro_mag_trend[-1] if gyro_mag_trend else 0
    if gyro_now < 20:      act, ac = "Immobile / repos", "#2ecc71"
    elif gyro_now < 100:   act, ac = "Mouvement léger", "#f39c12"
    else:                  act, ac = "Activité intense", "#e74c3c"
    html.append("<hr style='border-color:#444'>")
    html.append("<h3 style='color:#aaa'>ACTIVITÉ</h3>")
    html.append(row("Niveau de mouvement", act, "", ac))

    # --- batterie ---
    html.append("<hr style='border-color:#444'>")
    html.append(row("Batterie", bat, "%", _color(bat, 40, 20)))
    if volt is not None:
        html.append(f"<div style='color:#888;font-size:11px'>tension {volt} V</div>")

    # --- résumé session ---
    n = len(session_packets)
    dur = (datetime.now() - session_start_time).total_seconds() if session_start_time else 0
    html.append("<hr style='border-color:#444'>")
    html.append(f"<div style='color:#666;font-size:11px'>{n} paquets · "
                f"{int(dur//60)}m{int(dur%60)}s · {ecg_chunk_count} trames ECG</div>")

    return "".join(html)


# ================= CALCUL HR SUR LES PICS R =================
def compute_hr_from_ecg():
    """Détecte les pics R sur l'ECG filtré et estime la HR (cross-check capteur)."""
    sig = np.array(ecg_analysis, dtype=float)
    if np.std(sig) < 1e-6:
        return
    peaks, _ = find_peaks(sig, distance=int(0.33 * FS_ECG),
                          height=np.mean(sig) + 0.5 * np.std(sig))
    if len(peaks) >= 3:
        rr = np.diff(peaks) / FS_ECG
        rr = rr[(rr > 0.33) & (rr < 1.5)]      # 40..180 bpm
        if len(rr) >= 2:
            latest["hr_ecg"] = round(60.0 / np.median(rr), 1)


# ================= TIMERS D'AFFICHAGE =================
def update_plots():
    curve_ecg.setData(list(ecg_filt_buffer))
    curve_raw.setData(list(ecg_raw_buffer))
    curve_red.setData(list(ppg_red_trend))
    curve_ir.setData(list(ppg_ir_trend))
    curve_acc.setData(list(acc_mag_trend))
    curve_gyro.setData(list(gyro_mag_trend))
    # pics R sur la fenêtre affichée
    sig = np.array(ecg_filt_buffer, dtype=float)
    if np.std(sig) > 1e-6:
        pk, _ = find_peaks(sig, distance=int(0.33 * FS_ECG),
                           height=np.mean(sig) + 0.5 * np.std(sig))
        peaks_scatter.setData(pk, sig[pk])


def update_interpretation():
    compute_hr_from_ecg()
    panel.setHtml(build_interpretation())


timer_plot = QtCore.QTimer(); timer_plot.timeout.connect(update_plots); timer_plot.start(30)
timer_interp = QtCore.QTimer(); timer_interp.timeout.connect(update_interpretation); timer_interp.start(500)


# ================= WEBSOCKET CALLBACKS =================
def on_message(ws_obj, message):
    global ecg_chunk_count, session_start_time
    try:
        # ── Flux ECG léger : "ECG:v1,v2,...,v10" ──
        if message.startswith("ECG:"):
            ecg_chunk_count += 1
            vals = [int(v) for v in message[4:].split(",") if v.strip().lstrip("-").isdigit()]
            if not vals:
                return
            # 1) on garde le brut pour comparaison
            ecg_raw_buffer.extend(vals)
            # 2) FILTRAGE temps réel (état préservé entre chunks)
            filt = ecg_filter.process(vals)
            ecg_filt_buffer.extend(filt)
            ecg_analysis.extend(filt)
            return

        # ── Paquet JSON complet : "JSON:{...}" ──
        if message.startswith("JSON:"):
            packet = json.loads(message[5:])
            if session_start_time is None:
                session_start_time = datetime.now()
                print(f"[HPIS] Session démarrée à {session_start_time.strftime('%H:%M:%S')}")

            # --- mise à jour des dernières valeurs (interprétation) ---
            v = packet.get("vitals", {})
            latest["hr"]   = v.get("heart_rate", latest["hr"])
            latest["spo2"] = v.get("spo2", latest["spo2"])
            latest["temp"] = v.get("temperature", latest["temp"])
            e = packet.get("ecg", {})
            latest["sq"]       = e.get("signal_quality", latest["sq"])
            latest["noise"]    = e.get("noise_level", latest["noise"])
            latest["lead_off"] = e.get("lead_off", latest["lead_off"])
            b = packet.get("battery", {})
            latest["bat"]  = b.get("level", latest["bat"])
            latest["volt"] = b.get("voltage", latest["volt"])

            # --- PPG (tendance) ---
            ppg = packet.get("ppg", {})
            if "red" in ppg: ppg_red_trend.append(ppg["red"])
            if "ir" in ppg:  ppg_ir_trend.append(ppg["ir"])

            # --- IMU -> magnitudes (tendance) ---
            imu = packet.get("imu", {})
            if "acc" in imu:
                a = imu["acc"]
                acc_mag_trend.append((a.get("x",0)**2 + a.get("y",0)**2 + a.get("z",0)**2) ** 0.5)
            if "gyro" in imu:
                g = imu["gyro"]
                gyro_mag_trend.append((g.get("x",0)**2 + g.get("y",0)**2 + g.get("z",0)**2) ** 0.5)

            # on ne stocke pas les 250 samples ECG (trop volumineux)
            if "ecg" in packet and "samples" in packet["ecg"]:
                del packet["ecg"]["samples"]
            session_packets.append(packet)

            if len(session_packets) % 10 == 0:
                print(f"[HPIS] {len(session_packets)} paquets  |  HR={latest['hr']}  "
                      f"SpO2={latest['spo2']}  Temp={latest['temp']}")

    except Exception as ex:
        print(f"[HPIS] Erreur on_message : {ex}")


def on_open(ws_obj):
    print(f"[HPIS] Connecté à {ESP32_IP}")
    print("[HPIS] Collecte en cours... Fermer la fenêtre pour arrêter et générer le rapport.")


def on_error(ws_obj, error):
    print(f"[HPIS] Erreur WebSocket : {error}")


def on_close(ws_obj, code, msg):
    print("[HPIS] Connexion WebSocket fermée.")


# ================= CALCULS AGRÉGATS (rapport) =================
def safe_avg(x): return round(sum(x) / len(x), 2) if x else None
def safe_min(x): return min(x) if x else None
def safe_max(x): return max(x) if x else None


def generate_report():
    now = datetime.now()
    n_packets = len(session_packets)
    duration_s = (now - session_start_time).total_seconds() if session_start_time else 0

    hr_list   = [p["vitals"]["heart_rate"]  for p in session_packets if "vitals" in p]
    spo2_list = [p["vitals"]["spo2"]        for p in session_packets if "vitals" in p]
    temp_list = [p["vitals"]["temperature"] for p in session_packets if "vitals" in p]
    bat_list  = [p["battery"]["level"]      for p in session_packets if "battery" in p]
    volt_list = [p["battery"]["voltage"]    for p in session_packets if "battery" in p]
    sq_list   = [p["ecg"]["signal_quality"] for p in session_packets if "ecg" in p]
    nl_list   = [p["ecg"]["noise_level"]    for p in session_packets if "ecg" in p]
    lo_list   = [p["ecg"]["lead_off"]       for p in session_packets if "ecg" in p]

    L = []
    L.append("=" * 78)
    L.append("  HPIS — RAPPORT DE SESSION BIOMÉTRIQUE")
    L.append("  Human Performance Intelligence System")
    L.append("=" * 78)
    L.append("")
    L.append("  INFORMATIONS DE SESSION")
    L.append("-" * 78)
    L.append(f"  Début   : {session_start_time.strftime('%Y-%m-%d %H:%M:%S') if session_start_time else 'N/A'}")
    L.append(f"  Fin     : {now.strftime('%Y-%m-%d %H:%M:%S')}")
    L.append(f"  Durée   : {int(duration_s//60)} min {int(duration_s%60)} sec")
    L.append(f"  Source  : {ESP32_IP}")
    L.append(f"  Paquets JSON : {n_packets}   |   Trames ECG : {ecg_chunk_count}")
    L.append(f"  Échantillons ECG (≈) : {n_packets * FS_ECG}  (@ {FS_ECG} Hz)")
    L.append("")
    L.append("  VITALS")
    L.append("-" * 78)
    L.append(f"  HR   (bpm) : moy {safe_avg(hr_list)}  min {safe_min(hr_list)}  max {safe_max(hr_list)}")
    L.append(f"  SpO2 (%)   : moy {safe_avg(spo2_list)}  min {safe_min(spo2_list)}  max {safe_max(spo2_list)}")
    L.append(f"  Temp (°C)  : moy {safe_avg(temp_list)}  min {safe_min(temp_list)}  max {safe_max(temp_list)}")
    L.append("")
    L.append("  QUALITÉ ECG")
    L.append("-" * 78)
    L.append(f"  Qualité (%)  : moy {safe_avg(sq_list)}  min {safe_min(sq_list)}")
    L.append(f"  Bruit        : moy {safe_avg(nl_list)}  max {safe_max(nl_list)}")
    L.append(f"  Lead-off     : {sum(1 for v in lo_list if v)} fois / {len(lo_list)} paquets")
    L.append("")
    L.append("  BATTERIE")
    L.append("-" * 78)
    L.append(f"  Niveau (%) : début {bat_list[0] if bat_list else 'N/A'}  "
             f"fin {bat_list[-1] if bat_list else 'N/A'}  moy {safe_avg(bat_list)}")
    L.append(f"  Tension (V): moy {safe_avg(volt_list)}")
    L.append("")
    L.append("  JOURNAL DES PAQUETS")
    L.append("-" * 78)
    L.append(f"  {'#':<5}{'t(ms)':<10}{'HR':>4}{'SpO2':>6}{'Temp':>7}{'SQ':>5}{'Bruit':>7}{'Bat':>5}")
    for p in session_packets:
        L.append(f"  {str(p.get('packet','?')):<5}{str(p.get('timestamp_ms','?')):<10}"
                 f"{str(p.get('vitals',{}).get('heart_rate','?')):>4}"
                 f"{str(p.get('vitals',{}).get('spo2','?')):>6}"
                 f"{str(p.get('vitals',{}).get('temperature','?')):>7}"
                 f"{str(p.get('ecg',{}).get('signal_quality','?')):>5}"
                 f"{str(p.get('ecg',{}).get('noise_level','?')):>7}"
                 f"{str(p.get('battery',{}).get('level','?')):>5}")
    L.append("")
    L.append("=" * 78)
    L.append(f"  Généré le {now.strftime('%Y-%m-%d %H:%M:%S')}  —  {OUTPUT_FILE}")
    L.append("  Projet HPIS — Mohamed Amine Saad — ENIS 2025-2026")
    L.append("=" * 78)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    print(f"\n[HPIS] Rapport sauvegardé → {OUTPUT_FILE}  ({n_packets} paquets, {round(duration_s,1)} s)")


# ================= ARRÊT PROPRE =================
def shutdown():
    print("\n[HPIS] Arrêt de la session...")
    if ws_app:
        ws_app.close()
    generate_report()
    QtWidgets.QApplication.quit()


def signal_handler(sig, frame):
    shutdown()

signal.signal(signal.SIGINT, signal_handler)
app.aboutToQuit.connect(shutdown)


# ================= LANCEMENT =================
ws_app = websocket.WebSocketApp(
    ESP32_IP, on_message=on_message, on_open=on_open,
    on_error=on_error, on_close=on_close,
)
threading.Thread(target=ws_app.run_forever, daemon=True).start()

app.exec()