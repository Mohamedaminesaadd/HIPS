#include <Arduino.h>
#include <WiFi.h>
#include <ESPAsyncWebServer.h>

// =============================================
//  WIFI
// =============================================
const char* WIFI_SSID     = "Amine";
const char* WIFI_PASSWORD = "22222222";

// =============================================
//  PINS & CONSTANTES
// =============================================
#define ECG_PIN         34
#define LO_PLUS         26
#define LO_MINUS        27

#define ECG_SAMPLE_RATE     250
#define ECG_BUFFER_SIZE     250
#define SAMPLE_PERIOD_MS    4

#define JSON_BUF_SIZE       4096

// =============================================
//  SERVEUR WEB + WEBSOCKET
// =============================================
AsyncWebServer server(80);
AsyncWebSocket ws("/ws");

// =============================================
//  VARIABLES GLOBALES
// =============================================
uint16_t ecgBuffer[ECG_BUFFER_SIZE];
uint16_t sampleIndex = 0;
unsigned long lastSampleTime = 0;
unsigned long packetCounter = 0;

static char jsonBuf[JSON_BUF_SIZE];

// buffer pour grouper les échantillons ECG avant envoi
// (évite d'envoyer une trame WS à chaque échantillon = 250 trames/s)
#define ECG_CHUNK_SIZE 10
uint16_t ecgChunk[ECG_CHUNK_SIZE];
uint8_t ecgChunkIndex = 0;

// =============================================
//  FONCTIONS FAKE (simulation capteurs)
// =============================================
int getHeartRate() {
    return random(68, 82);
}

int getSpO2() {
    return random(97, 100);
}

float getTemperature() {
    return random(365, 372) / 10.0f;
}

int getBatteryLevel() {
    return random(75, 100);
}

float randomFloat(float minVal, float maxVal) {
    float r = (float)random(0, 10000) / 10000.0f;
    return minVal + r * (maxVal - minVal);
}

int getSignalQuality() {
    return random(92, 100);
}

int getNoiseLevel() {
    return random(0, 8);
}

// =============================================
//  LECTURE ECG
// =============================================
uint16_t readECG() {
    if (digitalRead(LO_PLUS) || digitalRead(LO_MINUS)) {
        return 0;   // électrodes décrochées
    }
    return analogRead(ECG_PIN);
}

// =============================================
//  ENVOI WEBSOCKET - FLUX ECG GROUPÉ
//  Format : ECG:v1,v2,v3,...,v10
// =============================================
void sendECGChunk() {
    if (ws.count() == 0) return; // personne connecté, on n'envoie pas pour rien

    char buf[128];
    int pos = 0;
    pos += snprintf(buf + pos, sizeof(buf) - pos, "ECG:");
    for (int i = 0; i < ECG_CHUNK_SIZE; i++) {
        pos += snprintf(buf + pos, sizeof(buf) - pos, "%u%s",
                         ecgChunk[i], (i < ECG_CHUNK_SIZE - 1) ? "," : "");
    }
    ws.textAll(buf, pos);
}

// =============================================
//  GESTION DU BUFFER (1 seconde de data)
// =============================================
void storeSample(uint16_t value) {
    ecgBuffer[sampleIndex] = value;
    sampleIndex++;
}

bool bufferIsFull() {
    return sampleIndex >= ECG_BUFFER_SIZE;
}

void resetBuffer() {
    sampleIndex = 0;
}

