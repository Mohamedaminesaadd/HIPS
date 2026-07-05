import websocket
import threading
import json
import signal
import sys
from collections import deque
from datetime import datetime

import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets, QtCore

# ================= CONFIGURATION =================
ESP32_IP       = "ws://10.42.0.71/ws"   # ⚠️  Remplacer par l'IP réelle de l'ESP32
OUTPUT_FILE    = "hpis_session.txt"
BUFFER_DISPLAY = 500                     # points affichés dans l'oscilloscope

# ================= BUFFER ECG (affichage) =================
ecg_buffer = deque([0] * BUFFER_DISPLAY, maxlen=BUFFER_DISPLAY)

# ================= STOCKAGE SESSION =================
# Chaque paquet JSON reçu est stocké ici pour le rapport final
session_packets = []          # liste de dict (un par paquet JSON complet)
ecg_chunk_count = 0           # nombre de trames ECG légères reçues
session_start_time = None     # datetime de début de session
ws_app = None                 # référence globale au websocket


# ================= GUI =================
app = QtWidgets.QApplication([])

win = pg.GraphicsLayoutWidget(show=True)
win.setWindowTitle("HPIS — ECG Real-Time Monitor")

plot = win.addPlot(title="ECG Signal (temps réel)")
curve = plot.plot(pen=pg.mkPen(color=(0, 200, 100), width=1))
plot.setYRange(0, 4095)
plot.setLabel("left",  "Amplitude (ADC 12-bit)")
plot.setLabel("bottom", "Échantillons (fenêtre glissante)")

def update_plot():
    curve.setData(list(ecg_buffer))

timer = QtCore.QTimer()
timer.timeout.connect(update_plot)
timer.start(20)   # 50 fps


# ================= CALCULS AGREGATS =================
def safe_avg(values):
    return round(sum(values) / len(values), 2) if values else None

def safe_min(values):
    return min(values) if values else None

def safe_max(values):
    return max(values) if values else None


