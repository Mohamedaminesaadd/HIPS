#include <Arduino.h>

#define ECG_PIN 34
#define LO_PLUS 26
#define LO_MINUS 27

void setup() {
    Serial.begin(115200);

    pinMode(LO_PLUS, INPUT);
    pinMode(LO_MINUS, INPUT);

    Serial.println("ECG START");
}

void loop() {

    if (digitalRead(LO_PLUS) || digitalRead(LO_MINUS)) {
        Serial.println(0);
    } else {
        int ecg = analogRead(ECG_PIN);
        Serial.println(ecg);
    }

    delay(4); // ~250 Hz
}