// =============================================
//  ENVOI WEBSOCKET - TRAME JSON COMPLÈTE (1s)
// =============================================
void sendJSONPacket() {
    if (ws.count() == 0) return;

    int pos = 0;
    bool leadOff = (digitalRead(LO_PLUS) || digitalRead(LO_MINUS));

    pos += snprintf(jsonBuf + pos, JSON_BUF_SIZE - pos,
        "JSON:{\"packet_version\":\"1.0\",\"packet\":%lu,\"timestamp_ms\":%lu,",
        packetCounter++, millis());

    pos += snprintf(jsonBuf + pos, JSON_BUF_SIZE - pos,
        "\"ecg\":{\"sample_rate\":250,\"lead_off\":%s,\"signal_quality\":%d,\"noise_level\":%d,\"samples\":[",
        leadOff ? "true" : "false", getSignalQuality(), getNoiseLevel());

    for (int i = 0; i < ECG_BUFFER_SIZE; i++) {
        pos += snprintf(jsonBuf + pos, JSON_BUF_SIZE - pos, "%u%s",
                         ecgBuffer[i], (i < ECG_BUFFER_SIZE - 1) ? "," : "");
    }
    pos += snprintf(jsonBuf + pos, JSON_BUF_SIZE - pos, "]},");

    // PPG simulé
    pos += snprintf(jsonBuf + pos, JSON_BUF_SIZE - pos,
        "\"ppg\":{\"red\":%d,\"ir\":%d},",
        random(50000, 52000), random(60000, 62000));

    // Vitals
    pos += snprintf(jsonBuf + pos, JSON_BUF_SIZE - pos,
        "\"vitals\":{\"heart_rate\":%d,\"spo2\":%d,\"temperature\":%.1f},",
        getHeartRate(), getSpO2(), getTemperature());

    // IMU simulée
    pos += snprintf(jsonBuf + pos, JSON_BUF_SIZE - pos,
        "\"imu\":{\"acc\":{\"x\":%.2f,\"y\":%.2f,\"z\":%.2f},\"gyro\":{\"x\":%.2f,\"y\":%.2f,\"z\":%.2f}},",
        randomFloat(-1, 1), randomFloat(-1, 1), randomFloat(9.3, 10.1),
        randomFloat(-2, 2), randomFloat(-2, 2), randomFloat(-2, 2));

    // Batterie
    pos += snprintf(jsonBuf + pos, JSON_BUF_SIZE - pos,
        "\"battery\":{\"level\":%d,\"voltage\":%.2f}}",
        getBatteryLevel(), randomFloat(3.7, 4.2));

    if (pos >= JSON_BUF_SIZE) {
        jsonBuf[JSON_BUF_SIZE - 1] = '\0';
        pos = JSON_BUF_SIZE - 1;
    }

    ws.textAll(jsonBuf, pos);
}

// =============================================
//  EVENEMENTS WEBSOCKET
// =============================================
void onWsEvent(AsyncWebSocket *server, AsyncWebSocketClient *client,
               AwsEventType type, void *arg, uint8_t *data, size_t len) {
    switch (type) {
        case WS_EVT_CONNECT:
            Serial.printf("[WS] Client #%u connecte depuis %s\n",
                          client->id(), client->remoteIP().toString().c_str());
            break;
        case WS_EVT_DISCONNECT:
            Serial.printf("[WS] Client #%u deconnecte\n", client->id());
            break;
        case WS_EVT_DATA:
            // on ne traite pas les messages entrants pour l'instant
            break;
        default:
            break;
    }
}

// =============================================
//  SETUP
// =============================================
void setup() {
    Serial.begin(115200);

    pinMode(LO_PLUS, INPUT);
    pinMode(LO_MINUS, INPUT);

    analogReadResolution(12);
    randomSeed(analogRead(35));

    // --- Connexion WiFi ---
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    Serial.print("Connexion WiFi");
    while (WiFi.status() != WL_CONNECTED) {
        delay(300);
        Serial.print(".");
    }
    Serial.println();
    Serial.print("Connecte ! IP : ");
    Serial.println(WiFi.localIP());

    // --- WebSocket ---
    ws.onEvent(onWsEvent);
    server.addHandler(&ws);

    // route de test optionnelle
    server.on("/", HTTP_GET, [](AsyncWebServerRequest *request) {
        request->send(200, "text/plain", "HPIS Wearable - WebSocket sur /ws");
    });

    server.begin();

    Serial.println("===============================");
    Serial.println("HPIS Wearable (WebSocket)");
    Serial.println("ECG Sampling : 250 Hz");
    Serial.println("Packet JSON  : 1 seconde");
    Serial.printf("WS URL       : ws://%s/ws\n", WiFi.localIP().toString().c_str());
    Serial.println("===============================");
}

// =============================================
//  LOOP PRINCIPAL
// =============================================
void loop() {
    // nettoie les clients WS deconnectes (recommande par la lib)
    ws.cleanupClients();

    unsigned long now = millis();

    if (now - lastSampleTime >= SAMPLE_PERIOD_MS) {
        lastSampleTime = now;

        uint16_t ecg = readECG();

        // 1. Regroupement + envoi WS du flux ECG (par paquets de 10)
        ecgChunk[ecgChunkIndex++] = ecg;
        if (ecgChunkIndex >= ECG_CHUNK_SIZE) {
            sendECGChunk();
            ecgChunkIndex = 0;
        }

        // 2. Stockage dans le buffer 1 seconde
        storeSample(ecg);

        // 3. Trame JSON complete toutes les secondes
        if (bufferIsFull()) {
            sendJSONPacket();
            resetBuffer();
        }
    }
}