# ================= GENERATION DU RAPPORT TXT =================
def generate_report():
    now        = datetime.now()
    n_packets  = len(session_packets)
    duration_s = (now - session_start_time).total_seconds() if session_start_time else 0

    # --- agréger les vitals sur toute la session ---
    hr_list    = [p["vitals"]["heart_rate"]  for p in session_packets if "vitals" in p]
    spo2_list  = [p["vitals"]["spo2"]        for p in session_packets if "vitals" in p]
    temp_list  = [p["vitals"]["temperature"] for p in session_packets if "vitals" in p]

    bat_list   = [p["battery"]["level"]      for p in session_packets if "battery" in p]
    volt_list  = [p["battery"]["voltage"]    for p in session_packets if "battery" in p]

    ppg_red_list = [p["ppg"]["red"] for p in session_packets if "ppg" in p]
    ppg_ir_list  = [p["ppg"]["ir"]  for p in session_packets if "ppg" in p]

    acc_x  = [p["imu"]["acc"]["x"] for p in session_packets if "imu" in p]
    acc_y  = [p["imu"]["acc"]["y"] for p in session_packets if "imu" in p]
    acc_z  = [p["imu"]["acc"]["z"] for p in session_packets if "imu" in p]
    gyro_x = [p["imu"]["gyro"]["x"] for p in session_packets if "imu" in p]
    gyro_y = [p["imu"]["gyro"]["y"] for p in session_packets if "imu" in p]
    gyro_z = [p["imu"]["gyro"]["z"] for p in session_packets if "imu" in p]

    sq_list = [p["ecg"]["signal_quality"] for p in session_packets if "ecg" in p]
    nl_list = [p["ecg"]["noise_level"]    for p in session_packets if "ecg" in p]
    lo_list = [p["ecg"]["lead_off"]       for p in session_packets if "ecg" in p]

    # nombre total d'échantillons ECG collectés
    total_ecg_samples = n_packets * 250

    # --- écriture du fichier ---
    lines = []
    lines.append("╔══════════════════════════════════════════════════════════════════════════════╗")
    lines.append("║              HPIS — RAPPORT DE SESSION BIOMÉTRIQUE                         ║")
    lines.append("║              Human Performance Intelligence System                          ║")
    lines.append("╚══════════════════════════════════════════════════════════════════════════════╝")
    lines.append("")

    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("  INFORMATIONS DE SESSION")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"  Date et heure de début   : {session_start_time.strftime('%Y-%m-%d  %H:%M:%S') if session_start_time else 'N/A'}")
    lines.append(f"  Date et heure de fin     : {now.strftime('%Y-%m-%d  %H:%M:%S')}")
    lines.append(f"  Durée totale             : {int(duration_s // 60)} min {int(duration_s % 60)} sec  ({round(duration_s, 1)} s)")
    lines.append(f"  Source ESP32             : {ESP32_IP}")
    lines.append(f"  Paquets JSON reçus       : {n_packets}")
    lines.append(f"  Trames ECG légères       : {ecg_chunk_count}")
    lines.append(f"  Échantillons ECG totaux  : {total_ecg_samples}  (@ 250 Hz)")
    lines.append("")

    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("  VITALS — FRÉQUENCE CARDIAQUE, SPO2, TEMPÉRATURE")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"  Fréquence cardiaque (bpm)")
    lines.append(f"      Moyenne : {safe_avg(hr_list)}")
    lines.append(f"      Min     : {safe_min(hr_list)}")
    lines.append(f"      Max     : {safe_max(hr_list)}")
    lines.append(f"")
    lines.append(f"  Saturation en oxygène SpO2 (%)")
    lines.append(f"      Moyenne : {safe_avg(spo2_list)}")
    lines.append(f"      Min     : {safe_min(spo2_list)}")
    lines.append(f"      Max     : {safe_max(spo2_list)}")
    lines.append(f"")
    lines.append(f"  Température cutanée (°C)")
    lines.append(f"      Moyenne : {safe_avg(temp_list)}")
    lines.append(f"      Min     : {safe_min(temp_list)}")
    lines.append(f"      Max     : {safe_max(temp_list)}")
    lines.append("")

    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("  ECG — QUALITÉ DU SIGNAL")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"  Qualité signal (%)")
    lines.append(f"      Moyenne : {safe_avg(sq_list)}")
    lines.append(f"      Min     : {safe_min(sq_list)}")
    lines.append(f"  Niveau de bruit")
    lines.append(f"      Moyenne : {safe_avg(nl_list)}")
    lines.append(f"      Max     : {safe_max(nl_list)}")
    lo_count = sum(1 for v in lo_list if v)
    lines.append(f"  Électrodes décrochées (lead-off) : {lo_count} fois sur {len(lo_list)} paquets")
    lines.append("")

    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("  PPG — PHOTOPLÉTHYSMOGRAPHIE (rouge + infrarouge)")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"  Canal rouge")
    lines.append(f"      Moyenne : {safe_avg(ppg_red_list)}")
    lines.append(f"      Min     : {safe_min(ppg_red_list)}")
    lines.append(f"      Max     : {safe_max(ppg_red_list)}")
    lines.append(f"  Canal infrarouge")
    lines.append(f"      Moyenne : {safe_avg(ppg_ir_list)}")
    lines.append(f"      Min     : {safe_min(ppg_ir_list)}")
    lines.append(f"      Max     : {safe_max(ppg_ir_list)}")
    lines.append("")

    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("  IMU — ACCÉLÉROMÈTRE & GYROSCOPE")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"  Accélération (m/s²)")
    lines.append(f"      X  →  moy {safe_avg(acc_x)}   min {safe_min(acc_x)}   max {safe_max(acc_x)}")
    lines.append(f"      Y  →  moy {safe_avg(acc_y)}   min {safe_min(acc_y)}   max {safe_max(acc_y)}")
    lines.append(f"      Z  →  moy {safe_avg(acc_z)}   min {safe_min(acc_z)}   max {safe_max(acc_z)}")
    lines.append(f"  Gyroscope (deg/s)")
    lines.append(f"      X  →  moy {safe_avg(gyro_x)}   min {safe_min(gyro_x)}   max {safe_max(gyro_x)}")
    lines.append(f"      Y  →  moy {safe_avg(gyro_y)}   min {safe_min(gyro_y)}   max {safe_max(gyro_y)}")
    lines.append(f"      Z  →  moy {safe_avg(gyro_z)}   min {safe_min(gyro_z)}   max {safe_max(gyro_z)}")
    lines.append("")

    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("  BATTERIE")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"  Niveau (%)")
    lines.append(f"      Début   : {bat_list[0] if bat_list else 'N/A'}")
    lines.append(f"      Fin     : {bat_list[-1] if bat_list else 'N/A'}")
    lines.append(f"      Moyenne : {safe_avg(bat_list)}")
    lines.append(f"  Tension (V)")
    lines.append(f"      Début   : {volt_list[0] if volt_list else 'N/A'}")
    lines.append(f"      Fin     : {volt_list[-1] if volt_list else 'N/A'}")
    lines.append(f"      Moyenne : {safe_avg(volt_list)}")
    lines.append("")

    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("  JOURNAL CHRONOLOGIQUE DES PAQUETS JSON")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"  {'#PKT':<6} {'t (ms)':<10} {'HR':>4} {'SpO2':>5} {'Temp':>6} {'HRV_SQ':>7} {'Bruit':>6} {'Bat%':>5} {'Volt':>5}")
    lines.append(f"  {'─'*6} {'─'*10} {'─'*4} {'─'*5} {'─'*6} {'─'*7} {'─'*6} {'─'*5} {'─'*5}")

    for p in session_packets:
        pkt  = p.get("packet", "?")
        ts   = p.get("timestamp_ms", "?")
        hr   = p.get("vitals", {}).get("heart_rate", "?")
        spo2 = p.get("vitals", {}).get("spo2", "?")
        temp = p.get("vitals", {}).get("temperature", "?")
        sq   = p.get("ecg", {}).get("signal_quality", "?")
        nl   = p.get("ecg", {}).get("noise_level", "?")
        bat  = p.get("battery", {}).get("level", "?")
        volt = p.get("battery", {}).get("voltage", "?")
        lines.append(f"  {str(pkt):<6} {str(ts):<10} {str(hr):>4} {str(spo2):>5} {str(temp):>6} {str(sq):>7} {str(nl):>6} {str(bat):>5} {str(volt):>5}")

    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"  Rapport généré le : {now.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"  Fichier           : {OUTPUT_FILE}")
    lines.append("  Projet            : HPIS — Human Performance Intelligence System")
    lines.append("  Auteur            : Mohamed Amine Saad — ENIS 2025–2026")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\n[HPIS] Rapport sauvegardé → {OUTPUT_FILE}  ({n_packets} paquets, {round(duration_s,1)} s)")


