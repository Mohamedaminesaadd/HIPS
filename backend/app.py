import websocket
import threading
from collections import deque

import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets

# ================= BUFFER ECG =================
buffer = deque([0]*500, maxlen=500)

# ================= GUI =================
app = QtWidgets.QApplication([])

win = pg.GraphicsLayoutWidget(show=True)
win.setWindowTitle("ECG Real-Time WebSocket")

plot = win.addPlot(title="ECG Signal")
curve = plot.plot()

plot.setYRange(0, 4095)

def update_plot():
    curve.setData(list(buffer))

timer = pg.QtCore.QTimer()
timer.timeout.connect(update_plot)
timer.start(20)

# ================= WEBSOCKET =================
ESP32_IP = "ws://10.42.0.71/ws"  # ⚠️ change IP

def on_message(ws, message):
    try:
        # message format: "ECG:123,124,125,..."
        if message.startswith("ECG:"):
            data = message[4:].split(",")

            for v in data:
                if v.isdigit():
                    buffer.append(int(v))

    except Exception as e:
        print("Error:", e)

def on_open(ws):
    print("Connected to ESP32")

def on_error(ws, error):
    print("WebSocket error:", error)

def on_close(ws, close_status_code, close_msg):
    print("Connection closed")

ws = websocket.WebSocketApp(
    ESP32_IP,
    on_message=on_message,
    on_open=on_open,
    on_error=on_error,
    on_close=on_close
)

# run websocket in background thread
threading.Thread(target=ws.run_forever, daemon=True).start()

# ================= START GUI =================
app.exec()