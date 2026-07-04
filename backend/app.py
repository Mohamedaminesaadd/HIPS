import serial
import matplotlib.pyplot as plt
from collections import deque

# PORT ESP32
ser = serial.Serial('/dev/ttyACM0', 115200)

# buffer ECG
data = deque([0]*500, maxlen=500)

plt.ion()
fig, ax = plt.subplots()
line, = ax.plot(data)

ax.set_ylim(0, 4095)
ax.set_title("ECG Real Time")
ax.set_xlabel("Samples")
ax.set_ylabel("Amplitude")

while True:
    try:
        line_raw = ser.readline().decode().strip()

        # garder seulement valeurs numériques
        if line_raw.isdigit():
            val = int(line_raw)

            data.append(val)

            line.set_ydata(data)
            line.set_xdata(range(len(data)))

            plt.pause(0.001)

    except:
        pass