# ================= WEBSOCKET CALLBACKS =================
def on_message(ws_obj, message):
    global ecg_chunk_count, session_start_time

    try:
        # ── Flux ECG léger : "ECG:v1,v2,...,v10" ──
        if message.startswith("ECG:"):
            ecg_chunk_count += 1
            values = message[4:].split(",")
            for v in values:
                v = v.strip()
                if v.isdigit():
                    ecg_buffer.append(int(v))
            return

        # ── Paquet JSON complet : "JSON:{...}" ──
        if message.startswith("JSON:"):
            raw = message[5:]
            packet = json.loads(raw)

            # horodatage de début de session au premier paquet reçu
            if session_start_time is None:
                session_start_time = datetime.now()
                print(f"[HPIS] Session démarrée à {session_start_time.strftime('%H:%M:%S')}")

            # on ne stocke pas les 250 samples ECG (trop volumineux)
            # on conserve uniquement les métadonnées ECG
            if "ecg" in packet and "samples" in packet["ecg"]:
                del packet["ecg"]["samples"]

            session_packets.append(packet)

            n = len(session_packets)
            if n % 10 == 0:
                print(f"[HPIS] {n} paquets collectés  |  "
                      f"HR={packet.get('vitals',{}).get('heart_rate','?')} bpm  |  "
                      f"SpO2={packet.get('vitals',{}).get('spo2','?')}%  |  "
                      f"Temp={packet.get('vitals',{}).get('temperature','?')}°C")

    except Exception as e:
        print(f"[HPIS] Erreur on_message : {e}")


def on_open(ws_obj):
    print(f"[HPIS] Connecté à {ESP32_IP}")
    print("[HPIS] Collecte en cours... Fermer la fenêtre pour arrêter et générer le rapport.")


def on_error(ws_obj, error):
    print(f"[HPIS] Erreur WebSocket : {error}")


def on_close(ws_obj, code, msg):
    print("[HPIS] Connexion WebSocket fermée.")


# ================= ARRÊT PROPRE =================
def shutdown():
    print("\n[HPIS] Arrêt de la session...")
    if ws_app:
        ws_app.close()
    generate_report()
    QtWidgets.QApplication.quit()


# Capture Ctrl+C dans le terminal
def signal_handler(sig, frame):
    shutdown()

signal.signal(signal.SIGINT, signal_handler)

# Fermeture via la croix de la fenêtre
app.aboutToQuit.connect(shutdown)


# ================= LANCEMENT WEBSOCKET =================
ws_app = websocket.WebSocketApp(
    ESP32_IP,
    on_message=on_message,
    on_open=on_open,
    on_error=on_error,
    on_close=on_close,
)

threading.Thread(target=ws_app.run_forever, daemon=True).start()

# ================= LANCEMENT GUI =================
app.exec()